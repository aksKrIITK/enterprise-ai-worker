import re
import json
from typing import Tuple, List, Dict, Any, Optional


class SystemPromptLeakGuardrail:
    """Ensures model outputs do not leak confidential system prompts or internal tokens."""

    LEAK_INDICATORS = [
        r"JWT_SECRET",
        r"SERVICE_TO_SERVICE_SECRET",
        r"OPENAI_API_KEY",
        r"GEMINI_API_KEY",
        r"System Prompt Override",
        r"You are Enterprise AI Worker multi-agent supervisor",
    ]

    @classmethod
    def check(cls, response_text: str) -> Tuple[bool, List[str]]:
        violations = []
        for indicator in cls.LEAK_INDICATORS:
            if re.search(indicator, response_text, flags=re.IGNORECASE):
                violations.append(f"Output leaked confidential token/system marker: '{indicator}'")
        return len(violations) == 0, violations


class SchemaValidationGuardrail:
    """Validates structured JSON response compliance."""

    @classmethod
    def validate_json_schema(cls, response_text: str, required_keys: List[str]) -> Tuple[bool, Optional[Dict[str, Any]], List[str]]:
        try:
            parsed = json.loads(response_text)
            if not isinstance(parsed, dict):
                return False, None, ["Response is not a valid JSON object dictionary."]

            missing = [k for k in required_keys if k not in parsed]
            if missing:
                return False, parsed, [f"Missing required JSON schema keys: {missing}"]

            return True, parsed, []
        except Exception as e:
            return False, None, [f"Invalid JSON string format: {str(e)}"]


class GroundednessGuardrail:
    """Measures overlap between output claims and source documents to prevent hallucination."""

    @classmethod
    def score_groundedness(cls, response_text: str, context_documents: List[str]) -> float:
        if not context_documents or not response_text:
            return 1.0

        combined_context = " ".join(context_documents).lower()
        words = [w.strip().lower() for w in response_text.split() if len(w) > 4]
        if not words:
            return 1.0

        matches = sum(1 for w in words if w in combined_context)
        return round(matches / len(words), 2)
