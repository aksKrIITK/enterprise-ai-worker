# Contributing to Enterprise AI Worker

Thank you for your interest in contributing to **Enterprise AI Worker**! We welcome bug reports, feature suggestions, documentation improvements, and pull requests from the community.

---

## Code of Conduct

We are committed to providing a welcoming, respectful, and inclusive community for everyone. Please maintain professionalism and courtesy in all discussions, issues, and pull requests.

---

## How to Contribute

### 1. Reporting Bugs
- Search existing GitHub Issues before submitting a new report.
- Include OS version, Python/Java versions, step-by-step reproduction steps, and full error stack traces.

### 2. Suggesting Features
- Open an issue describing the proposed feature, user motivation, and technical implementation idea.
- Tag the issue with `enhancement`.

### 3. Submitting Pull Requests (PRs)
- **Fork** the repository and create a feature branch (`git checkout -b feature/my-new-feature`).
- Follow established code formatting and design patterns:
  - **Python**: PEP 8 style, type annotations, Pydantic v2 schemas.
  - **Java**: Standard Spring Boot conventions, Lombok annotations.
  - **React / TypeScript**: Functional components, Tailwind CSS design tokens.
- **Write Tests**: Every new feature, MCP tool, or agent logic must be accompanied by unit tests in `orchestrator/tests/` or `gateway/src/test/`.
- Ensure all automated tests pass (`python -m pytest` and `mvn test`).
- Keep pull requests focused on a single logical change.

---

## Branching & Commit Conventions

- Branch naming: `feature/<description>`, `bugfix/<description>`, `docs/<description>`.
- Commit messages: Use clear, present-tense messages (e.g. `feat: add mcp-jira transition tool`, `fix: enforce SQL tenant predicate injection`).

---

## Security Vulnerabilities

If you discover a security vulnerability (such as a multi-tenant data leak or prompt-injection bypass), please **do not** open a public issue. Email security disclosures to **security@enterprise-ai.worker** so we can address the issue promptly.

Thank you for helping build the future of AI employee automation!
