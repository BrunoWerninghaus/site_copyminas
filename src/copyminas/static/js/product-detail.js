"use strict";

(() => {
    const mainImage = document.querySelector("[data-product-main-image]");
    const thumbs = Array.from(document.querySelectorAll("[data-product-thumb]"));

    if (!mainImage || thumbs.length < 2) {
        return;
    }

    thumbs.forEach((button) => {
        button.addEventListener("click", () => {
            const src = button.dataset.imageSrc;
            const alt = button.dataset.imageAlt;

            if (!src) return;

            mainImage.src = src;
            if (alt) mainImage.alt = alt;

            thumbs.forEach((candidate) => {
                const active = candidate === button;
                candidate.classList.toggle("is-active", active);
                candidate.setAttribute("aria-pressed", String(active));
            });
        });
    });
})();
