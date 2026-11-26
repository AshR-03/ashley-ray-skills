"""Tests for tools/lint_skills.py.

Each test builds a small repository that passes, breaks one rule, and checks
the linter reports exactly that. The last test lints this repository itself,
so a skill that breaks the rules fails the test suite as well as the linter.

Run from the repo root: python -m unittest discover -s tests
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("lint_skills", REPO / "tools" / "lint_skills.py")
lint = importlib.util.module_from_spec(_spec)
sys.modules["lint_skills"] = lint  # dataclasses look up their module while loading
_spec.loader.exec_module(lint)

GOOD_SKILL = """---
name: demo
description: Does a demo thing. Use when someone asks for a demo.
---

# Demo

## Workflow

1. Run `scripts/run.py`.
2. Read `references/guide.md` if stuck.

## When things go wrong

| Problem | What to do |
| --- | --- |
| `run.py` fails | Read its message and fix the input. |
"""

GOOD_SPEC = "\n\n".join(f"## {h}\n\nText." for h in lint.SPEC_HEADINGS)


class LintTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.skill = self.root / "skills" / "demo"
        self.write("skills/demo/SKILL.md", GOOD_SKILL)
        self.write("skills/demo/spec.md", GOOD_SPEC)
        self.write("skills/demo/scripts/run.py", "import json\nimport sys\n")
        self.write("skills/demo/references/guide.md", "# Guide\n")
        self.write("README.md", "| [demo](skills/demo) | Demo |\n")
        self.marketplace({"plugins": [{"name": "set", "source": "./", "skills": ["./skills/demo"]}]})

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def write(self, rel: str, text: str) -> None:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def marketplace(self, data: dict) -> None:
        self.write(".claude-plugin/marketplace.json", json.dumps(data))

    def findings(self) -> list[str]:
        found, _ = lint.lint_repo(self.root)
        return [str(f) for f in found]

    def assertOnly(self, *fragments: str) -> None:
        """Exactly one finding per fragment, each containing that fragment."""
        found = self.findings()
        self.assertEqual(len(found), len(fragments), found)
        for fragment, finding in zip(fragments, found):
            self.assertIn(fragment, finding)


class SkillTests(LintTestCase):
    def test_good_repo_passes(self):
        self.assertEqual(self.findings(), [])

    def test_name_must_match_folder(self):
        self.write("skills/demo/SKILL.md", GOOD_SKILL.replace("name: demo", "name: other"))
        self.assertOnly("error: name 'other' does not match folder 'demo'")

    def test_name_must_be_kebab_case(self):
        self.write("skills/Demo_X/SKILL.md", GOOD_SKILL.replace("name: demo", "name: Demo_X"))
        self.write("skills/Demo_X/spec.md", GOOD_SPEC)
        self.write("skills/Demo_X/scripts/run.py", "")
        self.write("skills/Demo_X/references/guide.md", "")
        self.write("README.md", "(skills/demo) (skills/Demo_X)")
        self.marketplace({"plugins": [{"name": "s", "source": "./",
                                       "skills": ["./skills/demo", "./skills/Demo_X"]}]})
        self.assertOnly("not lowercase kebab-case")

    def test_description_required_and_limited(self):
        self.write("skills/demo/SKILL.md", GOOD_SKILL.replace(
            "description: Does a demo thing. Use when someone asks for a demo.\n", ""))
        self.assertOnly("frontmatter has no 'description'")
        long = "x" * (lint.MAX_DESCRIPTION_CHARS + 1)
        self.write("skills/demo/SKILL.md", GOOD_SKILL.replace(
            "Does a demo thing. Use when someone asks for a demo.", long))
        self.assertOnly(f"description is {len(long)} characters")

    def test_quoted_and_multiline_frontmatter(self):
        fields, _ = lint.parse_frontmatter(
            '---\nname: "demo"\ndescription: >\n  Line one\n  line two\n---\nbody\n')
        self.assertEqual(fields, {"name": "demo", "description": "Line one line two"})

    def test_no_frontmatter(self):
        self.write("skills/demo/SKILL.md", GOOD_SKILL.split("---", 2)[2])
        found = self.findings()
        self.assertIn("no frontmatter", found[0])

    def test_body_length_limit(self):
        filler = "\n".join(f"Line {i}" for i in range(lint.MAX_BODY_LINES))
        self.write("skills/demo/SKILL.md", GOOD_SKILL + filler)
        self.assertOnly("body is")

    def test_recovery_section_required(self):
        self.write("skills/demo/SKILL.md", GOOD_SKILL.split("## When things go wrong")[0])
        self.assertOnly("no '## When things go wrong' section")

    def test_recovery_section_needs_a_table(self):
        self.write("skills/demo/SKILL.md", GOOD_SKILL.split("| Problem")[0] + "Try again.\n")
        self.assertOnly("needs a table of problems and fixes")

    def test_numbered_steps_warning(self):
        self.write("skills/demo/SKILL.md", GOOD_SKILL.replace("1. Run", "- Run").replace("2. Read", "- Read"))
        self.assertOnly("warning: no numbered steps")

    def test_mentioned_file_must_exist(self):
        self.write("skills/demo/SKILL.md", GOOD_SKILL + "\nSee `references/missing.md`.\n")
        self.assertOnly("mentions 'references/missing.md', which does not exist")

    def test_unmentioned_bundled_file_warns(self):
        self.write("skills/demo/assets/unused.txt", "x")
        self.assertOnly("assets/unused.txt: warning: is not mentioned")

    def test_mention_in_references_counts(self):
        self.write("skills/demo/assets/form.txt", "x")
        self.write("skills/demo/references/guide.md", "Fill in `assets/form.txt`.\n")
        self.assertEqual(self.findings(), [])

    def test_scripts_must_use_standard_library(self):
        self.write("skills/demo/scripts/run.py", "import json\nimport requests\nfrom yaml import safe_load\n")
        found = self.findings()
        self.assertEqual(len(found), 2, found)
        self.assertIn("imports 'requests' (line 2)", found[0])
        self.assertIn("imports 'yaml' (line 3)", found[1])

    def test_local_script_imports_allowed(self):
        self.write("skills/demo/scripts/helper.py", "")
        self.write("skills/demo/scripts/run.py", "import helper\nfrom . import helper as h\n")
        self.write("skills/demo/references/guide.md", "Uses `scripts/helper.py`.\n")
        self.assertEqual(self.findings(), [])

    def test_script_syntax_error(self):
        self.write("skills/demo/scripts/run.py", "def broken(:\n")
        self.assertOnly("does not parse")

    def test_spec_required(self):
        (self.skill / "spec.md").unlink()
        self.assertOnly("spec.md: error: missing")

    def test_spec_sections_required(self):
        self.write("skills/demo/spec.md", GOOD_SPEC.replace("## Must not", "## Never"))
        self.assertOnly("missing the '## Must not' section")


class RepoTests(LintTestCase):
    def test_skill_must_be_in_a_set(self):
        self.marketplace({"plugins": [{"name": "set", "source": "./", "skills": []}]})
        self.assertOnly("skill 'demo' is not in any set")

    def test_skill_listed_twice(self):
        self.marketplace({"plugins": [
            {"name": "a", "source": "./", "skills": ["./skills/demo"]},
            {"name": "b", "source": "./", "skills": ["./skills/demo/"]},
        ]})
        self.assertOnly("skill 'demo' is listed 2 times")

    def test_listed_path_must_be_a_skill(self):
        self.marketplace({"plugins": [{"name": "set", "source": "./",
                                       "skills": ["./skills/demo", "./skills/ghost"]}]})
        self.assertOnly("set 'set' lists './skills/ghost', which is not a skill folder")

    def test_invalid_marketplace_json(self):
        self.write(".claude-plugin/marketplace.json", "{not json")
        found = self.findings()
        self.assertIn("is not valid JSON", found[0])

    def test_readme_must_link_skill(self):
        self.write("README.md", "# Skills\n")
        self.assertOnly("does not link to skill 'demo'")

    def test_exit_codes(self):
        def run(*extra: str) -> int:
            with contextlib.redirect_stdout(io.StringIO()):
                return lint.main([str(self.root), *extra])

        self.assertEqual(run(), 0)
        self.write("skills/demo/assets/unused.txt", "x")
        self.assertEqual(run(), 0, "warnings alone pass")
        self.assertEqual(run("--strict"), 1, "--strict fails on warnings")
        (self.skill / "spec.md").unlink()
        self.assertEqual(run(), 1, "errors fail")


class ThisRepoTests(unittest.TestCase):
    def test_repository_skills_pass_lint(self):
        found, count = lint.lint_repo(REPO)
        self.assertGreater(count, 0)
        self.assertEqual([str(f) for f in found], [])


if __name__ == "__main__":
    unittest.main()
