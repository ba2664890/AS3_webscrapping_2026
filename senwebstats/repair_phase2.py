"""
SenWebStats — Script de réparation Phase 2
Place ce fichier dans senwebstats/ et lance : python repair_phase2.py
Il vérifie et recrée tous les fichiers manquants au bon endroit.
"""

import os, sys

BASE = os.path.dirname(os.path.abspath(__file__))

print("\n" + "="*60)
print("   REPARATION PHASE 2")
print(f"   Dossier : {BASE}")
print("="*60)

# ── 1. Vérification de la structure actuelle ──────────────────
print("\nVERIFICATION DE LA STRUCTURE :")
expected = [
    "phase2",
    "phase2/__init__.py",
    "phase2/keywords",
    "phase2/keywords/__init__.py",
    "phase2/keywords/keywords_db.py",
    "phase2/serp_scraper",
    "phase2/serp_scraper/__init__.py",
    "phase2/serp_scraper/serp_scraper.py",
    "phase2/traffic_model",
    "phase2/traffic_model/__init__.py",
    "phase2/traffic_model/traffic_estimator.py",
    "phase2/data",
    "run_phase2.py",
]
for item in expected:
    full = os.path.join(BASE, item.replace("/", os.sep))
    exists = os.path.exists(full)
    print(f"  {'OK' if exists else 'MANQUANT':<10} {item}")

# ── 2. Créer tous les dossiers ────────────────────────────────
print("\nCREATION DES DOSSIERS :")
for d in ["phase2", "phase2/keywords", "phase2/serp_scraper",
          "phase2/traffic_model", "phase2/data"]:
    path = os.path.join(BASE, d.replace("/", os.sep))
    os.makedirs(path, exist_ok=True)
    print(f"  OK {d}/")

# ── 3. Créer tous les __init__.py ─────────────────────────────
for init in ["phase2/__init__.py", "phase2/keywords/__init__.py",
             "phase2/serp_scraper/__init__.py", "phase2/traffic_model/__init__.py"]:
    path = os.path.join(BASE, init.replace("/", os.sep))
    with open(path, "w") as f:
        f.write("")

