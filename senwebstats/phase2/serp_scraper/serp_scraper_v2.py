"""
SenWebStats Phase 2 — Scraper SERP ANTI-CAPTCHA
================================================
Stratégie en 3 niveaux pour éviter les blocages Google :

  Niveau 1 : Google Custom Search API (officielle, gratuite 100 req/jour)
  Niveau 2 : DuckDuckGo HTML (pas de captcha, résultats proches de Google)
  Niveau 3 : Bing Search (fallback supplémentaire)

SETUP Google Custom Search API (5 minutes) :
  1. Va sur https://console.developers.google.com/
  2. Active "Custom Search API" (différente de PageSpeed !)
  3. Va sur https://cse.google.com/cse/all
  4. Crée un moteur de recherche → note ton CX_ID
  5. Récupère ta clé API → note ta GOOGLE_API_KEY
  6. Colle les deux dans config.py ci-dessous
"""

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import random
import os
import sys
import json
from datetime import datetime
from urllib.parse import quote_plus, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from phase2.keywords.keywords_db import ALL_KEYWORDS

# ── CONFIGURATION — À REMPLIR ────────────────────────────────────────────────
GOOGLE_API_KEY = "AIzaSyCEj9OsTdXWAd9FzPaeVoBpOYpw-SKvt4Y"   # Ta clé API Google (même que PageSpeed ou nouvelle)
GOOGLE_CX_ID   = "703e3e9992c4f43e1"   # ID du moteur Custom Search (https://cse.google.com)

# ── Base de données ───────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "phase2.db")

TARGET_DOMAINS = [
    "seneweb.com", "dakaractu.com", "senenews.com", "senego.com",
    "leral.net", "rewmi.com", "pressafrik.com", "xibaaru.com",
    "dakarmatin.com", "lobservateur.sn", "actusen.sn",
    "jumia.sn", "expat-dakar.com", "sn.coinafrique.com",
    "orange.sn", "free.sn", "wave.com", "orangemoney.sn",
    "cbao.sn", "ecobank.com", "senjob.com", "emploi.sn",
]

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
]


# ══════════════════════════════════════════════════════════════════════════════
# NIVEAU 1 — Google Custom Search API (officielle, sans captcha)
# ══════════════════════════════════════════════════════════════════════════════
def search_google_api(keyword: str, num: int = 10) -> list:
    """
    Utilise l'API officielle Google Custom Search.
    Quota : 100 requêtes/jour gratuites.
    Retourne liste de {position, url, domain, title, snippet}
    """
    if not GOOGLE_API_KEY or not GOOGLE_CX_ID:
        return None  # Pas configurée → passer au niveau suivant

    url = "https://www.googleapis.com/customsearch/v1"
    results = []

    # L'API retourne max 10 résultats par appel, on fait 2 appels pour avoir 20
    for start in [1, 11]:
        params = {
            "key": GOOGLE_API_KEY,
            "cx":  GOOGLE_CX_ID,
            "q":   keyword,
            "num": 10,
            "start": start,
            "gl":  "sn",   # Géolocalisation Sénégal
            "hl":  "fr",   # Langue française
        }
        try:
            r = requests.get(url, params=params, timeout=15)
            if r.status_code == 429:
                print(f"      API Google quota atteint (429)")
                break
            if r.status_code != 200:
                print(f"      API Google erreur {r.status_code}")
                break

            data = r.json()
            items = data.get("items", [])

            for i, item in enumerate(items):
                position = (start - 1) + i + 1
                link = item.get("link", "")
                domain = urlparse(link).netloc.replace("www.", "")
                results.append({
                    "position": position,
                    "url":      link,
                    "domain":   domain,
                    "title":    item.get("title", ""),
                    "snippet":  item.get("snippet", "")[:200],
                    "source":   "google_api",
                })

            time.sleep(1)  # Petit délai entre les 2 appels

        except Exception as e:
            print(f"      Erreur API Google: {str(e)[:80]}")
            break

    return results if results else None


