"use strict";

(() => {
    const header = document.querySelector("[data-public-header]");
    const toggle = document.querySelector("[data-public-menu-toggle]");
    const nav = document.querySelector("[data-public-nav]");

    if (!header || !toggle || !nav) return;

    const setOpen = (open) => {
        header.classList.toggle("is-open", open);
        toggle.setAttribute("aria-expanded", String(open));
        toggle.setAttribute("aria-label", open ? "Fechar menu" : "Abrir menu");
    };

    toggle.addEventListener("click", () => {
        setOpen(!header.classList.contains("is-open"));
    });

    nav.addEventListener("click", (event) => {
        if (event.target.closest("a")) {
            setOpen(false);
        }
    });

    document.addEventListener("keydown", (event) => {
        if (event.key === "Escape" && header.classList.contains("is-open")) {
            setOpen(false);
            toggle.focus();
        }
    });

    window.addEventListener("resize", () => {
        if (window.matchMedia("(min-width: 861px)").matches) {
            setOpen(false);
        }
    });
})();
