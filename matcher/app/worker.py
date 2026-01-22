import os
import json
import time
import requests
import asyncio
from datetime import datetime
from .utils import extract_text
from .config import settings
from .database import SessionLocal, Evaluation, CVMetadata, JDMetadata
from .ai_providers import load_active_provider_from_db
from pathlib import Path
from rq import get_current_job

BASE_DIR = Path(__file__).parent.parent
JD_DIR = BASE_DIR / "jd"
CV_DIR = BASE_DIR / "cv"
REPORT_DIR = BASE_DIR / "reports"


def call_ai_provider(jd_text: str, cv_text: str, criteria: list[str] = None, max_retries: int = 3) -> dict:
    """
    Call configured AI provider to evaluate CV against JD.
    Returns structured evaluation with score, strengths, weaknesses.
    """
    for attempt in range(max_retries):
        try:
            # Load active AI provider from database
            provider = load_active_provider_from_db()
            
            # FORCE FIX FOR DOCKER:
            # If provider is Ollama AND we are in Docker (host is usually 'ollama' or we can detect env),
            # force host to 'ollama' to ensure internal networking works, overriding any user 'localhost' setting.
            if provider.name == 'ollama':
                # Check if we can resolve 'ollama' hostname
                import socket
                try:
                    socket.gethostbyname('ollama')
                    # If successful, we are likely in docker-compose and 'ollama' service exists
                    provider.config['host'] = 'ollama'
                    print("DEBUG: Forced Ollama host to 'ollama' for Docker networking")
                except:
                    # Fallback to host.docker.internal if ollama service not found
                    try:
                        socket.gethostbyname('host.docker.internal')
                        provider.config['host'] = 'host.docker.internal'
                        print("DEBUG: Forced Ollama host to 'host.docker.internal'")
                    except:
                        pass # Keep original config if neither works

            # Run async evaluate method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                evaluation = loop.run_until_complete(provider.evaluate(jd_text, cv_text, criteria=criteria))

                # Check if evaluation has error
                if "error" not in evaluation or evaluation["error"] is None:
                    return evaluation

                # If error, retry
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return evaluation

            finally:
                loop.close()

        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(3)
                continue
            return get_fallback_evaluation(f"Error: {str(e)}")

    return get_fallback_evaluation("Max retries exceeded")


def get_fallback_evaluation(error_msg: str) -> dict:
    """Return a fallback evaluation when AI provider fails."""
    return {
        "score": 5,
        "strengths": "Unable to analyze - AI provider unavailable",
        "weaknesses": "Unable to analyze - AI provider unavailable",
        "justification": f"Automatic evaluation failed: {error_msg}. Please review manually.",
        "recommendation": "CONSIDER",
        "error": error_msg
    }


