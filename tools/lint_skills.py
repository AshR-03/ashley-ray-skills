#!/usr/bin/env python3
"""Lint every skill in the repository against its authoring rules.

Errors fail the run (exit 1); warnings are reported but pass unless --strict.

Per skill (skills/<name>/):
  - SKILL.md has frontmatter with `name` and `description`; the name matches
    the folder, is kebab-case and at most 64 characters; the description is at
    most 1024 characters.
  - The SKILL.md body is at most 500 lines, has numbered steps (warning if
    not) and a "When things go wrong" section with a table of errors and fixes.
  - Every scripts/, references/ or assets/ path the skill mentions exists, and
    every bundled file is mentioned somewhere in the skill (warning if not).
  - spec.md exists with the required headings (see template/spec.md).
  - Bundled Python scripts parse and import only the standard library.
  - The skill has eval cases in evals/<name>/ (warning if not).

Across the repository:
  - Every skill is listed exactly once in .claude-plugin/marketplace.json, and
    every listed path is a skill.
  - Every skill is linked from the README.

Standard library only (Python 3.10+). Usage:
  python tools/lint_skills.py [repo-root] [--strict]
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_BODY_LINES = 500
MAX_NAME_CHARS = 64
MAX_DESCRIPTION_CHARS = 1024
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SPEC_HEADINGS = ["Goal", "Outputs", "Must", "Must not", "Should trigger", "Should not trigger"]
RECOVERY_RE = re.compile(
    r"^##+\s+(when things go wrong|error recovery|errors|troubleshooting)\s*$", re.I | re.M
)
NUMBERED_STEP_RE = re.compile(r"^\s*1\.\s+\S", re.M)
TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$", re.M)
RESOURCE_RE = re.compile(r"(?<![\w.-])((?:references|scripts|assets)/[\w./-]*[\w-])")
RESOURCE_DIRS = ("references", "scripts", "assets")


@dataclass(frozen=True)
class Finding:
    level: str  # "error" or "warning"
    path: str
    message: str

    def __str__(self) -> str:
        return f"{self.path}: {self.level}: {self.message}"


def parse_frontmatter(text: str) -> tuple[dict[str, str] | None, str]:
    """Return (frontmatter, body). Handles `key: value` lines, quoted values
    and indented continuation lines (enough for SKILL.md; not full YAML)."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        return None, text
    fields: dict[str, str] = {}
    key = None
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z0-9_-]+):\s*(.*)$", line)
        if match:
            key, value = match.group(1), match.group(2).strip()
            if value in (">", "|", ">-", "|-"):
                value = ""
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            fields[key] = value
        elif key and line[:1] in (" ", "\t"):
            fields[key] = f"{fields[key]} {line.strip()}".strip()
    return fields, "\n".join(lines[end + 1:])


def rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def lint_python(script: Path, root: Path) -> list[Finding]:
    where = rel(script, root)
    try:
        tree = ast.parse(script.read_text(encoding="utf-8"), filename=where)
    except SyntaxError as exc:
        return [Finding("error", where, f"does not parse: {exc.msg} (line {exc.lineno})")]
    local = {p.stem for p in script.parent.glob("*.py")}
    allowed = set(sys.stdlib_module_names) | {"__future__"} | local
    findings = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            modules = [node.module]
        else:
            continue
        for module in modules:
            top = module.split(".")[0]
            if top not in allowed:
                findings.append(Finding(
                    "error", where,
                    f"imports '{top}' (line {node.lineno}), which is not in the standard "
                    "library; bundled scripts must install with no dependencies",
                ))
    return findings


def lint_spec(skill_dir: Path, root: Path) -> list[Finding]:
    spec = skill_dir / "spec.md"
    where = rel(spec, root)
    if not spec.is_file():
        return [Finding("error", where, "missing; write the spec first (copy template/spec.md)")]
    text = spec.read_text(encoding="utf-8")
    found = {m.group(1).strip().lower() for m in re.finditer(r"^##\s+(.+?)\s*$", text, re.M)}
    return [
        Finding("error", where, f"missing the '## {heading}' section")
        for heading in SPEC_HEADINGS if heading.lower() not in found
    ]


