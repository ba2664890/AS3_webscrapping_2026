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

    print(f"\nCollecte PageSpeed ({strategy}) — {len(sites)} sites")
    print("=" * 60)

    for i, (site_id, name, url) in enumerate(sites, 1):
        print(f"\n[{i}/{len(sites)}] {name}")
        data = fetch_pagespeed(url, strategy)
        if data.get("error"):
            print(f"  ERREUR: {data['error']}")
        else:
            save_performance(site_id, data)

            def grade(s):
                if s is None: return "?"
                return "BIEN" if s >= 90 else ("MOYEN" if s >= 50 else "FAIBLE")

            print(f"  Performance: {data['performance_score']} ({grade(data['performance_score'])})")
            print(f"  SEO: {data['seo_score']} | Access.: {data['accessibility_score']}")
            print(f"  LCP: {data['lcp_ms']}ms | FCP: {data['fcp_ms']}ms | TTFB: {data['ttfb_ms']}ms")
        time.sleep(2)

    print("\nCollecte PageSpeed terminée.")


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
