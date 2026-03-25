"""
Collecteur Google Trends via pytrends (100% gratuit, sans clé API).

Données collectées :
  - Score d'intérêt moyen sur 12 mois (0-100, relatif au mot-clé le plus populaire)
  - Tendance mensuelle (série temporelle)
  - Comparaison intra-secteur

Limites :
  - Les scores sont RELATIFS : 100 = pic max, les autres sont proportionnels
  - Max 5 mots-clés par requête (limite Google Trends)
  - Rate-limit non officiel → délai de 10s entre requêtes

Usage :
    python -m data_collection.apis.trends_collector
    python -m data_collection.apis.trends_collector --category presse
"""

import time
import sys
import os
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))
from database.schema import get_connection

try:
    from pytrends.request import TrendReq
    PYTRENDS_OK = True
except ImportError:
    PYTRENDS_OK = False

GEO      = "SN"          # Sénégal
TIMEFRAME = "today 12-m"
DELAY     = 12           # secondes entre requêtes (évite le rate-limit)

# Mots-clés de recherche par site (ce que les gens tapent dans Google)
SITE_KEYWORDS = {
    # Presse
    "senenews.com":    "senenews",
    "seneweb.com":     "seneweb",
    "dakaractu.com":   "dakaractu",
    "senego.com":      "senego",
    "leral.net":       "leral",
    "rewmi.com":       "rewmi",
    "pressafrik.com":  "pressafrik",
    "actusen.sn":      "actusen",
    "sudquotidien.sn": "sud quotidien",
    "dakarmatin.com":  "dakarmatin",
    "igfm.sn":         "igfm senegal",
    "xibaaru.com":     "xibaaru",
    # E-commerce
    "jumia.sn":        "jumia senegal",
    "expat-dakar.com": "expat dakar",
    "sn.coinafrique.com": "coinafrique",
    "afrikrea.com":    "afrikrea",
    "dakardeal.com":   "dakar deal",
    # Téléphonie
    "orange.sn":       "orange senegal",
    "free.sn":         "free senegal",
    "expressotelecom.sn": "expresso telecom",
    "sonatel.com":     "sonatel",
    # Banque / Finance
    "cbao.sn":         "cbao",
    "ecobank.com":     "ecobank senegal",
    "wave.com":        "wave senegal",
    "orangemoney.sn":  "orange money senegal",
    # Emploi
    "emploi.sn":       "emploi sn",
    "rekrute.com":     "rekrute senegal",
    "senjob.com":      "senjob",
}


def ensure_trends_table():
    """Crée la table site_trends si elle n'existe pas."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS site_trends (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id      INTEGER NOT NULL,
            collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            keyword      TEXT NOT NULL,
            trends_score REAL,
            trends_geo   TEXT DEFAULT 'SN',
            timeframe    TEXT DEFAULT 'today 12-m',
            trend_data   TEXT,
            FOREIGN KEY (site_id) REFERENCES sites(id)
        )
    """)
    conn.commit()
    conn.close()


def save_trend(site_id: int, keyword: str, score: float, monthly_data: list):
    conn   = get_connection()
    cursor = conn.cursor()
    # Supprimer l'ancienne entrée pour ce site
    cursor.execute(
        "DELETE FROM site_trends WHERE site_id = ? AND keyword = ?",
        (site_id, keyword)
    )
    cursor.execute(
        """INSERT INTO site_trends
           (site_id, keyword, trends_score, trends_geo, timeframe, trend_data)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (site_id, keyword, score, GEO, TIMEFRAME, json.dumps(monthly_data))
    )
    conn.commit()
    conn.close()


def query_batch(keywords: list[str], pt: "TrendReq") -> dict:
    """
    Interroge Google Trends pour un batch de max 5 mots-clés.
    Retourne {keyword: score_moyen} ou {} en cas d'erreur.
    """
    try:
        pt.build_payload(keywords, cat=0, timeframe=TIMEFRAME, geo=GEO)
        df = pt.interest_over_time()
        if df is None or df.empty:
            return {}
        results = {}
        for kw in keywords:
            if kw in df.columns:
                mean_score = float(df[kw].mean())
                monthly    = df[kw].reset_index()[["date", kw]].rename(
                    columns={kw: "score"}
                ).assign(date=lambda x: x["date"].dt.strftime("%Y-%m")).to_dict("records")
                results[kw] = {"mean": round(mean_score, 1), "monthly": monthly}
        return results
    except Exception as e:
        print(f"    Erreur pytrends : {e}")
        return {}


def collect_all_trends(category: str | None = None):
    if not PYTRENDS_OK:
        print("ERREUR : pytrends non installé.")
        print("  Installer : pip install pytrends")
        return

    ensure_trends_table()

    conn   = get_connection()
    cursor = conn.cursor()
    if category:
        cursor.execute(
            "SELECT id, name, domain FROM sites WHERE category=? ORDER BY name",
            (category,)
        )
    else:
        cursor.execute("SELECT id, name, domain FROM sites ORDER BY category, name")
    sites = cursor.fetchall()
    conn.close()

    # Construire la liste (site_id, name, domain, keyword)
    tasks = []
    for site in sites:
        sid, name, domain = site["id"], site["name"], site["domain"]
        kw = SITE_KEYWORDS.get(domain)
        if kw:
            tasks.append((sid, name, domain, kw))
        else:
            print(f"  [SKIP] {name} — aucun mot-clé défini pour {domain}")

    print(f"\nCollecte Google Trends (Sénégal, 12 mois) — {len(tasks)} sites")
    print("=" * 65)
    print("  Source : Google Trends via pytrends (données réelles)")
    print("  Échelle : 0-100 (relatif — 100 = pic max de la période)")
    print("=" * 65)

    pt = TrendReq(hl="fr-SN", tz=0, timeout=(10, 30))

    # Traitement par batch de 5 (limite Google Trends)
    batch_size = 5
    for batch_start in range(0, len(tasks), batch_size):
        batch = tasks[batch_start:batch_start + batch_size]
        keywords = [t[3] for t in batch]
        names    = [t[1] for t in batch]

        batch_ids = batch_start // batch_size + 1
        total_batches = (len(tasks) + batch_size - 1) // batch_size
        print(f"\nBatch [{batch_ids}/{total_batches}] : {', '.join(names)}")

        results = query_batch(keywords, pt)

        for sid, name, domain, kw in batch:
            if kw in results:
                score   = results[kw]["mean"]
                monthly = results[kw]["monthly"]
                save_trend(sid, kw, score, monthly)
                print(f"  {name:<28} score={score:>5.1f}/100  ({kw})")
            else:
                print(f"  {name:<28} ECHEC (données vides pour '{kw}')")

        if batch_start + batch_size < len(tasks):
            print(f"  Pause {DELAY}s (rate-limit Google Trends)...")
            time.sleep(DELAY)

    print(f"\nCollecte Google Trends terminée.")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", type=str)
    parser.add_argument("--domain",   type=str, help="Tester un seul domaine")
    args = parser.parse_args()

    if args.domain:
        ensure_trends_table()
        kw = SITE_KEYWORDS.get(args.domain, args.domain.split(".")[0])
        pt = TrendReq(hl="fr-SN", tz=0, timeout=(10, 30))
        r  = query_batch([kw], pt)
        print(f"\n{args.domain} [{kw}] : {r}")
    else:
        collect_all_trends(category=args.category)
