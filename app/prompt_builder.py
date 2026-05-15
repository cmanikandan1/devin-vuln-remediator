"""Load and fill the CVE remediation prompt template.

The prompt is the engineering IP of this system. Versioned independently
from orchestration code in `prompts/remediate_cve.txt`.
"""
import os
from pathlib import Path

PROMPT_PATH = Path(os.getenv("PROMPT_PATH", "prompts/remediate_cve.txt"))


def build_prompt(fields: dict, *, issue_number: int, repo_url: str) -> str:
    template = PROMPT_PATH.read_text()

    # Detect file ecosystem to give Devin the right install/test commands.
    fp = fields["file_path"].lower()
    is_python = fp.endswith((".txt", "requirements.in", "pyproject.toml", "setup.py"))
    is_javascript = fp.endswith(("yarn.lock", "package-lock.json", "package.json"))

    if is_python:
        ecosystem = "python"
        install_cmd = f"pip install -r {fields['file_path']}"
        test_cmd = "pytest tests/unit_tests/ -x --timeout=60"
    elif is_javascript:
        ecosystem = "javascript"
        # yarn.lock implies yarn — package-lock.json implies npm
        if "yarn.lock" in fp:
            install_cmd = "cd docs && yarn install --frozen-lockfile"
            test_cmd = "cd docs && yarn test --watchAll=false 2>/dev/null || true"
        else:
            install_cmd = "cd docs && npm ci"
            test_cmd = "cd docs && npm test 2>/dev/null || true"
    else:
        ecosystem = "unknown"
        install_cmd = f"# Inspect {fields['file_path']} and use the right package manager"
        test_cmd = "# Run the project's standard test command"

    return template.format(
        repo_url=repo_url,
        issue_number=issue_number,
        cve_id=fields["cve_id"],
        cve_id_lower=fields["cve_id"].lower(),
        package=fields["package"],
        current_version=fields["current_version"],
        fixed_version=fields["fixed_version"],
        file_path=fields["file_path"],
        severity=fields.get("severity", "UNKNOWN"),
        ecosystem=ecosystem,
        install_cmd=install_cmd,
        test_cmd=test_cmd,
        github_owner=os.getenv("GITHUB_OWNER", ""),
        github_repo=os.getenv("GITHUB_REPO", ""),
    )