# ── 4. keywords_db.py ─────────────────────────────────────────
kw_path = os.path.join(BASE, "phase2", "keywords", "keywords_db.py")
with open(kw_path, "w", encoding="utf-8") as f:
    f.write('''
KEYWORDS = {
    "presse": [
        {"keyword": "seneweb",               "volume_est": 90000, "intent": "nav",    "lang": "fr"},
        {"keyword": "dakaractu",             "volume_est": 60000, "intent": "nav",    "lang": "fr"},
        {"keyword": "senenews",              "volume_est": 40000, "intent": "nav",    "lang": "fr"},
        {"keyword": "senego",                "volume_est": 35000, "intent": "nav",    "lang": "fr"},
        {"keyword": "leral net",             "volume_est": 25000, "intent": "nav",    "lang": "fr"},
        {"keyword": "rewmi",                 "volume_est": 20000, "intent": "nav",    "lang": "fr"},
        {"keyword": "actualite senegal",     "volume_est": 45000, "intent": "info",   "lang": "fr"},
        {"keyword": "news senegal",          "volume_est": 25000, "intent": "info",   "lang": "fr"},
        {"keyword": "ousmane sonko",         "volume_est": 70000, "intent": "info",   "lang": "fr"},
        {"keyword": "bassirou diomaye faye", "volume_est": 55000, "intent": "info",   "lang": "fr"},
        {"keyword": "sadio mane",            "volume_est": 40000, "intent": "info",   "lang": "fr"},
        {"keyword": "can 2025 senegal",      "volume_est": 30000, "intent": "info",   "lang": "fr"},
        {"keyword": "lion de la teranga",    "volume_est": 25000, "intent": "info",   "lang": "fr"},
        {"keyword": "journal senegal",       "volume_est": 20000, "intent": "info",   "lang": "fr"},
        {"keyword": "politique senegal",     "volume_est": 20000, "intent": "info",   "lang": "fr"},
        {"keyword": "elections senegal",     "volume_est": 18000, "intent": "info",   "lang": "fr"},
        {"keyword": "ligue 1 senegal",       "volume_est": 15000, "intent": "info",   "lang": "fr"},
        {"keyword": "senegal today",         "volume_est": 12000, "intent": "info",   "lang": "fr"},
        {"keyword": "xibaaru",               "volume_est": 12000, "intent": "nav",    "lang": "fr"},
        {"keyword": "dakarmatin",            "volume_est": 10000, "intent": "nav",    "lang": "fr"},
    ],
    "ecommerce": [
        {"keyword": "jumia senegal",           "volume_est": 35000, "intent": "nav",    "lang": "fr"},
        {"keyword": "expat dakar",             "volume_est": 25000, "intent": "nav",    "lang": "fr"},
        {"keyword": "appartement louer dakar", "volume_est": 22000, "intent": "transac","lang": "fr"},
        {"keyword": "voiture occasion dakar",  "volume_est": 20000, "intent": "transac","lang": "fr"},
        {"keyword": "iphone senegal",          "volume_est": 15000, "intent": "transac","lang": "fr"},
        {"keyword": "acheter en ligne senegal","volume_est": 15000, "intent": "transac","lang": "fr"},
        {"keyword": "smartphone senegal prix", "volume_est": 18000, "intent": "transac","lang": "fr"},
        {"keyword": "location maison dakar",   "volume_est": 18000, "intent": "transac","lang": "fr"},
        {"keyword": "coinafrique senegal",     "volume_est": 12000, "intent": "nav",    "lang": "fr"},
        {"keyword": "terrain vendre dakar",    "volume_est": 12000, "intent": "transac","lang": "fr"},
    ],
    "telephonie": [
        {"keyword": "orange senegal",          "volume_est": 40000, "intent": "nav",    "lang": "fr"},
        {"keyword": "wave senegal",            "volume_est": 35000, "intent": "nav",    "lang": "fr"},
        {"keyword": "free senegal",            "volume_est": 25000, "intent": "nav",    "lang": "fr"},
        {"keyword": "orange money senegal",    "volume_est": 25000, "intent": "nav",    "lang": "fr"},
        {"keyword": "recharge orange senegal", "volume_est": 20000, "intent": "transac","lang": "fr"},
        {"keyword": "forfait internet senegal","volume_est": 15000, "intent": "transac","lang": "fr"},
        {"keyword": "sonatel",                 "volume_est": 15000, "intent": "nav",    "lang": "fr"},
        {"keyword": "5g senegal",              "volume_est": 10000, "intent": "info",   "lang": "fr"},
    ],
    "banque_finance": [
        {"keyword": "transfert argent senegal","volume_est": 20000, "intent": "transac","lang": "fr"},
        {"keyword": "taux change fcfa euro",   "volume_est": 15000, "intent": "info",   "lang": "fr"},
        {"keyword": "bitcoin senegal",         "volume_est": 12000, "intent": "info",   "lang": "fr"},
        {"keyword": "banque senegal",          "volume_est": 12000, "intent": "info",   "lang": "fr"},
        {"keyword": "western union dakar",     "volume_est":  8000, "intent": "transac","lang": "fr"},
        {"keyword": "cbao senegal",            "volume_est":  8000, "intent": "nav",    "lang": "fr"},
    ],
    "emploi": [
        {"keyword": "emploi senegal",          "volume_est": 25000, "intent": "info",   "lang": "fr"},
        {"keyword": "offre emploi dakar",      "volume_est": 20000, "intent": "info",   "lang": "fr"},
        {"keyword": "concours senegal 2025",   "volume_est": 20000, "intent": "info",   "lang": "fr"},
        {"keyword": "recrutement senegal",     "volume_est": 15000, "intent": "info",   "lang": "fr"},
        {"keyword": "senjob",                  "volume_est": 10000, "intent": "nav",    "lang": "fr"},
        {"keyword": "bourse etude senegal",    "volume_est": 10000, "intent": "info",   "lang": "fr"},
    ],
}

ALL_KEYWORDS = []
for cat, kws in KEYWORDS.items():
    for kw in kws:
        ALL_KEYWORDS.append({**kw, "category": cat})
ALL_KEYWORDS.sort(key=lambda x: x["volume_est"], reverse=True)
TOTAL_KEYWORDS = len(ALL_KEYWORDS)
TOTAL_VOLUME   = sum(k["volume_est"] for k in ALL_KEYWORDS)
''')
print("\n  OK phase2/keywords/keywords_db.py")

