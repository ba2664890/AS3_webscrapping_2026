"""
Client Majestic API (tier gratuit) — domaines référents réels.

Données collectées :
  - referring_domains : nombre de domaines référents uniques (RefDomains)
  - total_backlinks   : nombre total de backlinks externes (ExtBackLinks)

Inscription gratuite :
  1. Aller sur https://majestic.com
  2. Créer un compte gratuit → onglet "API"
  3. Copier la clé API gratuite ("Free API Key")
  4. Ajouter dans .env : MAJESTIC_API_KEY=ta_cle

Limites du tier gratuit :
  - 10 000 requêtes/mois
  - Données de l'index Fresh (derniers 90 jours)
  - Suffisant pour 28 sites plusieurs fois/semaine
"""

import requests
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.schema import get_connection

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

MAJESTIC_API_URL = "https://api.majestic.com/api/json"
MAJESTIC_API_KEY = os.getenv("MAJESTIC_API_KEY", "")
MAJESTIC_DELAY   = 0.5  # secondes entre requêtes


def fetch_referring_domains(domains: list[str]) -> dict:
    """
    Interroge Majestic GetIndexItemInfo pour une liste de domaines.
    Retourne {domain: {"referring_domains": int, "total_backlinks": int}}.
    Traite par batch de 10 (limite de l'API gratuite par appel).
    """
    if not MAJESTIC_API_KEY:
        return {}

    results = {}
    batch_size = 10

    for i in range(0, len(domains), batch_size):
        batch = domains[i:i + batch_size]
        params = {
            "app_api_key": MAJESTIC_API_KEY,
            "cmd":         "GetIndexItemInfo",
            "items":       len(batch),
            "datasource":  "fresh",  # index des 90 derniers jours
        }
        for j, d in enumerate(batch):
            params[f"item{j}"] = d

        try:
            r = requests.get(MAJESTIC_API_URL, params=params, timeout=20)
            if r.status_code != 200:
                print(f"  Majestic HTTP {r.status_code}")
                continue

            data = r.json()
            if data.get("Code") != "OK":
                print(f"  Majestic erreur : {data.get('ErrorMessage', 'inconnue')}")
                continue

            for item in data.get("DataTables", {}).get("Results", {}).get("Data", []):
                domain = item.get("Item", "")
                ref_d  = item.get("RefDomains", 0)
                backl  = item.get("ExtBackLinks", 0)
                if domain:
                    results[domain] = {
                        "referring_domains": int(ref_d) if ref_d else 0,
                        "total_backlinks":   int(backl) if backl else 0,
                    }
        except Exception as e:
            print(f"  Erreur Majestic : {e}")

        if i + batch_size < len(domains):
            time.sleep(MAJESTIC_DELAY)

    return results


def save_referring_domains(site_id: int, referring_domains: int, total_backlinks: int):
    """Met à jour la table site_backlinks avec les données Majestic."""
    conn   = get_connection()
    cursor = conn.cursor()

    # Récupérer l'entrée la plus récente pour calculer la variation
    cursor.execute(
        "SELECT referring_domains FROM site_backlinks "
        "WHERE site_id = ? ORDER BY collected_at DESC LIMIT 1",
        (site_id,)
    )
    prev = cursor.fetchone()

    if prev and prev["referring_domains"] is not None:
        # Mettre à jour la ligne existante
        cursor.execute(
            "UPDATE site_backlinks SET referring_domains = ?, total_backlinks = ?, "
            "top_referring_domains = ? "
            "WHERE site_id = ? AND collected_at = ("
            "  SELECT MAX(collected_at) FROM site_backlinks WHERE site_id = ?)",
            (referring_domains, total_backlinks,
             '{"source": "Majestic Fresh Index"}',
             site_id, site_id)
        )
    else:
        cursor.execute(
            """INSERT INTO site_backlinks
               (site_id, total_backlinks, referring_domains, backlinks_change,
                top_referring_domains)
               VALUES (?, ?, ?, ?, ?)""",
            (site_id, total_backlinks, referring_domains, 0,
             '{"source": "Majestic Fresh Index"}')
        )

    conn.commit()
    conn.close()


def collect_all_referring_domains():
    """
    Collecte les domaines référents via Majestic pour tous les sites.
    """
    if not MAJESTIC_API_KEY:
        print("\nMajestic API non configurée.")
        print("  1. Inscription gratuite sur https://majestic.com")
        print("  2. Onglet API → copier la clé gratuite")
        print("  3. Ajouter dans .env : MAJESTIC_API_KEY=ta_cle")
        return

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, domain FROM sites ORDER BY category, name")
    sites  = cursor.fetchall()
    conn.close()

    domains  = [s["domain"] for s in sites]
    site_map = {s["domain"]: (s["id"], s["name"]) for s in sites}

    print(f"\nCollecte Majestic (domaines référents) — {len(domains)} sites")
    print("=" * 65)

    results = fetch_referring_domains(domains)

    if not results:
        print("  Aucun résultat reçu.")
        return

    print(f"  {'Site':<28} {'Domaine':<28} {'Réf. Dom.':>10}  {'Backlinks':>10}")
    print(f"  {'-'*80}")

    found = 0
    for domain in domains:
        if domain not in results:
            continue
        sid, name = site_map.get(domain, (None, domain))
        if not sid:
            continue
        rd = results[domain]["referring_domains"]
        bl = results[domain]["total_backlinks"]
        save_referring_domains(sid, rd, bl)
        print(f"  {name:<28} {domain:<28} {rd:>10,}  {bl:>10,}")
        found += 1

    missing = [d for d in domains if d not in results]
    if missing:
        print(f"\n  Sites sans données ({len(missing)}) :")
        for d in missing:
            _, name = site_map.get(d, (None, d))
            print(f"    {name} ({d})")

    print(f"\n  {found}/{len(domains)} sites avec données Majestic")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, help="Tester un seul domaine")
    args = parser.parse_args()

    if args.domain:
        r = fetch_referring_domains([args.domain])
        if r:
            d = r[args.domain]
            print(f"\n{args.domain}")
            print(f"  Domaines référents : {d['referring_domains']:,}")
            print(f"  Backlinks totaux   : {d['total_backlinks']:,}")
        else:
            print("Aucune donnée (vérifier MAJESTIC_API_KEY)")
    else:
        collect_all_referring_domains()
