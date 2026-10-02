"use strict";

(() => {
    const screen = document.querySelector("[data-intro-screen]");

    if (!screen) {
        return;
    }

    const homeUrl = screen.dataset.homeUrl;
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    let leaving = false;
    let touchStartY = null;

    const goHome = () => {
        if (leaving || !homeUrl) {
            return;
        }

        leaving = true;

        if (reduceMotion) {
            window.location.assign(homeUrl);
            return;
        }

        screen.classList.add("intro-screen--leaving");

        window.setTimeout(() => {
            window.location.assign(homeUrl);
        }, 360);
    };

    screen.addEventListener("click", goHome);

    window.addEventListener(
        "wheel",
        (event) => {
            if (event.deltaY > 8) {
                event.preventDefault();
                goHome();
            }
        },
        { passive: false }
    );

    window.addEventListener("keydown", (event) => {
        if (["Enter", " ", "ArrowDown", "PageDown"].includes(event.key)) {
            event.preventDefault();
            goHome();
        }
    });

    window.addEventListener(
        "touchstart",
        (event) => {
            touchStartY = event.changedTouches[0]?.clientY ?? null;
        },
        { passive: true }
    );

    window.addEventListener(
        "touchend",
        (event) => {
            if (touchStartY === null) {
                return;
            }

            const touchEndY = event.changedTouches[0]?.clientY ?? touchStartY;
            const distance = touchStartY - touchEndY;
            touchStartY = null;

            if (distance > 36) {
                goHome();
            }
        },
        { passive: true }
    );

    requestAnimationFrame(() => {
        screen.focus({ preventScroll: true });
    });
})();