# ── 5. serp_scraper.py ────────────────────────────────────────
serp_path = os.path.join(BASE, "phase2", "serp_scraper", "serp_scraper.py")
with open(serp_path, "w", encoding="utf-8") as f:
    f.write(r'''
import requests
from bs4 import BeautifulSoup
import sqlite3, time, random, os, sys, json
from datetime import datetime
from urllib.parse import quote_plus, urlparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from phase2.keywords.keywords_db import ALL_KEYWORDS

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "phase2.db")

# ── CONFIGURATION API GOOGLE (optionnel) ─────────────────────
# Remplis ces deux champs si tu as une clé Custom Search API
# Sinon laisser vide -> DuckDuckGo sera utilisé automatiquement
GOOGLE_API_KEY = ""   # Ex: "AIzaSyXXXXXXXXXXXXXXXX"
GOOGLE_CX_ID   = ""   # Ex: "017576662512468239146:xxxxxx"

TARGET_DOMAINS = [
    "seneweb.com","dakaractu.com","senenews.com","senego.com",
    "leral.net","rewmi.com","pressafrik.com","xibaaru.com","dakarmatin.com",
    "lobservateur.sn","actusen.sn","jumia.sn","expat-dakar.com",
    "sn.coinafrique.com","orange.sn","free.sn","wave.com","orangemoney.sn",
    "cbao.sn","ecobank.com","senjob.com","emploi.sn",
]
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
]


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS serp_positions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT, keyword_category TEXT, keyword_volume INTEGER,
        domain TEXT, position INTEGER, url TEXT, title TEXT,
        snippet TEXT, source TEXT,
        scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    c.execute("""CREATE TABLE IF NOT EXISTS traffic_estimates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        domain TEXT, period TEXT, estimated_visits INTEGER,
        keywords_ranked INTEGER, keywords_top3 INTEGER, keywords_top10 INTEGER,
        top_keywords TEXT, calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    conn.commit(); conn.close()


def get_headers():
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
    }


def search_google_api(keyword):
    """Niveau 1 : Google Custom Search API officielle."""
    if not GOOGLE_API_KEY or not GOOGLE_CX_ID:
        return None
    results = []
    for start in [1, 11]:
        try:
            r = requests.get("https://www.googleapis.com/customsearch/v1",
                params={"key": GOOGLE_API_KEY, "cx": GOOGLE_CX_ID,
                        "q": keyword, "num": 10, "start": start, "gl": "sn", "hl": "fr"},
                timeout=15)
            if r.status_code != 200: break
            for i, item in enumerate(r.json().get("items", [])):
                pos = (start - 1) + i + 1
                link = item.get("link", "")
                domain = urlparse(link).netloc.replace("www.", "")
                results.append({"position": pos, "url": link, "domain": domain,
                                "title": item.get("title",""), "snippet": item.get("snippet","")[:200]})
            time.sleep(1)
        except Exception as e:
            print(f"      Google API erreur: {str(e)[:60]}"); break
    return results if results else None


def search_duckduckgo(keyword):
    """Niveau 2 : DuckDuckGo HTML — pas de captcha, pas de clé."""
    url = f"https://html.duckduckgo.com/html/?q={quote_plus(keyword)}&kl=sn-fr&kp=-1"
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, "html.parser")
        results, pos = [], 1
        for block in soup.select(".result"):
            a = block.select_one("a.result__a")
            if not a: continue
            href = a.get("href","")
            if not href.startswith("http"): continue
            domain = urlparse(href).netloc.replace("www.","")
            if not domain or "duckduckgo" in domain: continue
            title = a.get_text(strip=True)
            snip = block.select_one(".result__snippet")
            snippet = snip.get_text(strip=True)[:200] if snip else ""
            results.append({"position":pos,"url":href,"domain":domain,
                            "title":title,"snippet":snippet})
            pos += 1
            if pos > 20: break
        return results if results else None
    except Exception as e:
        print(f"      DuckDuckGo erreur: {str(e)[:60]}"); return None


def search_bing(keyword):
    """Niveau 3 : Bing — fallback final."""
    url = f"https://www.bing.com/search?q={quote_plus(keyword)}&cc=SN&setlang=fr&count=20"
    try:
        r = requests.get(url, headers=get_headers(), timeout=15)
        if r.status_code != 200: return None
        soup = BeautifulSoup(r.text, "html.parser")
        results, pos = [], 1
        for block in soup.select("li.b_algo"):
            a = block.select_one("h2 a")
            if not a: continue
            href = a.get("href","")
            if not href.startswith("http"): continue
            domain = urlparse(href).netloc.replace("www.","")
            snip = block.select_one(".b_caption p")
            snippet = snip.get_text(strip=True)[:200] if snip else ""
            results.append({"position":pos,"url":href,"domain":domain,
                            "title":a.get_text(strip=True),"snippet":snippet})
            pos += 1
            if pos > 20: break
        return results if results else None
    except Exception as e:
        print(f"      Bing erreur: {str(e)[:60]}"); return None


def search_keyword(keyword):
    """Cascade : Google API → DuckDuckGo → Bing."""
    if GOOGLE_API_KEY and GOOGLE_CX_ID:
        results = search_google_api(keyword)
        if results: return results, "google_api"
        print("      Google API echouee -> DuckDuckGo...")
    results = search_duckduckgo(keyword)
    if results: return results, "duckduckgo"
    print("      DuckDuckGo echoue -> Bing...")
    results = search_bing(keyword)
    if results: return results, "bing"
    return [], "none"


def find_target_positions(results):
    found = {}
    for r in results:
        for target in TARGET_DOMAINS:
            if target in r["domain"] or r["domain"] in target:
                if target not in found:
                    found[target] = {"position":r["position"],"url":r["url"],
                                    "title":r["title"],"snippet":r["snippet"]}
    return found


def save_results(kw_data, positions, source):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    for domain in TARGET_DOMAINS:
        if domain in positions:
            d = positions[domain]
            c.execute("INSERT INTO serp_positions (keyword,keyword_category,keyword_volume,domain,position,url,title,snippet,source) VALUES (?,?,?,?,?,?,?,?,?)",
                (kw_data["keyword"],kw_data["category"],kw_data["volume_est"],
                 domain,d["position"],d["url"],d["title"],d["snippet"],source))
        else:
            c.execute("INSERT INTO serp_positions (keyword,keyword_category,keyword_volume,domain,position,source) VALUES (?,?,?,?,NULL,?)",
                (kw_data["keyword"],kw_data["category"],kw_data["volume_est"],domain,source))
    conn.commit(); conn.close()


def run_serp_scraping(max_keywords=20, category=None, skip_existing=True):
    init_db()
    keywords = [k for k in ALL_KEYWORDS if not category or k["category"]==category]
    if skip_existing:
        conn = sqlite3.connect(DB_PATH)
        done = {r[0] for r in conn.cursor().execute(
            "SELECT DISTINCT keyword FROM serp_positions WHERE date(scraped_at)=date('now')").fetchall()}
        conn.close()
        keywords = [k for k in keywords if k["keyword"] not in done]
    keywords = keywords[:max_keywords]

    source_label = "Google API" if (GOOGLE_API_KEY and GOOGLE_CX_ID) else "DuckDuckGo + Bing"
    print(f"\n{'='*55}")
    print(f"  SCRAPING SERP — {len(keywords)} mots-cles")
    print(f"  Source : {source_label}")
    print(f"{'='*55}\n")

    total_found = 0
    for i, kw_data in enumerate(keywords, 1):
        keyword = kw_data["keyword"]
        print(f"[{i:3}/{len(keywords)}] '{keyword}' (vol: {kw_data['volume_est']:,})")
        results, source = search_keyword(keyword)
        if not results:
            print("       Toutes les sources ont echoue"); continue
        print(f"       Source: {source} -> {len(results)} resultats")
        positions = find_target_positions(results)
        save_results(kw_data, positions, source)
        if positions:
            total_found += len(positions)
            for domain, data in sorted(positions.items(), key=lambda x: x[1]["position"]):
                print(f"       OK  #{data['position']:2} — {domain}")
        else:
            print("       — Aucun site senegalais dans le top 20")
        if i < len(keywords):
            delay = random.uniform(1,2) if source=="google_api" else random.uniform(5,12)
            print(f"       Pause {delay:.1f}s...")
            time.sleep(delay)

    print(f"\n  Termine : {len(keywords)} mots-cles, {total_found} positions trouvees")
    return {"scraped": len(keywords), "found": total_found}


def show_serp_report():
    if not os.path.exists(DB_PATH):
        print("Aucune donnee SERP."); return
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    print(f"\n{'='*55}\n  RAPPORT SERP\n{'='*55}")
    c.execute("SELECT COUNT(DISTINCT keyword) FROM serp_positions")
    print(f"  Mots-cles analyses : {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM serp_positions WHERE position IS NOT NULL")
    print(f"  Positions trouvees : {c.fetchone()[0]}")
    c.execute("""SELECT domain,
                   SUM(CASE WHEN position IS NOT NULL THEN 1 ELSE 0 END) as ranked,
                   SUM(CASE WHEN position<=3 THEN 1 ELSE 0 END) as top3,
                   SUM(CASE WHEN position<=10 THEN 1 ELSE 0 END) as top10,
                   ROUND(AVG(CASE WHEN position IS NOT NULL THEN position END),1)
               FROM serp_positions GROUP BY domain HAVING ranked>0 ORDER BY top10 DESC""")
    rows = c.fetchall()
    if rows:
        print(f"\n  {'Domaine':<28} {'Rankés':<8} {'Top3':<6} {'Top10':<7} Pos.moy")
        print("  "+"-"*55)
        for d, ranked, t3, t10, avg in rows:
            print(f"  {d:<28} {ranked:<8} {t3:<6} {t10:<7} {avg or '-'}")
    conn.close()
    print(f"{'='*55}\n")
''')
print("  OK phase2/serp_scraper/serp_scraper.py")

