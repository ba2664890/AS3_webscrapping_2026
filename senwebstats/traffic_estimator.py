"""
Modèle d'estimation de trafic — Phase 2 SenWebStats
Le cœur du système : reproduit la logique de Semrush/Ahrefs.

Formule :
    Trafic estimé = Σ (Volume_mensuel_keyword × CTR[position])

Modèle CTR utilisé : Sistrix 2023 (le plus fiable sur mobile)
Source : https://www.sistrix.com/blog/ctr-studie/
"""

import sqlite3
import json
import os
import sys
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "phase2.db")

# ── Modèle CTR par position ───────────────────────────────────────────────────
# Basé sur les études Sistrix 2023 + Backlinko
# Ces taux sont pour la recherche organique mobile (dominant en Afrique)
CTR_MODEL = {
    1:  0.285,   # Position 1  → 28.5% des clics
    2:  0.157,   # Position 2  → 15.7%
    3:  0.110,   # Position 3  → 11.0%
    4:  0.080,   # Position 4  →  8.0%
    5:  0.072,   # Position 5  →  7.2%
    6:  0.051,   # Position 6  →  5.1%
    7:  0.040,   # Position 7  →  4.0%
    8:  0.032,   # Position 8  →  3.2%
    9:  0.028,   # Position 9  →  2.8%
    10: 0.025,   # Position 10 →  2.5%
    # Pages 2 (positions 11-20) — trafic très faible
    11: 0.010,
    12: 0.009,
    13: 0.008,
    14: 0.007,
    15: 0.006,
    16: 0.005,
    17: 0.004,
    18: 0.004,
    19: 0.003,
    20: 0.003,
}


def get_ctr(position: int) -> float:
    """Retourne le CTR pour une position donnée."""
    if position is None or position < 1:
        return 0.0
    if position in CTR_MODEL:
        return CTR_MODEL[position]
    if position <= 30:
        return 0.002
    return 0.001