# ══════════════════════════════════════════════════════════════════════════════
# NIVEAU 2 — DuckDuckGo HTML (sans captcha, sans clé API)
# ══════════════════════════════════════════════════════════════════════════════
def search_duckduckgo(keyword: str) -> list:
    """
    Scrape DuckDuckGo HTML — pas de captcha, pas de clé API.
    Résultats très proches de Google pour les requêtes sénégalaises.
    """
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Referer": "https://duckduckgo.com/",
    }

    # DuckDuckGo avec région Sénégal (kl=sn-fr)
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(keyword)}&kl=sn-fr&kp=-1"

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            print(f"      DuckDuckGo erreur {r.status_code}")
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        position = 1

        # Sélecteur DuckDuckGo HTML
        for result in soup.select(".result__body, .result"):
            link_el = result.select_one(".result__url, .result__a")
            title_el = result.select_one(".result__title, .result__a")
            snippet_el = result.select_one(".result__snippet")

            if not link_el:
                continue

            # Extraire l'URL
            href = link_el.get("href", "") or link_el.get_text(strip=True)
            if not href.startswith("http"):
                href_from_a = result.select_one("a.result__a")
                if href_from_a:
                    href = href_from_a.get("href", "")
            if not href.startswith("http"):
                continue

            domain = urlparse(href).netloc.replace("www.", "")
            if not domain or "duckduckgo" in domain:
                continue

            title   = title_el.get_text(strip=True) if title_el else ""
            snippet = snippet_el.get_text(strip=True)[:200] if snippet_el else ""

            results.append({
                "position": position,
                "url":      href,
                "domain":   domain,
                "title":    title,
                "snippet":  snippet,
                "source":   "duckduckgo",
            })
            position += 1

            if position > 20:
                break

        return results if results else None

    except Exception as e:
        print(f"      DuckDuckGo erreur: {str(e)[:80]}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# NIVEAU 3 — Bing Search HTML (fallback supplémentaire)
# ══════════════════════════════════════════════════════════════════════════════
def search_bing(keyword: str) -> list:
    """Bing comme dernier recours — bonne couverture Afrique francophone."""
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "fr-FR,fr;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    url = f"https://www.bing.com/search?q={quote_plus(keyword)}&cc=SN&setlang=fr&count=20"

    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code != 200:
            return None

        soup = BeautifulSoup(r.text, "html.parser")
        results = []
        position = 1

        for result in soup.select("li.b_algo"):
            link_el = result.select_one("h2 a")
            if not link_el:
                continue
            href = link_el.get("href", "")
            if not href.startswith("http"):
                continue
            domain = urlparse(href).netloc.replace("www.", "")
            title = link_el.get_text(strip=True)
            snippet_el = result.select_one(".b_caption p, .b_algoSlug")
            snippet = snippet_el.get_text(strip=True)[:200] if snippet_el else ""

            results.append({
                "position": position,
                "url":      href,
                "domain":   domain,
                "title":    title,
                "snippet":  snippet,
                "source":   "bing",
            })
            position += 1
            if position > 20:
                break

        return results if results else None

    except Exception as e:
        print(f"      Bing erreur: {str(e)[:80]}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# MOTEUR PRINCIPAL — Essaie les 3 niveaux en cascade
# ══════════════════════════════════════════════════════════════════════════════
def search_keyword(keyword: str) -> tuple:
    """
    Cherche un mot-clé en essayant les sources dans l'ordre :
    1. Google API (si configurée)
    2. DuckDuckGo HTML
    3. Bing HTML

    Retourne : (résultats, source_utilisée)
    """
    # Niveau 1 — Google API officielle
    if GOOGLE_API_KEY and GOOGLE_CX_ID:
        results = search_google_api(keyword)
        if results:
            return results, "google_api"
        print(f"      Google API échouée → DuckDuckGo...")

    # Niveau 2 — DuckDuckGo
    results = search_duckduckgo(keyword)
    if results:
        return results, "duckduckgo"
    print(f"      DuckDuckGo échoué → Bing...")

    # Niveau 3 — Bing
    results = search_bing(keyword)
    if results:
        return results, "bing"

    return [], "none"


# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
# ══════════════════════════════════════════════════════════════════════════════
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS serp_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            keyword_category TEXT,
            keyword_volume INTEGER,
            domain TEXT NOT NULL,
            position INTEGER,
            url TEXT,
            title TEXT,
            snippet TEXT,
            source TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS traffic_estimates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            period TEXT NOT NULL,
            estimated_visits INTEGER,
            keywords_ranked INTEGER,
            keywords_top3 INTEGER,
            keywords_top10 INTEGER,
            top_keywords TEXT,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def find_target_positions(results: list) -> dict:
    found = {}
    for r in results:
        domain = r["domain"]
        for target in TARGET_DOMAINS:
            if target in domain or domain in target:
                if target not in found:
                    found[target] = {
                        "position": r["position"],
                        "url":      r["url"],
                        "title":    r["title"],
                        "snippet":  r["snippet"],
                    }
    return found


def save_results(kw_data: dict, positions: dict, source: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for domain in TARGET_DOMAINS:
        if domain in positions:
            d = positions[domain]
            c.execute("""INSERT INTO serp_positions
                (keyword,keyword_category,keyword_volume,domain,position,url,title,snippet,source)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (kw_data["keyword"], kw_data["category"], kw_data["volume_est"],
                 domain, d["position"], d["url"], d["title"], d["snippet"], source))
        else:
            c.execute("""INSERT INTO serp_positions
                (keyword,keyword_category,keyword_volume,domain,position,source)
                VALUES (?,?,?,?,NULL,?)""",
                (kw_data["keyword"], kw_data["category"],
                 kw_data["volume_est"], domain, source))
    conn.commit()
    conn.close()


# ══════════════════════════════════════════════════════════════════════════════
# COLLECTE PRINCIPALE
# ══════════════════════════════════════════════════════════════════════════════
def run_serp_scraping(max_keywords: int = 20, category: str = None, skip_existing: bool = True):
    init_db()

    # Sélection des mots-clés
    keywords = [k for k in ALL_KEYWORDS if not category or k["category"] == category]

    # Sauter ceux déjà scrapés aujourd'hui
    if skip_existing:
        conn = sqlite3.connect(DB_PATH)
        done = {r[0] for r in conn.cursor().execute(
            "SELECT DISTINCT keyword FROM serp_positions WHERE date(scraped_at)=date('now')"
        ).fetchall()}
        conn.close()
        keywords = [k for k in keywords if k["keyword"] not in done]
        if done:
            print(f"  {len(done)} mots-clés déjà faits aujourd'hui — ignorés")

    keywords = keywords[:max_keywords]

    # Afficher la source qui sera utilisée
    if GOOGLE_API_KEY and GOOGLE_CX_ID:
        source_info = "Google Custom Search API"
    else:
        source_info = "DuckDuckGo + Bing (fallback)"

    print(f"\n{'='*55}")
    print(f"  SCRAPING SERP ANTI-CAPTCHA")
    print(f"  Source    : {source_info}")
    print(f"  Mots-clés : {len(keywords)}")
    print(f"  Domaines  : {len(TARGET_DOMAINS)} sites sénégalais trackés")
    print(f"{'='*55}\n")

    total_found  = 0
    total_errors = 0
    sources_used = {}

    for i, kw_data in enumerate(keywords, 1):
        keyword = kw_data["keyword"]
        print(f"[{i:3}/{len(keywords)}] '{keyword}' (vol: {kw_data['volume_est']:,})")

        results, source = search_keyword(keyword)
        sources_used[source] = sources_used.get(source, 0) + 1

        if not results:
            print(f"       Aucun résultat — toutes les sources ont échoué")
            total_errors += 1
            time.sleep(5)
            continue

        print(f"       Source: {source} → {len(results)} résultats")

        positions = find_target_positions(results)
        save_results(kw_data, positions, source)

        if positions:
            total_found += len(positions)
            for domain, data in sorted(positions.items(), key=lambda x: x[1]["position"]):
                print(f"       OK  #{data['position']:2} — {domain}")
        else:
            print(f"       — Aucun site sénégalais dans le top 20")

        # Délai adapté selon la source
        if i < len(keywords):
            if source == "google_api":
                delay = random.uniform(1, 2)    # API officielle → délai court
            else:
                delay = random.uniform(5, 12)   # Scraping → délai plus long
            print(f"       Pause {delay:.1f}s...")
            time.sleep(delay)

    # Rapport final
    print(f"\n{'='*55}")
    print(f"  SCRAPING TERMINÉ")
    print(f"  Mots-clés traités : {len(keywords) - total_errors}/{len(keywords)}")
    print(f"  Positions trouvées: {total_found}")
    print(f"  Sources utilisées : {sources_used}")
    print(f"{'='*55}")

    return {"scraped": len(keywords), "found": total_found, "errors": total_errors}


def show_serp_report():
    if not os.path.exists(DB_PATH):
        print("Aucune donnée SERP. Lance le scraper d'abord.")
        return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    print(f"\n{'='*55}\n  RAPPORT SERP\n{'='*55}")
    c.execute("SELECT COUNT(DISTINCT keyword) FROM serp_positions")
    print(f"  Mots-clés analysés : {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM serp_positions WHERE position IS NOT NULL")
    print(f"  Positions trouvées : {c.fetchone()[0]}")
    c.execute("SELECT source, COUNT(*) FROM serp_positions GROUP BY source")
    print(f"  Par source :")
    for source, count in c.fetchall():
        print(f"    {source or 'N/A':<20} {count} entrées")

    c.execute("""
        SELECT domain,
               SUM(CASE WHEN position IS NOT NULL THEN 1 ELSE 0 END) as ranked,
               SUM(CASE WHEN position<=3  THEN 1 ELSE 0 END) as top3,
               SUM(CASE WHEN position<=10 THEN 1 ELSE 0 END) as top10,
               ROUND(AVG(CASE WHEN position IS NOT NULL THEN position END),1) as avg_pos
        FROM serp_positions
        GROUP BY domain
        HAVING ranked > 0
        ORDER BY top10 DESC, top3 DESC
    """)
    rows = c.fetchall()
    if rows:
        print(f"\n  {'Domaine':<28} {'Rankés':<8} {'Top3':<6} {'Top10':<7} Pos.moy")
        print("  "+"-"*55)
        for domain, ranked, top3, top10, avg_pos in rows:
            print(f"  {domain:<28} {ranked:<8} {top3:<6} {top10:<7} {avg_pos or '-'}")
    else:
        print("  Aucune position trouvée encore.")
    conn.close()
    print(f"{'='*55}\n")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SenWebStats SERP Anti-Captcha")
    parser.add_argument("--max",    type=int,  default=20)
    parser.add_argument("--cat",    type=str,  default=None)
    parser.add_argument("--report", action="store_true")
    args = parser.parse_args()

    if args.report:
        show_serp_report()
    else:
        run_serp_scraping(max_keywords=args.max, category=args.cat)
