"use strict";

(() => {
    const body = document.body;
    const sidebar = document.querySelector("[data-admin-sidebar]");
    const collapseButton = document.querySelector("[data-admin-sidebar-toggle]");
    const mobileButton = document.querySelector("[data-admin-mobile-menu]");
    const sidebarBackdrop = document.querySelector("[data-admin-sidebar-backdrop]");

    const searchDialog = document.querySelector("[data-admin-search-dialog]");
    const searchOpeners = Array.from(document.querySelectorAll("[data-admin-search-open]"));
    const searchClosers = Array.from(document.querySelectorAll("[data-admin-search-close]"));
    const searchInput = document.querySelector("[data-admin-global-search]");
    const searchResults = document.querySelector("[data-admin-search-results]");
    const searchStatus = document.querySelector("[data-admin-search-status]");

    const STORAGE_KEY = "copyminas.admin.sidebar.collapsed";
    let searchTimer = null;
    let searchController = null;

    const setCollapsed = (collapsed) => {
        body.classList.toggle("admin-sidebar-collapsed", collapsed);

        if (collapseButton) {
            collapseButton.setAttribute("aria-expanded", String(!collapsed));
            collapseButton.setAttribute(
                "aria-label",
                collapsed ? "Expandir navegação" : "Recolher navegação"
            );
        }

        try {
            window.localStorage.setItem(STORAGE_KEY, collapsed ? "1" : "0");
        } catch (_error) {
            // Local persistence is optional.
        }
    };

    const initializeSidebar = () => {
        if (!sidebar) return;

        let collapsed = false;
        try {
            collapsed = window.localStorage.getItem(STORAGE_KEY) === "1";
        } catch (_error) {
            collapsed = false;
        }

        if (window.matchMedia("(min-width: 901px)").matches) {
            setCollapsed(collapsed);
        }
    };

    const setMobileOpen = (open) => {
        body.classList.toggle("admin-sidebar-open", open);

        if (mobileButton) {
            mobileButton.setAttribute("aria-expanded", String(open));
        }

        if (sidebarBackdrop) {
            sidebarBackdrop.hidden = !open;
        }
    };

    const clearResults = () => {
        if (searchResults) {
            searchResults.replaceChildren();
        }
    };

    const setSearchStatus = (message) => {
        if (searchStatus) {
            searchStatus.textContent = message;
        }
    };

    const createResult = (result) => {
        const link = document.createElement("a");
        link.className = "admin-global-search__result";
        link.href = result.href;

        const kind = document.createElement("span");
        kind.className = `admin-global-search__kind admin-global-search__kind--${result.kind}`;
        kind.textContent = result.kind_label;

        const copy = document.createElement("span");
        copy.className = "admin-global-search__copy";

        const title = document.createElement("strong");
        title.textContent = result.title;

        const meta = document.createElement("small");
        meta.textContent = result.meta || "";

        copy.append(title, meta);

        const arrow = document.createElement("span");
        arrow.className = "admin-global-search__arrow";
        arrow.setAttribute("aria-hidden", "true");
        arrow.textContent = "→";

        link.append(kind, copy, arrow);
        return link;
    };

    const renderSearch = (payload) => {
        clearResults();

        const results = Array.isArray(payload.results) ? payload.results : [];
        if (results.length === 0) {
            setSearchStatus("Nenhum resultado encontrado.");
            return;
        }

        const fragment = document.createDocumentFragment();
        results.forEach((result) => fragment.appendChild(createResult(result)));
        searchResults.appendChild(fragment);

        const unavailable = Object.entries(payload.sources || {})
            .filter(([, available]) => available === false)
            .map(([source]) => source);

        if (unavailable.length > 0) {
            setSearchStatus(
                `${results.length} resultado(s). Parte das fontes está temporariamente indisponível.`
            );
        } else {
            setSearchStatus(`${results.length} resultado(s).`);
        }
    };

    const runSearch = async () => {
        if (!searchInput) return;

        const query = searchInput.value.trim();
        if (!query) {
            clearResults();
            setSearchStatus("Digite para buscar em Produtos, Categorias e Contatos.");
            return;
        }

        if (searchController) {
            searchController.abort();
        }

        searchController = new AbortController();
        setSearchStatus("Buscando...");

        try {
            const response = await fetch(
                `/admin/busca?q=${encodeURIComponent(query)}`,
                {
                    headers: {"Accept": "application/json"},
                    signal: searchController.signal,
                    credentials: "same-origin",
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            renderSearch(await response.json());
        } catch (error) {
            if (error.name === "AbortError") {
                return;
            }
            clearResults();
            setSearchStatus("Não foi possível concluir a busca agora.");
        }
    };

    const openSearch = () => {
        if (!searchDialog) return;

        searchDialog.hidden = false;
        body.classList.add("admin-search-open");

        window.requestAnimationFrame(() => {
            searchInput?.focus();
            searchInput?.select();
        });
    };

    const closeSearch = () => {
        if (!searchDialog) return;

        searchDialog.hidden = true;
        body.classList.remove("admin-search-open");

        if (searchController) {
            searchController.abort();
            searchController = null;
        }
    };

    collapseButton?.addEventListener("click", () => {
        setCollapsed(!body.classList.contains("admin-sidebar-collapsed"));
    });

    mobileButton?.addEventListener("click", () => {
        setMobileOpen(!body.classList.contains("admin-sidebar-open"));
    });

    sidebarBackdrop?.addEventListener("click", () => setMobileOpen(false));

    searchOpeners.forEach((button) => button.addEventListener("click", openSearch));
    searchClosers.forEach((button) => button.addEventListener("click", closeSearch));

    searchInput?.addEventListener("input", () => {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(runSearch, 170);
    });

    searchInput?.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            const first = searchResults?.querySelector("a");
            if (first) {
                event.preventDefault();
                first.click();
            }
        }
    });

    document.addEventListener("keydown", (event) => {
        const shortcut = (event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k";
        if (shortcut) {
            event.preventDefault();
            if (searchDialog?.hidden) {
                openSearch();
            } else {
                closeSearch();
            }
            return;
        }

        if (event.key === "Escape") {
            if (searchDialog && !searchDialog.hidden) {
                closeSearch();
                return;
            }

            if (body.classList.contains("admin-sidebar-open")) {
                setMobileOpen(false);
            }
        }
    });

    window.addEventListener("resize", () => {
        if (window.matchMedia("(min-width: 901px)").matches) {
            setMobileOpen(false);
        }
    });

    initializeSidebar();
})();
