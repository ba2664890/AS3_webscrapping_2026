"""
Collecteur d'autorité via CommonCrawl CDX API (100% gratuit, 0 inscription).

CE QUE CETTE SOURCE DONNE VRAIMENT :
  - total_backlinks  = nombre de pages du domaine indexées par CommonCrawl
                       (proxy fiable de la taille et de l'autorité du site)
  - referring_domains = NULL — les vraies backlinks externes nécessitent
                         AWS Athena sur les fichiers WAT de CommonCrawl.
                         On ne génère PAS de chiffre fictif.

Pour les referring_domains réels → utiliser Open PageRank (openpagerank_client.py).

Index utilisé : CC-MAIN-2024-51 (dernier index disponible ~déc. 2024)
Limite : ~10 000 pages max par domaine (CDX pagine par 100)
"""

import requests
import json
import time
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.schema import get_connection

CC_INDEX   = "CC-MAIN-2024-51"
CC_API_URL = f"http://index.commoncrawl.org/{CC_INDEX}-index"

# Délai entre requêtes pour ne pas surcharger CommonCrawl
CC_DELAY = 1.5


def count_indexed_pages(domain: str, max_pages: int = 10000) -> int:
    """
    Compte le nombre de pages du domaine indexées dans CommonCrawl.
    Utilise le streaming (une seule requête, limit élevée) — méthode validée
    qui retourne les vrais chiffres (ex: ~5000 pour senenews.com).
    Retourne le compte réel ou -1 en cas d'erreur réseau.
    """
    params = {
        "url":    f"*.{domain}",
        "output": "json",
        "limit":  max_pages,
        "fl":     "url",   # on ne veut que l'URL pour compter
    }
    try:
        r = requests.get(CC_API_URL, params=params, timeout=60, stream=True)
        if r.status_code == 404:
            return 0
        if r.status_code != 200:
            print(f"    CC HTTP {r.status_code} pour {domain}")
            return 0
        # Compter ligne par ligne sans charger tout en mémoire
        count = sum(1 for line in r.iter_lines() if line)
        return count
    except requests.exceptions.Timeout:
        print(f"    Timeout CommonCrawl pour {domain}")
        return -1
    except Exception as e:
        print(f"    Erreur CommonCrawl pour {domain}: {e}")
        return -1


def save_backlinks(site_id: int, cc_indexed: int, referring: int | None = None):
    """
    Sauvegarde les données en base.
    referring=None signifie 'non disponible' (pas de fausse valeur).
    """
    conn   = get_connection()
    cursor = conn.cursor()

    # Récupérer l'ancienne valeur pour calculer la variation
    cursor.execute(
        "SELECT total_backlinks FROM site_backlinks "
        "WHERE site_id = ? ORDER BY collected_at DESC LIMIT 1",
        (site_id,)
    )
    prev = cursor.fetchone()
    change = cc_indexed - (prev["total_backlinks"] if prev and prev["total_backlinks"] else 0)

    cursor.execute(
        """INSERT INTO site_backlinks
           (site_id, total_backlinks, referring_domains, backlinks_change,
            top_referring_domains)
           VALUES (?, ?, ?, ?, ?)""",
        (site_id, cc_indexed, referring, change,
         json.dumps({"source": "CommonCrawl CDX", "index": CC_INDEX,
                     "note": "Pages indexees du domaine (proxy autorite)"}))
    )
    conn.commit()
    conn.close()


def purge_fake_backlinks():
    """
    Supprime toutes les entrées de backlinks qui correspondent aux données
    factices initiales (valeurs rondes identiques : 100, 67, 29...).
    Cette fonction doit être appelée AVANT toute collecte réelle.
    """
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM site_backlinks")
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"  {deleted} entrées de backlinks effacées (données factices supprimées)")


def collect_all_backlinks(purge_first: bool = True):
    """
    Collecte les pages indexées CommonCrawl pour tous les sites.
    """
    if purge_first:
        print("\nSuppression des données factices...")
        purge_fake_backlinks()

    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, domain FROM sites ORDER BY category, name")
    sites  = cursor.fetchall()
    conn.close()

    print(f"\nCollecte CommonCrawl CDX ({CC_INDEX}) — {len(sites)} sites")
    print("=" * 65)
    print("  Donnée collectée : pages indexées du domaine (proxy autorité)")
    print("  Donnée absente   : referring_domains (nécessite AWS Athena)")
    print("=" * 65)

    results = []
    for i, site in enumerate(sites, 1):
        sid, name, domain = site["id"], site["name"], site["domain"]
        print(f"\n[{i:2d}/{len(sites)}] {name} ({domain})")

        count = count_indexed_pages(domain)

        if count >= 0:
            save_backlinks(sid, count, referring=None)
            print(f"  Pages indexées CC : {count:,}")
            results.append((name, domain, count, "OK"))
        else:
            print(f"  ECHEC — aucune donnée sauvegardée")
            results.append((name, domain, 0, "ERREUR"))

        time.sleep(CC_DELAY)

    print(f"\n{'='*65}")
    print("RÉSULTATS FINAUX")
    print(f"{'='*65}")
    print(f"  {'Site':<28} {'Domaine':<30} {'Pages CC':>9}  Statut")
    print(f"  {'-'*75}")
    for name, domain, count, status in sorted(results, key=lambda x: -x[2]):
        print(f"  {name:<28} {domain:<30} {count:>9,}  {status}")
    print(f"\n  Total : {sum(r[2] for r in results):,} pages indexées")
    print(f"  OK    : {sum(1 for r in results if r[3]=='OK')}/{len(results)} sites")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--domain", type=str, help="Tester un seul domaine")
    parser.add_argument("--no-purge", action="store_true",
                        help="Ne pas effacer les données existantes")
    args = parser.parse_args()

    if args.domain:
        count = count_indexed_pages(args.domain)
        print(f"\n{args.domain} : {count:,} pages indexées dans CommonCrawl {CC_INDEX}")
    else:
        collect_all_backlinks(purge_first=not args.no_purge)
