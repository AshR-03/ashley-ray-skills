"""Golden tests for skills/brainstorm/scripts/brainstorm_graph.py.

Fixed inputs with expected outputs, no model involved. The definition of done
lives in this script, so these tests guard the rule the skill relies on to
decide when a brainstorm is finished.

Run from the repo root: python -m unittest discover -s tests
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "skills" / "brainstorm" / "scripts" / "brainstorm_graph.py"
_spec = importlib.util.spec_from_file_location("brainstorm_graph", SCRIPT)
bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bg)


class GraphTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name)
        self.graph_path = self.dir / "docs" / "brainstorm" / "graph.json"

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def run_cmd(self, *args: str) -> tuple[int, str]:
        """Run a command in-process. Returns (exit code, stdout + exit message)."""
        out = io.StringIO()
        code = 0
        with contextlib.redirect_stdout(out):
            try:
                bg.main(["--graph", str(self.graph_path), *args])
            except SystemExit as exc:
                if isinstance(exc.code, str):
                    code = 1
                    out.write(exc.code)
                else:
                    code = exc.code or 0
        return code, out.getvalue()

    def ok(self, *args: str) -> str:
        code, out = self.run_cmd(*args)
        self.assertEqual(code, 0, f"{args} failed: {out}")
        return out

    def graph(self) -> dict:
        return json.loads(self.graph_path.read_text(encoding="utf-8"))

    def report(self) -> dict:
        return bg.evaluate(self.graph())

    def build_complete(self, horizon: str = "short") -> None:
        """A small graph that meets the definition of done."""
        self.ok("init", "--title", "Gym app", "--idea", "An app that keeps gym members coming back",
                "--horizon", horizon)
        for node_type, node_id, label in [
            ("purpose", "business", "Business"),
            ("stakeholder", "members", "Gym members"),
            ("goal", "retention", "Keep members coming back"),
            ("vision", "streaks", "Members see their weekly streak first"),
            ("feature", "progress-emails", "Weekly progress emails"),
        ]:
            self.ok("add-node", "--type", node_type, "--id", node_id, "--label", label)
        for source, target, edge_type in [
            ("business", "retention", "motivates"),
            ("progress-emails", "retention", "achieves"),
            ("progress-emails", "members", "serves"),
            ("progress-emails", "idea", "refines"),
            ("streaks", "members", "serves"),
        ]:
            self.ok("add-edge", "--from", source, "--to", target, "--type", edge_type)


class InitTests(GraphTestCase):
    def test_init_creates_seed_node(self):
        self.ok("init", "--title", "T", "--idea", "My idea")
        graph = self.graph()
        self.assertEqual(graph["nodes"]["idea"]["label"], "My idea")
        self.assertEqual(graph["nodes"]["idea"]["type"], "idea")
        self.assertEqual(graph["horizon"], "unknown")
        self.assertEqual(graph["edges"], [])

    def test_init_refuses_to_overwrite(self):
        self.ok("init", "--title", "T", "--idea", "First")
        code, out = self.run_cmd("init", "--title", "T", "--idea", "Second")
        self.assertEqual(code, 1)
        self.assertIn("already exists", out)
        self.assertEqual(self.graph()["nodes"]["idea"]["label"], "First")

    def test_init_force_starts_over(self):
        self.ok("init", "--title", "T", "--idea", "First")
        self.ok("init", "--title", "T", "--idea", "Second", "--force")
        self.assertEqual(self.graph()["nodes"]["idea"]["label"], "Second")

    def test_commands_need_a_graph(self):
        code, out = self.run_cmd("show")
        self.assertEqual(code, 1)
        self.assertIn("Run `init` first", out)


class EditTests(GraphTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.ok("init", "--title", "T", "--idea", "Idea")

    def test_add_node_generates_id(self):
        self.ok("add-node", "--type", "feature", "--label", "Offline Mode!")
        self.assertIn("feature-offline-mode", self.graph()["nodes"])

    def test_add_node_rejects_duplicate_id(self):
        self.ok("add-node", "--type", "goal", "--id", "g", "--label", "A")
        code, out = self.run_cmd("add-node", "--type", "goal", "--id", "g", "--label", "B")
        self.assertEqual(code, 1)
        self.assertIn("already exists", out)

    def test_add_edge_rules(self):
        self.ok("add-node", "--type", "goal", "--id", "g", "--label", "Goal")
        self.ok("add-edge", "--from", "g", "--to", "idea", "--type", "relates-to")
        for args, message in [
            (("--from", "g", "--to", "idea", "--type", "relates-to"), "already exists"),
            (("--from", "g", "--to", "g", "--type", "relates-to"), "two different nodes"),
            (("--from", "g", "--to", "nope", "--type", "relates-to"), "Unknown node 'nope'"),
        ]:
            code, out = self.run_cmd("add-edge", *args)
            self.assertEqual(code, 1, args)
            self.assertIn(message, out)
        self.assertEqual(len(self.graph()["edges"]), 1)

    def test_same_nodes_different_edge_type_allowed(self):
        self.ok("add-node", "--type", "goal", "--id", "g", "--label", "Goal")
        self.ok("add-edge", "--from", "g", "--to", "idea", "--type", "relates-to")
        self.ok("add-edge", "--from", "g", "--to", "idea", "--type", "refines")
        self.assertEqual(len(self.graph()["edges"]), 2)

    def test_remove_node_removes_its_edges(self):
        self.ok("add-node", "--type", "goal", "--id", "g", "--label", "Goal")
        self.ok("add-edge", "--from", "g", "--to", "idea", "--type", "relates-to")
        self.ok("remove-node", "--id", "g")
        self.assertNotIn("g", self.graph()["nodes"])
        self.assertEqual(self.graph()["edges"], [])

    def test_seed_cannot_be_removed(self):
        code, out = self.run_cmd("remove-node", "--id", "idea")
        self.assertEqual(code, 1)
        self.assertIn("cannot be removed", out)

    def test_questions_open_and_close(self):
        self.ok("add-node", "--type", "goal", "--id", "g", "--label", "Goal",
                "--question", "Q1", "--question", "Q2")
        self.ok("add-question", "--id", "g", "--question", "Q3")
        self.ok("close-question", "--id", "g", "--index", "2")
        self.assertEqual(self.graph()["nodes"]["g"]["open_questions"], ["Q1", "Q3"])
        code, out = self.run_cmd("close-question", "--id", "g", "--index", "3")
        self.assertEqual(code, 1)
        self.assertIn("index must be 1..2", out)
        self.ok("close-question", "--id", "g", "--all")
        self.assertEqual(self.graph()["nodes"]["g"]["open_questions"], [])

    def test_update_node_and_park(self):
        self.ok("add-node", "--type", "feature", "--id", "f", "--label", "Old")
        self.ok("update-node", "--id", "f", "--label", "New", "--parked", "true")
        node = self.graph()["nodes"]["f"]
        self.assertEqual((node["label"], node["status"]), ("New", "parked"))

    def test_record_logs_answer(self):
        self.ok("record", "--question", "Who uses it?", "--answer", "Members", "--node", "idea")
        log = self.graph()["log"]
        self.assertEqual(len(log), 1)
        self.assertEqual((log[0]["answer"], log[0]["nodes"]), ("Members", ["idea"]))


class DefinitionOfDoneTests(GraphTestCase):
    def test_new_graph_is_not_done(self):
        self.ok("init", "--title", "T", "--idea", "Idea")
        report = self.report()
        self.assertFalse(report["done"])
        for node_type in bg.CORE_TYPES:
            self.assertIn(node_type, report["missing_coverage"])
        self.assertTrue(any(m.startswith("horizon") for m in report["missing_coverage"]))

    def test_complete_graph_is_done(self):
        self.build_complete()
        report = self.report()
        self.assertTrue(report["done"], report)
        self.assertEqual(report["components"], 1)

    def test_open_question_blocks_done(self):
        self.build_complete()
        self.ok("add-question", "--id", "members", "--question", "Which gyms?")
        report = self.report()
        self.assertFalse(report["done"])
        self.assertEqual(report["open_questions"], [("members", "Which gyms?")])

    def test_isolated_node_blocks_done(self):
        self.build_complete()
        self.ok("add-node", "--type", "risk", "--id", "churn", "--label", "Gyms churn")
        report = self.report()
        self.assertFalse(report["done"])
        self.assertEqual(report["isolated"], ["churn"])

    def test_parked_node_still_needs_a_link(self):
        self.build_complete()
        self.ok("add-node", "--type", "feature", "--id", "later", "--label", "Later", "--parked")
        self.assertEqual(self.report()["isolated"], ["later"])

    def test_detached_group_blocks_done(self):
        self.build_complete()
        self.ok("add-node", "--type", "risk", "--id", "r", "--label", "Risk")
        self.ok("add-node", "--type", "constraint", "--id", "c", "--label", "Constraint")
        self.ok("add-edge", "--from", "r", "--to", "c", "--type", "threatens")
        report = self.report()
        self.assertFalse(report["done"])
        self.assertEqual(report["isolated"], [])
        self.assertEqual(report["detached_components"], [["c", "r"]])

    def test_edge_direction_ignored_for_connectedness(self):
        self.build_complete()
        self.ok("add-node", "--type", "risk", "--id", "r", "--label", "Risk")
        self.ok("add-edge", "--from", "r", "--to", "retention", "--type", "threatens")
        self.assertTrue(self.report()["done"])

    def test_long_horizon_needs_milestones(self):
        self.build_complete(horizon="long")
        self.assertIn("milestone (long-term project needs a roadmap)", self.report()["missing_coverage"])
        self.ok("add-node", "--type", "milestone", "--id", "m1", "--label", "MVP")
        self.ok("add-edge", "--from", "m1", "--to", "progress-emails", "--type", "delivers")
        self.assertTrue(self.report()["done"])

    def test_check_fails_with_json_report_when_not_done(self):
        self.ok("init", "--title", "T", "--idea", "Idea")
        code, out = self.run_cmd("check", "--json")
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(out)["done"])

    def test_check_passes_when_done(self):
        self.build_complete()
        code, out = self.run_cmd("check")
        self.assertEqual(code, 0)
        self.assertIn("DONE: definition of done met.", out)


class RenderTests(GraphTestCase):
    def test_render_writes_document(self):
        self.build_complete()
        self.ok("record", "--question", "Who uses it?", "--answer", "Gym members", "--node", "members")
        self.ok("render")
        doc = (self.graph_path.parent / "BRAINSTORM.md").read_text(encoding="utf-8")
        self.assertTrue(doc.startswith("# Gym app"))
        self.assertIn("**Status:** complete", doc)
        self.assertIn("```mermaid", doc)
        self.assertIn("-->|serves|", doc)
        self.assertIn("## Features", doc)
        self.assertIn("**A:** Gym members", doc)

    def test_render_escapes_quotes_in_mermaid(self):
        self.ok("init", "--title", "T", "--idea", 'The "best" idea')
        self.ok("render")
        doc = (self.graph_path.parent / "BRAINSTORM.md").read_text(encoding="utf-8")
        self.assertIn("idea: The 'best' idea", doc)


class CliTests(GraphTestCase):
    def test_runs_as_a_script(self):
        """The skill runs the file directly, so check it works outside unittest."""
        base = [sys.executable, str(SCRIPT), "--graph", str(self.graph_path)]
        subprocess.run([*base, "init", "--title", "T", "--idea", "Idea"], check=True, capture_output=True)
        result = subprocess.run([*base, "check"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("NOT DONE", result.stdout)


if __name__ == "__main__":
    unittest.main()
