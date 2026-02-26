"""
Script principal SenWebStats.
Lance l'initialisation, la collecte et fournit des commandes utiles.

Usage:
    python main.py init          # Initialiser la base de données
    python main.py crawl         # Crawler tous les sites
    python main.py crawl --cat presse   # Crawler une catégorie
    python main.py perf          # Collecter les performances PageSpeed
    python main.py backlinks     # Collecter les backlinks
    python main.py full          # Collecte complète (tout)
    python main.py report        # Afficher un rapport rapide
"""

import sys
import os
import argparse
import json
from datetime import datetime

# Setup path
sys.path.insert(0, os.path.dirname(__file__))


def cmd_init():
    """Initialise la base de données et insère les sites."""
    print("🔧 Initialisation de SenWebStats...")
    from database.schema import init_db, seed_sites
    init_db()
    seed_sites()
    print("✅ Prêt ! Lance 'python main.py crawl' pour démarrer la collecte.")


def cmd_crawl(category=None):
    """Lance le crawl de métadonnées."""
    from database.schema import init_db, seed_sites
    from data_collection.scrapers.metadata_scraper import crawl_all_sites
    
    # S'assurer que la DB est initialisée
    init_db()
    seed_sites()
    
    result = crawl_all_sites(category=category)
    return result


def cmd_perf(strategy="mobile"):
    """Collecte les performances PageSpeed."""
    from data_collection.apis.pagespeed_collector import collect_performance_all
    collect_performance_all(strategy=strategy)


def cmd_backlinks():
    """Collecte les backlinks via CommonCrawl."""
    from data_collection.apis.backlinks_collector import collect_all_backlinks
    collect_all_backlinks()


def cmd_report():
    """Affiche un rapport rapide des données collectées."""
    from database.schema import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("📊 RAPPORT SENWEBSTATS")
    print(f"   {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("=" * 60)
    
    # Nombre de sites par catégorie
    cursor.execute("""
        SELECT category, COUNT(*) as count
        FROM sites GROUP BY category ORDER BY count DESC
    """)
    cats = cursor.fetchall()
    
    print("\n🗂️  Sites par catégorie:")
    for cat, count in cats:
        print(f"   {cat:<20} {count} sites")
    
    # Dernière collecte de métadonnées
    cursor.execute("""
        SELECT s.name, s.category, sm.status_code, sm.response_time_ms,
               sm.word_count, sm.has_ssl, sm.has_sitemap, sm.crawled_at
        FROM site_metadata sm
        JOIN sites s ON s.id = sm.site_id
        WHERE sm.crawled_at = (
            SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = sm.site_id
        )
        ORDER BY sm.crawled_at DESC
        LIMIT 20
    """)
    metadata = cursor.fetchall()
    
    if metadata:
        print(f"\n🌐 Dernières métadonnées collectées ({len(metadata)} sites):")
        print(f"   {'Site':<20} {'Catég.':<12} {'Status':<8} {'Temps(ms)':<12} {'Mots':<8} {'SSL':<5} {'Sitemap'}")
        print("   " + "-" * 75)
        for row in metadata:
            name, cat, status, rt, words, ssl, sitemap, crawled = row
            ssl_icon = "✓" if ssl else "✗"
            sitemap_icon = "✓" if sitemap else "✗"
            print(f"   {name[:20]:<20} {cat[:12]:<12} {str(status):<8} {str(round(rt or 0)):<12} {str(words or 0):<8} {ssl_icon:<5} {sitemap_icon}")
    else:
        print("\n⚠️  Aucune métadonnée collectée. Lance 'python main.py crawl' d'abord.")
    
    # Stats Performance
    cursor.execute("""
        SELECT COUNT(*) FROM site_performance
    """)
    perf_count = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT AVG(performance_score), AVG(seo_score) FROM site_performance
    """)
    perf_avgs = cursor.fetchone()
    
    if perf_count > 0:
        print(f"\n⚡ Performance PageSpeed ({perf_count} mesures):")
        print(f"   Score moyen Performance : {round(perf_avgs[0] or 0, 1)}/100")
        print(f"   Score moyen SEO         : {round(perf_avgs[1] or 0, 1)}/100")
    
    conn.close()
    print("\n" + "=" * 60)


def cmd_full():
    """Lance une collecte complète."""
    print("\n🚀 COLLECTE COMPLÈTE SENWEBSTATS")
    print("=" * 60)
    
    print("\n📌 Étape 1/3 : Métadonnées HTML")
    cmd_crawl()
    
    print("\n📌 Étape 2/3 : Performances PageSpeed")
    cmd_perf()
    
    print("\n📌 Étape 3/3 : Backlinks CommonCrawl")
    cmd_backlinks()
    
    print("\n✅ Collecte complète terminée !")
    cmd_report()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="SenWebStats — Statistiques web des sites sénégalais"
    )
    parser.add_argument("command", choices=["init", "crawl", "perf", "backlinks", "full", "report"])
    parser.add_argument("--cat", type=str, help="Catégorie (presse, ecommerce, telephonie...)")
    parser.add_argument("--strategy", choices=["mobile", "desktop"], default="mobile")
    
    args = parser.parse_args()
    
    if args.command == "init":
        cmd_init()
    elif args.command == "crawl":
        cmd_crawl(category=args.cat)
    elif args.command == "perf":
        cmd_perf(strategy=args.strategy)
    elif args.command == "backlinks":
        cmd_backlinks()
    elif args.command == "full":
        cmd_full()
    elif args.command == "report":
        cmd_report()
