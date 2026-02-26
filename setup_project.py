"""
╔══════════════════════════════════════════════════════════════╗
║           SENWEBSTATS — Script d'installation                ║
║     Lance ce fichier UNE SEULE FOIS pour tout créer         ║
║                                                              ║
║  Usage : python setup_project.py                            ║
╚══════════════════════════════════════════════════════════════╝
"""

import os
import sys
import subprocess

# ── Dossier racine du projet ──────────────────────────────────────────────────
BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "senwebstats")

# ── Contenu de chaque fichier ─────────────────────────────────────────────────
FILES = {}

# ─────────────────────────────────────────────────────────────────────────────
FILES["requirements.txt"] = """\
requests==2.31.0
beautifulsoup4==4.12.3
lxml==5.1.0
pandas==2.2.0
numpy==1.26.4
streamlit==1.31.0
plotly==5.18.0
apscheduler==3.10.4
python-dotenv==1.0.1
tqdm==4.66.2
"""

# ─────────────────────────────────────────────────────────────────────────────
FILES["config/__init__.py"] = "# SenWebStats\n"

FILES["config/sites.py"] = '''\
"""
Configuration des sites cibles sénégalais par catégorie.
"""

SITES = {
    "presse": [
        {"name": "Seneweb",      "url": "https://www.seneweb.com",      "domain": "seneweb.com"},
        {"name": "Dakaractu",    "url": "https://www.dakaractu.com",    "domain": "dakaractu.com"},
        {"name": "Senenews",     "url": "https://www.senenews.com",     "domain": "senenews.com"},
        {"name": "Rewmi",        "url": "https://www.rewmi.com",        "domain": "rewmi.com"},
        {"name": "Leral",        "url": "https://www.leral.net",        "domain": "leral.net"},
        {"name": "Pressafrik",   "url": "https://www.pressafrik.com",   "domain": "pressafrik.com"},
        {"name": "Actusen",      "url": "https://actusen.sn",           "domain": "actusen.sn"},
        {"name": "Senego",       "url": "https://senego.com",           "domain": "senego.com"},
        {"name": "Sud Quotidien","url": "https://www.sudquotidien.sn",  "domain": "sudquotidien.sn"},
        {"name": "Xibaaru",      "url": "https://xibaaru.com",          "domain": "xibaaru.com"},
        {"name": "Dakarmatin",   "url": "https://www.dakarmatin.com",   "domain": "dakarmatin.com"},
        {"name": "L\'Observateur","url": "https://www.lobservateur.sn", "domain": "lobservateur.sn"},
    ],
    "ecommerce": [
        {"name": "Jumia Sénégal","url": "https://www.jumia.sn",         "domain": "jumia.sn"},
        {"name": "Expat Dakar",  "url": "https://www.expat-dakar.com",  "domain": "expat-dakar.com"},
        {"name": "CoinAfrique",  "url": "https://sn.coinafrique.com",   "domain": "sn.coinafrique.com"},
        {"name": "Afrikrea",     "url": "https://www.afrikrea.com",     "domain": "afrikrea.com"},
        {"name": "Dakar Deal",   "url": "https://www.dakardeal.com",    "domain": "dakardeal.com"},
    ],
    "telephonie": [
        {"name": "Orange Sénégal","url": "https://www.orange.sn",            "domain": "orange.sn"},
        {"name": "Free Sénégal",  "url": "https://www.free.sn",              "domain": "free.sn"},
        {"name": "Expresso",      "url": "https://www.expressotelecom.sn",   "domain": "expressotelecom.sn"},
        {"name": "Sonatel",       "url": "https://www.sonatel.com",          "domain": "sonatel.com"},
    ],
    "banque_finance": [
        {"name": "CBAO",         "url": "https://www.cbao.sn",          "domain": "cbao.sn"},
        {"name": "Ecobank",      "url": "https://ecobank.com/sn",       "domain": "ecobank.com"},
        {"name": "Wave",         "url": "https://www.wave.com/fr/sen",  "domain": "wave.com"},
        {"name": "Orange Money", "url": "https://www.orangemoney.sn",   "domain": "orangemoney.sn"},
    ],
    "emploi": [
        {"name": "Senjob",       "url": "https://www.senjob.com",       "domain": "senjob.com"},
        {"name": "Emploi.sn",    "url": "https://www.emploi.sn",        "domain": "emploi.sn"},
        {"name": "Rekrute",      "url": "https://www.rekrute.com",      "domain": "rekrute.com"},
    ],
}

ALL_SITES = []
for category, sites in SITES.items():
    for site in sites:
        ALL_SITES.append({**site, "category": category})

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
]

SCRAPE_DELAY_MIN = 2
SCRAPE_DELAY_MAX = 5

PAGESPEED_API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
PAGESPEED_API_KEY = ""
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["database/__init__.py"] = ""
FILES["database/schema.py"] = '''\
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
            device TEXT DEFAULT \'mobile\',
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
            print(f"Erreur insertion {site[\'domain\']}: {e}")
    conn.commit()
    conn.close()
    print(f"{inserted} sites insérés en base de données.")


