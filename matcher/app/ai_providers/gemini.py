"""Google Gemini AI Provider"""
import requests
import json
from typing import Dict, Any
from .base import AIProvider


class GeminiProvider(AIProvider):
    """Google Gemini AI provider"""

    @property
    def name(self) -> str:
        return "gemini"

    def test_connection(self) -> bool:
        """Test Gemini API connection"""
        try:
            api_key = self.config.get('api_key', '')
            if not api_key:
                return False

            url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        except:
            return False

    async def evaluate(self, jd_text: str, cv_text: str, criteria: list[str] = None) -> Dict[str, Any]:
        """Evaluate using Gemini"""
        api_key = self.config.get('api_key', '')
        model = self.config.get('model', 'gemini-1.5-flash')

        if not api_key:
            return self._get_fallback_evaluation("API key not configured")

        # Truncate texts
        jd_truncated = jd_text[:4000] if len(jd_text) > 4000 else jd_text
        cv_truncated = cv_text[:6000] if len(cv_text) > 6000 else cv_text
        
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

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

        try:
            response = requests.post(
                url,
                json={
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": 0.3,
                        "maxOutputTokens": 1000
                    }
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                # Extract text from Gemini response
                try:
                    text = result['candidates'][0]['content']['parts'][0]['text']
                    return self._parse_response(text)
                except (KeyError, IndexError):
                    return self._get_fallback_evaluation("Invalid response format")
            else:
                return self._get_fallback_evaluation(f"API error: {response.status_code}")

        except Exception as e:
            return self._get_fallback_evaluation(str(e))

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse Gemini response"""
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
            "strengths": "Unable to analyze - Gemini unavailable",
            "weaknesses": "Unable to analyze - Gemini unavailable",
            "justification": f"Automatic evaluation failed: {error_msg}",
            "recommendation": "CONSIDER",
            "error": error_msg
        }
