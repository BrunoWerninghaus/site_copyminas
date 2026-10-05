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


    def test_products_mobile_contract_compacts_catalog(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertIn("/* Products mobile contract */", source)
        self.assertRegex(
            source,
            r"@media \(max-width: 720px\)[\s\S]*?\.page-products\s*\{[\s\S]*?--page-x:\s*1rem",
        )
        self.assertRegex(
            source,
            r"\.page-products \.catalog-filter-group\s*\{[\s\S]*?display:\s*grid[\s\S]*?grid-template-columns:\s*repeat\(2",
        )
        self.assertRegex(
            source,
            r"\.page-products \.product-card\s*\{[\s\S]*?grid-template-columns:\s*clamp\(116px, 35vw, 150px\)",
        )
        self.assertRegex(
            source,
            r"\.page-products \.product-card__media\s*\{[\s\S]*?border-right:\s*1px solid var\(--paper-line\)[\s\S]*?border-bottom:\s*0",
        )

    def test_products_mobile_touch_targets_are_preserved(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.page-products \.catalog-search input\s*\{[\s\S]*?min-height:\s*50px",
        )
        self.assertRegex(
            source,
            r"\.page-products \.catalog-filter\s*\{[\s\S]*?min-height:\s*46px",
        )
        self.assertRegex(
            source,
            r"\.page-products \.catalog-unavailable \.paper-action\s*\{[\s\S]*?min-height:\s*50px",
        )

    def test_products_mobile_does_not_mask_overflow(self):
        source = PAPER_CSS.read_text(encoding="utf-8").replace(" ", "").lower()

        mobile_start = source.index("/*productsmobilecontract*/")
        mobile = source[mobile_start:]

        self.assertNotIn("overflow-x:hidden", mobile)
        self.assertNotIn("overflow-x:clip", mobile)

    def test_catalog_script_keeps_customer_facing_filter_counts(self):
        script = (
            ROOT / "src/copyminas/static/js/products.js"
        ).read_text(encoding="utf-8")

        self.assertIn('button.textContent = \`${label} (${matchingCount})\`;', script)
        self.assertNotIn('button.textContent = \`${label} / ${matchingCount}\`;', script)


if __name__ == "__main__":
    unittest.main()
