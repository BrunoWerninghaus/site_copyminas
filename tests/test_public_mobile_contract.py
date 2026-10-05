from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAPER_CSS = ROOT / "src/copyminas/static/css/paper.css"


class PublicMobileContractTestCase(unittest.TestCase):
    def test_solutions_mobile_contract_is_explicit(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertIn("/* Solutions mobile contract */", source)
        self.assertRegex(
            source,
            r"@media \(max-width: 720px\)[\s\S]*?\.page-solutions\s*\{[\s\S]*?--page-x:\s*1rem",
        )

    def test_solutions_mobile_actions_use_full_width_touch_targets(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.page-solutions \.solutions-hero__actions \.paper-action\s*\{[\s\S]*?width:\s*100%[\s\S]*?min-height:\s*50px",
        )
        self.assertRegex(
            source,
            r"\.page-solutions \.solution-row__action a\s*\{[\s\S]*?width:\s*100%[\s\S]*?min-height:\s*46px",
        )
        self.assertRegex(
            source,
            r"\.page-solutions \.solutions-decision__actions \.button,[\s\S]*?\.page-solutions \.solutions-decision__link\s*\{[\s\S]*?min-height:\s*50px[\s\S]*?width:\s*100%",
        )

    def test_solutions_mobile_matrix_does_not_require_horizontal_scroll(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.page-solutions \.solutions-matrix\s*\{[\s\S]*?overflow:\s*visible",
        )
        self.assertRegex(
            source,
            r"\.page-solutions \.solutions-matrix__table\s*\{[\s\S]*?min-width:\s*0[\s\S]*?width:\s*100%",
        )
        self.assertRegex(
            source,
            r"\.page-solutions \.solutions-matrix__row\s*\{[\s\S]*?grid-template-columns:\s*minmax\(86px, 1\.4fr\)",
        )

    def test_solutions_mobile_does_not_mask_overflow(self):
        source = PAPER_CSS.read_text(encoding="utf-8").replace(" ", "").lower()

        mobile_start = source.index("/*solutionsmobilecontract*/")
        mobile = source[mobile_start:]

        self.assertNotIn("overflow-x:hidden", mobile)
        self.assertNotIn("overflow-x:clip", mobile)


if __name__ == "__main__":
    unittest.main()
