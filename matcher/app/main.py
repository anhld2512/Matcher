from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional  # Added imports
import shutil
import redis

from .schemas import JDCreate, JDUpdate, CVCreate, CVUpdate
from .utils import save_uploaded_file, extract_text
from .queue import get_queue, get_redis_connection
from .config import settings, update_settings
from .worker import process_evaluation
from .database import init_db, get_db, Evaluation, CVMetadata, AISettings
from .ai_providers import (
    GeminiProvider, ChatGPTProvider,
    DeepSeekProvider, HuggingFaceProvider, get_ai_provider
)

app = FastAPI(title="CV‑JD Matcher")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    """Initialize database tables on startup"""
    try:
        init_db()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"⚠️  Database initialization failed: {e}")
        print("Will retry on first request...")

# Base directories (relative to project root)
BASE_DIR = Path(__file__).parent.parent
JD_DIR = BASE_DIR / "jd"
CV_DIR = BASE_DIR / "cv"
REPORT_DIR = BASE_DIR / "reports"
FRONTEND_DIR = BASE_DIR / "frontend"

# Ensure directories exist
for d in (JD_DIR, CV_DIR, REPORT_DIR, FRONTEND_DIR):
    d.mkdir(parents=True, exist_ok=True)

# Root endpoint - serve index.html
@app.get("/")
def get_index():
    return FileResponse(str(FRONTEND_DIR / "index.html"))

# Serve other HTML pages
@app.get("/jd-management.html")
def get_jd_management():
    return FileResponse(str(FRONTEND_DIR / "jd-management.html"))

@app.get("/cv-management.html")
def get_cv_management():
    return FileResponse(str(FRONTEND_DIR / "cv-management.html"))

@app.get("/history.html")
def get_history():
    return FileResponse(str(FRONTEND_DIR / "history.html"))

@app.get("/report.html")
def get_report_page():
    return FileResponse(str(FRONTEND_DIR / "report.html"))

# Serve static frontend files (CSS, JS, images, etc)
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

# ---------- Settings Endpoints ----------
class RedisConfig(BaseModel):
    host: str
    port: int
    password: str = ""

@app.get("/settings")
def get_settings():
    # Check connection
    status = "disconnected"
    try:
        r = get_redis_connection()
        if r.ping():
            status = "connected"
    except Exception as e:
        status = f"error: {str(e)}"
        
    return {
        "redis_host": settings.redis_host,
        "redis_port": settings.redis_port,
        "redis_password_set": bool(settings.redis_password),
        "connection_status": status
    }

@app.post("/settings")
def set_settings(config: RedisConfig):
    update_settings(config.host, config.port, config.password)
    # Validate
    try:
        r = get_redis_connection()
        r.ping()
        return {"status": "updated", "connection": "ok"}
    except Exception as e:
        return {"status": "updated", "connection": "failed", "error": str(e)}

