"use strict";

(() => {
    const search = document.querySelector("[data-admin-contact-search]");
    const status = document.querySelector("[data-admin-contact-status]");
    const service = document.querySelector("[data-admin-contact-service]");
    const rows = Array.from(document.querySelectorAll("[data-admin-contact]"));
    const count = document.querySelector("[data-admin-contact-count]");
    const empty = document.querySelector("[data-admin-contact-empty]");

    if (!search || rows.length === 0) {
        return;
    }

    const normalize = (value) =>
        value
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .toLowerCase()
            .trim();

    const apply = () => {
        const term = normalize(search.value);
        const statusValue = status?.value || "all";
        const serviceValue = service?.value || "all";
        let visible = 0;

        rows.forEach((row) => {
            const matchesSearch =
                !term || normalize(row.dataset.search || "").includes(term);
            const matchesStatus =
                statusValue === "all" || row.dataset.status === statusValue;
            const matchesService =
                serviceValue === "all" || row.dataset.service === serviceValue;

            const show = matchesSearch && matchesStatus && matchesService;
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
    status?.addEventListener("change", apply);
    service?.addEventListener("change", apply);

    apply();
})();