# ── 6. traffic_estimator.py ───────────────────────────────────
traffic_path = os.path.join(BASE, "phase2", "traffic_model", "traffic_estimator.py")
with open(traffic_path, "w", encoding="utf-8") as f:
    f.write(r'''
import sqlite3, json, os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "phase2.db")
CTR_MODEL = {1:0.285,2:0.157,3:0.110,4:0.080,5:0.072,6:0.051,7:0.040,
             8:0.032,9:0.028,10:0.025,11:0.010,12:0.009,13:0.008,
             14:0.007,15:0.006,16:0.005,17:0.004,18:0.004,19:0.003,20:0.003}

def get_ctr(pos):
    if not pos or pos < 1: return 0.0
    return CTR_MODEL.get(pos, 0.001 if pos > 30 else 0.002)

def calculate_traffic_for_domain(domain, period=None):
    if not os.path.exists(DB_PATH): return {"error":"Base introuvable"}
    conn = sqlite3.connect(DB_PATH)
    rows = conn.cursor().execute(
        "SELECT keyword,keyword_volume,position FROM serp_positions WHERE domain=? AND position IS NOT NULL ORDER BY position",
        (domain,)).fetchall()
    conn.close()
    if not rows:
        return {"domain":domain,"estimated_visits":0,"keywords_ranked":0,
                "keywords_top3":0,"keywords_top10":0,"top_keywords":[],
                "period":period or datetime.now().strftime("%Y-%m")}
    total, top3, top10, details = 0, 0, 0, []
    for keyword, volume, position in rows:
        ctr = get_ctr(position)
        contrib = int((volume or 0) * ctr)
        total += contrib
        if position <= 3: top3 += 1
        if position <= 10: top10 += 1
        details.append({"keyword":keyword,"position":position,"volume":volume,
                        "ctr":round(ctr*100,1),"traffic":contrib})
    details.sort(key=lambda x: x["traffic"], reverse=True)
    return {"domain":domain,"estimated_visits":total,"keywords_ranked":len(rows),
            "keywords_top3":top3,"keywords_top10":top10,"top_keywords":details[:15],
            "period":period or datetime.now().strftime("%Y-%m")}

def calculate_all_traffic(period=None):
    if not os.path.exists(DB_PATH): print("Base introuvable."); return []
    conn = sqlite3.connect(DB_PATH)
    domains = [r[0] for r in conn.cursor().execute(
        "SELECT DISTINCT domain FROM serp_positions WHERE position IS NOT NULL").fetchall()]
    conn.close()
    if not domains: print("Aucune donnee SERP. Lance le scraper d abord."); return []
    period = period or datetime.now().strftime("%Y-%m")
    results = []
    print(f"\n{'='*55}\n  CALCUL TRAFIC — Modele CTR Sistrix\n{'='*55}\n")
    for domain in domains:
        data = calculate_traffic_for_domain(domain, period)
        conn = sqlite3.connect(DB_PATH)
        conn.cursor().execute(
            "INSERT OR REPLACE INTO traffic_estimates (domain,period,estimated_visits,keywords_ranked,keywords_top3,keywords_top10,top_keywords) VALUES (?,?,?,?,?,?,?)",
            (data["domain"],data["period"],data["estimated_visits"],data["keywords_ranked"],
             data["keywords_top3"],data["keywords_top10"],json.dumps(data["top_keywords"],ensure_ascii=False)))
        conn.commit(); conn.close()
        results.append(data)
        print(f"  {domain:<30} {data['estimated_visits']:>8,} visites/mois ({data['keywords_top10']} top10)")
    results.sort(key=lambda x: x["estimated_visits"], reverse=True)
    print(f"\n  CLASSEMENT FINAL :")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r['domain']:<30} {r['estimated_visits']:>10,} visites/mois")
    print(f"\n  TOTAL : {sum(r['estimated_visits'] for r in results):,} visites/mois")
    return results

def get_traffic_report():
    if not os.path.exists(DB_PATH): return []
    conn = sqlite3.connect(DB_PATH)
    rows = conn.cursor().execute("""
        SELECT domain,period,estimated_visits,keywords_ranked,keywords_top3,keywords_top10,top_keywords
        FROM traffic_estimates te
        WHERE calculated_at=(SELECT MAX(calculated_at) FROM traffic_estimates WHERE domain=te.domain)
        ORDER BY estimated_visits DESC""").fetchall()
    conn.close()
    return [{"domain":r[0],"period":r[1],"estimated_visits":r[2],"keywords_ranked":r[3],
             "keywords_top3":r[4],"keywords_top10":r[5],
             "top_keywords":json.loads(r[6]) if r[6] else []} for r in rows]
''')
print("  OK phase2/traffic_model/traffic_estimator.py")

# ── 7. run_phase2.py ──────────────────────────────────────────
run_path = os.path.join(BASE, "run_phase2.py")
with open(run_path, "w", encoding="utf-8") as f:
    f.write(r'''"""
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
''')
print("  OK run_phase2.py")

# ── 8. Vérification finale ────────────────────────────────────
print(f"\n{'='*60}")
print("  VERIFICATION FINALE :")
all_ok = True
for item in expected:
    full = os.path.join(BASE, item.replace("/", os.sep))
    ok = os.path.exists(full)
    if not ok:
        all_ok = False
    print(f"  {'OK' if ok else 'ERREUR':<10} {item}")

print(f"\n{'='*60}")
if all_ok:
    print("  TOUT EST OK ! Lance maintenant :")
    print()
    print("  python run_phase2.py keywords")
    print("  python run_phase2.py scrape --max 5")
else:
    print("  Certains fichiers manquent encore — relance ce script")
print(f"{'='*60}\n")
