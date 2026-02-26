"""
SenWebStats Phase 2 — Script principal
Commandes :
  python run_phase2.py keywords
  python run_phase2.py scrape --max 5
  python run_phase2.py scrape --max 30 --cat presse
  python run_phase2.py traffic
  python run_phase2.py report
"""
import sys, os, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def cmd_keywords():
    from phase2.keywords.keywords_db import KEYWORDS, ALL_KEYWORDS, TOTAL_VOLUME
    print(f"\n{'='*55}\n  MOTS-CLES : {len(ALL_KEYWORDS)} | Volume : {TOTAL_VOLUME:,}/mois\n{'='*55}")
    for cat, kws in KEYWORDS.items():
        vol = sum(k["volume_est"] for k in kws)
        print(f"  {cat:<22} {len(kws):3} mots-cles | {vol:>8,} vol./mois")
    print(f"\n  Top 10 :")
    for i, kw in enumerate(ALL_KEYWORDS[:10], 1):
        print(f"  {i:2}. {kw['keyword']:<35} {kw['volume_est']:>7,}/mois")

def cmd_scrape(max_kw=20, category=None):
    from phase2.serp_scraper.serp_scraper import run_serp_scraping
    print(f"\nScraping SERP ({max_kw} mots-cles)...")
    run_serp_scraping(max_keywords=max_kw, category=category)

def cmd_traffic():
    from phase2.traffic_model.traffic_estimator import calculate_all_traffic
    calculate_all_traffic()

def cmd_report():
    from phase2.serp_scraper.serp_scraper import show_serp_report
    from phase2.traffic_model.traffic_estimator import get_traffic_report
    show_serp_report()
    results = get_traffic_report()
    if results:
        print(f"\nESTIMATIONS DE TRAFIC :")
        print(f"  {'Domaine':<30} {'Visites/mois':>14} {'Mots-cles':>10} {'Top10':>6}")
        print("  "+"-"*62)
        for r in results:
            print(f"  {r['domain']:<30} {r['estimated_visits']:>12,}  {r['keywords_ranked']:>8}  {r['keywords_top10']:>5}")
    else:
        print("\nAucune estimation. Lance d abord : scrape puis traffic")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SenWebStats Phase 2")
    parser.add_argument("command", choices=["keywords","scrape","traffic","report"])
    parser.add_argument("--max",  type=int, default=20)
    parser.add_argument("--cat",  type=str, default=None)
    args = parser.parse_args()
    if   args.command == "keywords": cmd_keywords()
    elif args.command == "scrape":   cmd_scrape(args.max, args.cat)
    elif args.command == "traffic":  cmd_traffic()
    elif args.command == "report":   cmd_report()
