"""
Scraper de métadonnées HTML pour les sites sénégalais.
Collecte : title, meta description, structure, liens, performance basique.
Respecte les bonnes pratiques (délais, rotation UA, gestion erreurs).
"""

import requests
from bs4 import BeautifulSoup
import time
import random
import sqlite3
import json
import sys
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse

# Ajout du répertoire parent au path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from config.sites import USER_AGENTS, SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX, ALL_SITES
from database.schema import get_connection

# ─── Timeout & headers ──────────────────────────────────────────────────────

TIMEOUT = 15


def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }


# ─── Fonctions utilitaires ───────────────────────────────────────────────────

def check_url_exists(url, timeout=10):
    """Vérifie si une URL répond (HEAD request rapide)."""
    try:
        r = requests.head(url, headers=get_headers(), timeout=timeout, allow_redirects=True)
        return r.status_code, r.elapsed.total_seconds() * 1000
    except Exception:
        return None, None


def check_sitemap(base_url):
    """Vérifie l'existence d'un sitemap."""
    candidates = [
        urljoin(base_url, "/sitemap.xml"),
        urljoin(base_url, "/sitemap_index.xml"),
        urljoin(base_url, "/sitemap"),
    ]
    for url in candidates:
        try:
            r = requests.get(url, headers=get_headers(), timeout=8)
            if r.status_code == 200 and ("xml" in r.headers.get("Content-Type", "") or "<urlset" in r.text[:500]):
                return True
        except Exception:
            pass
    return False


def check_robots_txt(base_url):
    """Vérifie l'existence d'un robots.txt."""
    try:
        r = requests.get(urljoin(base_url, "/robots.txt"), headers=get_headers(), timeout=8)
        return r.status_code == 200
    except Exception:
        return False


# ─── Scraper principal ───────────────────────────────────────────────────────

def scrape_metadata(url: str) -> dict:
    """
    Scrape les métadonnées complètes d'une URL.
    Retourne un dictionnaire avec toutes les métriques.
    """
    start_time = time.time()
    result = {
        "url": url,
        "status_code": None,
        "response_time_ms": None,
        "has_ssl": url.startswith("https://"),
        "title": None,
        "meta_description": None,
        "meta_keywords": None,
        "canonical_url": None,
        "robots_meta": None,
        "og_title": None,
        "og_description": None,
        "og_image": None,
        "h1_count": 0,
        "h2_count": 0,
        "internal_links_count": 0,
        "external_links_count": 0,
        "images_count": 0,
        "images_with_alt": 0,
        "word_count": 0,
        "has_sitemap": False,
        "has_robots_txt": False,
        "error": None,
    }

    try:
        response = requests.get(
            url,
            headers=get_headers(),
            timeout=TIMEOUT,
            allow_redirects=True
        )
        elapsed = (time.time() - start_time) * 1000

        result["status_code"] = response.status_code
        result["response_time_ms"] = round(elapsed, 2)

        if response.status_code != 200:
            result["error"] = f"HTTP {response.status_code}"
            return result

        # Encodage
        response.encoding = response.apparent_encoding or "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        base_domain = urlparse(url).netloc

        # ── Métadonnées de base ──
        title_tag = soup.find("title")
        result["title"] = title_tag.get_text(strip=True) if title_tag else None

        def get_meta(name=None, property=None):
            if name:
                tag = soup.find("meta", attrs={"name": name})
            else:
                tag = soup.find("meta", attrs={"property": property})
            return tag.get("content", "").strip() if tag else None

        result["meta_description"] = get_meta(name="description")
        result["meta_keywords"] = get_meta(name="keywords")
        result["robots_meta"] = get_meta(name="robots")

        # ── Open Graph ──
        result["og_title"] = get_meta(property="og:title")
        result["og_description"] = get_meta(property="og:description")
        result["og_image"] = get_meta(property="og:image")

        # ── Canonical ──
        canonical = soup.find("link", attrs={"rel": "canonical"})
        result["canonical_url"] = canonical.get("href") if canonical else None

        # ── Headings ──
        result["h1_count"] = len(soup.find_all("h1"))
        result["h2_count"] = len(soup.find_all("h2"))

        # ── Liens ──
        all_links = soup.find_all("a", href=True)
        internal_count = 0
        external_count = 0
        for link in all_links:
            href = link["href"]
            parsed = urlparse(href)
            if parsed.netloc == "" or base_domain in parsed.netloc:
                internal_count += 1
            elif parsed.netloc and parsed.netloc != base_domain:
                external_count += 1
        result["internal_links_count"] = internal_count
        result["external_links_count"] = external_count

        # ── Images ──
        imgs = soup.find_all("img")
        result["images_count"] = len(imgs)
        result["images_with_alt"] = sum(1 for img in imgs if img.get("alt", "").strip())

        # ── Comptage de mots (body text) ──
        body = soup.find("body")
        if body:
            text = body.get_text(separator=" ", strip=True)
            result["word_count"] = len(text.split())

        # ── Sitemap & Robots ──
        result["has_sitemap"] = check_sitemap(url)
        result["has_robots_txt"] = check_robots_txt(url)

    except requests.exceptions.Timeout:
        result["error"] = "timeout"
    except requests.exceptions.ConnectionError as e:
        result["error"] = f"connection_error: {str(e)[:100]}"
    except Exception as e:
        result["error"] = f"error: {str(e)[:200]}"

    return result