if __name__ == "__main__":
    init_db()
    seed_sites()
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["data_collection/__init__.py"] = ""
FILES["data_collection/scrapers/__init__.py"] = ""
FILES["data_collection/scrapers/metadata_scraper.py"] = '''\
"""
Scraper de métadonnées HTML pour les sites sénégalais.
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import json
import sys
import os
from urllib.parse import urljoin, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from config.sites import USER_AGENTS, SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX
from database.schema import get_connection

TIMEOUT = 15


def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
    }


def check_sitemap(base_url):
    for path in ["/sitemap.xml", "/sitemap_index.xml"]:
        try:
            r = requests.get(urljoin(base_url, path), headers=get_headers(), timeout=8)
            if r.status_code == 200 and "<urlset" in r.text[:500]:
                return True
        except Exception:
            pass
    return False


def check_robots_txt(base_url):
    try:
        r = requests.get(urljoin(base_url, "/robots.txt"), headers=get_headers(), timeout=8)
        return r.status_code == 200
    except Exception:
        return False


def scrape_metadata(url: str) -> dict:
    result = {
        "url": url, "status_code": None, "response_time_ms": None,
        "has_ssl": url.startswith("https://"), "title": None,
        "meta_description": None, "meta_keywords": None,
        "canonical_url": None, "robots_meta": None,
        "og_title": None, "og_description": None, "og_image": None,
        "h1_count": 0, "h2_count": 0,
        "internal_links_count": 0, "external_links_count": 0,
        "images_count": 0, "images_with_alt": 0, "word_count": 0,
        "has_sitemap": False, "has_robots_txt": False, "error": None,
    }
    try:
        start = time.time()
        response = requests.get(url, headers=get_headers(), timeout=TIMEOUT, allow_redirects=True)
        result["response_time_ms"] = round((time.time() - start) * 1000, 2)
        result["status_code"] = response.status_code

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            return result

        response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        base_domain = urlparse(url).netloc

        title_tag = soup.find("title")
        result["title"] = title_tag.get_text(strip=True) if title_tag else None

        def get_meta(name=None, property=None):
            tag = soup.find("meta", attrs={"name": name} if name else {"property": property})
            return tag.get("content", "").strip() if tag else None

        result["meta_description"] = get_meta(name="description")
        result["meta_keywords"]    = get_meta(name="keywords")
        result["robots_meta"]      = get_meta(name="robots")
        result["og_title"]         = get_meta(property="og:title")
        result["og_description"]   = get_meta(property="og:description")
        result["og_image"]         = get_meta(property="og:image")

        canonical = soup.find("link", attrs={"rel": "canonical"})
        result["canonical_url"] = canonical.get("href") if canonical else None

        result["h1_count"] = len(soup.find_all("h1"))
        result["h2_count"] = len(soup.find_all("h2"))

        internal, external = 0, 0
        for link in soup.find_all("a", href=True):
            parsed = urlparse(link["href"])
            if not parsed.netloc or base_domain in parsed.netloc:
                internal += 1
            elif parsed.netloc:
                external += 1
        result["internal_links_count"] = internal
        result["external_links_count"] = external

        imgs = soup.find_all("img")
        result["images_count"]    = len(imgs)
        result["images_with_alt"] = sum(1 for img in imgs if img.get("alt", "").strip())

        body = soup.find("body")
        if body:
            result["word_count"] = len(body.get_text(separator=" ", strip=True).split())

        result["has_sitemap"]    = check_sitemap(url)
        result["has_robots_txt"] = check_robots_txt(url)

    except requests.exceptions.Timeout:
        result["error"] = "timeout"
    except Exception as e:
        result["error"] = str(e)[:200]

    return result


def save_metadata(site_id: int, data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO site_metadata (
            site_id, title, meta_description, meta_keywords,
            h1_count, h2_count, canonical_url, robots_meta,
            og_title, og_description, og_image,
            internal_links_count, external_links_count,
            images_count, images_with_alt, word_count,
            has_sitemap, has_robots_txt, has_ssl, status_code, response_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        site_id, data.get("title"), data.get("meta_description"), data.get("meta_keywords"),
        data.get("h1_count", 0), data.get("h2_count", 0),
        data.get("canonical_url"), data.get("robots_meta"),
        data.get("og_title"), data.get("og_description"), data.get("og_image"),
        data.get("internal_links_count", 0), data.get("external_links_count", 0),
        data.get("images_count", 0), data.get("images_with_alt", 0), data.get("word_count", 0),
        1 if data.get("has_sitemap") else 0,
        1 if data.get("has_robots_txt") else 0,
        1 if data.get("has_ssl") else 0,
        data.get("status_code"), data.get("response_time_ms"),
    ))
    conn.commit()
    conn.close()


def log_crawl(site_id, status, error=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO crawl_logs (site_id, finished_at, status, error_message) VALUES (?, datetime(\'now\'), ?, ?)",
        (site_id, status, error)
    )
    conn.commit()
    conn.close()


def crawl_all_sites(category=None):
    conn = get_connection()
    cursor = conn.cursor()
    if category:
        cursor.execute("SELECT id, domain, name, url, category FROM sites WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT id, domain, name, url, category FROM sites")
    sites = cursor.fetchall()
    conn.close()

    total = len(sites)
    success, errors = 0, 0
    print(f"\\nDémarrage du crawl — {total} sites")
    print("=" * 60)

    for i, site in enumerate(sites, 1):
        site_id, domain, name, url, cat = site
        print(f"\\n[{i}/{total}] {name} ({cat})")

        data = scrape_metadata(url)

        if data.get("error"):
            print(f"  ERREUR: {data[\'error\']}")
            log_crawl(site_id, "error", data["error"])
            errors += 1
        else:
            save_metadata(site_id, data)
            log_crawl(site_id, "success")
            success += 1
            print(f"  OK | Status: {data[\'status_code\']} | Temps: {data[\'response_time_ms\']}ms")
            print(f"  Title: {(data.get(\'title\') or \'N/A\')[:60]}")
            print(f"  Liens: {data[\'internal_links_count\']} int. / {data[\'external_links_count\']} ext.")
            print(f"  SSL: {\'Oui\' if data[\'has_ssl\'] else \'Non\'} | Sitemap: {\'Oui\' if data[\'has_sitemap\'] else \'Non\'}")

        if i < total:
            delay = random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX)
            print(f"  Pause {delay:.1f}s...")
            time.sleep(delay)

    print(f"\\nCrawl terminé : {success} succès, {errors} erreurs sur {total} sites")
    return {"success": success, "errors": errors, "total": total}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str)
    parser.add_argument("--category", type=str)
    args = parser.parse_args()

    if args.url:
        print(json.dumps(scrape_metadata(args.url), indent=2, ensure_ascii=False))
    else:
        crawl_all_sites(category=args.category)
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["data_collection/apis/__init__.py"] = ""
FILES["data_collection/apis/pagespeed_collector.py"] = '''\
"""
Collecteur Google PageSpeed API (gratuite — 25 000 req/jour).
"""

