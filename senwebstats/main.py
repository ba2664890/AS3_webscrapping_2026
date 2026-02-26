"""
SenWebStats — Point d'entrée principal.

Commandes disponibles :
  python main.py init          Initialiser la base de données
  python main.py crawl         Crawler tous les sites
  python main.py crawl --cat presse   Crawler une catégorie
  python main.py perf          Collecter les performances PageSpeed
  python main.py backlinks     Collecter les backlinks
  python main.py full          Collecte complète
  python main.py report        Rapport rapide en terminal
"""

import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def cmd_init():
    from database.schema import init_db, seed_sites
    print("Initialisation de SenWebStats...")
    init_db()
    seed_sites()
    print("Prêt ! Lance : python main.py crawl")


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
    collect_all_backlinks()


def cmd_report():
    from database.schema import get_connection
    conn = get_connection()
    cursor = conn.cursor()

    print("\n" + "=" * 60)
    print("RAPPORT SENWEBSTATS")
    print("=" * 60)

    cursor.execute("SELECT category, COUNT(*) FROM sites GROUP BY category ORDER BY COUNT(*) DESC")
    print("\nSites par catégorie:")
    for cat, count in cursor.fetchall():
        print(f"  {cat:<20} {count} sites")

    cursor.execute("""
        SELECT s.name, s.category, sm.status_code, sm.response_time_ms,
               sm.word_count, sm.has_ssl, sm.has_sitemap
        FROM site_metadata sm
        JOIN sites s ON s.id = sm.site_id
        WHERE sm.crawled_at = (SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = sm.site_id)
        ORDER BY sm.crawled_at DESC LIMIT 20
    """)
    rows = cursor.fetchall()
    if rows:
        print(f"\nDernières métadonnées ({len(rows)} sites):")
        print(f"  {'Site':<22} {'Catég.':<14} {'Status':<8} {'ms':<8} {'Mots':<8} SSL  Sitemap")
        print("  " + "-" * 70)
        for name, cat, status, rt, words, ssl, sitemap in rows:
            print(f"  {name[:22]:<22} {cat[:14]:<14} {str(status):<8} {str(round(rt or 0)):<8} "
                  f"{str(words or 0):<8} {'Oui' if ssl else 'Non':<5} {'Oui' if sitemap else 'Non'}")
    else:
        print("\nAucune métadonnée. Lance : python main.py crawl")

    conn.close()
    print("\n" + "=" * 60)


def cmd_full():
    print("\nCOLLECTE COMPLÈTE SENWEBSTATS")
    print("=" * 60)
    print("\nÉtape 1/3 : Métadonnées HTML")
    cmd_crawl()
    print("\nÉtape 2/3 : Performances PageSpeed")
    cmd_perf()
    print("\nÉtape 3/3 : Backlinks CommonCrawl")
    cmd_backlinks()
    print("\nCollecte complète terminée !")
    cmd_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SenWebStats — Stats web des sites sénégalais")
    parser.add_argument("command", choices=["init", "crawl", "perf", "backlinks", "full", "report"])
    parser.add_argument("--cat", type=str, help="Catégorie : presse, ecommerce, telephonie...")
    parser.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    args = parser.parse_args()

    if   args.command == "init":      cmd_init()
    elif args.command == "crawl":     cmd_crawl(category=args.cat)
    elif args.command == "perf":      cmd_perf(strategy=args.strategy)
    elif args.command == "backlinks": cmd_backlinks()
    elif args.command == "full":      cmd_full()
    elif args.command == "report":    cmd_report()
