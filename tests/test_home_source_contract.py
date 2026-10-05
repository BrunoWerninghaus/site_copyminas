from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
GLOBE_JS = ROOT / "src/copyminas/static/js/globe.js"
HOME_CSS = ROOT / "src/copyminas/static/css/pages/home.css"
BASE_CSS = ROOT / "src/copyminas/static/css/base.css"


class HomeSourceContractTestCase(unittest.TestCase):
    def test_home_preview_has_stable_orientation(self):
        source = GLOBE_JS.read_text(encoding="utf-8")

        preview_config = re.search(
            r'mode:\s*"preview"[\s\S]{0,140}?autoRotate:\s*(true|false)',
            source,
        )

        self.assertIsNotNone(preview_config)
        self.assertEqual(
            preview_config.group(1),
            "false",
            "Home preview must not drift away from the canonical Brazil/Minas view.",
        )

    def test_every_globe_is_focused_from_location_data(self):
        source = GLOBE_JS.read_text(encoding="utf-8")

        self.assertIn(
            "focusGlobeOnLocation(earth, location);",
            source,
            "Initial globe orientation must be derived from the same location data.",
        )

    def test_pin_label_position_is_clamped_to_its_mount(self):
        source = GLOBE_JS.read_text(encoding="utf-8")

        self.assertIn(
            "clampPinLabelPosition",
            source,
            "Projected globe labels must be constrained to the visible mount.",
        )

    def test_home_grid_children_are_allowed_to_shrink(self):
        source = HOME_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.home-hero\s*>\s*\*[\s\S]{0,120}?min-width:\s*0",
        )
        self.assertRegex(
            source,
            r"\.home-product__copy[\s\S]{0,120}?min-width:\s*0",
        )

    def test_home_text_has_safe_wrapping_rules(self):
        source = HOME_CSS.read_text(encoding="utf-8")

        self.assertIn("overflow-wrap: anywhere;", source)
        self.assertIn("text-wrap: balance;", source)

    def test_visual_contract_keeps_typewriter_typography(self):
        base = BASE_CSS.read_text(encoding="utf-8")

        self.assertIn("--font-display: var(--font-mono);", base)
        self.assertNotIn('"Segoe UI"', base)
        self.assertNotIn("sans-serif", base)

    def test_small_red_text_uses_readable_accent_token(self):
        base = BASE_CSS.read_text(encoding="utf-8")
        home = HOME_CSS.read_text(encoding="utf-8")

        self.assertIn("--red-text:", base)
        self.assertRegex(
            home,
            r"\.section-kicker\s*\{[^}]*color:\s*var\(--red-text\)",
        )


    def test_home_uses_container_driven_display_type(self):
        source = HOME_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.paper-panel--hero\s*\{[^}]*container-type:\s*inline-size",
        )
        self.assertRegex(
            source,
            r"\.paper-panel--hero h1\s*\{[^}]*font-size:[^;}]*cqi",
        )
        self.assertRegex(
            source,
            r"\.location-copy\s*\{[^}]*container-type:\s*inline-size",
        )

    def test_home_keeps_internal_register_metadata_without_showing_it(self):
        template = (ROOT / "src/copyminas/templates/public/home.html").read_text(encoding="utf-8")
        source = HOME_CSS.read_text(encoding="utf-8")

        for marker in (
            'data-section="00 / HOME"',
            'data-section="01 / SOLUÇÕES"',
            'data-section="02 / PRODUTOS"',
            'data-section="03 / EMPRESA"',
            'data-section="04 / LOCALIZAÇÃO"',
        ):
            self.assertIn(marker, template)

        self.assertRegex(
            source,
            r"\.page-home \[data-section\]::after,[\s\S]{0,420}?display:\s*none",
        )
        self.assertIn(".page-home .paper-panel::after", source)
        self.assertIn(".page-home .product-strip::before", source)
        self.assertIn(".page-home .location-copy::before", source)
        self.assertIn(".page-home .globe-card::before", source)

    def test_service_matrix_belongs_to_solutions_not_home(self):
        home = (ROOT / "src/copyminas/templates/public/home.html").read_text(encoding="utf-8")
        solutions = (ROOT / "src/copyminas/templates/public/solutions.html").read_text(encoding="utf-8")

        self.assertNotIn("ATENDIMENTO / MATRIZ", home)
        self.assertNotIn("service-matrix", home)
        self.assertIn("Formas de atendimento", solutions)
        self.assertIn(">Impressoras<", solutions)
        self.assertIn(">Computadores<", solutions)
        self.assertIn(">iPhones<", solutions)
        self.assertEqual(solutions.count('aria-label="Aluguel não disponível"'), 1)
        self.assertEqual(solutions.count('aria-label="Venda disponível"'), 3)
        self.assertEqual(solutions.count('aria-label="Manutenção disponível"'), 3)

    def test_catalog_hidden_state_overrides_card_display(self):
        source = (ROOT / "src/copyminas/static/css/paper.css").read_text(encoding="utf-8")
        self.assertIn(".product-card[hidden]", source)
        self.assertIn(".catalog-category[hidden]", source)
        self.assertIn("display: none !important;", source)

    def test_catalog_product_media_is_square(self):
        source = (ROOT / "src/copyminas/static/css/paper.css").read_text(encoding="utf-8")
        self.assertRegex(
            source,
            r"\.product-card__media\s*\{[^}]*aspect-ratio:\s*1\s*/\s*1",
        )
        self.assertRegex(
            source,
            r"\.page-products \.product-card\s*\{[^}]*grid-template-rows:\s*auto\s+1fr",
        )

    def test_home_featured_products_use_real_images_when_available(self):
        template = (ROOT / "src/copyminas/templates/public/home.html").read_text(encoding="utf-8")

        self.assertIn("{% if product.image_url %}", template)
        self.assertIn("filename=product.image_url", template)
        self.assertIn('class="home-product__media"', template)

    def test_public_shell_is_shared_from_home(self):
        template = (ROOT / "src/copyminas/templates/public/home.html").read_text(encoding="utf-8")

        self.assertIn('{% include "public/_site_header.html" %}', template)
        self.assertIn('{% include "public/_site_footer.html" %}', template)

    def test_home_never_masks_horizontal_overflow(self):
        source = HOME_CSS.read_text(encoding="utf-8").replace(" ", "").lower()

        self.assertNotIn("overflow-x:hidden", source)
        self.assertNotIn("overflow-x:clip", source)

    def test_navigation_items_wrap_as_items_not_inside_words(self):
        source = HOME_CSS.read_text(encoding="utf-8")

        self.assertRegex(
            source,
            r"\.site-nav a,[\s\S]{0,180}?white-space:\s*nowrap",
        )


if __name__ == "__main__":
    unittest.main()
