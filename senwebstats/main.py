"""
SenWebStats — Point d'entrée principal.

Commandes disponibles :
  python main.py init          Initialiser la base de données
  python main.py crawl         Crawler tous les sites (metadonnées HTML)
  python main.py crawl --cat presse   Crawler une catégorie seulement
  python main.py perf          Collecter les performances PageSpeed (gratuit)
  python main.py backlinks     Collecter pages indexées CommonCrawl (gratuit)
  python main.py trends        Collecter Google Trends — popularité réelle (gratuit)
  python main.py pagerank      Collecter Open PageRank (gratuit, clé requise)
  python main.py refdomains    Collecter domaines référents via Majestic (gratuit, clé requise)
  python main.py full          Collecte complète dans l'ordre logique
  python main.py status        Rapport de couverture des données
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_init():
    from database.schema import init_db, seed_sites
    from data_collection.apis.trends_collector import ensure_trends_table
    from data_collection.apis.openpagerank_client import ensure_authority_table
    print("Initialisation de SenWebStats...")
    init_db()
    ensure_trends_table()
    ensure_authority_table()
    seed_sites()
    print("Prêt ! Lancer dans cet ordre :")
    print("  1. python main.py crawl      (metadonnées HTML)")
    print("  2. python main.py perf       (PageSpeed Lighthouse)")
    print("  3. python main.py backlinks  (CommonCrawl CDX)")
    print("  4. python main.py trends     (Google Trends)")
    print("  5. python main.py pagerank   (Open PageRank — clé .env requise)")


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
    collect_all_backlinks(purge_first=True)


def cmd_trends(category=None):
    from data_collection.apis.trends_collector import collect_all_trends
    collect_all_trends(category=category)


def cmd_pagerank():
    from data_collection.apis.openpagerank_client import collect_all_pagerank
    collect_all_pagerank()


def cmd_refdomains():
    from data_collection.apis.majestic_client import collect_all_referring_domains
    collect_all_referring_domains()


def cmd_status():
    """Rapport de couverture — ce qu'on a, ce qu'il manque."""
    from database.schema import get_connection
    conn   = get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 70)
    print("SENWEBSTATS — COUVERTURE DES DONNÉES")
    print("=" * 70)

    # Compter les sites
    cursor.execute("SELECT COUNT(*) FROM sites")
    n_sites = cursor.fetchone()[0]
    print(f"\nSites enregistrés : {n_sites}")

    sections = [
        ("Métadonnées HTML",   "site_metadata",    "crawled_at"),
        ("PageSpeed",          "site_performance",  "measured_at"),
        ("CommonCrawl (pages indexées)", "site_backlinks", "collected_at"),
    ]

    for label, table, date_col in sections:
        try:
            cursor.execute(
                f"SELECT COUNT(DISTINCT site_id) FROM {table}"
            )
            n = cursor.fetchone()[0]
            pct = n / n_sites * 100
            bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
            print(f"\n  {label:<35} [{bar}] {n:2d}/{n_sites} ({pct:.0f}%)")
        except Exception:
            print(f"\n  {label:<35} table absente")

    # Google Trends
    try:
        cursor.execute("SELECT COUNT(DISTINCT site_id) FROM site_trends")
        n = cursor.fetchone()[0]
        pct = n / n_sites * 100
        bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        print(f"\n  {'Google Trends':<35} [{bar}] {n:2d}/{n_sites} ({pct:.0f}%)")
    except Exception:
        print(f"\n  {'Google Trends':<35} table absente — lancer : python main.py trends")

    # Open PageRank
    try:
        cursor.execute("SELECT COUNT(DISTINCT site_id) FROM site_authority")
        n = cursor.fetchone()[0]
        pct = n / n_sites * 100
        bar = "#" * int(pct / 5) + "." * (20 - int(pct / 5))
        print(f"\n  {'Open PageRank':<35} [{bar}] {n:2d}/{n_sites} ({pct:.0f}%)")
    except Exception:
        print(f"\n  {'Open PageRank':<35} table absente — lancer : python main.py pagerank")

    # Sites sans aucune donnée
    cursor.execute("""
        SELECT s.name, s.category, s.domain
        FROM sites s
        WHERE s.id NOT IN (SELECT DISTINCT site_id FROM site_metadata)
        ORDER BY s.category, s.name
    """)
    missing = cursor.fetchall()
    if missing:
        print(f"\n  Sites sans métadonnées ({len(missing)}) :")
        for row in missing:
            print(f"    [{row[1]:<15}] {row[0]:<25} ({row[2]})")

    # Erreurs de crawl
    cursor.execute("""
        SELECT s.name, cl.error_message
        FROM crawl_logs cl JOIN sites s ON s.id=cl.site_id
        WHERE cl.status='error'
        AND cl.started_at=(SELECT MAX(started_at) FROM crawl_logs WHERE site_id=cl.site_id)
    """)
    errors = cursor.fetchall()
    if errors:
        print(f"\n  Dernières erreurs de crawl ({len(errors)}) :")
        for name, err in errors:
            print(f"    {name:<25} {str(err)[:55]}")

    conn.close()
    print("\n" + "=" * 70)
    print("Pour relancer une collecte : python main.py full")
    print("=" * 70 + "\n")


def cmd_full():
    """Collecte complète dans l'ordre logique."""
    print("\n" + "=" * 70)
    print("COLLECTE COMPLÈTE SENWEBSTATS")
    print("Données 100% réelles — aucune valeur générée")
    print("=" * 70)

    print("\nÉtape 1/4 : Métadonnées HTML (crawl direct)")
    cmd_crawl()

    print("\nÉtape 2/4 : Performances PageSpeed Lighthouse (API Google gratuite)")
    cmd_perf()

    print("\nÉtape 3/4 : Pages indexées CommonCrawl (autorité réelle)")
    cmd_backlinks()

    print("\nÉtape 4/4 : Google Trends (popularité réelle au Sénégal)")
    cmd_trends()

    print("\nOpen PageRank (optionnel) :")
    print("  Ajouter OPENPAGERANK_API_KEY dans .env puis lancer : python main.py pagerank")
    print("\nDomaines référents Majestic (optionnel) :")
    print("  Ajouter MAJESTIC_API_KEY dans .env puis lancer : python main.py refdomains")

    print("\nCollecte complète terminée.")
    cmd_status()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SenWebStats — Observatoire web sénégalais",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "command",
        choices=["init", "crawl", "perf", "backlinks", "trends", "pagerank", "refdomains", "full", "status"]
    )
    parser.add_argument("--cat",      type=str, help="Filtrer par catégorie")
    parser.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    args = parser.parse_args()

    cmds = {
        "init":      cmd_init,
        "crawl":     lambda: cmd_crawl(category=args.cat),
        "perf":      lambda: cmd_perf(strategy=args.strategy),
        "backlinks": cmd_backlinks,
        "trends":    lambda: cmd_trends(category=args.cat),
        "pagerank":   cmd_pagerank,
        "refdomains": cmd_refdomains,
        "full":       cmd_full,
        "status":    cmd_status,
    }
    cmds[args.command]()