import requests
import time
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from config.sites import PAGESPEED_API_URL, PAGESPEED_API_KEY
from database.schema import get_connection


def fetch_pagespeed(url: str, strategy: str = "mobile") -> dict:
    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "accessibility", "best-practices", "seo"],
    }
    if PAGESPEED_API_KEY:
        params["key"] = PAGESPEED_API_KEY

    result = {
        "url": url, "strategy": strategy,
        "performance_score": None, "accessibility_score": None,
        "seo_score": None, "best_practices_score": None,
        "lcp_ms": None, "fid_ms": None, "cls_score": None,
        "fcp_ms": None, "ttfb_ms": None, "tti_ms": None, "error": None,
    }

    try:
        response = requests.get(PAGESPEED_API_URL, params=params, timeout=30)
        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            return result

        data = response.json()
        cats   = data.get("lighthouseResult", {}).get("categories", {})
        audits = data.get("lighthouseResult", {}).get("audits", {})

        def score(key):
            v = cats.get(key, {}).get("score")
            return round(v * 100, 1) if v is not None else None

        result["performance_score"]    = score("performance")
        result["accessibility_score"]  = score("accessibility")
        result["seo_score"]            = score("seo")
        result["best_practices_score"] = score("best-practices")

        def audit_val(key):
            return audits.get(key, {}).get("numericValue")

        result["lcp_ms"]    = audit_val("largest-contentful-paint")
        result["fid_ms"]    = audit_val("max-potential-fid")
        result["cls_score"] = audit_val("cumulative-layout-shift")
        result["fcp_ms"]    = audit_val("first-contentful-paint")
        result["ttfb_ms"]   = audit_val("server-response-time")
        result["tti_ms"]    = audit_val("interactive")

        for k in ["lcp_ms", "fid_ms", "fcp_ms", "ttfb_ms", "tti_ms"]:
            if result[k] is not None:
                result[k] = round(result[k], 2)
        if result["cls_score"] is not None:
            result["cls_score"] = round(result["cls_score"], 4)

    except Exception as e:
        result["error"] = str(e)[:200]

    return result


