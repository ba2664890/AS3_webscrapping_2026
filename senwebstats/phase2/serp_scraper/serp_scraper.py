
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
