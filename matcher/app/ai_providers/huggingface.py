"""HuggingFace AI Provider"""
import requests
import json
from typing import Dict, Any
from .base import AIProvider


class HuggingFaceProvider(AIProvider):
    """HuggingFace Inference API provider"""

    @property
    def name(self) -> str:
        return "huggingface"

    def test_connection(self) -> bool:
        """Test HuggingFace API connection"""
        try:
            api_key = self.config.get('api_key', '')
            if not api_key:
                return False

            # Test with OpenAI-compatible chat completions endpoint
            model = self.config.get('model', 'mistralai/Mistral-7B-Instruct-v0.3')
            url = "https://router.huggingface.co/v1/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": "Hi"}],
                "max_tokens": 5
            }
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"HuggingFace test connection error: {e}")
            return False

    async def evaluate(self, jd_text: str, cv_text: str, criteria: list[str] = None) -> Dict[str, Any]:
        """Evaluate using HuggingFace OpenAI-compatible API"""
        api_key = self.config.get('api_key', '')
        model = self.config.get('model', 'mistralai/Mistral-7B-Instruct-v0.3')

        if not api_key:
            return self._get_fallback_evaluation("API key not configured")

        # Truncate texts
        jd_truncated = jd_text[:3000] if len(jd_text) > 3000 else jd_text
        cv_truncated = cv_text[:4000] if len(cv_text) > 4000 else cv_text
        
        # Build Criteria Text
        criteria_text = ""
        if criteria and len(criteria) > 0:
            tags_str = "\n".join([f"- {t}" for t in criteria])
            criteria_text = f"\nKEY CRITERIA / TAGS (MUST HAVE):\n{tags_str}\n\nIMPORTANT: Use these tags to filter candidates. If they miss critical tags, penalize the score."

        prompt = f"""You are a strict technical recruiter. Analyze the CV against the JD.

JOB DESCRIPTION:
{jd_truncated}

{criteria_text}

CANDIDATE CV:
{cv_truncated}

EVALUATION RULES:
1. If the candidate's core technology stack (e.g., Java vs Python, React vs Angular) does NOT match the JD, the 'technical_skills_score' MUST be between 0 and 2.
2. If the candidate lacks the required years of experience, 'experience_score' MUST be between 0 and 4.
3. If the candidate is irrelevant (e.g., Sales apply for Dev), the 'score' (Overall) MUST be between 0 and 2.
4. Do NOT give high scores (4-10) for "potential" if the hard skills are missing. Be strict.

Provide output in this JSON format ONLY:
{{
    "score": <number 0-10, overall fit>,
    "technical_skills_score": <number 0-10>,
    "experience_score": <number 0-10>,
    "culture_fit_score": <number 0-10>,
    "soft_skills_score": <number 0-10>,
    "strengths": "<3-5 key strengths>",
    "weaknesses": "<critical missing skills or mismatches>",
    "justification": "<Explain WHY the score is low/high. Check tech stack match.>",
    "recommendation": "<RECOMMEND / CONSIDER / REJECT>"
}}"""

        # Use OpenAI-compatible endpoint
        url = "https://router.huggingface.co/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json={
                    "model": model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                try:
                    content = result['choices'][0]['message']['content']
                    return self._parse_response(content)
                except (KeyError, IndexError) as e:
                    return self._get_fallback_evaluation(f"Invalid response format: {str(e)}")
            else:
                return self._get_fallback_evaluation(f"API error ({response.status_code}): {response.text}")

        except Exception as e:
            return self._get_fallback_evaluation(str(e))

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse HuggingFace response"""
        try:
            # Try direct JSON parse
            return json.loads(response_text)
        except:
            pass

        # Try to find JSON in response
        try:
            start = response_text.find('{')
            end = response_text.rfind('}') + 1
            if start != -1 and end > start:
                return json.loads(response_text[start:end])
        except:
            pass

        return self._get_fallback_evaluation("Failed to parse response")

    def _get_fallback_evaluation(self, error_msg: str) -> Dict[str, Any]:
        """Return fallback evaluation"""
        return {
            "score": 5,
            "strengths": "Unable to analyze - HuggingFace unavailable",
            "weaknesses": "Unable to analyze - HuggingFace unavailable",
            "justification": f"Automatic evaluation failed: {error_msg}",
            "recommendation": "CONSIDER",
            "error": error_msg
        }
