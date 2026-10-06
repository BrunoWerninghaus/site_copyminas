from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PAPER_CSS = ROOT / "src/copyminas/static/css/paper.css"
CONTACT_CSS = ROOT / "src/copyminas/static/css/pages/contact.css"


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

        self.assertIn('button.textContent = `${label} (${matchingCount})`;', script)
        self.assertNotIn('button.textContent = `${label} / ${matchingCount}`;', script)


    def test_product_detail_mobile_contract_is_explicit(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertIn("/* Product detail mobile contract */", source)
        self.assertRegex(
            source,
            r"@media \(max-width: 720px\)[\s\S]*?\.page-product-detail\s*\{[\s\S]*?--page-x:\s*1rem",
        )

    def test_product_detail_mobile_media_and_gallery_fit_screen(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.page-product-detail \.product-sheet__media\s*\{[\s\S]*?aspect-ratio:\s*1\s*/\s*1",
        )
        self.assertRegex(
            source,
            r"\.page-product-detail \.product-sheet__gallery\s*\{[\s\S]*?grid-template-columns:\s*repeat\(3",
        )
        self.assertRegex(
            source,
            r"\.page-product-detail \.product-thumb\s*\{[\s\S]*?min-height:\s*64px",
        )

    def test_product_detail_mobile_actions_and_specs_are_readable(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.page-product-detail \.paper-actions\s*\{[\s\S]*?grid-template-columns:\s*1fr",
        )
        self.assertRegex(
            source,
            r"\.page-product-detail \.paper-actions \.paper-action\s*\{[\s\S]*?width:\s*100%[\s\S]*?min-height:\s*50px",
        )
        self.assertRegex(
            source,
            r"\.page-product-detail \.spec-sheet dl > div\s*\{[\s\S]*?grid-template-columns:\s*1fr",
        )
        self.assertRegex(
            source,
            r"\.page-product-detail \.spec-sheet__heading\s*\{[\s\S]*?position:\s*static",
        )

    def test_product_detail_mobile_does_not_mask_overflow(self):
        source = PAPER_CSS.read_text(encoding="utf-8").replace(" ", "").lower()

        mobile_start = source.index("/*productdetailmobilecontract*/")
        mobile = source[mobile_start:]

        self.assertNotIn("overflow-x:hidden", mobile)
        self.assertNotIn("overflow-x:clip", mobile)


    def test_company_mobile_contract_is_explicit(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertIn("/* Company mobile contract */", source)
        self.assertRegex(
            source,
            r"@media \(max-width: 720px\)[\s\S]*?\.page-company\s*\{[\s\S]*?--page-x:\s*1rem",
        )

    def test_company_mobile_register_is_compact_and_readable(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.page-company \.company-register__item\s*\{[\s\S]*?grid-template-columns:\s*minmax\(104px, \.42fr\) minmax\(0, 1\.58fr\)",
        )
        self.assertRegex(
            source,
            r"\.page-company \.company-register__item\s*\{[\s\S]*?min-height:\s*0",
        )
        self.assertRegex(
            source,
            r"@media \(max-width: 380px\)[\s\S]*?\.page-company \.company-register__item\s*\{[\s\S]*?grid-template-columns:\s*1fr",
        )

    def test_company_mobile_directory_uses_single_column_touch_rows(self):
        source = PAPER_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.page-company \.company-directory__links\s*\{[\s\S]*?grid-template-columns:\s*1fr",
        )
        self.assertRegex(
            source,
            r"\.page-company \.company-directory__links a\s*\{[\s\S]*?min-height:\s*74px",
        )

    def test_company_mobile_does_not_mask_overflow(self):
        source = PAPER_CSS.read_text(encoding="utf-8").replace(" ", "").lower()

        mobile_start = source.index("/*companymobilecontract*/")
        mobile = source[mobile_start:]

        self.assertNotIn("overflow-x:hidden", mobile)
        self.assertNotIn("overflow-x:clip", mobile)


    def test_contact_mobile_contract_is_explicit(self):
        source = CONTACT_CSS.read_text(encoding="utf-8")

        self.assertIn("/* Contact mobile contract */", source)
        self.assertRegex(
            source,
            r"@media \(max-width: 720px\)[\s\S]*?\.contact-page\s*\{[\s\S]*?--page-x:\s*1rem",
        )

    def test_contact_mobile_form_is_touch_friendly(self):
        source = CONTACT_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.contact-form input,[\s\S]*?\.contact-form select\s*\{[\s\S]*?min-height:\s*52px[\s\S]*?font-size:\s*16px",
        )
        self.assertRegex(
            source,
            r"\.contact-form textarea\s*\{[\s\S]*?min-height:\s*140px[\s\S]*?font-size:\s*16px",
        )
        self.assertRegex(
            source,
            r"\.contact-form__submit \.paper-action\s*\{[\s\S]*?width:\s*100%[\s\S]*?min-height:\s*52px",
        )
        self.assertRegex(
            source,
            r"\.contact-consent input\s*\{[\s\S]*?width:\s*20px[\s\S]*?height:\s*20px",
        )

    def test_contact_mobile_channels_and_directory_are_compact(self):
        source = CONTACT_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.contact-channel\s*\{[\s\S]*?min-height:\s*0",
        )
        self.assertRegex(
            source,
            r"\.contact-channel a\s*\{[\s\S]*?min-height:\s*44px",
        )
        self.assertRegex(
            source,
            r"\.contact-directory dl > div\s*\{[\s\S]*?grid-template-columns:\s*minmax\(100px, \.4fr\) minmax\(0, 1\.6fr\)",
        )

    def test_contact_mobile_does_not_mask_overflow(self):
        source = CONTACT_CSS.read_text(encoding="utf-8").replace(" ", "").lower()

        mobile_start = source.index("/*contactmobilecontract*/")
        mobile = source[mobile_start:]

        self.assertNotIn("overflow-x:hidden", mobile)
        self.assertNotIn("overflow-x:clip", mobile)


if __name__ == "__main__":
    unittest.main()