# ---------- JD Endpoints ----------
@app.get("/jds")
def list_jds(page: int = 1, limit: int = 10, search: str = "", db: Session = Depends(get_db)):
    """List JDs with pagination and search"""
    from .database import JDMetadata

    all_files = [p for p in JD_DIR.iterdir() if p.is_file() and p.suffix == '.docx']

    # Filter by search
    if search:
        all_files = [f for f in all_files if search.lower() in f.name.lower()]

    # Sort by modification time (newest first)
    all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Pagination
    total = len(all_files)
    start = (page - 1) * limit
    end = start + limit
    files = all_files[start:end]

    # Get metadata for each file
    items = []
    for f in files:
        meta = db.query(JDMetadata).filter(JDMetadata.filename == f.name).first()
        items.append({
            "name": f.name,
            "size": f.stat().st_size,
            "modified": f.stat().st_mtime,
            "category": meta.category if meta else None,
            "department": meta.department if meta else None,
            "tags": meta.tags if meta and meta.tags else []
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@app.post("/jds")
async def upload_jd(file: UploadFile = File(...), db: Session = Depends(get_db)):
    from .database import JDMetadata
    from datetime import datetime

    if not file.filename.lower().endswith('.docx'):
        raise HTTPException(status_code=400, detail="JD must be a .docx file")
    dest = save_uploaded_file(file, str(JD_DIR))
    filename = Path(dest).name

    # Create or update metadata
    jd_meta = db.query(JDMetadata).filter(JDMetadata.filename == filename).first()
    if not jd_meta:
        jd_meta = JDMetadata(
            filename=filename,
            upload_date=datetime.utcnow(),
            file_size=Path(dest).stat().st_size,
            usage_count=0
        )
        db.add(jd_meta)
        db.commit()

    return {"filename": filename}

@app.put("/jds/{name}")
async def update_jd(name: str, description: str = ""):
    if not (JD_DIR / name).exists():
        raise HTTPException(status_code=404, detail="JD not found")
    return {"name": name, "description": description}

@app.delete("/jds/{name}")
def delete_jd(name: str):
    target = JD_DIR / name
    if not target.exists():
        raise HTTPException(status_code=404, detail="JD not found")
    target.unlink()
    return {"deleted": name}

@app.post("/jds/bulk")
async def bulk_upload_jds(files: list[UploadFile] = File(...)):
    """Bulk upload JD files"""
    saved = []
    for f in files:
        if not f.filename.lower().endswith('.docx'):
            raise HTTPException(status_code=400, detail="All JDs must be .docx files")
        saved.append(save_uploaded_file(f, str(JD_DIR)))
    return {"uploaded": [Path(p).name for p in saved]}

@app.delete("/jds/bulk")
async def bulk_delete_jds(filenames: list[str]):
    """Bulk delete JD files"""
    deleted = []
    for name in filenames:
        target = JD_DIR / name
        if target.exists():
            target.unlink()
            deleted.append(name)
    return {"deleted": deleted}

# ---------- CV Endpoints ----------
@app.get("/cvs")
def list_cvs(page: int = 1, limit: int = 10, search: str = "", db: Session = Depends(get_db)):
    """List CVs with pagination and search"""
    all_files = [p for p in CV_DIR.iterdir() if p.is_file() and p.suffix in ['.pdf', '.docx']]

    # Filter by search
    if search:
        all_files = [f for f in all_files if search.lower() in f.name.lower()]

    # Sort by modification time (newest first)
    all_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

    # Pagination
    total = len(all_files)
    start = (page - 1) * limit
    end = start + limit
    files = all_files[start:end]

    # Get metadata for each file
    items = []
    for f in files:
        meta = db.query(CVMetadata).filter(CVMetadata.filename == f.name).first()
        items.append({
            "name": f.name,
            "size": f.stat().st_size,
            "type": f.suffix[1:].upper(),
            "modified": f.stat().st_mtime,
            "category": meta.category if meta else None,
            "department": meta.department if meta else None,
            "email": meta.email if meta else None,
            "phone": meta.phone if meta else None
        })

    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }

@app.post("/cvs")
async def upload_cv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    from datetime import datetime

    if not (file.filename.lower().endswith('.pdf') or file.filename.lower().endswith('.docx')):
        raise HTTPException(status_code=400, detail="CV must be .pdf or .docx")
    dest = save_uploaded_file(file, str(CV_DIR))
    filename = Path(dest).name

    # Create or update metadata
    cv_meta = db.query(CVMetadata).filter(CVMetadata.filename == filename).first()
    if not cv_meta:
        cv_meta = CVMetadata(
            filename=filename,
            upload_date=datetime.utcnow(),
            file_size=Path(dest).stat().st_size,
            file_type=Path(dest).suffix[1:].upper(),
            evaluation_count=0
        )
        db.add(cv_meta)
        db.commit()

    return {"filename": filename}

@app.put("/cvs/{name}")
async def update_cv(name: str, description: str = ""):
    if not (CV_DIR / name).exists():
        raise HTTPException(status_code=404, detail="CV not found")
    return {"name": name, "description": description}

@app.delete("/cvs/{name}")
def delete_cv(name: str):
    target = CV_DIR / name
    if not target.exists():
        raise HTTPException(status_code=404, detail="CV not found")
    target.unlink()
    return {"deleted": name}

@app.post("/cvs/bulk")
async def bulk_upload_cvs(files: list[UploadFile] = File(...)):
    """Bulk upload CV files"""
    saved = []
    for f in files:
        if not (f.filename.lower().endswith('.pdf') or f.filename.lower().endswith('.docx')):
            raise HTTPException(status_code=400, detail="All CVs must be .pdf or .docx")
        saved.append(save_uploaded_file(f, str(CV_DIR)))
    return {"uploaded": [Path(p).name for p in saved]}

@app.delete("/cvs/bulk")
async def bulk_delete_cvs(filenames: list[str]):
    """Bulk delete CV files"""
    deleted = []
    for name in filenames:
        target = CV_DIR / name
        if target.exists():
            target.unlink()
            deleted.append(name)
    return {"deleted": deleted}

# ---------- Evaluation Endpoint ----------
class EvalRequest(BaseModel):
    jd_name: str
    cv_names: list[str]

MAX_CVS_PER_EVALUATION = 3

@app.post("/evaluate")
async def evaluate(payload: EvalRequest):
    # Validate inputs
    if not payload.jd_name:
        raise HTTPException(status_code=400, detail="JD name is required")

    if not payload.cv_names or len(payload.cv_names) == 0:
        raise HTTPException(status_code=400, detail="At least one CV is required")

    if len(payload.cv_names) > MAX_CVS_PER_EVALUATION:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum {MAX_CVS_PER_EVALUATION} CVs allowed per evaluation"
        )

    # Check JD exists
    if not (JD_DIR / payload.jd_name).exists():
        raise HTTPException(status_code=404, detail=f"JD '{payload.jd_name}' not found")

    # Check all CVs exist
    for cv_name in payload.cv_names:
        if not (CV_DIR / cv_name).exists():
            raise HTTPException(status_code=404, detail=f"CV '{cv_name}' not found")

    try:
        q = get_queue()
        job = q.enqueue(
            process_evaluation,
            payload.jd_name,
            payload.cv_names,
            job_timeout=600  # 10 minutes timeout for large files
        )
        return {"task_id": job.id, "status": "queued"}
    except redis.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis connection failed. Please check settings.")

