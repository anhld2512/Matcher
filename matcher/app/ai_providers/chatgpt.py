"""OpenAI ChatGPT AI Provider"""
import requests
import json
from typing import Dict, Any
from .base import AIProvider


class ChatGPTProvider(AIProvider):
    """OpenAI ChatGPT provider"""

    @property
    def name(self) -> str:
        return "chatgpt"

    def test_connection(self) -> bool:
        """Test OpenAI API connection"""
        try:
            api_key = self.config.get('api_key', '')
            if not api_key:
                return False

            url = "https://api.openai.com/v1/models"
            headers = {"Authorization": f"Bearer {api_key}"}
            response = requests.get(url, headers=headers, timeout=5)
            return response.status_code == 200
        except:
            return False

    async def evaluate(self, jd_text: str, cv_text: str) -> Dict[str, Any]:
        """Evaluate using ChatGPT"""
        api_key = self.config.get('api_key', '')
        model = self.config.get('model', 'gpt-3.5-turbo')

        if not api_key:
            return self._get_fallback_evaluation("API key not configured")

        # Truncate texts
        jd_truncated = jd_text[:4000] if len(jd_text) > 4000 else jd_text
        cv_truncated = cv_text[:6000] if len(cv_text) > 6000 else cv_text

        prompt = f"""You are an expert HR recruiter. Analyze the following CV against the Job Description and provide an evaluation.

JOB DESCRIPTION:
{jd_truncated}

CANDIDATE CV:
{cv_truncated}

Provide your evaluation in the following JSON format ONLY (no other text):
{{
    "score": <number from 1-10>,
    "strengths": "<3-5 key strengths of the candidate>",
    "weaknesses": "<2-3 areas where candidate doesn't match or could improve>",
    "justification": "<2-3 sentences explaining the score>",
    "recommendation": "<RECOMMEND, CONSIDER, or REJECT with brief reason>"
}}

Be objective and thorough. Consider: skills match, experience level, education fit, and overall alignment with role requirements."""

        url = "https://api.openai.com/v1/chat/completions"
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
                        {"role": "system", "content": "You are an expert HR recruiter."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=60
            )

            if response.status_code == 200:
                result = response.json()
                try:
                    text = result['choices'][0]['message']['content']
                    return self._parse_response(text)
                except (KeyError, IndexError):
                    return self._get_fallback_evaluation("Invalid response format")
            else:
                return self._get_fallback_evaluation(f"API error: {response.status_code}")

        except Exception as e:
            return self._get_fallback_evaluation(str(e))

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse ChatGPT response"""
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
            "strengths": "Unable to analyze - ChatGPT unavailable",
            "weaknesses": "Unable to analyze - ChatGPT unavailable",
            "justification": f"Automatic evaluation failed: {error_msg}",
            "recommendation": "CONSIDER",
            "error": error_msg
        }
