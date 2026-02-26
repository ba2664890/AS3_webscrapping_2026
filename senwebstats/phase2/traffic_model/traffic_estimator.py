
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
