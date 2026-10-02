"use strict";

(() => {
    const search = document.querySelector("[data-catalog-search]");
    const items = Array.from(document.querySelectorAll("[data-catalog-item]"));
    const filters = Array.from(document.querySelectorAll("[data-category-filter]"));
    const sections = Array.from(document.querySelectorAll("[data-category-section]"));
    const count = document.querySelector("[data-catalog-count]");
    const empty = document.querySelector("[data-catalog-empty]");

    if (!search || items.length === 0) {
        return;
    }

    let activeCategory = "all";

    const normalize = (value) =>
        value
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim();

    const apply = () => {
        const term = normalize(search.value);
        let visibleCount = 0;

        items.forEach((item) => {
            const matchesCategory =
                activeCategory === "all" ||
                item.dataset.category === activeCategory;

            const haystack = normalize(item.dataset.search || "");
            const matchesSearch = !term || haystack.includes(term);
            const visible = matchesCategory && matchesSearch;

            item.hidden = !visible;
            if (visible) visibleCount += 1;
        });

        sections.forEach((section) => {
            const visibleCards = section.querySelectorAll(
                "[data-catalog-item]:not([hidden])"
            );
            section.hidden = visibleCards.length === 0;
        });

        if (count) {
            count.textContent =
                visibleCount === 1
                    ? "1 produto"
                    : `${visibleCount} produtos`;
        }

        if (empty) {
            empty.hidden = visibleCount !== 0;
        }
    };

    search.addEventListener("input", apply);

    filters.forEach((button) => {
        button.addEventListener("click", () => {
            activeCategory = button.dataset.categoryFilter || "all";

            filters.forEach((candidate) => {
                const active = candidate === button;
                candidate.classList.toggle("is-active", active);
                candidate.setAttribute("aria-pressed", String(active));
            });

            apply();
        });
    });
})();
