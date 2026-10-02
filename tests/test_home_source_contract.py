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
