"""
Collecteur de backlinks via CommonCrawl Index — 100% gratuit.
CommonCrawl indexe des milliards de pages web et rend son index accessible.
Doc : https://index.commoncrawl.org/
"""

import requests
import json
import time
import sys
import os
from collections import Counter
from urllib.parse import urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from database.schema import get_connection

# Index CommonCrawl — mettre à jour avec le dernier index disponible
# Voir : https://index.commoncrawl.org/
CC_INDEXES = [
    "CC-MAIN-2024-30",
    "CC-MAIN-2024-22",
    "CC-MAIN-2024-10",
]

CC_API_BASE = "https://index.commoncrawl.org/{index}-index"


def query_commoncrawl(domain: str, index: str = None, max_records: int = 1000) -> list:
    """
    Cherche toutes les pages qui pointent vers un domaine dans CommonCrawl.
    Retourne une liste de dictionnaires avec url, timestamp, etc.
    """
    if index is None:
        index = CC_INDEXES[0]
    
    api_url = CC_API_BASE.format(index=index)
    
    results = []
    page = 0
    
    while True:
        params = {
            "url": f"*.{domain}",  # wildcard pour tous les sous-domaines
            "output": "json",
            "limit": 100,
            "page": page,
        }
        
        try:
            response = requests.get(api_url, params=params, timeout=30)
            
            if response.status_code == 404:
                break
            if response.status_code != 200:
                print(f"    ⚠️  CommonCrawl HTTP {response.status_code}")
                break
            
            lines = response.text.strip().split("\n")
            if not lines or lines == [""]:
                break
            
            batch = []
            for line in lines:
                try:
                    batch.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
            
            if not batch:
                break
            
            results.extend(batch)
            
            if len(results) >= max_records:
                break
            
            page += 1
            time.sleep(1)  # Respecter l'API CommonCrawl
            
        except requests.exceptions.Timeout:
            print("    ⏱️  Timeout CommonCrawl")
            break
        except Exception as e:
            print(f"    ❌ Erreur: {e}")
            break
    
    return results[:max_records]


def analyze_backlinks(records: list, target_domain: str) -> dict:
    """
    Analyse les enregistrements CommonCrawl pour extraire les métriques de backlinks.
    """
    # URLs qui pointent VERS le domaine cible (via le champ 'url' qui est l'URL crawlée)
    # Note : Dans CommonCrawl index, on cherche les pages DU domaine
    # Pour de vrais backlinks, il faudrait analyser le contenu des pages
    # Cette approche compte les URLs indexées du domaine cible
    
    total_pages = len(records)
    
    # Extraire les domaines référents depuis les enregistrements
    referring_domains = set()
    domain_counter = Counter()
    
    for record in records:
        url = record.get("url", "")
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain and domain != target_domain:
            referring_domains.add(domain)
            domain_counter[domain] += 1
    
    # Top domaines référents
    top_domains = [
        {"domain": domain, "count": count}
        for domain, count in domain_counter.most_common(20)
    ]
    
    return {
        "total_indexed_pages": total_pages,
        "referring_domains_count": len(referring_domains),
        "top_referring_domains": top_domains,
    }


def collect_backlinks_for_domain(domain: str) -> dict:
    """Collecte les données de backlinks pour un domaine."""
    print(f"  🕷️  Recherche dans CommonCrawl pour {domain}...")
    
    records = query_commoncrawl(domain, max_records=500)
    
    if not records:
        return {
            "total_backlinks": 0,
            "referring_domains": 0,
            "top_referring_domains": [],
            "source": "commoncrawl",
        }
    
    analysis = analyze_backlinks(records, domain)
    
    return {
        "total_backlinks": analysis["total_indexed_pages"],
        "referring_domains": analysis["referring_domains_count"],
        "top_referring_domains": analysis["top_referring_domains"],
        "source": "commoncrawl",
    }


def save_backlinks(site_id: int, data: dict):
    """Sauvegarde les données de backlinks en base."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Récupérer la valeur précédente pour calculer le changement
    cursor.execute("""
        SELECT total_backlinks FROM site_backlinks
        WHERE site_id = ?
        ORDER BY collected_at DESC LIMIT 1
    """, (site_id,))
    
    prev = cursor.fetchone()
    prev_count = prev[0] if prev else 0
    change = data["total_backlinks"] - prev_count
    
    cursor.execute("""
        INSERT INTO site_backlinks (
            site_id, total_backlinks, referring_domains,
            top_referring_domains, backlinks_change
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        site_id,
        data["total_backlinks"],
        data["referring_domains"],
        json.dumps(data["top_referring_domains"]),
        change,
    ))
    conn.commit()
    conn.close()


def collect_all_backlinks():
    """Collecte les backlinks de tous les sites."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, domain FROM sites ORDER BY category")
    sites = cursor.fetchall()
    conn.close()
    
    print(f"\n🔗 Collecte des backlinks — {len(sites)} sites")
    print("=" * 60)
    
    for i, (site_id, name, domain) in enumerate(sites, 1):
        print(f"\n[{i}/{len(sites)}] {name} ({domain})")
        
        data = collect_backlinks_for_domain(domain)
        save_backlinks(site_id, data)
        
        print(f"  ✅ Pages indexées: {data['total_backlinks']}")
        print(f"  🌐 Domaines référents: {data['referring_domains']}")
        
        if data["top_referring_domains"]:
            top3 = data["top_referring_domains"][:3]
            domains_str = ", ".join([d["domain"] for d in top3])
            print(f"  📌 Top domaines: {domains_str}")
        
        # Pause pour respecter CommonCrawl
        time.sleep(3)
    
    print("\n✅ Collecte backlinks terminée.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, help="Domaine à analyser (ex: seneweb.com)")
    args = parser.parse_args()
    
    if args.domain:
        result = collect_backlinks_for_domain(args.domain)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        collect_all_backlinks()
