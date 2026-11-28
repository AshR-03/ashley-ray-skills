"""Check the brainstorm eval fixtures are in the state their cases assume.

The eval cases in evals/brainstorm/ seed the workspace with these graphs and
grade the agent against what is still open in them. If a fixture or the
definition of done changes, these tests fail before a paid eval run does.

Run from the repo root: python -m unittest discover -s tests
"""

from __future__ import annotations

import importlib.util
import json
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "evals" / "brainstorm" / "fixtures"
_spec = importlib.util.spec_from_file_location(
    "brainstorm_graph", REPO / "skills" / "brainstorm" / "scripts" / "brainstorm_graph.py")
bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bg)


def report(name: str) -> dict:
    return bg.evaluate(json.loads((FIXTURES / f"{name}.json").read_text(encoding="utf-8")))


class FixtureStateTests(unittest.TestCase):
    def test_partial(self):
        r = report("partial")
        self.assertFalse(r["done"])
        self.assertEqual(r["open_questions"], [("members", "Independent gyms or chains?")])
        self.assertEqual(r["detached_components"], [["owner-adoption", "solo-dev"]])
        self.assertEqual(r["isolated"], [])
        self.assertEqual(r["horizon"], "unknown")
        self.assertIn("vision", r["missing_coverage"])

    def test_near_done(self):
        r = report("near-done")
        self.assertFalse(r["done"])
        self.assertEqual(r["open_questions"], [("owners", "Would owners pay per member or a flat fee?")])
        self.assertEqual(r["isolated"], ["early-churn"])
        self.assertEqual(r["detached_components"], [])
        self.assertEqual(r["missing_coverage"], [])

    def test_complete(self):
        r = report("complete")
        self.assertTrue(r["done"], r)


class CaseWiringTests(unittest.TestCase):
    def test_setup_scripts_point_at_existing_fixtures(self):
        scripts = sorted((REPO / "evals").glob("**/setup.sh"))
        self.assertTrue(scripts)
        for script in scripts:
            for ref in re.findall(r"fixtures/([\w-]+\.json)", script.read_text(encoding="utf-8")):
                self.assertTrue((FIXTURES / ref).is_file(), f"{script}: fixtures/{ref} missing")

    def test_every_case_loads_this_repo_and_has_graders(self):
        cases = sorted(p.parent for p in (REPO / "evals").glob("**/prompt.md"))
        self.assertTrue(cases)
        for case in cases:
            front = (case / "prompt.md").read_text(encoding="utf-8").split("---")[1]
            self.assertIn('plugins: ["../../.."]', front, f"{case.name}: must load the repo root as the plugin")
            self.assertTrue(list((case / "graders").glob("*.md")), f"{case.name}: no graders")

    def test_cases_need_no_sandbox(self):
        """Bash, Write and Edit are gated in `claude plugin eval` and need the OS
        sandbox. Cases stay read-only; the script is covered by unit tests."""
        gated = ("Bash", "Write", "Edit")
        for prompt in sorted((REPO / "evals").glob("**/prompt.md")):
            front = prompt.read_text(encoding="utf-8").split("---")[1]
            tools = re.search(r"^allowed_tools:\s*\[(.*)\]", front, re.M)
            self.assertTrue(tools, f"{prompt.parent.name}: set allowed_tools explicitly")
            used = {t.strip() for t in tools.group(1).split(",")}
            self.assertFalse(used & set(gated), f"{prompt.parent.name}: allows {used & set(gated)}")
        for grader in sorted((REPO / "evals").glob("**/graders/*.md")):
            text = grader.read_text(encoding="utf-8")
            self.assertNotRegex(text, r"(?m)^\s*(tool|type):\s*(Bash|Write|Edit|file_exists)\b",
                                f"{grader}: needs a tool the eval can't use")


if __name__ == "__main__":
    unittest.main()
