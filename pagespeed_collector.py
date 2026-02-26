"""
Collecteur Google PageSpeed API (gratuite — 25 000 req/jour).
Version avec retry automatique et délais longs pour éviter le HTTP 429.
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
    """Appelle l'API PageSpeed Insights pour une URL."""
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
        response = requests.get(PAGESPEED_API_URL, params=params, timeout=60)

        if response.status_code == 429:
            result["error"] = "HTTP 429 - quota depasse"
            return result
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


def fetch_pagespeed_with_retry(url: str, strategy: str = "mobile", max_retries: int = 3) -> dict:
    """Retry automatique avec délais croissants sur erreur 429."""
    delays = [15, 45, 90]
    for attempt in range(max_retries):
        result = fetch_pagespeed(url, strategy)
        if "429" in str(result.get("error", "")):
            wait = delays[min(attempt, len(delays) - 1)]
            print(f"  Quota 429 — attente {wait}s (tentative {attempt + 1}/{max_retries})...")
            time.sleep(wait)
        else:
            return result
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


def collect_performance_all(strategy: str = "mobile"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, url FROM sites ORDER BY category")
    sites = cursor.fetchall()
    conn.close()

    print(f"\nCollecte PageSpeed ({strategy}) - {len(sites)} sites")
    print(f"Delai de 12s entre chaque site (~{len(sites) * 12 // 60} min au total)")
    print("=" * 60)

    success, errors = 0, 0

    for i, (site_id, name, url) in enumerate(sites, 1):
        print(f"\n[{i}/{len(sites)}] {name}")
        data = fetch_pagespeed_with_retry(url, strategy)

        if data.get("error"):
            print(f"  ERREUR: {data['error']}")
            errors += 1
        else:
            save_performance(site_id, data)
            success += 1

            def grade(s):
                if s is None: return "?"
                if s >= 90: return "BIEN"
                if s >= 50: return "MOYEN"
                return "FAIBLE"

            print(f"  OK - Performance: {data['performance_score']} ({grade(data['performance_score'])})")
            print(f"     SEO: {data['seo_score']} | Accessibilite: {data['accessibility_score']}")
            print(f"     LCP: {data['lcp_ms']}ms | FCP: {data['fcp_ms']}ms | TTFB: {data['ttfb_ms']}ms")

        if i < len(sites):
            print(f"  Pause 12s...")
            time.sleep(12)

    print(f"\nCollecte PageSpeed terminee: {success} succes, {errors} erreurs sur {len(sites)} sites")


def collect_performance_category(category: str, strategy: str = "mobile"):
    """Collecte les performances d'une seule categorie."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, url FROM sites WHERE category = ? ORDER BY name", (category,))
    sites = cursor.fetchall()
    conn.close()

    if not sites:
        print(f"Aucun site pour la categorie '{category}'")
        return

    print(f"\nCollecte PageSpeed - '{category}' ({len(sites)} sites)")
    print("=" * 60)

    for i, (site_id, name, url) in enumerate(sites, 1):
        print(f"\n[{i}/{len(sites)}] {name}")
        data = fetch_pagespeed_with_retry(url, strategy)

        if data.get("error"):
            print(f"  ERREUR: {data['error']}")
        else:
            save_performance(site_id, data)
            print(f"  OK - Perf: {data['performance_score']} | SEO: {data['seo_score']}")
            print(f"     LCP: {data['lcp_ms']}ms | TTFB: {data['ttfb_ms']}ms")

        if i < len(sites):
            print(f"  Pause 12s...")
            time.sleep(12)

    print(f"\nCategorie '{category}' terminee.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--url",      type=str)
    parser.add_argument("--cat",      type=str, help="presse, ecommerce, telephonie...")
    parser.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    args = parser.parse_args()

    if args.url:
        result = fetch_pagespeed_with_retry(args.url, args.strategy)
        print(json.dumps(result, indent=2))
    elif args.cat:
        collect_performance_category(args.cat, args.strategy)
    else:
        collect_performance_all(args.strategy)