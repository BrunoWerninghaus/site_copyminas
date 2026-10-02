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

    const pluralize = (value) =>
        value === 1 ? "1 produto" : `${value} produtos`;

    const apply = () => {
        const term = normalize(search.value);
        let visibleCount = 0;

        const matchesSearch = new Map();

        items.forEach((item) => {
            const haystack = normalize(item.dataset.search || "");
            const matches = !term || haystack.includes(term);
            matchesSearch.set(item, matches);

            const matchesCategory =
                activeCategory === "all" ||
                item.dataset.category === activeCategory;

            const visible = matchesCategory && matches;
            item.hidden = !visible;

            if (visible) {
                visibleCount += 1;
            }
        });

        filters.forEach((button) => {
            const category = button.dataset.categoryFilter || "all";
            const label = button.dataset.categoryLabel || "Categoria";

            const matchingCount = items.filter((item) => {
                if (!matchesSearch.get(item)) return false;
                return category === "all" || item.dataset.category === category;
            }).length;

            button.textContent = `${label} / ${matchingCount}`;
        });

        sections.forEach((section) => {
            const visibleCards = Array.from(
                section.querySelectorAll("[data-catalog-item]")
            ).filter((item) => !item.hidden);

            section.hidden = visibleCards.length === 0;

            const sectionCount = section.querySelector("[data-category-count]");
            if (sectionCount) {
                sectionCount.textContent = pluralize(visibleCards.length);
            }
        });

        if (count) {
            count.textContent = pluralize(visibleCount);
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

    apply();
})();
