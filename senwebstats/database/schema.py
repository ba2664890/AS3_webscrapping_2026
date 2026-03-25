"""
Schéma de base de données SQLite.
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "senwebstats.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            title TEXT,
            meta_description TEXT,
            meta_keywords TEXT,
            h1_count INTEGER DEFAULT 0,
            h2_count INTEGER DEFAULT 0,
            canonical_url TEXT,
            robots_meta TEXT,
            og_title TEXT,
            og_description TEXT,
            og_image TEXT,
            internal_links_count INTEGER DEFAULT 0,
            external_links_count INTEGER DEFAULT 0,
            images_count INTEGER DEFAULT 0,
            images_with_alt INTEGER DEFAULT 0,
            word_count INTEGER DEFAULT 0,
            has_sitemap INTEGER DEFAULT 0,
            has_robots_txt INTEGER DEFAULT 0,
            has_ssl INTEGER DEFAULT 0,
            status_code INTEGER,
            response_time_ms REAL,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            performance_score REAL,
            accessibility_score REAL,
            seo_score REAL,
            best_practices_score REAL,
            lcp_ms REAL,
            fid_ms REAL,
            cls_score REAL,
            fcp_ms REAL,
            ttfb_ms REAL,
            tti_ms REAL,
            device TEXT DEFAULT 'mobile',
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_backlinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            total_backlinks INTEGER DEFAULT 0,
            referring_domains INTEGER DEFAULT 0,
            top_referring_domains TEXT,
            backlinks_change INTEGER DEFAULT 0,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_authority (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id      INTEGER NOT NULL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            page_rank    REAL,
            global_rank  INTEGER,
            source       TEXT DEFAULT 'openpagerank',
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_trends (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id      INTEGER NOT NULL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            keyword      TEXT NOT NULL,
            trends_score REAL,
            trends_geo   TEXT DEFAULT 'SN',
            timeframe    TEXT DEFAULT 'today 12-m',
            trend_data   TEXT,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            status TEXT,
            error_message TEXT,
            metrics_collected TEXT
        )
    """)

    conn.commit()
    conn.close()
    print(f"Base de données initialisée : {DB_PATH}")


def seed_sites():
    from config.sites import ALL_SITES
    conn = get_connection()
    cursor = conn.cursor()
    inserted = 0
    for site in ALL_SITES:
        try:
            cursor.execute(
                "INSERT OR IGNORE INTO sites (domain, name, url, category) VALUES (?, ?, ?, ?)",
                (site["domain"], site["name"], site["url"], site["category"])
            )
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Erreur insertion {site['domain']}: {e}")
    conn.commit()
    conn.close()
    print(f"{inserted} sites insérés en base de données.")


if __name__ == "__main__":
    init_db()
    seed_sites()
