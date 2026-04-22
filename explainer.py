import os
from typing import Dict, Any

from vertexai import init
from vertexai.generative_models import GenerativeModel


class ReflexExplainer:
    def __init__(self, project_id: str | None = None, location: str = "us-central1") -> None:
        self.project_id = project_id or os.getenv("PROJECT_ID") or os.getenv("GOOGLE_CLOUD_PROJECT")
        self.location = location

        init(project=self.project_id, location=self.location)
        self.model = GenerativeModel("gemini-1.5-pro")

    def explain(self, decision: Dict[str, Any]) -> str:
        prompt = f"""
You are explaining a clinical reflex-testing decision in simple and safe language.

Decision:
{decision}

Write:
1. A short explanation
2. Why the action was taken
3. Whether this was normal, routine abnormal, or critical

Keep it concise, professional, and easy to understand.
"""

        response = self.model.generate_content(prompt)
        return response.text