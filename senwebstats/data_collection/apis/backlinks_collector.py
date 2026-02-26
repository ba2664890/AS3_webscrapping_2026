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
            lines = [l for l in r.text.strip().split("\n") if l]
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

    print(f"\nCollecte backlinks — {len(sites)} sites")
    print("=" * 60)

    for i, (site_id, name, domain) in enumerate(sites, 1):
        print(f"\n[{i}/{len(sites)}] {name} ({domain})")
        data = collect_backlinks_for_domain(domain)
        save_backlinks(site_id, data)
        print(f"  Pages indexées: {data['total_backlinks']}")
        print(f"  Domaines référents: {data['referring_domains']}")
        time.sleep(3)

    print("\nCollecte backlinks terminée.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str)
    args = parser.parse_args()
    if args.domain:
        print(json.dumps(collect_backlinks_for_domain(args.domain), indent=2, ensure_ascii=False))
    else:
        collect_all_backlinks()