@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    try:
        q = get_queue()
        job = q.fetch_job(task_id)
        if not job:
            raise HTTPException(status_code=404, detail="Task not found")
        
        return {
            "task_id": task_id,
            "status": job.get_status(),
            "result": job.result,
            "error": job.exc_info
        }
    except redis.exceptions.ConnectionError:
        raise HTTPException(status_code=503, detail="Redis connection failed")

# ---------- Report serving ----------
@app.get("/report/{filename}")
def get_report(filename: str):
    report_path = REPORT_DIR / filename
    if not report_path.exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(str(report_path))
# Add this to the end of app/main.py after the report serving section

# ---------- Evaluation History Endpoints ----------
@app.get("/evaluations")
def list_evaluations(
    page: int = 1,
    limit: int = 10,
    jd: str = "",
    cv: str = "",
    score_min: float = 0,
    score_max: float = 10,
    db: Session = Depends(get_db)
):
    """List all evaluations with filters and pagination"""
    query = db.query(Evaluation)
    
    # Apply filters
    if jd:
        query = query.filter(Evaluation.jd_name.ilike(f"%{jd}%"))
    if cv:
        query = query.filter(Evaluation.cv_name.ilike(f"%{cv}%"))
    if score_min > 0 or score_max < 10:
        query = query.filter(Evaluation.score >= score_min, Evaluation.score <= score_max)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    evaluations = query.order_by(Evaluation.created_at.desc()).offset((page - 1) * limit).limit(limit).all()
    
    # Format results
    items = [{
        "id": e.id,
        "jd_name": e.jd_name,
        "cv_name": e.cv_name,
        "score": e.score,
        "status": e.status,
        "report_file": e.report_file,
        "created_at": e.created_at.isoformat() if e.created_at else None,
        "completed_at": e.completed_at.isoformat() if e.completed_at else None,
        "error_message": e.error_message
    } for e in evaluations]
    
    # Calculate stats
    all_completed = db.query(Evaluation).filter(Evaluation.status == "completed").all()
    total_evals = len(all_completed)
    avg_score = sum(e.score for e in all_completed if e.score) / total_evals if total_evals > 0 else 0
    excellent_count = sum(1 for e in all_completed if e.score and e.score >= 8)
    
    # Today's count
    from datetime import datetime, timedelta
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = db.query(Evaluation).filter(
        Evaluation.created_at >= today_start,
        Evaluation.status == "completed"
    ).count()
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit,
        "stats": {
            "total_evaluations": total_evals,
            "avg_score": round(avg_score, 1),
            "excellent_count": excellent_count,
            "today_count": today_count
        }
    }


