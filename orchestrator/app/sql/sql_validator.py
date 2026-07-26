import re
from typing import Dict, Any, Tuple


class SQLValidator:
    """SQL Sandbox Validator enforcing read-only SELECT execution, tenant predicate injection, and row limits."""

    FORBIDDEN_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
        "TRUNCATE", "GRANT", "REVOKE", "EXECUTE", "SHUTDOWN"
    ]

    @classmethod
    def validate_and_sanitize(cls, raw_sql: str, tenant_id: str, max_rows: int = 100) -> Tuple[bool, str, str]:
        sql_clean = raw_sql.strip()

        # Remove trailing semicolon if present
        if sql_clean.endswith(";"):
            sql_clean = sql_clean[:-1].strip()

        # 1. Block DDL / DML Statements
        upper_sql = sql_clean.upper()
        for kw in cls.FORBIDDEN_KEYWORDS:
            # Check for keyword surrounded by word boundaries or at string start
            pattern = rf"\b{kw}\b"
            if re.search(pattern, upper_sql):
                return False, "", f"Forbidden SQL operation detected: {kw} statements are not allowed."

        if not upper_sql.startswith("SELECT"):
            return False, "", "Only SELECT queries are permitted in read-only mode."

        # 2. Inject tenant_id predicate if tenant_id is provided
        if tenant_id:
            if "WHERE" in upper_sql:
                # Append tenant_id to existing WHERE clause
                sql_clean = re.sub(
                    r"\bWHERE\b",
                    f"WHERE tenant_id = '{tenant_id}' AND ",
                    sql_clean,
                    flags=re.IGNORECASE,
                    count=1
                )
            else:
                # Append WHERE tenant_id predicate before ORDER BY / LIMIT if present
                if "ORDER BY" in upper_sql:
                    sql_clean = re.sub(
                        r"\bORDER BY\b",
                        f"WHERE tenant_id = '{tenant_id}' ORDER BY ",
                        sql_clean,
                        flags=re.IGNORECASE,
                        count=1
                    )
                elif "LIMIT" in upper_sql:
                    sql_clean = re.sub(
                        r"\bLIMIT\b",
                        f"WHERE tenant_id = '{tenant_id}' LIMIT ",
                        sql_clean,
                        flags=re.IGNORECASE,
                        count=1
                    )
                else:
                    sql_clean += f" WHERE tenant_id = '{tenant_id}'"

        # 3. Enforce Max Row Limit
        if "LIMIT" not in sql_clean.upper():
            sql_clean += f" LIMIT {max_rows}"

        return True, sql_clean, ""