def calculate_traffic_for_domain(domain: str, period: str = None) -> dict:
    """
    Calcule le trafic estimé pour un domaine en appliquant
    le modèle CTR sur toutes ses positions SERP.

    Returns:
        dict avec estimated_visits, keywords_ranked, top_keywords, etc.
    """
    if not os.path.exists(DB_PATH):
        return {"error": "Base Phase 2 non initialisée"}

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupérer toutes les positions de ce domaine
    cursor.execute("""
        SELECT keyword, keyword_volume, position
        FROM serp_positions
        WHERE domain = ? AND position IS NOT NULL
        ORDER BY position ASC
    """, (domain,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {
            "domain": domain,
            "estimated_visits": 0,
            "keywords_ranked": 0,
            "keywords_top3": 0,
            "keywords_top10": 0,
            "top_keywords": [],
            "period": period or datetime.now().strftime("%Y-%m"),
        }

    # ── Calcul du trafic ──────────────────────────────────────────
    total_traffic = 0
    keywords_top3 = 0
    keywords_top10 = 0
    keyword_details = []

    for keyword, volume, position in rows:
        ctr = get_ctr(position)
        traffic_contribution = int(volume * ctr)
        total_traffic += traffic_contribution

        if position <= 3:  keywords_top3 += 1
        if position <= 10: keywords_top10 += 1

        keyword_details.append({
            "keyword":    keyword,
            "position":   position,
            "volume":     volume,
            "ctr":        round(ctr * 100, 1),
            "traffic":    traffic_contribution,
        })

    # Trier par contribution trafic
    keyword_details.sort(key=lambda x: x["traffic"], reverse=True)
    top_keywords = keyword_details[:15]  # Garder les 15 meilleurs

    return {
        "domain":           domain,
        "estimated_visits": total_traffic,
        "keywords_ranked":  len(rows),
        "keywords_top3":    keywords_top3,
        "keywords_top10":   keywords_top10,
        "top_keywords":     top_keywords,
        "period":           period or datetime.now().strftime("%Y-%m"),
    }


def calculate_all_traffic(period: str = None):
    """
    Calcule et sauvegarde les estimations de trafic pour tous les domaines.
    """
    if not os.path.exists(DB_PATH):
        print("Base Phase 2 introuvable. Lance d'abord le scraper SERP.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Récupérer tous les domaines ayant des données SERP
    cursor.execute("SELECT DISTINCT domain FROM serp_positions WHERE position IS NOT NULL")
    domains = [r[0] for r in cursor.fetchall()]
    conn.close()

    if not domains:
        print("Aucune donnée SERP. Lance d'abord : python serp_scraper.py")
        return

    period = period or datetime.now().strftime("%Y-%m")
    results = []

    print(f"\n{'='*60}")
    print(f"  CALCUL TRAFIC ESTIMÉ — {period}")
    print(f"  Modèle CTR Sistrix 2023")
    print(f"{'='*60}\n")

    for domain in domains:
        data = calculate_traffic_for_domain(domain, period)

        # Sauvegarder en base
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO traffic_estimates
            (domain, period, estimated_visits, keywords_ranked,
             keywords_top3, keywords_top10, top_keywords)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data["domain"],
            data["period"],
            data["estimated_visits"],
            data["keywords_ranked"],
            data["keywords_top3"],
            data["keywords_top10"],
            json.dumps(data["top_keywords"], ensure_ascii=False),
        ))
        conn.commit()
        conn.close()

        results.append(data)
        print(f"  {domain:<30} {data['estimated_visits']:>8,} visites/mois  "
              f"({data['keywords_ranked']} mots-clés, "
              f"{data['keywords_top10']} dans top10)")

    # Classement final
    results.sort(key=lambda x: x["estimated_visits"], reverse=True)

    print(f"\n{'='*60}")
    print(f"  CLASSEMENT FINAL PAR TRAFIC ESTIMÉ")
    print(f"{'='*60}")
    print(f"  {'#':<4} {'Domaine':<30} {'Visites/mois':>14} {'Top10':>6}")
    print(f"  {'-'*58}")

    for i, r in enumerate(results, 1):
        print(f"  {i:<4} {r['domain']:<30} {r['estimated_visits']:>12,}  {r['keywords_top10']:>5}")

    print(f"\n  TOTAL estimé : {sum(r['estimated_visits'] for r in results):,} visites/mois")
    print(f"{'='*60}\n")

    return results


def get_traffic_report() -> list:
    """Récupère les dernières estimations de trafic depuis la base."""
    if not os.path.exists(DB_PATH):
        return []

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT domain, period, estimated_visits, keywords_ranked,
               keywords_top3, keywords_top10, top_keywords
        FROM traffic_estimates
        WHERE calculated_at = (
            SELECT MAX(calculated_at) FROM traffic_estimates WHERE domain = te.domain
        )
        ORDER BY estimated_visits DESC
    """)
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        domain, period, visits, ranked, top3, top10, top_kw = row
        results.append({
            "domain":           domain,
            "period":           period,
            "estimated_visits": visits,
            "keywords_ranked":  ranked,
            "keywords_top3":    top3,
            "keywords_top10":   top10,
            "top_keywords":     json.loads(top_kw) if top_kw else [],
        })

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Calcul trafic estimé — SenWebStats Phase 2")
    parser.add_argument("--domain", type=str, help="Calculer pour un domaine spécifique")
    parser.add_argument("--period", type=str, help="Période ex: 2025-02")
    args = parser.parse_args()

    if args.domain:
        result = calculate_traffic_for_domain(args.domain, args.period)
        print(f"\nEstimation trafic pour {args.domain} :")
        print(f"  Visites estimées : {result['estimated_visits']:,}/mois")
        print(f"  Mots-clés rankés : {result['keywords_ranked']}")
        print(f"  Dans le top 3    : {result['keywords_top3']}")
        print(f"  Dans le top 10   : {result['keywords_top10']}")
        if result["top_keywords"]:
            print(f"\n  Top mots-clés :")
            for kw in result["top_keywords"][:5]:
                print(f"    #{kw['position']} '{kw['keyword']}' → {kw['traffic']:,} visites "
                      f"(vol:{kw['volume']:,} × CTR:{kw['ctr']}%)")
    else:
        calculate_all_traffic(args.period)
