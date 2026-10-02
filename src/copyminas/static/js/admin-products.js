"use strict";

(() => {
    const search = document.querySelector("[data-admin-product-search]");
    const rows = Array.from(document.querySelectorAll("[data-admin-product]"));
    const filters = Array.from(document.querySelectorAll("[data-admin-status]"));
    const count = document.querySelector("[data-admin-product-count]");
    const empty = document.querySelector("[data-admin-product-empty]");

    if (!search || rows.length === 0) {
        return;
    }

    let status = "all";

    const normalize = (value) =>
        value
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim();

    const apply = () => {
        const term = normalize(search.value);
        let visible = 0;

        rows.forEach((row) => {
            const matchesStatus =
                status === "all" || row.dataset.status === status;
            const matchesSearch =
                !term || normalize(row.dataset.search || "").includes(term);
            const show = matchesStatus && matchesSearch;

            row.hidden = !show;
            if (show) visible += 1;
        });

        if (count) {
            count.textContent =
                visible === 1 ? "1 registro" : `${visible} registros`;
        }

        if (empty) {
            empty.hidden = visible !== 0;
        }
    };

    search.addEventListener("input", apply);

    filters.forEach((button) => {
        button.addEventListener("click", () => {
            status = button.dataset.adminStatus || "all";
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
