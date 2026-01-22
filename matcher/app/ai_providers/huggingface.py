"""HuggingFace AI Provider using OpenAI Client"""
import json
from typing import Dict, Any
from openai import OpenAI
from .base import AIProvider


class HuggingFaceProvider(AIProvider):
    """HuggingFace Inference API provider using OpenAI-compatible client"""

    @property
    def name(self) -> str:
        return "huggingface"

    def test_connection(self) -> bool:
        """Test HuggingFace API connection"""
        try:
            api_key = self.config.get('api_key', '')
            if not api_key:
                return False

            client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=api_key
            )
            
            model = self.config.get('model', 'deepseek-ai/DeepSeek-V3.2-Exp:novita')
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5
            )
            return True
        except Exception as e:
            print(f"HuggingFace test connection error: {e}")
            return False

    async def evaluate(self, jd_text: str, cv_text: str, criteria: list[str] = None) -> Dict[str, Any]:
        """Evaluate using HuggingFace via OpenAI client"""
        api_key = self.config.get('api_key', '')
        model = self.config.get('model', 'deepseek-ai/DeepSeek-V3.2-Exp:novita')

        if not api_key:
            return self._get_fallback_evaluation("API key not configured")

        # Truncate texts
        jd_truncated = jd_text[:3000] if len(jd_text) > 3000 else jd_text
        cv_truncated = cv_text[:4000] if len(cv_text) > 4000 else cv_text
        
        # Build Criteria Text
        criteria_text = ""
        if criteria and len(criteria) > 0:
            tags_str = "\n".join([f"- {t}" for t in criteria])
            criteria_text = f"\n🎯 KEY EVALUATION CRITERIA:\n{tags_str}\n\nPrioritize candidates who meet these requirements."

        prompt = f"""You are a SUPPORTIVE recruiter looking for POTENTIAL in candidates. Evaluate this CV holistically.

JOB DESCRIPTION:
{jd_truncated}

{criteria_text}

CANDIDATE CV:
{cv_truncated}

SCORING APPROACH - Be GENEROUS and consider ALL factors:

📊 OVERALL SCORE (0-10) - Consider the WHOLE picture:
- 8-10: Strong candidate - has most required skills OR strong transferable skills + good attitude
- 6-7: Good potential - may lack some requirements but shows promise and learning ability
- 4-5: Worth considering - has some relevant background, trainable
- 2-3: Significant gaps - but might fit a junior/entry role
- 0-1: Completely unrelated field

🔧 TECHNICAL SKILLS (0-10) - Be generous with transferable skills:
- Has required tech stack: 8-10
- Has related/similar tech: 6-8
- Has programming background but different stack: 5-7
- Some technical exposure: 4-6

💼 WORK EXPERIENCE (0-10) - Value ALL experience:
- Relevant industry experience: 8-10
- Related field experience: 6-8
- Any professional experience: 5-7
- Fresh graduate with projects: 4-6

🤝 CULTURAL FIT (0-10) - Look for positive indicators:
- Shows teamwork, communication, growth mindset: 7-10
- Basic professional demeanor: 5-7

💡 SOFT SKILLS (0-10) - Consider any evidence of:
- Leadership, initiative, problem-solving, learning: 6-10
- Communication, collaboration: 5-8

⚠️ IMPORTANT RULES:
1. START with 6/10 as baseline for anyone with relevant experience
2. Add points for strengths, only subtract for major gaps
3. Consider POTENTIAL, not just current skills
4. A developer with 2 years can still score 7+ if skills align

Return JSON only:
{{
    "score": <0-10>,
    "technical_skills_score": <0-10>,
    "experience_score": <0-10>,
    "culture_fit_score": <0-10>,
    "soft_skills_score": <0-10>,
    "strengths": "<what this candidate brings to the table>",
    "weaknesses": "<gaps that can be addressed with training>",
    "justification": "<why this score - focus on positives>",
    "recommendation": "<RECOMMEND/CONSIDER/REJECT>"
}}"""

        try:
            client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=api_key
            )
            
            print(f"[HuggingFace] Evaluating CV ({len(cv_text)} chars) with model: {model}")
            
            completion = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500
            )
            
            content = completion.choices[0].message.content
            print(f"[HuggingFace] Response received, parsing...")
            
            parsed = self._parse_response(content)
            print(f"[HuggingFace] Score: {parsed.get('score', 'N/A')}")
            return parsed
            
        except Exception as e:
            print(f"[HuggingFace] Error: {str(e)}")
            return self._get_fallback_evaluation(str(e))

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse response to JSON"""
        try:
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
        """Return fallback evaluation with error info"""
        return {
            "score": 0,
            "technical_skills_score": 0,
            "experience_score": 0,
            "culture_fit_score": 0,
            "soft_skills_score": 0,
            "strengths": "Evaluation failed",
            "weaknesses": "Evaluation failed", 
            "justification": f"AI evaluation error: {error_msg}",
            "recommendation": "REJECT",
            "error": error_msg
        }
