"""
Parse structured CVE fields from a GitHub issue body.

Accepts both formats:
  * `**CVE ID:** CVE-2024-12345`   (markdown bold)
  * `CVE ID: CVE-2024-12345`        (plain text)

The lenient parser tolerates issue authors who don't strictly follow the
template — defensive engineering for a production-style system.
"""
import re

# Matches "Key: value" with optional surrounding ** for markdown bold.
# The (?:\*\*)? captures optional bold markers around the key.
_FIELD_RE = re.compile(r"(?:\*\*)?([\w\s]+?)(?:\*\*)?:\s*(.+)")


def parse_issue_body(body: str) -> dict:
    """Extract Key: value pairs from issue markdown."""
    raw: dict[str, str] = {}
    for line in (body or "").splitlines():
        m = _FIELD_RE.match(line.strip())
        if m:
            key = m.group(1).strip().lower().replace(" ", "_")
            # Strip surrounding ** if the value has bold markers on either side
            val = m.group(2).strip()
            if val.startswith("**"):
                val = val[2:].lstrip()
            if val.endswith("**"):
                val = val[:-2].rstrip()
            raw[key] = val
    return {
        "cve_id":          raw.get("cve_id") or raw.get("cve"),
        "package":         raw.get("package"),
        "current_version": raw.get("current_version"),
        "fixed_version":   raw.get("fixed_version"),
        "severity":        raw.get("severity", "UNKNOWN"),
        "file_path":       raw.get("file") or raw.get("file_path"),
    }


REQUIRED_FIELDS = (
    "cve_id", "package", "current_version", "fixed_version", "file_path",
)


def all_fields_present(fields: dict) -> bool:
    return all(fields.get(k) for k in REQUIRED_FIELDS)