def save_performance(site_id: int, data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO site_performance (
            site_id, performance_score, accessibility_score,
            seo_score, best_practices_score,
            lcp_ms, fid_ms, cls_score, fcp_ms, ttfb_ms, tti_ms, device
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        site_id,
        data.get("performance_score"), data.get("accessibility_score"),
        data.get("seo_score"), data.get("best_practices_score"),
        data.get("lcp_ms"), data.get("fid_ms"), data.get("cls_score"),
        data.get("fcp_ms"), data.get("ttfb_ms"), data.get("tti_ms"),
        data.get("strategy", "mobile"),
    ))
    conn.commit()
    conn.close()


def collect_performance_all(strategy="mobile"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, url FROM sites ORDER BY category")
    sites = cursor.fetchall()
    conn.close()

    print(f"\\nCollecte PageSpeed ({strategy}) — {len(sites)} sites")
    print("=" * 60)

    for i, (site_id, name, url) in enumerate(sites, 1):
        print(f"\\n[{i}/{len(sites)}] {name}")
        data = fetch_pagespeed(url, strategy)
        if data.get("error"):
            print(f"  ERREUR: {data[\'error\']}")
        else:
            save_performance(site_id, data)

            def grade(s):
                if s is None: return "?"
                return "BIEN" if s >= 90 else ("MOYEN" if s >= 50 else "FAIBLE")

            print(f"  Performance: {data[\'performance_score\']} ({grade(data[\'performance_score\'])})")
            print(f"  SEO: {data[\'seo_score\']} | Access.: {data[\'accessibility_score\']}")
            print(f"  LCP: {data[\'lcp_ms\']}ms | FCP: {data[\'fcp_ms\']}ms | TTFB: {data[\'ttfb_ms\']}ms")
        time.sleep(2)

    print("\\nCollecte PageSpeed terminée.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str)
    parser.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    args = parser.parse_args()
    if args.url:
        print(json.dumps(fetch_pagespeed(args.url, args.strategy), indent=2))
    else:
        collect_performance_all(args.strategy)
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["data_collection/apis/backlinks_collector.py"] = '''\
"""
Collecteur de backlinks via CommonCrawl Index (100% gratuit).
"""

import requests
import json
import time
import sys
import os
from collections import Counter
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.schema import get_connection

CC_INDEX   = "CC-MAIN-2024-30"
CC_API_URL = f"https://index.commoncrawl.org/{CC_INDEX}-index"


def query_commoncrawl(domain: str, max_records=500) -> list:
    results = []
    page = 0
    while len(results) < max_records:
        params = {"url": f"*.{domain}", "output": "json", "limit": 100, "page": page}
        try:
            r = requests.get(CC_API_URL, params=params, timeout=30)
            if r.status_code == 404:
                break
            if r.status_code != 200:
                break
            lines = [l for l in r.text.strip().split("\\n") if l]
            if not lines:
                break
            for line in lines:
                try:
                    results.append(json.loads(line))
                except Exception:
                    pass
            page += 1
            time.sleep(1)
        except Exception as e:
            print(f"  Erreur CommonCrawl: {e}")
            break
    return results[:max_records]


def analyze_backlinks(records, target_domain):
    domain_counter = Counter()
    for rec in records:
        d = urlparse(rec.get("url", "")).netloc
        if d and d != target_domain:
            domain_counter[d] += 1
    top = [{"domain": d, "count": c} for d, c in domain_counter.most_common(20)]
    return {
        "total_indexed_pages": len(records),
        "referring_domains_count": len(domain_counter),
        "top_referring_domains": top,
    }


def collect_backlinks_for_domain(domain: str) -> dict:
    print(f"  Recherche CommonCrawl pour {domain}...")
    records  = query_commoncrawl(domain, max_records=500)
    analysis = analyze_backlinks(records, domain)
    return {
        "total_backlinks": analysis["total_indexed_pages"],
        "referring_domains": analysis["referring_domains_count"],
        "top_referring_domains": analysis["top_referring_domains"],
    }


def save_backlinks(site_id: int, data: dict):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT total_backlinks FROM site_backlinks WHERE site_id = ? ORDER BY collected_at DESC LIMIT 1",
        (site_id,)
    )
    prev = cursor.fetchone()
    change = data["total_backlinks"] - (prev[0] if prev else 0)
    cursor.execute("""
        INSERT INTO site_backlinks (site_id, total_backlinks, referring_domains, top_referring_domains, backlinks_change)
        VALUES (?, ?, ?, ?, ?)
    """, (site_id, data["total_backlinks"], data["referring_domains"],
          json.dumps(data["top_referring_domains"]), change))
    conn.commit()
    conn.close()


def collect_all_backlinks():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, domain FROM sites ORDER BY category")
    sites = cursor.fetchall()
    conn.close()

    print(f"\\nCollecte backlinks — {len(sites)} sites")
    print("=" * 60)

    for i, (site_id, name, domain) in enumerate(sites, 1):
        print(f"\\n[{i}/{len(sites)}] {name} ({domain})")
        data = collect_backlinks_for_domain(domain)
        save_backlinks(site_id, data)
        print(f"  Pages indexées: {data[\'total_backlinks\']}")
        print(f"  Domaines référents: {data[\'referring_domains\']}")
        time.sleep(3)

    print("\\nCollecte backlinks terminée.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str)
    args = parser.parse_args()
    if args.domain:
        print(json.dumps(collect_backlinks_for_domain(args.domain), indent=2, ensure_ascii=False))
    else:
        collect_all_backlinks()
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["main.py"] = '''\
"""
SenWebStats — Point d\'entrée principal.

Commandes disponibles :
  python main.py init          Initialiser la base de données
  python main.py crawl         Crawler tous les sites
  python main.py crawl --cat presse   Crawler une catégorie
  python main.py perf          Collecter les performances PageSpeed
  python main.py backlinks     Collecter les backlinks
  python main.py full          Collecte complète
  python main.py report        Rapport rapide en terminal
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_init():
    from database.schema import init_db, seed_sites
    print("Initialisation de SenWebStats...")
    init_db()
    seed_sites()
    print("Prêt ! Lance : python main.py crawl")


def cmd_crawl(category=None):
    from database.schema import init_db, seed_sites
    from data_collection.scrapers.metadata_scraper import crawl_all_sites
    init_db()
    seed_sites()
    return crawl_all_sites(category=category)


def cmd_perf(strategy="mobile"):
    from data_collection.apis.pagespeed_collector import collect_performance_all
    collect_performance_all(strategy=strategy)


def cmd_backlinks():
    from data_collection.apis.backlinks_collector import collect_all_backlinks
    collect_all_backlinks()


def cmd_report():
    from database.schema import get_connection
    conn = get_connection()
    cursor = conn.cursor()

    print("\\n" + "=" * 60)
    print("RAPPORT SENWEBSTATS")
    print("=" * 60)

    cursor.execute("SELECT category, COUNT(*) FROM sites GROUP BY category ORDER BY COUNT(*) DESC")
    print("\\nSites par catégorie:")
    for cat, count in cursor.fetchall():
        print(f"  {cat:<20} {count} sites")

    cursor.execute("""
        SELECT s.name, s.category, sm.status_code, sm.response_time_ms,
               sm.word_count, sm.has_ssl, sm.has_sitemap
        FROM site_metadata sm
        JOIN sites s ON s.id = sm.site_id
        WHERE sm.crawled_at = (SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = sm.site_id)
        ORDER BY sm.crawled_at DESC LIMIT 20
    """)
    rows = cursor.fetchall()
    if rows:
        print(f"\\nDernières métadonnées ({len(rows)} sites):")
        print(f"  {\'Site\':<22} {\'Catég.\':<14} {\'Status\':<8} {\'ms\':<8} {\'Mots\':<8} SSL  Sitemap")
        print("  " + "-" * 70)
        for name, cat, status, rt, words, ssl, sitemap in rows:
            print(f"  {name[:22]:<22} {cat[:14]:<14} {str(status):<8} {str(round(rt or 0)):<8} "
                  f"{str(words or 0):<8} {\'Oui\' if ssl else \'Non\':<5} {\'Oui\' if sitemap else \'Non\'}")
    else:
        print("\\nAucune métadonnée. Lance : python main.py crawl")

    conn.close()
    print("\\n" + "=" * 60)


def cmd_full():
    print("\\nCOLLECTE COMPLÈTE SENWEBSTATS")
    print("=" * 60)
    print("\\nÉtape 1/3 : Métadonnées HTML")
    cmd_crawl()
    print("\\nÉtape 2/3 : Performances PageSpeed")
    cmd_perf()
    print("\\nÉtape 3/3 : Backlinks CommonCrawl")
    cmd_backlinks()
    print("\\nCollecte complète terminée !")
    cmd_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SenWebStats — Stats web des sites sénégalais")
    parser.add_argument("command", choices=["init", "crawl", "perf", "backlinks", "full", "report"])
    parser.add_argument("--cat", type=str, help="Catégorie : presse, ecommerce, telephonie...")
    parser.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    args = parser.parse_args()

    if   args.command == "init":      cmd_init()
    elif args.command == "crawl":     cmd_crawl(category=args.cat)
    elif args.command == "perf":      cmd_perf(strategy=args.strategy)
    elif args.command == "backlinks": cmd_backlinks()
    elif args.command == "full":      cmd_full()
    elif args.command == "report":    cmd_report()
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["app/__init__.py"] = ""
FILES["app/streamlit_app.py"] = '''\
"""
SenWebStats — Dashboard Streamlit
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os

st.set_page_config(
    page_title="SenWebStats",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
div[data-testid="metric-container"] {
    background: white;
    border: 1px solid #e0e0e0;
    border-radius: 10px;
    padding: 1rem;
    box-shadow: 0 2px 6px rgba(0,0,0,0.06);
}
</style>
""", unsafe_allow_html=True)

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "senwebstats.db")


@st.cache_resource
def get_conn():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def query_df(sql, params=()):
    conn = get_conn()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    except Exception:
        return pd.DataFrame()


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1a6d3c,#00a86b,#ffd700);
            padding:1.5rem 2rem;border-radius:12px;margin-bottom:2rem;text-align:center">
    <h1 style="color:white;font-size:2.5rem;margin:0;font-weight:800">📊 SenWebStats 🇸🇳</h1>
    <p style="color:rgba(255,255,255,0.9);margin:0.5rem 0 0 0;font-size:1.1rem">
        Statistiques & performances des sites web sénégalais
    </p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🎛️ Filtres")
    categories = query_df("SELECT DISTINCT category FROM sites ORDER BY category")
    all_cats = ["Toutes"] + list(categories["category"].values) if not categories.empty else ["Toutes"]
    selected_cat = st.selectbox("📂 Catégorie", all_cats)
    st.markdown("---")
    st.info("Collecte : `python main.py crawl`")
    last = query_df("SELECT MAX(crawled_at) as last FROM site_metadata")
    if not last.empty and last[\'last\'].values[0]:
        st.caption(f"Dernière collecte: {last[\'last\'].values[0][:16]}")

# ── Vérification DB ───────────────────────────────────────────────────────────
if get_conn() is None:
    st.error("Base de données introuvable. Lance : `python main.py init`")
    st.code("python main.py init\\npython main.py crawl", language="bash")
    st.stop()

# ── KPIs ─────────────────────────────────────────────────────────────────────
st.subheader("📈 Vue d\'ensemble")
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    n = query_df("SELECT COUNT(*) as n FROM sites")
    st.metric("🌐 Sites suivis", n["n"].values[0] if not n.empty else 0)
with col2:
    n = query_df("SELECT COUNT(DISTINCT site_id) as n FROM site_metadata")
    st.metric("✅ Sites crawlés", n["n"].values[0] if not n.empty else 0)
with col3:
    n = query_df("SELECT COUNT(DISTINCT site_id) as n FROM site_performance")
    st.metric("⚡ Scores perf.", n["n"].values[0] if not n.empty else 0)
with col4:
    v = query_df("SELECT ROUND(AVG(performance_score),1) as v FROM site_performance")
    val = v["v"].values[0] if not v.empty else None
    st.metric("🏅 Perf. moy.", f"{val}/100" if val else "N/A")
with col5:
    v = query_df("SELECT ROUND(AVG(seo_score),1) as v FROM site_performance")
    val = v["v"].values[0] if not v.empty else None
    st.metric("🔍 SEO moy.", f"{val}/100" if val else "N/A")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["🌐 Métadonnées", "⚡ Performance", "🔗 Backlinks", "📊 Comparaison"])

cat_sql = "" if selected_cat == "Toutes" else f"WHERE s.category = \'{selected_cat}\'"
cat_and = "" if selected_cat == "Toutes" else f"AND s.category = \'{selected_cat}\'"

# ── Tab 1 — Métadonnées ───────────────────────────────────────────────────────
with tab1:
    df = query_df(f"""
        SELECT s.name, s.domain, s.category, sm.status_code, sm.response_time_ms,
               sm.word_count, sm.internal_links_count, sm.external_links_count,
               sm.images_count, sm.has_ssl, sm.has_sitemap, sm.has_robots_txt
        FROM sites s
        LEFT JOIN site_metadata sm ON sm.site_id = s.id
            AND sm.crawled_at = (SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = s.id)
        {cat_sql}
        ORDER BY s.category, s.name
    """)

    if df.empty:
        st.warning("Aucune donnée. Lance : `python main.py crawl`")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(df["category"].value_counts().reset_index(),
                         names="category", values="count",
                         title="Répartition par catégorie")
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            df_rt = df.dropna(subset=["response_time_ms"])
            if not df_rt.empty:
                avg_rt = df_rt.groupby("category")["response_time_ms"].mean().reset_index()
                fig2 = px.bar(avg_rt, x="category", y="response_time_ms",
                              title="Temps de réponse moyen (ms) par catégorie",
                              color="response_time_ms", color_continuous_scale="RdYlGn_r")
                st.plotly_chart(fig2, use_container_width=True)

        # Tableau
        d = df[["name","category","status_code","response_time_ms","word_count",
                "has_ssl","has_sitemap","has_robots_txt"]].copy()
        d.columns = ["Site","Catégorie","Status","Temps(ms)","Mots","SSL","Sitemap","Robots.txt"]
        for c in ["SSL","Sitemap","Robots.txt"]:
            d[c] = d[c].apply(lambda x: "✅" if x == 1 else "❌")
        st.dataframe(d, use_container_width=True, hide_index=True)

# ── Tab 2 — Performance ───────────────────────────────────────────────────────
with tab2:
    df_p = query_df(f"""
        SELECT s.name, s.category, sp.performance_score, sp.seo_score,
               sp.accessibility_score, sp.best_practices_score,
               sp.lcp_ms, sp.fcp_ms, sp.ttfb_ms, sp.cls_score
        FROM site_performance sp JOIN sites s ON s.id = sp.site_id
        WHERE sp.measured_at = (SELECT MAX(measured_at) FROM site_performance WHERE site_id = sp.site_id)
        {cat_and}
        ORDER BY sp.performance_score DESC
    """)

    if df_p.empty:
        st.warning("Aucune donnée. Lance : `python main.py perf`")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_p.nlargest(10, "performance_score"),
                         x="performance_score", y="name", orientation="h",
                         title="Top 10 — Score Performance",
                         color="performance_score", color_continuous_scale="RdYlGn", range_color=[0,100])
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df_p.nlargest(10, "seo_score"),
                         x="seo_score", y="name", orientation="h",
                         title="Top 10 — Score SEO",
                         color="seo_score", color_continuous_scale="Blues", range_color=[0,100])
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)

        # Core Web Vitals
        st.subheader("Core Web Vitals")
        st.caption("LCP < 2500ms ✅ | FCP < 1800ms ✅ | TTFB < 800ms ✅")
        d = df_p[["name","lcp_ms","fcp_ms","ttfb_ms","cls_score"]].copy()
        d.columns = ["Site","LCP (ms)","FCP (ms)","TTFB (ms)","CLS"]
        st.dataframe(d.round(1), use_container_width=True, hide_index=True)

# ── Tab 3 — Backlinks ─────────────────────────────────────────────────────────
with tab3:
    df_b = query_df(f"""
        SELECT s.name, s.category, s.domain,
               sb.total_backlinks, sb.referring_domains, sb.backlinks_change
        FROM site_backlinks sb JOIN sites s ON s.id = sb.site_id
        WHERE sb.collected_at = (SELECT MAX(collected_at) FROM site_backlinks WHERE site_id = sb.site_id)
        {cat_and}
        ORDER BY sb.total_backlinks DESC
    """)

    if df_b.empty:
        st.warning("Aucune donnée. Lance : `python main.py backlinks`")
    else:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_b.nlargest(10, "total_backlinks"),
                         x="total_backlinks", y="name", orientation="h",
                         title="Top 10 — Pages indexées", color="total_backlinks",
                         color_continuous_scale="Viridis")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig = px.bar(df_b.nlargest(10, "referring_domains"),
                         x="referring_domains", y="name", orientation="h",
                         title="Top 10 — Domaines référents", color="referring_domains",
                         color_continuous_scale="Plasma")
            fig.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        d = df_b[["name","category","domain","total_backlinks","referring_domains","backlinks_change"]].copy()
        d.columns = ["Site","Catégorie","Domaine","Pages indexées","Domaines réf.","Variation"]
        st.dataframe(d, use_container_width=True, hide_index=True)

# ── Tab 4 — Comparaison ───────────────────────────────────────────────────────
with tab4:
    st.subheader("Comparer des sites")
    sites_list = query_df("SELECT name FROM sites ORDER BY name")
    if not sites_list.empty:
        selected = st.multiselect("Sélectionne les sites",
                                  options=sites_list["name"].tolist(),
                                  default=sites_list["name"].tolist()[:5],
                                  max_selections=8)
        if selected:
            ph = ",".join(["?" for _ in selected])
            df_c = query_df(f"""
                SELECT s.name, s.category,
                       sm.word_count, sm.response_time_ms,
                       sp.performance_score, sp.seo_score,
                       sb.total_backlinks, sb.referring_domains
                FROM sites s
                LEFT JOIN site_metadata sm ON sm.site_id = s.id
                    AND sm.crawled_at = (SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = s.id)
                LEFT JOIN site_performance sp ON sp.site_id = s.id
                    AND sp.measured_at = (SELECT MAX(measured_at) FROM site_performance WHERE site_id = s.id)
                LEFT JOIN site_backlinks sb ON sb.site_id = s.id
                    AND sb.collected_at = (SELECT MAX(collected_at) FROM site_backlinks WHERE site_id = s.id)
                WHERE s.name IN ({ph})
            """, tuple(selected))

            if not df_c.empty:
                metrics = st.multiselect("Métriques",
                    ["performance_score","seo_score","word_count","total_backlinks","response_time_ms"],
                    default=["performance_score","seo_score"])
                if metrics:
                    fig = go.Figure()
                    for m in metrics:
                        d = df_c[["name", m]].dropna()
                        fig.add_trace(go.Bar(name=m.replace("_"," ").title(),
                                             x=d["name"], y=d[m]))
                    fig.update_layout(barmode="group", title="Comparaison multi-métriques",
                                      xaxis_tickangle=-30)
                    st.plotly_chart(fig, use_container_width=True)
                st.dataframe(df_c, use_container_width=True, hide_index=True)

st.markdown("---")
st.markdown("<div style=\'text-align:center;color:#888;font-size:0.85rem\'>"
            "SenWebStats 🇸🇳 — PageSpeed API · CommonCrawl · Scraping HTML</div>",
            unsafe_allow_html=True)
'''

# ─────────────────────────────────────────────────────────────────────────────
FILES["processing/__init__.py"] = ""
FILES["logs/.gitkeep"] = ""
FILES["data/.gitkeep"] = ""


# ══════════════════════════════════════════════════════════════════════════════
# CRÉATION DES FICHIERS
# ══════════════════════════════════════════════════════════════════════════════

def create_project():
    print("\n" + "="*60)
    print("   SENWEBSTATS — Installation automatique")
    print("="*60)

    # Créer les dossiers nécessaires
    dirs = [
        "", "config", "database", "data",
        "data_collection", "data_collection/scrapers", "data_collection/apis",
        "processing", "app", "logs",
    ]
    for d in dirs:
        path = os.path.join(BASE, d)
        os.makedirs(path, exist_ok=True)

    print(f"\n📁 Dossiers créés dans : {BASE}")

    # Écrire chaque fichier
    created = 0
    for relative_path, content in FILES.items():
        full_path = os.path.join(BASE, relative_path.replace("/", os.sep))
        with open(full_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"  ✅ {relative_path}")
        created += 1

    print(f"\n{created} fichiers créés avec succès !")

    # Installer les dépendances
    print("\n" + "="*60)
    print("📦 Installation des dépendances...")
    print("="*60)

    deps = [
        "requests", "beautifulsoup4", "lxml",
        "pandas", "numpy", "streamlit", "plotly",
        "apscheduler", "python-dotenv", "tqdm"
    ]

    result = subprocess.run(
        [sys.executable, "-m", "pip", "install"] + deps,
        capture_output=False
    )

    if result.returncode == 0:
        print("\n✅ Dépendances installées !")
    else:
        print("\n⚠️  Certaines dépendances ont échoué. Essaie manuellement :")
        print(f"   pip install {' '.join(deps)}")

    # Initialiser la base de données
    print("\n" + "="*60)
    print("🗄️  Initialisation de la base de données...")
    print("="*60)

    init_result = subprocess.run(
        [sys.executable, "main.py", "init"],
        cwd=BASE,
        capture_output=False
    )

    # Instructions finales
    print("\n" + "="*60)
    print("🚀 SENWEBSTATS EST PRÊT !")
    print("="*60)
    print(f"\n📂 Projet installé dans : {BASE}")
    print("\n🔧 Commandes disponibles (depuis le dossier senwebstats) :")
    print(f"\n   cd {BASE}")
    print("   python main.py crawl          ← Scraper les sites")
    print("   python main.py perf           ← Collecter les scores PageSpeed")
    print("   python main.py backlinks      ← Collecter les backlinks")
    print("   python main.py report         ← Voir un rapport rapide")
    print("   streamlit run app/streamlit_app.py  ← Lancer le dashboard")
    print("\n💡 Conseil : commence par 'python main.py crawl --cat presse'")
    print("   pour tester sur les sites de presse uniquement.\n")
    print("="*60)


if __name__ == "__main__":
    create_project()