@app.get("/evaluations/{evaluation_id}")
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db)):
    """Get single evaluation detail"""
    evaluation = db.query(Evaluation).filter(Evaluation.id == evaluation_id).first()
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    return {
        "id": evaluation.id,
        "jd_name": evaluation.jd_name,
        "cv_name": evaluation.cv_name,
        "score": evaluation.score,
        "status": evaluation.status,
        "report_file": evaluation.report_file,
        "details": evaluation.details, # Return full JSON analysis
        "task_id": evaluation.task_id,
        "created_at": evaluation.created_at.isoformat() if evaluation.created_at else None,
        "completed_at": evaluation.completed_at.isoformat() if evaluation.completed_at else None,
        "error_message": evaluation.error_message
    }


# ---------- AI Provider Settings Endpoints ----------
class AISettingsCreate(BaseModel):
    provider: str
    model_name: str
    api_key: str = ""
    host: str = "localhost"
    port: int = 11434

@app.get("/ai-settings")
def get_ai_settings(db: Session = Depends(get_db)):
    """Get current AI provider settings"""
    settings = db.query(AISettings).filter(AISettings.is_active == 1).first()
    if not settings:
        return {
            "provider": "ollama",
            "model_name": "llama2",
            "host": "ollama",
            "port": 11434,
            "configured": False
        }
    return {
        "id": settings.id,
        "provider": settings.provider,
        "model_name": settings.model_name,
        "api_key": settings.api_key,  # Include actual key for test connection
        "api_key_set": bool(settings.api_key),
        "host": settings.host,
        "port": settings.port,
        "configured": True,
        "created_at": settings.created_at.isoformat() if settings.created_at else None,
        "updated_at": settings.updated_at.isoformat() if settings.updated_at else None
    }

