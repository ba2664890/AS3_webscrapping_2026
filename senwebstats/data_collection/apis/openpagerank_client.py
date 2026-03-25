"""
Client Open PageRank (domcop.com) — gratuit, pas de carte bancaire.

Données collectées :
  - page_rank_decimal : score 0-10 (analogue au PageRank Google original)
  - rank              : rang mondial (plus petit = plus autoritaire)

Inscription (email simple, pas de mail pro requis) :
  1. Aller sur https://www.domcop.com/openpagerank/
  2. Cliquer "Get Free API Key"
  3. Entrer n'importe quel email → recevoir la clé
  4. Ajouter dans .env : OPENPAGERANK_API_KEY=ta_cle

Limites :
  - 100 domaines par requête
  - Usage gratuit : suffisant pour 28 sites
"""

import requests
import os
import sys
import json
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.schema import get_connection

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

OPR_API_URL = "https://openpagerank.com/api/v1.0/getPageRank"
OPR_API_KEY  = os.getenv("OPENPAGERANK_API_KEY", "")


def ensure_authority_table():
    """Crée la table site_authority si elle n'existe pas."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_authority (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id         INTEGER NOT NULL,
            collected_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            page_rank       REAL,
            global_rank     INTEGER,
            source          TEXT DEFAULT 'openpagerank',
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)
    conn.commit()
    conn.close()


def fetch_pagerank_batch(domains: list[str]) -> dict:
    """
    Interroge l'API Open PageRank pour un batch de domaines.
    Retourne {domain: {"page_rank": float, "rank": int}} ou {} si pas de clé.
    """
    if not OPR_API_KEY:
        return {}

    # L'API accepte jusqu'à 100 domaines via le paramètre répété domains[]
    params  = [("domains[]", d) for d in domains[:100]]
    headers = {"API-OPR": OPR_API_KEY}

    try:
        r = requests.get(OPR_API_URL, params=params, headers=headers, timeout=20)
        if r.status_code == 403:
            print("  ERREUR : clé API Open PageRank invalide ou absente")
            return {}
        if r.status_code != 200:
            print(f"  ERREUR HTTP {r.status_code}")
            return {}

        data    = r.json()
        results = {}
        for item in data.get("response", []):
            domain = item.get("domain", "")
            pr     = item.get("page_rank_decimal")
            rank   = item.get("rank")
            if domain and pr is not None:
                results[domain] = {
                    "page_rank": round(float(pr), 2),
                    "rank":      int(rank) if rank else None,
                }
        return results
    except Exception as e:
        print(f"  Erreur Open PageRank : {e}")
        return {}


def save_authority(site_id: int, page_rank: float, global_rank: int | None):
    conn   = get_connection()
    cursor = conn.cursor()
    # Supprimer l'ancienne entrée
    cursor.execute("DELETE FROM site_authority WHERE site_id = ?", (site_id,))
    cursor.execute(
        "INSERT INTO site_authority (site_id, page_rank, global_rank, source) VALUES (?,?,?,?)",
        (site_id, page_rank, global_rank, "openpagerank")
    )
    conn.commit()
    conn.close()


def collect_all_pagerank():
    if not OPR_API_KEY:
        print("\nOpen PageRank non configuré.")
        print("  1. Inscription gratuite sur https://www.domcop.com/openpagerank/")
        print("  2. Ajouter dans .env : OPENPAGERANK_API_KEY=ta_cle")
        print("  3. Relancer : python main.py pagerank")
        return

    ensure_authority_table()

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, domain FROM sites ORDER BY category, name")
    sites  = cursor.fetchall()
    conn.close()

    domains    = [s["domain"] for s in sites]
    site_map   = {s["domain"]: (s["id"], s["name"]) for s in sites}

    print(f"\nCollecte Open PageRank — {len(domains)} domaines")
    print("=" * 65)

    # On peut tout envoyer en une seule requête (max 100, on en a 28)
    results = fetch_pagerank_batch(domains)

    if not results:
        print("  Aucun résultat reçu.")
        return

    print(f"  {'Site':<28} {'Domaine':<30} {'PageRank':>9}  {'Rang mondial':>12}")
    print(f"  {'-'*80}")

    found = 0
    for domain in sorted(results, key=lambda d: -(results[d]["page_rank"] or 0)):
        sid, name = site_map.get(domain, (None, domain))
        if sid:
            pr   = results[domain]["page_rank"]
            rank = results[domain]["rank"]
            save_authority(sid, pr, rank)
            rank_str = f"{rank:,}" if rank else "—"
            print(f"  {name:<28} {domain:<30} {pr:>9.2f}  {rank_str:>12}")
            found += 1

    # Sites sans résultat
    missing = [d for d in domains if d not in results]
    if missing:
        print(f"\n  Sites sans données OPR ({len(missing)}) :")
        for d in missing:
            _, name = site_map.get(d, (None, d))
            print(f"    {name} ({d})")

    print(f"\n  {found}/{len(domains)} sites avec données PageRank réelles")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str)
    args = parser.parse_args()

    if args.domain:
        ensure_authority_table()
        r = fetch_pagerank_batch([args.domain])
        print(json.dumps(r, indent=2))
    else:
        collect_all_pagerank()
