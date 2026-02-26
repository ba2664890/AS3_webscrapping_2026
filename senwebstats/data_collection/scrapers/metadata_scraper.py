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
        "INSERT INTO crawl_logs (site_id, finished_at, status, error_message) VALUES (?, datetime('now'), ?, ?)",
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
    print(f"\nDémarrage du crawl — {total} sites")
    print("=" * 60)

    for i, site in enumerate(sites, 1):
        site_id, domain, name, url, cat = site
        print(f"\n[{i}/{total}] {name} ({cat})")

        data = scrape_metadata(url)

        if data.get("error"):
            print(f"  ERREUR: {data['error']}")
            log_crawl(site_id, "error", data["error"])
            errors += 1
        else:
            save_metadata(site_id, data)
            log_crawl(site_id, "success")
            success += 1
            print(f"  OK | Status: {data['status_code']} | Temps: {data['response_time_ms']}ms")
            print(f"  Title: {(data.get('title') or 'N/A')[:60]}")
            print(f"  Liens: {data['internal_links_count']} int. / {data['external_links_count']} ext.")
            print(f"  SSL: {'Oui' if data['has_ssl'] else 'Non'} | Sitemap: {'Oui' if data['has_sitemap'] else 'Non'}")

        if i < total:
            delay = random.uniform(SCRAPE_DELAY_MIN, SCRAPE_DELAY_MAX)
            print(f"  Pause {delay:.1f}s...")
            time.sleep(delay)

    print(f"\nCrawl terminé : {success} succès, {errors} erreurs sur {total} sites")
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
