-- Copy Minas Site 3 — Home Manager v1
-- Adds editorial Home configuration inside the existing main_bd database.
-- Non-destructive: does not alter produtos, categorias or contatos.

CREATE TABLE IF NOT EXISTS site_home_config (
    id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
    announcement_active TINYINT(1) NOT NULL DEFAULT 0,
    announcement_label VARCHAR(80) NOT NULL DEFAULT 'AVISO',
    announcement_text VARCHAR(255) NOT NULL DEFAULT '',
    announcement_link_label VARCHAR(80) NOT NULL DEFAULT '',
    announcement_link_url VARCHAR(255) NOT NULL DEFAULT '',
    hero_kicker VARCHAR(180) NOT NULL,
    hero_title VARCHAR(255) NOT NULL,
    hero_summary TEXT NOT NULL,
    primary_cta_label VARCHAR(80) NOT NULL,
    primary_cta_url VARCHAR(255) NOT NULL,
    secondary_cta_label VARCHAR(80) NOT NULL,
    secondary_cta_url VARCHAR(255) NOT NULL,
    featured_product_ids TEXT NOT NULL,
    show_solutions TINYINT(1) NOT NULL DEFAULT 1,
    show_company TINYINT(1) NOT NULL DEFAULT 1,
    show_location TINYINT(1) NOT NULL DEFAULT 1,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS site_home_news (
    id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
    label VARCHAR(80) NOT NULL DEFAULT 'NOVIDADE',
    title VARCHAR(180) NOT NULL,
    body TEXT NOT NULL,
    link_label VARCHAR(80) NOT NULL DEFAULT '',
    link_url VARCHAR(255) NOT NULL DEFAULT '',
    active TINYINT(1) NOT NULL DEFAULT 1,
    sort_order INT UNSIGNED NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_site_home_news_active_order (active, sort_order, id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
