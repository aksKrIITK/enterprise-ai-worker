import re
from typing import Dict, Any, List, Tuple


class PromptInjectionGuardrail:
    """Detects prompt injection, jailbreak attempts, and system override attempts."""

    INJECTION_PATTERNS = [
        r"ignore (all )?prior instructions",
        r"ignore above instructions",
        r"system prompt override",
        r"you are now in (dan|unrestricted) mode",
        r"reveal (all )?secrets",
        r"bypass security",
        r"disregard safety guidelines",
    ]

    @classmethod
    def check(cls, text: str) -> Tuple[bool, List[str]]:
        violations = []
        for pattern in cls.INJECTION_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                violations.append(f"Prompt injection pattern detected: '{pattern}'")
        return len(violations) == 0, violations


class PIIGuardrail:
    """Detects and redacts Personally Identifiable Information (PII) & Secret Keys."""

    # Note: API_KEY is checked before PHONE to avoid partial numeric token matching
    PII_PATTERNS = {
        "API_KEY": r"\b(sk-proj-[A-Za-z0-9_-]{16,}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,}|AIzaSy[A-Za-z0-9_-]{33})\b",
        "EMAIL": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "CREDIT_CARD": r"\b(?:\d[ -]*?){13,16}\b",
        "PHONE": r"(?<![A-Za-z0-9_-])\b\+?\d{1,4}?[-.\s]?\(?\d{1,3}?\)?[-.\s]?\d{3,4}[-.\s]?\d{4}\b(?![A-Za-z0-9_-])",
        "IP_ADDRESS": r"\b(?:\d{1,3}\.){3}\d{1,3}\b",
    }

    @classmethod
    def redact(cls, text: str) -> Tuple[str, Dict[str, int]]:
        redacted = text
        stats = {}
        for pii_type, pattern in cls.PII_PATTERNS.items():
            matches = len(re.findall(pattern, redacted))
            if matches > 0:
                stats[pii_type] = matches
                redacted = re.sub(pattern, f"[REDACTED_{pii_type}]", redacted)
        return redacted, stats


class SafetyGuardrail:
    """Validates user instructions against malicious system actions."""

    DESTRUCTIVE_COMMANDS = [
        r"rm -rf",
        r"mkfs",
        r"dd if=",
        r"chmod -R 777",
        r":\(\)\{ :\|:\& \};:",
    ]

    @classmethod
    def check(cls, text: str) -> Tuple[bool, List[str]]:
        violations = []
        for cmd in cls.DESTRUCTIVE_COMMANDS:
            if re.search(cmd, text, flags=re.IGNORECASE):
                violations.append(f"Destructive system command detected: '{cmd}'")
        return len(violations) == 0, violations