@app.post("/ai-settings")
def save_ai_settings(config: AISettingsCreate, db: Session = Depends(get_db)):
    """Create or update AI provider settings"""
    from datetime import datetime

    # Deactivate all existing settings
    db.query(AISettings).update({"is_active": 0})

    # Create new settings
    new_settings = AISettings(
        provider=config.provider,
        model_name=config.model_name,
        api_key=config.api_key if config.api_key else None,
        host=config.host if config.provider == "ollama" else None,
        port=config.port if config.provider == "ollama" else None,
        is_active=1,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.add(new_settings)
    db.commit()
    db.refresh(new_settings)

    return {
        "id": new_settings.id,
        "provider": new_settings.provider,
        "model_name": new_settings.model_name,
        "status": "saved"
    }

@app.get("/ai-providers")
def list_ai_providers():
    """List available AI providers"""
    return {
        "providers": [
            {
                "id": "ollama",
                "name": "Ollama",
                "description": "Local AI models via Ollama",
                "requires_api_key": False,
                "requires_host": True
            },
            # {
            #     "id": "gemini",
            #     "name": "Google Gemini",
            #     "description": "Google's Gemini AI models",
            #     "requires_api_key": True,
            #     "requires_host": False
            # },
            # {
            #     "id": "chatgpt",
            #     "name": "ChatGPT (OpenAI)",
            #     "description": "OpenAI's GPT models",
            #     "requires_api_key": True,
            #     "requires_host": False
            # },
            # {
            #     "id": "deepseek",
            #     "name": "DeepSeek",
            #     "description": "DeepSeek AI models",
            #     "requires_api_key": True,
            #     "requires_host": False
            # },
            {
                "id": "huggingface",
                "name": "HuggingFace",
                "description": "HuggingFace Inference API",
                "requires_api_key": True,
                "requires_host": False
            }
        ]
    }

@app.get("/ai-models/{provider}")
def list_ai_models(provider: str):
    """List available models for a provider"""
    if provider == "gemini":
        return {"models": ["gemini-1.5-pro", "gemini-1.5-flash", "gemini-pro"]}
    elif provider == "chatgpt":
        return {"models": ["gpt-4", "gpt-4-turbo", "gpt-3.5-turbo"]}
    elif provider == "deepseek":
        return {"models": ["deepseek-chat", "deepseek-coder"]}
    elif provider == "huggingface":
        return {"models": [
            "deepseek-ai/DeepSeek-V3.2-Exp:novita",
            "mistralai/Mistral-7B-Instruct-v0.3",
            "meta-llama/Llama-3.2-3B-Instruct"
        ]}
    else:
        raise HTTPException(status_code=400, detail="Unknown provider")

@app.get("/ai-settings/test")
def test_ai_connection(db: Session = Depends(get_db)):
    """Test current AI provider connection"""
    settings = db.query(AISettings).filter(AISettings.is_active == 1).first()
    if not settings:
        return {
            "status": "not_configured",
            "message": "No AI provider configured. Please configure Gemini or HuggingFace in Settings."
        }

    try:
        # Build config based on provider
        config = {"model": settings.model_name}

        if settings.provider in ["gemini", "chatgpt", "deepseek", "huggingface"]:
            config["api_key"] = settings.api_key or ""

        # Get provider instance and test connection
        provider = get_ai_provider(settings.provider, config)
        connected = provider.test_connection()

        return {
            "status": "connected" if connected else "disconnected",
            "provider": settings.provider,
            "model": settings.model_name
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to test connection: {str(e)}"
        }

class TestAIRequest(BaseModel):
    provider: str
    config: dict

@app.post("/test-ai")
async def test_ai_with_config(request: TestAIRequest):
    """Test AI provider connection with provided config (without saving)"""
    try:
        provider_instance = get_ai_provider(request.provider, request.config)
        connected = provider_instance.test_connection()
        
        return {
            "connected": connected,
            "provider": request.provider,
            "message": "Connection successful" if connected else "Connection failed"
        }
    except Exception as e:
        return {
            "connected": False,
            "message": str(e)
        }

# ---------- New Endpoints for Redesign ----------

@app.get("/cvs/{cv_name}/evaluations")
def get_cv_evaluations(cv_name: str, db: Session = Depends(get_db)):
    """Get all evaluations for a specific CV"""
    evaluations = db.query(Evaluation).filter(
        Evaluation.cv_name == cv_name,
        Evaluation.status == "completed"
    ).order_by(Evaluation.created_at.desc()).all()
    
    if not evaluations:
        return {
            "cv_name": cv_name,
            "total": 0,
            "best_score": None,
            "average_score": None,
            "evaluations": []
        }
    
    scores = [e.score for e in evaluations if e.score is not None]
    
    return {
        "cv_name": cv_name,
        "total": len(evaluations),
        "best_score": max(scores) if scores else None,
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
        "evaluations": [
            {
                "id": e.id,
                "jd_name": e.jd_name,
                "score": e.score,
                "created_at": e.created_at.isoformat() if e.created_at else None,
                "jd_category": e.jd_category,
                "jd_department": e.jd_department
            }
            for e in evaluations
        ]
    }

@app.get("/evaluations/grouped")
def get_grouped_evaluations(
    group_by: str = "jd",  # jd, cv, date, category, department
    category: str = None,
    department: str = None,
    db: Session = Depends(get_db)
):
    """Get evaluations grouped by specified field"""
    from sqlalchemy import func
    from datetime import datetime
    
    query = db.query(Evaluation).filter(Evaluation.status == "completed")
    
    # Apply filters
    if category:
        query = query.filter(Evaluation.jd_category == category)
    if department:
        query = query.filter(Evaluation.jd_department == department)
    
    evaluations = query.all()
    
    # Group results
    grouped = {}
    for eval in evaluations:
        if group_by == "jd":
            key = eval.jd_name
        elif group_by == "cv":
            key = eval.cv_name
        elif group_by == "category":
            key = eval.jd_category or "Uncategorized"
        elif group_by == "department":
            key = eval.jd_department or "Unassigned"
        elif group_by == "date":
            key = eval.created_at.date().isoformat() if eval.created_at else "Unknown"
        else:
            key = "All"
        
        if key not in grouped:
            grouped[key] = []
        
        grouped[key].append({
            "id": eval.id,
            "jd_name": eval.jd_name,
            "cv_name": eval.cv_name,
            "score": eval.score,
            "created_at": eval.created_at.isoformat() if eval.created_at else None
        })
    
    return {
        "group_by": group_by,
        "groups": grouped
    }

class JDMetadataUpdate(BaseModel):
    category: str = None
    department: str = None
    tags: List[str] = None

@app.patch("/jds/{jd_name}/metadata")
def update_jd_metadata(jd_name: str, data: JDMetadataUpdate, db: Session = Depends(get_db)):
    """Update JD metadata (category, department, tags)"""
    from .database import JDMetadata

    jd_meta = db.query(JDMetadata).filter(JDMetadata.filename == jd_name).first()
    if not jd_meta:
        from datetime import datetime

        jd_path = JD_DIR / jd_name
        if not jd_path.exists():
            raise HTTPException(status_code=404, detail="JD not found")

        jd_meta = JDMetadata(
            filename=jd_name,
            upload_date=datetime.utcnow(),
            file_size=jd_path.stat().st_size,
            usage_count=0
        )
        db.add(jd_meta)
        db.commit()

    if data.category is not None:
        jd_meta.category = data.category
    if data.department is not None:
        jd_meta.department = data.department
    if data.tags is not None:
        jd_meta.tags = data.tags

    db.commit()

    return {
        "filename": jd_meta.filename,
        "category": jd_meta.category,
        "department": jd_meta.department,
        "tags": jd_meta.tags
    }

class CVMetadataUpdate(BaseModel):
    category: str = None
    department: str = None
    email: str = None
    phone: str = None

@app.patch("/cvs/{cv_name}/metadata")
def update_cv_metadata(cv_name: str, data: CVMetadataUpdate, db: Session = Depends(get_db)):
    """Update CV metadata (category, department, email, phone)"""
    cv_meta = db.query(CVMetadata).filter(CVMetadata.filename == cv_name).first()
    if not cv_meta:
        raise HTTPException(status_code=404, detail="CV not found")

    if data.category is not None:
        cv_meta.category = data.category
    if data.department is not None:
        cv_meta.department = data.department
    if data.email is not None:
        cv_meta.email = data.email
    if data.phone is not None:
        cv_meta.phone = data.phone

    db.commit()

    return {
        "filename": cv_meta.filename,
        "category": cv_meta.category,
        "department": cv_meta.department,
        "email": cv_meta.email,
        "phone": cv_meta.phone
    }

@app.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """Get list of unique categories"""
    from sqlalchemy import distinct
    from .database import JDMetadata
    
    categories = db.query(distinct(JDMetadata.category)).filter(
        JDMetadata.category.isnot(None)
    ).all()
    
    return {"categories": [c[0] for c in categories if c[0]]}

@app.get("/departments")
def get_departments(db: Session = Depends(get_db)):
    """Get list of unique departments"""
    from sqlalchemy import distinct
    from .database import JDMetadata
    
    departments = db.query(distinct(JDMetadata.department)).filter(
        JDMetadata.department.isnot(None)
    ).all()
    
    return {"departments": [d[0] for d in departments if d[0]]}