def process_evaluation(jd_name: str, cv_names: list[str]) -> dict:
    """
    Background task to process the evaluation.
    1. Extract text from JD and CVs
    2. Call Ollama for each CV
    3. Generate and save reports
    4. Save results to PostgreSQL
    5. Return results
    """
    
    # Get current job for task_id
    job = get_current_job()
    task_id = job.id if job else None
    
    # Database session
    db = SessionLocal()
    
    try:
        # Ensure directories exist
        REPORT_DIR.mkdir(parents=True, exist_ok=True)

        jd_path = JD_DIR / jd_name
        if not jd_path.exists():
            return {"status": "error", "error": f"JD {jd_name} not found"}

        # Extract JD text
        try:
            jd_text = extract_text(str(jd_path))
            if not jd_text.strip():
                return {"status": "error", "error": "JD file is empty or unreadable"}
        except Exception as e:
            return {"status": "error", "error": f"Failed to extract JD text: {str(e)}"}

        # Fetch JD Metadata to get Tags/Criteria
        jd_meta = db.query(JDMetadata).filter(JDMetadata.filename == jd_name).first()
        criteria = jd_meta.tags if jd_meta and jd_meta.tags else []

        results = []

        for index, cv_name in enumerate(cv_names):
            cv_path = CV_DIR / cv_name
            
            # Generate unique DB task_id for this specific CV in the batch
            # RQ Job ID is unique per batch, so we append index to make it unique per CV in DB
            db_task_id = f"{task_id}_{index}" if task_id else f"manual_{int(time.time())}_{index}"

            # Check for existing evaluation first (Api might have created it)
            evaluation = db.query(Evaluation).filter(
                Evaluation.task_id == db_task_id,
                Evaluation.cv_name == cv_name
            ).first()

            if not evaluation:
                # Create evaluation record in DB if likely transient or old pending logic
                evaluation = Evaluation(
                    jd_name=jd_name,
                    cv_name=cv_name,
                    status="processing",
                    task_id=db_task_id,
                    created_at=datetime.utcnow()
                )
                db.add(evaluation)
            else:
                # Update status
                evaluation.status = "processing"
            
            db.commit()
            
            if not cv_path.exists():
                evaluation.status = "failed"
                evaluation.error_message = "CV not found"
                evaluation.completed_at = datetime.utcnow()
                db.commit()
                
                results.append({
                    "cv": cv_name,
                    "error": "CV not found",
                    "status": "failed"
                })
                continue

            # Extract CV text
            try:
                cv_text = extract_text(str(cv_path))
                if not cv_text.strip():
                    evaluation.status = "failed"
                    evaluation.error_message = "CV file is empty or unreadable"
                    evaluation.completed_at = datetime.utcnow()
                    db.commit()
                    
                    results.append({
                        "cv": cv_name,
                        "error": "CV file is empty or unreadable",
                        "status": "failed"
                    })
                    continue
            except Exception as e:
                evaluation.status = "failed"
                evaluation.error_message = f"Extraction failed: {str(e)}"
                evaluation.completed_at = datetime.utcnow()
                db.commit()
                
                results.append({
                    "cv": cv_name,
                    "error": f"Extraction failed: {str(e)}",
                    "status": "failed"
                })
                continue

            # Update status to processing
            evaluation.status = "processing"
            db.commit()

            # Call AI provider for evaluation
            ai_evaluation = call_ai_provider(jd_text, cv_text, criteria=criteria)

            # Extract results
            score = ai_evaluation.get("score", 5)
            strengths = ai_evaluation.get("strengths", "N/A")
            weaknesses = ai_evaluation.get("weaknesses", "N/A")
            justification = ai_evaluation.get("justification", "N/A")
            recommendation = ai_evaluation.get("recommendation", "CONSIDER")
            error_note = ai_evaluation.get("error", "")

            # Prepare JSON data for DB
            json_data = {
                "jd_name": jd_name,
                "cv_name": cv_name,
                "score": score,
                "strengths": strengths,
                "weaknesses": weaknesses,
                "justification": justification,
                "recommendation": recommendation,
                "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "provider_error": error_note
            }
            
            # Update evaluation in DB
            evaluation.score = float(score)
            evaluation.status = "completed"
            evaluation.details = json_data  # Save to new JSON column
            evaluation.completed_at = datetime.utcnow()
            if error_note:
                evaluation.error_message = error_note
            db.commit()
            
            # Update CV metadata
            cv_meta = db.query(CVMetadata).filter(CVMetadata.filename == cv_name).first()
            if cv_meta:
                cv_meta.last_evaluated_at = datetime.utcnow()
                cv_meta.evaluation_count += 1
            else:
                cv_meta = CVMetadata(
                    filename=cv_name,
                    file_size=cv_path.stat().st_size,
                    file_type=cv_path.suffix[1:].upper(),
                    last_evaluated_at=datetime.utcnow(),
                    evaluation_count=1
                )
                db.add(cv_meta)
            db.commit()

            results.append({
                "cv": cv_name,
                "score": score,
                "recommendation": recommendation,
                "status": "completed",
                "details": json_data,
                "evaluation_id": evaluation.id
            })
        
        # Update JD metadata
        jd_meta = db.query(JDMetadata).filter(JDMetadata.filename == jd_name).first()
        if jd_meta:
            jd_meta.usage_count += 1
        else:
            jd_meta = JDMetadata(
                filename=jd_name,
                file_size=jd_path.stat().st_size,
                usage_count=1
            )
            db.add(jd_meta)
        db.commit()

        return {
            "status": "finished",
            "jd": jd_name,
            "total_cvs": len(cv_names),
            "results": results
        }
    
    finally:
        db.close()
