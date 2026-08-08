from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from audit_planning_docs import audit


class PlanningDocsAuditTests(unittest.TestCase):
    def make_root(self) -> tuple[TemporaryDirectory, Path]:
        temporary = TemporaryDirectory()
        root = Path(temporary.name)
        (root / "docs" / "planning").mkdir(parents=True)
        return temporary, root

    def test_valid_index_and_links_pass(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        planning = root / "docs" / "planning"
        (planning / "README.md").write_text(
            "# Index\n\n[technical-design.md](technical-design.md)\n", encoding="utf-8"
        )
        (planning / "technical-design.md").write_text(
            "# Design\n\n[project readme](<../../Project README.md>)\n", encoding="utf-8"
        )
        (root / "Project README.md").write_text("# Project\n", encoding="utf-8")

        self.assertEqual(audit(root), [])

    def test_unindexed_document_fails(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        planning = root / "docs" / "planning"
        (planning / "README.md").write_text("# Index\n", encoding="utf-8")
        (planning / "prd.md").write_text("# PRD\n", encoding="utf-8")

        self.assertEqual(
            audit(root), ["unindexed planning document: docs/planning/prd.md"]
        )

    def test_broken_relative_link_fails(self) -> None:
        temporary, root = self.make_root()
        self.addCleanup(temporary.cleanup)
        planning = root / "docs" / "planning"
        (planning / "README.md").write_text(
            "# Index\n\n[prd.md](prd.md)\n", encoding="utf-8"
        )
        (planning / "prd.md").write_text(
            "# PRD\n\n[missing](../missing.md)\n", encoding="utf-8"
        )

        self.assertEqual(
            audit(root), ["broken local link in docs/planning/prd.md: ../missing.md"]
        )


if __name__ == "__main__":
    unittest.main()