def lint_skill(skill_dir: Path, root: Path) -> list[Finding]:
    skill_md = skill_dir / "SKILL.md"
    where = rel(skill_md, root)
    if not skill_md.is_file():
        return [Finding("error", where, "missing")]
    findings: list[Finding] = []
    text = skill_md.read_text(encoding="utf-8")
    fields, body = parse_frontmatter(text)

    if fields is None:
        findings.append(Finding("error", where, "no frontmatter (a block between '---' lines)"))
        fields = {}
    name = fields.get("name", "")
    description = fields.get("description", "")
    if not name:
        findings.append(Finding("error", where, "frontmatter has no 'name'"))
    else:
        if name != skill_dir.name:
            findings.append(Finding("error", where, f"name '{name}' does not match folder '{skill_dir.name}'"))
        if not NAME_RE.match(name):
            findings.append(Finding("error", where, f"name '{name}' is not lowercase kebab-case"))
        if len(name) > MAX_NAME_CHARS:
            findings.append(Finding("error", where, f"name is {len(name)} characters (max {MAX_NAME_CHARS})"))
    if not description:
        findings.append(Finding("error", where, "frontmatter has no 'description'"))
    elif len(description) > MAX_DESCRIPTION_CHARS:
        findings.append(Finding(
            "error", where,
            f"description is {len(description)} characters (max {MAX_DESCRIPTION_CHARS})",
        ))

    body_lines = len(body.splitlines())
    if body_lines > MAX_BODY_LINES:
        findings.append(Finding(
            "error", where,
            f"body is {body_lines} lines (max {MAX_BODY_LINES}); move detail into references/",
        ))
    if not NUMBERED_STEP_RE.search(body):
        findings.append(Finding("warning", where, "no numbered steps; give the workflow as a numbered list"))
    recovery = RECOVERY_RE.search(body)
    if not recovery:
        findings.append(Finding(
            "error", where,
            "no '## When things go wrong' section listing errors and how to recover",
        ))
    else:
        section = body[recovery.end():]
        next_heading = re.search(r"^##\s", section, re.M)
        section = section[:next_heading.start()] if next_heading else section
        if len(TABLE_ROW_RE.findall(section)) < 3:  # header, divider, at least one row
            findings.append(Finding(
                "error", where,
                "'When things go wrong' needs a table of problems and fixes",
            ))

    # Mentioned resources exist; bundled resources are mentioned.
    docs = [skill_md, *sorted(skill_dir.glob("references/**/*.md")), skill_dir / "spec.md"]
    mentioned: set[str] = set()
    for doc in docs:
        if doc.is_file():
            mentioned |= set(RESOURCE_RE.findall(doc.read_text(encoding="utf-8")))
    for ref in sorted(set(RESOURCE_RE.findall(text))):
        if not (skill_dir / ref).exists():
            findings.append(Finding("error", where, f"mentions '{ref}', which does not exist"))
    for sub in RESOURCE_DIRS:
        for path in sorted((skill_dir / sub).rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                local = path.relative_to(skill_dir).as_posix()
                if local not in mentioned:
                    findings.append(Finding(
                        "warning", rel(path, root),
                        "is not mentioned in SKILL.md or references/, so the agent won't know to use it",
                    ))

    for script in sorted(skill_dir.glob("scripts/**/*.py")):
        findings += lint_python(script, root)
    findings += lint_spec(skill_dir, root)

    evals = root / "evals" / skill_dir.name
    if not any(evals.glob("**/prompt.md")) and not any(evals.glob("**/case.yaml")):
        findings.append(Finding(
            "warning", rel(evals, root),
            "has no eval cases; add cases from the spec's trigger lists and must/must-not rules",
        ))
    return findings


def lint_repo(root: Path) -> tuple[list[Finding], int]:
    """Lint the whole repository. Returns (findings, number of skills)."""
    findings: list[Finding] = []
    skills_root = root / "skills"
    skill_dirs = sorted(p for p in skills_root.iterdir() if p.is_dir()) if skills_root.is_dir() else []
    for skill_dir in skill_dirs:
        findings += lint_skill(skill_dir, root)

    marketplace = root / ".claude-plugin" / "marketplace.json"
    where = rel(marketplace, root)
    listed: dict[str, int] = {}
    if not marketplace.is_file():
        findings.append(Finding("error", where, "missing"))
    else:
        try:
            data = json.loads(marketplace.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            findings.append(Finding("error", where, f"is not valid JSON: {exc}"))
            data = {}
        for plugin in data.get("plugins", []):
            base = root / plugin.get("source", "./")
            for entry in plugin.get("skills", []):
                path = (base / entry).resolve()
                if not (path / "SKILL.md").is_file():
                    findings.append(Finding(
                        "error", where,
                        f"set '{plugin.get('name')}' lists '{entry}', which is not a skill folder",
                    ))
                listed[str(path)] = listed.get(str(path), 0) + 1
    for skill_dir in skill_dirs:
        count = listed.get(str(skill_dir.resolve()), 0)
        if marketplace.is_file() and count == 0:
            findings.append(Finding("error", where, f"skill '{skill_dir.name}' is not in any set"))
        elif count > 1:
            findings.append(Finding("error", where, f"skill '{skill_dir.name}' is listed {count} times"))

    readme = root / "README.md"
    readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    for skill_dir in skill_dirs:
        if f"(skills/{skill_dir.name})" not in readme_text and f"(skills/{skill_dir.name}/)" not in readme_text:
            findings.append(Finding(
                "error", "README.md",
                f"does not link to skill '{skill_dir.name}' (expected '(skills/{skill_dir.name})')",
            ))
    return findings, len(skill_dirs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("root", nargs="?", default=Path(__file__).resolve().parent.parent, type=Path,
                        help="Repository root (default: the repo this script is in)")
    parser.add_argument("--strict", action="store_true", help="Treat warnings as errors")
    args = parser.parse_args(argv)

    root = args.root.resolve()
    findings, skill_count = lint_repo(root)
    for finding in findings:
        print(finding)
    errors = sum(f.level == "error" for f in findings)
    warnings = len(findings) - errors
    print(f"\nChecked {skill_count} skill(s): {errors} error(s), {warnings} warning(s).")
    failed = errors > 0 or (args.strict and warnings > 0)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
