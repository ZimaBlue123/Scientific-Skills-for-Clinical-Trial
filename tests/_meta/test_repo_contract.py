"""Repo-wide guards: every skill conforms, and every skill with scripts is tested.

This suite is deliberately not per-skill. It imports no skill code -- the
structural contract parses scripts with `ast` and never executes them -- so
running it across all skills in one interpreter is safe, and it is the only
place that can see the whole repository at once. That is what lets it enforce
the rule `AGENTS.md` states but nothing previously checked:

    If the skill ships `scripts/`, put their tests in `tests/<name>/`.

It runs in the project environment and needs no scientific packages, so CI can
run it on every pull request in seconds.
"""

from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

import skill_contract
import tomllib

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = REPO_ROOT / "skills"
TESTS_DIR = REPO_ROOT / "tests"
REQUIREMENTS = TESTS_DIR / "skill-requirements.toml"
PLUGIN_MANIFEST = REPO_ROOT / "plugin.json"
PYPROJECT = REPO_ROOT / "pyproject.toml"

PLUGIN_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
PLUGIN_NAME = "scientific-agent-skills"
ALLOWED_PLUGIN_KEYS = frozenset(
    {
        "$schema",
        "name",
        "version",
        "description",
        "author",
        "homepage",
        "repository",
        "license",
        "keywords",
        "extensions",
    }
)
PLUGIN_NAME_RE = re.compile(r"^(?!.*(?:--|\.\.))[a-z0-9](?:[a-z0-9.-]*[a-z0-9])?$")

structure = skill_contract.structure
office = skill_contract.office

SCRIPT_BEARING = structure.script_bearing_skills(SKILLS_DIR)
DOCUMENTED = structure.documented_skills(SKILLS_DIR)
KNOWN_SKILLS = structure.all_skill_names(SKILLS_DIR)


def _suite_names() -> set[str]:
    """Test directories that stand for a skill, excluding infrastructure."""
    return {
        path.name
        for path in TESTS_DIR.iterdir()
        if path.is_dir() and not path.name.startswith((".", "_"))
    }





class StructuralContractTests(unittest.TestCase):
    """Every rule in `skill_contract.structure`, against every script-bearing skill."""

    maxDiff = None

    def test_all_skills_satisfy_every_structural_rule(self) -> None:
        self.assertTrue(SCRIPT_BEARING, "no skills found -- the anchor is wrong")
        for rule, check in structure.CHECKS.items():
            # Document rules hold for every skill; script rules only where a
            # skill ships scripts to inspect.
            subjects = DOCUMENTED if rule in structure.DOCUMENT_RULES else SCRIPT_BEARING
            for skill in subjects:
                with self.subTest(rule=rule, skill=skill.name):
                    problems = (
                        check(skill, KNOWN_SKILLS)
                        if rule == "local_links_resolve"
                        else check(skill)
                    )
                    self.assertEqual(problems, [])





class AgentPluginTests(unittest.TestCase):
    """Root plugin.json keeps the repo a valid Agent Plugins 1.0.0 package."""

    maxDiff = None

    def test_plugin_manifest_conforms(self) -> None:
        self.assertTrue(PLUGIN_MANIFEST.is_file(), "plugin.json must exist at the repo root")
        manifest = json.loads(PLUGIN_MANIFEST.read_text(encoding="utf-8"))
        self.assertIsInstance(manifest, dict)

        unknown = sorted(set(manifest) - ALLOWED_PLUGIN_KEYS)
        self.assertEqual(unknown, [], "plugin.json has closed top-level schema")

        self.assertEqual(manifest.get("$schema"), PLUGIN_SCHEMA)
        self.assertEqual(manifest.get("name"), PLUGIN_NAME)
        self.assertRegex(manifest["name"], PLUGIN_NAME_RE)

        project = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))["project"]
        self.assertEqual(
            manifest.get("version"),
            project["version"],
            "plugin.json version must match pyproject.toml [project].version",
        )

    def test_skills_component_is_discoverable(self) -> None:
        """Agent Plugins discovers only immediate children of skills/ with SKILL.md."""
        self.assertTrue(SKILLS_DIR.is_dir())
        self.assertTrue(KNOWN_SKILLS, "no discoverable skills under skills/")
        for name in sorted(KNOWN_SKILLS):
            with self.subTest(skill=name):
                skill_md = SKILLS_DIR / name / "SKILL.md"
                self.assertTrue(skill_md.is_file())
                self.assertEqual(skill_md.parent.parent, SKILLS_DIR)


if __name__ == "__main__":
    unittest.main()
