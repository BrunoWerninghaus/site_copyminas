import os
from pathlib import Path
from urllib.parse import urldefrag, urlparse
import unittest

from playwright.sync_api import sync_playwright


BASE_URL = os.getenv("PUBLIC_GATE_BASE_URL", "http://127.0.0.1:5000")
UNAVAILABLE_BASE_URL = os.getenv(
    "PUBLIC_GATE_UNAVAILABLE_BASE_URL",
    "http://127.0.0.1:5001",
)
ARTIFACT_DIR = Path(
    os.getenv("PUBLIC_GATE_ARTIFACT_DIR", "artifacts/public-gate")
)

VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "tablet": {"width": 820, "height": 1180},
    "mobile": {"width": 390, "height": 844},
}

PUBLIC_ROUTES = (
    ("/", 200, "home", "home"),
    ("/solucoes", 200, "solutions", "solutions"),
    ("/produtos", 200, "products", "products"),
    (
        "/produtos/brother-dcp-8157dn",
        200,
        "product-detail",
        "products",
    ),
    ("/empresa", 200, "company", "company"),
    ("/contato", 200, "contact", "contact"),
    ("/pagina-que-nao-existe", 404, "not-found", None),
)


class PublicBrowserGateTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)
        cls._playwright = sync_playwright().start()
        cls._browser = cls._playwright.chromium.launch(headless=True)

    @classmethod
    def tearDownClass(cls):
        cls._browser.close()
        cls._playwright.stop()

    def _new_page(self, viewport):
        context = self._browser.new_context(
            viewport=viewport,
            locale="pt-BR",
            color_scheme="dark",
        )
        page = context.new_page()
        page.set_default_timeout(8_000)
        return context, page

    def _assert_no_horizontal_overflow(self, page, label):
        metrics = page.evaluate(
            """() => ({
                viewport: document.documentElement.clientWidth,
                scroll: document.documentElement.scrollWidth,
                bodyScroll: document.body ? document.body.scrollWidth : 0
            })"""
        )
        overflow = max(metrics["scroll"], metrics["bodyScroll"]) - metrics["viewport"]
        self.assertLessEqual(
            overflow,
            1,
            f"{label}: horizontal overflow detected: {metrics}",
        )

    def _assert_page_semantics(self, page, expected_nav):
        self.assertEqual(page.locator("main#main-content").count(), 1)
        self.assertEqual(page.locator("h1").count(), 1)
        self.assertTrue(page.locator("title").count() == 0 or page.title().strip())
        self.assertTrue(
            page.locator('meta[name="description"]').get_attribute("content").strip()
        )

        for image in page.locator("img").all():
            self.assertIsNotNone(
                image.get_attribute("alt"),
                "Every public image must declare alt, including decorative alt=''.",
            )

        current = page.locator('.public-nav a[aria-current="page"]')
        if expected_nav is None:
            self.assertEqual(current.count(), 0)
        else:
            self.assertEqual(current.count(), 1)
            href = current.first.get_attribute("href")
            expected_fragment = {
                "home": "/home",
                "solutions": "/solucoes",
                "products": "/produtos",
                "company": "/empresa",
                "contact": "/contato",
            }[expected_nav]
            self.assertIn(expected_fragment, href)

    def _assert_keyboard_entry(self, page):
        page.locator("body").press("Home")
        page.keyboard.press("Tab")
        active = page.evaluate(
            """() => ({
                className: document.activeElement?.className || "",
                focusVisible: !!document.activeElement?.matches?.(":focus-visible")
            })"""
        )
        self.assertIn("skip-link", active["className"])
        self.assertTrue(active["focusVisible"])

    def _assert_navigation(self, page, viewport_name):
        toggle = page.locator("[data-public-menu-toggle]")
        nav = page.locator("[data-public-nav]")

        if viewport_name == "desktop":
            self.assertFalse(toggle.is_visible())
            self.assertTrue(nav.is_visible())
            return

        self.assertTrue(toggle.is_visible())
        self.assertEqual(toggle.get_attribute("aria-expanded"), "false")
        toggle.click()
        self.assertEqual(toggle.get_attribute("aria-expanded"), "true")
        self.assertTrue(nav.is_visible())
        self.assertIn("public-menu-open", page.locator("html").get_attribute("class") or "")
        self.assertEqual(
            page.locator("[data-public-menu-label]").inner_text().strip(),
            "FECHAR",
        )

        page.keyboard.press("Escape")
        self.assertEqual(toggle.get_attribute("aria-expanded"), "false")
        self.assertNotIn(
            "public-menu-open",
            page.locator("html").get_attribute("class") or "",
        )
        self.assertEqual(
            page.locator("[data-public-menu-label]").inner_text().strip(),
            "MENU",
        )

    def _assert_no_console_errors(
        self,
        console_errors,
        page_errors,
        label,
        expected_status=200,
    ):
        if expected_status == 404:
            console_errors = [
                message
                for message in console_errors
                if "server responded with a status of 404" not in message
            ]

        self.assertEqual(
            console_errors,
            [],
            f"{label}: console errors: {console_errors}",
        )
        self.assertEqual(
            page_errors,
            [],
            f"{label}: page errors: {page_errors}",
        )

    def test_public_route_matrix_desktop_tablet_mobile(self):
        for viewport_name, viewport in VIEWPORTS.items():
            for path, expected_status, screenshot_name, expected_nav in PUBLIC_ROUTES:
                with self.subTest(viewport=viewport_name, path=path):
                    context, page = self._new_page(viewport)
                    console_errors = []
                    page_errors = []
                    page.on(
                        "console",
                        lambda message: (
                            console_errors.append(message.text)
                            if message.type == "error"
                            else None
                        ),
                    )
                    page.on("pageerror", lambda error: page_errors.append(str(error)))

                    response = page.goto(
                        BASE_URL + path,
                        wait_until="domcontentloaded",
                    )
                    self.assertIsNotNone(response)
                    self.assertEqual(response.status, expected_status)

                    if path == "/":
                        page.wait_for_timeout(1_500)
                    else:
                        page.wait_for_timeout(150)

                    self._assert_page_semantics(page, expected_nav)
                    self._assert_no_horizontal_overflow(
                        page,
                        f"{viewport_name} {path}",
                    )

                    screenshot_dir = ARTIFACT_DIR / viewport_name
                    screenshot_dir.mkdir(parents=True, exist_ok=True)
                    page.screenshot(
                        path=str(screenshot_dir / f"{screenshot_name}.png"),
                        full_page=True,
                    )

                    self._assert_keyboard_entry(page)
                    self._assert_navigation(page, viewport_name)

                    self._assert_no_console_errors(
                        console_errors,
                        page_errors,
                        f"{viewport_name} {path}",
                        expected_status=expected_status,
                    )
                    context.close()

    def test_catalog_search_and_filters_in_desktop_and_mobile(self):
        for viewport_name in ("desktop", "mobile"):
            with self.subTest(viewport=viewport_name):
                context, page = self._new_page(VIEWPORTS[viewport_name])
                response = page.goto(
                    BASE_URL + "/produtos",
                    wait_until="domcontentloaded",
                )
                self.assertEqual(response.status, 200)

                search = page.locator("[data-catalog-search]")
                search.fill("cabo")
                self.assertEqual(
                    page.locator("[data-catalog-count]").inner_text().strip().casefold(),
                    "1 produto",
                )
                self.assertEqual(
                    page.locator("[data-catalog-item]:visible").count(),
                    1,
                )
                self._assert_no_horizontal_overflow(
                    page,
                    f"{viewport_name} catalog search",
                )

                search.fill("")
                page.locator(
                    '[data-category-filter][data-category-label="Impressoras"]'
                ).click()
                self.assertEqual(
                    page.locator("[data-catalog-count]").inner_text().strip().casefold(),
                    "6 produtos",
                )
                self.assertEqual(
                    page.locator("[data-catalog-item]:visible").count(),
                    6,
                )
                self.assertIn(
                    "(6)",
                    page.locator(
                        '[data-category-filter][data-category-label="Impressoras"]'
                    ).inner_text(),
                )
                context.close()

    def test_product_detail_specs_and_no_image_state(self):
        for viewport_name in VIEWPORTS:
            with self.subTest(viewport=viewport_name):
                context, page = self._new_page(VIEWPORTS[viewport_name])
                response = page.goto(
                    BASE_URL + "/produtos/brother-dcp-8157dn",
                    wait_until="domcontentloaded",
                )
                self.assertEqual(response.status, 200)
                self.assertTrue(
                    page.get_by_text("IMAGEM DO PRODUTO", exact=False).is_visible()
                )
                self.assertGreater(
                    page.locator(".spec-sheet dl > div").count(),
                    5,
                )
                self.assertTrue(
                    page.get_by_role(
                        "link",
                        name="Consultar este produto",
                    ).is_visible()
                )
                self._assert_no_horizontal_overflow(
                    page,
                    f"{viewport_name} product detail",
                )
                context.close()

    def test_product_gallery_script_switches_image(self):
        context, page = self._new_page(VIEWPORTS["desktop"])
        page.goto(
            BASE_URL + "/produtos/brother-dcp-8157dn",
            wait_until="domcontentloaded",
        )
        page.set_content(
            """
            <img data-product-main-image src="/static/a.png" alt="Imagem A">
            <button
                data-product-thumb
                data-image-src="/static/a.png"
                data-image-alt="Imagem A"
                aria-pressed="true"
            >A</button>
            <button
                data-product-thumb
                data-image-src="/static/b.png"
                data-image-alt="Imagem B"
                aria-pressed="false"
            >B</button>
            """
        )
        page.add_script_tag(url=BASE_URL + "/static/js/product-detail.js")
        thumbs = page.locator("[data-product-thumb]")
        thumbs.nth(1).click()

        main_image = page.locator("[data-product-main-image]")
        self.assertTrue(main_image.get_attribute("src").endswith("/static/b.png"))
        self.assertEqual(main_image.get_attribute("alt"), "Imagem B")
        self.assertEqual(thumbs.nth(0).get_attribute("aria-pressed"), "false")
        self.assertEqual(thumbs.nth(1).get_attribute("aria-pressed"), "true")
        context.close()

    def test_contact_native_validation_and_product_prefill(self):
        for viewport_name in ("desktop", "mobile"):
            with self.subTest(viewport=viewport_name):
                context, page = self._new_page(VIEWPORTS[viewport_name])
                page.goto(BASE_URL + "/contato", wait_until="domcontentloaded")
                page.get_by_role("button", name="Enviar solicitação").click()
                self.assertGreater(page.locator("form :invalid").count(), 0)
                self.assertTrue(page.url.endswith("/contato"))

                page.goto(
                    BASE_URL + "/contato?product=brother-dcp-8157dn",
                    wait_until="domcontentloaded",
                )
                self.assertTrue(
                    page.get_by_text("Produto selecionado", exact=True).is_visible()
                )
                self.assertIn(
                    "Brother DCP-8157DN",
                    page.locator('textarea[name="message"]').input_value(),
                )
                context.close()

    def test_internal_public_links_resolve(self):
        context, page = self._new_page(VIEWPORTS["desktop"])
        urls = set()

        for path, expected_status, _, _ in PUBLIC_ROUTES:
            page.goto(BASE_URL + path, wait_until="domcontentloaded")
            if expected_status not in (200, 404):
                continue
            hrefs = page.locator("a[href]").evaluate_all(
                """(nodes) => nodes.map((node) => ({
                    raw: node.getAttribute("href"),
                    absolute: node.href
                }))"""
            )
            for entry in hrefs:
                raw = entry["raw"] or ""
                if raw.startswith("#"):
                    continue
                href = entry["absolute"]
                parsed = urlparse(href)
                if parsed.scheme not in ("http", "https"):
                    continue
                if parsed.netloc != urlparse(BASE_URL).netloc:
                    continue
                clean, _ = urldefrag(href)
                urls.add(clean)

        failures = []
        for url in sorted(urls):
            response = context.request.get(url, fail_on_status_code=False)
            if response.status >= 400:
                failures.append((url, response.status))

        self.assertEqual(failures, [], f"Broken internal links: {failures}")
        context.close()

    def test_catalog_503_is_branded_and_responsive(self):
        for viewport_name, viewport in VIEWPORTS.items():
            with self.subTest(viewport=viewport_name):
                context, page = self._new_page(viewport)
                response = page.goto(
                    UNAVAILABLE_BASE_URL + "/produtos",
                    wait_until="domcontentloaded",
                )
                self.assertEqual(response.status, 503)
                self.assertTrue(
                    page.get_by_text(
                        "Não foi possível consultar os produtos agora.",
                        exact=True,
                    ).is_visible()
                )
                self.assertTrue(page.locator(".public-header").is_visible())
                self.assertTrue(page.locator(".public-footer").is_visible())
                self._assert_no_horizontal_overflow(
                    page,
                    f"{viewport_name} catalog 503",
                )

                screenshot_dir = ARTIFACT_DIR / viewport_name
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                page.screenshot(
                    path=str(screenshot_dir / "catalog-503.png"),
                    full_page=True,
                )
                context.close()


    def test_public_brand_assets_render_with_visible_shell(self):
        for viewport_name, viewport in VIEWPORTS.items():
            with self.subTest(viewport=viewport_name):
                context, page = self._new_page(viewport)
                page.goto(BASE_URL + "/", wait_until="domcontentloaded")

                header_image = page.locator(".public-header__brand img")
                footer_image = page.locator(".public-footer__brand img")

                self.assertGreater(
                    header_image.evaluate("(img) => img.naturalWidth"),
                    0,
                )
                self.assertGreater(
                    footer_image.evaluate("(img) => img.naturalWidth"),
                    0,
                )

                header_bg = page.locator(".public-header__brand").evaluate(
                    "(node) => getComputedStyle(node).backgroundColor"
                )
                footer_bg = footer_image.evaluate(
                    "(node) => getComputedStyle(node).backgroundColor"
                )

                self.assertNotIn(header_bg, ("rgba(0, 0, 0, 0)", "transparent"))
                self.assertNotIn(footer_bg, ("rgba(0, 0, 0, 0)", "transparent"))

                pixel_stats = header_image.evaluate(
                    """(img) => {
                        const canvas = document.createElement("canvas");
                        canvas.width = img.naturalWidth;
                        canvas.height = img.naturalHeight;
                        const ctx = canvas.getContext("2d", {willReadFrequently: true});
                        ctx.drawImage(img, 0, 0);
                        const data = ctx.getImageData(
                            0,
                            0,
                            canvas.width,
                            canvas.height
                        ).data;

                        let visible = 0;
                        let minLuma = 255;
                        let maxLuma = 0;

                        for (let i = 0; i < data.length; i += 4) {
                            const alpha = data[i + 3];
                            if (alpha < 16) continue;
                            visible += 1;
                            const luma =
                                data[i] * 0.2126 +
                                data[i + 1] * 0.7152 +
                                data[i + 2] * 0.0722;
                            minLuma = Math.min(minLuma, luma);
                            maxLuma = Math.max(maxLuma, luma);
                        }

                        return {
                            width: canvas.width,
                            height: canvas.height,
                            visible,
                            total: canvas.width * canvas.height,
                            lumaRange: maxLuma - minLuma,
                        };
                    }"""
                )

                self.assertGreater(
                    pixel_stats["visible"],
                    max(10, int(pixel_stats["total"] * 0.01)),
                    f"Brand asset has too few visible pixels: {pixel_stats}",
                )
                self.assertGreater(
                    pixel_stats["lumaRange"],
                    20,
                    f"Brand asset lacks visible tonal detail: {pixel_stats}",
                )
                context.close()

    def test_mobile_menu_visual_evidence(self):
        for viewport_name in ("tablet", "mobile"):
            with self.subTest(viewport=viewport_name):
                context, page = self._new_page(VIEWPORTS[viewport_name])
                page.goto(BASE_URL + "/", wait_until="domcontentloaded")

                page.locator("[data-public-menu-toggle]").click()
                page.wait_for_timeout(220)
                self.assertEqual(
                    page.locator("[data-public-menu-toggle]").get_attribute(
                        "aria-expanded"
                    ),
                    "true",
                )

                screenshot_dir = ARTIFACT_DIR / viewport_name
                screenshot_dir.mkdir(parents=True, exist_ok=True)
                page.screenshot(
                    path=str(screenshot_dir / "menu-open.png"),
                    full_page=False,
                )
                context.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