# ─── Sauvegarde en base ──────────────────────────────────────────────────────

def save_metadata(site_id: int, data: dict):
    """Sauvegarde les métadonnées en base de données."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT INTO site_metadata (
            site_id, title, meta_description, meta_keywords,
            h1_count, h2_count, canonical_url, robots_meta,
            og_title, og_description, og_image,
            internal_links_count, external_links_count,
            images_count, images_with_alt, word_count,
            has_sitemap, has_robots_txt, has_ssl,
            status_code, response_time_ms
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        site_id,
        data.get("title"),
        data.get("meta_description"),
        data.get("meta_keywords"),
        data.get("h1_count", 0),
        data.get("h2_count", 0),
        data.get("canonical_url"),
        data.get("robots_meta"),
        data.get("og_title"),
        data.get("og_description"),
        data.get("og_image"),
        data.get("internal_links_count", 0),
        data.get("external_links_count", 0),
        data.get("images_count", 0),
        data.get("images_with_alt", 0),
        data.get("word_count", 0),
        1 if data.get("has_sitemap") else 0,
        1 if data.get("has_robots_txt") else 0,
        1 if data.get("has_ssl") else 0,
        data.get("status_code"),
        data.get("response_time_ms"),
    ))
    
    conn.commit()
    conn.close()


def log_crawl(site_id: int, status: str, error: str = None, metrics: dict = None):
    """Enregistre un log de crawl."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO crawl_logs (site_id, finished_at, status, error_message, metrics_collected)
        VALUES (?, ?, ?, ?, ?)
    """, (
        site_id,
        datetime.now().isoformat(),
        status,
        error,
        json.dumps(list(metrics.keys())) if metrics else None,
    ))
    conn.commit()
    conn.close()


# ─── Crawl de tous les sites ─────────────────────────────────────────────────

def crawl_all_sites(category: str = None, verbose: bool = True):
    """
    Crawle tous les sites (ou une catégorie spécifique).
    Respecte les délais pour ne pas surcharger les serveurs.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    if category:
        cursor.execute("SELECT id, domain, name, url, category FROM sites WHERE category = ?", (category,))
    else:
        cursor.execute("SELECT id, domain, name, url, category FROM sites")
    
    sites = cursor.fetchall()
    conn.close()
    
    total = len(sites)
    success_count = 0
    error_count = 0
    
    print(f"\n🚀 Démarrage du crawl — {total} sites à analyser")
    print("=" * 60)
    
    for i, site in enumerate(sites, 1):
        site_id, domain, name, url, cat = site
        
        print(f"\n[{i}/{total}] 🌐 {name} ({cat})")
        print(f"    URL: {url}")
        
        # Scraping
        data = scrape_metadata(url)
        
        if data.get("error"):
            print(f"    ❌ Erreur: {data['error']}")
            log_crawl(site_id, "error", data["error"])
            error_count += 1
        else:
            save_metadata(site_id, data)
            log_crawl(site_id, "success", metrics=data)
            success_count += 1
            
            # Affichage résumé
            print(f"    ✅ Status: {data['status_code']} | Temps: {data['response_time_ms']}ms")
            print(f"    📝 Title: {(data.get('title') or 'N/A')[:60]}")
            print(f"    🔗 Liens: {data['internal_links_count']} internes, {data['external_links_count']} externes")
            print(f"    📸 Images: {data['images_count']} ({data['images_with_alt']} avec alt)")
            print(f"    📊 Mots: {data['word_count']} | H1: {data['h1_count']} | H2: {data['h2_count']}")
            print(f"    🔒 SSL: {'✓' if data['has_ssl'] else '✗'} | Sitemap: {'✓' if data['has_sitemap'] else '✗'} | Robots: {'✓' if data['has_robots_txt'] else '✗'}")
        
        # Délai anti-ban entre chaque site
        if i < total:
            delay = random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX)
            print(f"    ⏳ Pause {delay:.1f}s...")
            time.sleep(delay)
    
    print("\n" + "=" * 60)
    print(f"✅ Crawl terminé : {success_count} succès, {error_count} erreurs")
    return {"success": success_count, "errors": error_count, "total": total}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Scraper de métadonnées SenWebStats")
    parser.add_argument("--category", type=str, help="Catégorie à crawler (presse, ecommerce...)")
    parser.add_argument("--url", type=str, help="URL unique à tester")
    args = parser.parse_args()
    
    if args.url:
        print(f"Test sur : {args.url}")
        result = scrape_metadata(args.url)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        crawl_all_sites(category=args.category)
