import re
from typing import Dict, Any


class PromptSanitizer:
    """Prompt Injection Defense Layer. Treats all retrieved text as untrusted data."""

    INJECTION_PATTERNS = [
        r"ignore (all )?prior instructions",
        r"ignore above instructions",
        r"system prompt override",
        r"you are now in (dan|unrestricted) mode",
        r"reveal (all )?secrets",
        r"bypass security",
    ]

    @classmethod
    def wrap_untrusted_content(cls, content: str, source_type: str, source_id: str) -> str:
        """Sanitize text and wrap within structured untrusted data tags."""
        sanitized = content
        for pattern in cls.INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "[REDACTED PROMPT INJECTION ATTEMPT]", sanitized, flags=re.IGNORECASE)

        return (
            f'<untrusted_data source_type="{source_type}" source_id="{source_id}">\n'
            f"{sanitized}\n"
            f"</untrusted_data>"
        )

    @classmethod
    def contains_injection_attempt(cls, text: str) -> bool:
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return True
        return False
