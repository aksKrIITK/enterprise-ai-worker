import re
from typing import Tuple, List


class SQLCommandGuardrail:
    """Analyzes generated SQL queries to block illegal DDL and destructive operations."""

    ILLEGAL_PATTERNS = [
        r"\bDROP\s+DATABASE\b",
        r"\bDROP\s+SCHEMA\b",
        r"\bTRUNCATE\b",
        r"\bALTER\s+USER\b",
        r"\bGRANT\s+ALL\b",
    ]

    @classmethod
    def check_query(cls, sql_query: str, tenant_id: str) -> Tuple[bool, List[str]]:
        violations = []
        clean_sql = sql_query.upper()

        for pattern in cls.ILLEGAL_PATTERNS:
            if re.search(pattern, clean_sql):
                violations.append(f"Forbidden SQL DDL operation detected: '{pattern}'")

        # Ensure tenant isolation filter is present on SELECT/UPDATE/DELETE queries
        if any(keyword in clean_sql for keyword in ["SELECT", "UPDATE", "DELETE"]):
            if "TENANT_ID" not in clean_sql:
                violations.append("SQL query lacks mandatory 'tenant_id' isolation clause.")

        return len(violations) == 0, violations
