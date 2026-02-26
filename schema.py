"""
Schéma de base de données — SQLite pour développement, PostgreSQL pour production.
Toutes les métriques collectées sont stockées ici.
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
    """Initialise toutes les tables de la base de données."""
    conn = get_connection()
    cursor = conn.cursor()

    # Table principale des sites
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            url TEXT NOT NULL,
            category TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Métadonnées HTML des sites (collectées à chaque crawl)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Métadonnées SEO
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
            
            -- Structure
            internal_links_count INTEGER DEFAULT 0,
            external_links_count INTEGER DEFAULT 0,
            images_count INTEGER DEFAULT 0,
            images_with_alt INTEGER DEFAULT 0,
            word_count INTEGER DEFAULT 0,
            
            -- Technique
            has_sitemap INTEGER DEFAULT 0,
            has_robots_txt INTEGER DEFAULT 0,
            has_ssl INTEGER DEFAULT 0,
            status_code INTEGER,
            response_time_ms REAL,
            
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    # Performance (Google PageSpeed)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_performance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Scores PageSpeed (0-100)
            performance_score REAL,
            accessibility_score REAL,
            seo_score REAL,
            best_practices_score REAL,
            
            -- Core Web Vitals
            lcp_ms REAL,          -- Largest Contentful Paint
            fid_ms REAL,          -- First Input Delay  
            cls_score REAL,       -- Cumulative Layout Shift
            fcp_ms REAL,          -- First Contentful Paint
            ttfb_ms REAL,         -- Time To First Byte
            tti_ms REAL,          -- Time To Interactive
            
            -- Mobile vs Desktop
            device TEXT DEFAULT 'mobile',
            
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    # Backlinks via CommonCrawl
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_backlinks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            total_backlinks INTEGER DEFAULT 0,
            referring_domains INTEGER DEFAULT 0,
            
            -- Top domaines référents (JSON)
            top_referring_domains TEXT,  -- JSON list
            
            -- Évolution
            backlinks_change INTEGER DEFAULT 0,  -- vs collecte précédente
            
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    # Estimation de trafic (modèle CTR × Volume)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS traffic_estimates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            estimated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            period TEXT NOT NULL,  -- ex: '2024-01'
            
            -- Trafic estimé
            estimated_visits INTEGER DEFAULT 0,
            estimated_organic_visits INTEGER DEFAULT 0,
            
            -- Mots-clés (JSON)
            top_keywords TEXT,  -- JSON: [{keyword, position, volume, ctr, traffic}]
            total_keywords INTEGER DEFAULT 0,
            keywords_top3 INTEGER DEFAULT 0,
            keywords_top10 INTEGER DEFAULT 0,
            
            -- Score de visibilité maison (0-100)
            visibility_score REAL DEFAULT 0,
            
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    # Présence sur les réseaux sociaux
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_presence (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER NOT NULL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            facebook_url TEXT,
            facebook_followers INTEGER,
            twitter_url TEXT,
            twitter_followers INTEGER,
            instagram_url TEXT,
            instagram_followers INTEGER,
            youtube_url TEXT,
            youtube_subscribers INTEGER,
            
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)

    # Logs des crawls
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS crawl_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            finished_at TIMESTAMP,
            status TEXT,  -- 'success', 'error', 'timeout'
            error_message TEXT,
            metrics_collected TEXT  -- JSON des métriques récupérées
        )
    """)

    conn.commit()
    conn.close()
    print(f"✅ Base de données initialisée : {DB_PATH}")


def seed_sites():
    """Insère les sites cibles dans la base de données."""
    from config.sites import ALL_SITES
    
    conn = get_connection()
    cursor = conn.cursor()
    
    inserted = 0
    for site in ALL_SITES:
        try:
            cursor.execute("""
                INSERT OR IGNORE INTO sites (domain, name, url, category)
                VALUES (?, ?, ?, ?)
            """, (site["domain"], site["name"], site["url"], site["category"]))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"⚠️  Erreur insertion {site['domain']}: {e}")
    
    conn.commit()
    conn.close()
    print(f"✅ {inserted} sites insérés en base de données.")


if __name__ == "__main__":
    init_db()
    seed_sites()
