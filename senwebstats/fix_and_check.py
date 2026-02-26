"""
Script de diagnostic et correction pour SenWebStats.
Place ce fichier dans le dossier senwebstats/ et lance :
    python fix_and_check.py
"""

import sqlite3
import os
import sys

# S'assurer qu'on est dans le bon dossier
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

DB_PATH = os.path.join(script_dir, "data", "senwebstats.db")

print("=" * 60)
print("DIAGNOSTIC SENWEBSTATS")
print("=" * 60)

# ── Étape 1 : Vérifier la DB ─────────────────────────────────
print(f"\n📂 Base de données : {DB_PATH}")
print(f"   Existe : {'OUI' if os.path.exists(DB_PATH) else 'NON'}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"   Tables : {tables}")

cursor.execute("SELECT COUNT(*) FROM sites")
nb_sites = cursor.fetchone()[0]
print(f"   Sites en base : {nb_sites}")

cursor.execute("SELECT COUNT(*) FROM site_metadata")
nb_meta = cursor.fetchone()[0]
print(f"   Métadonnées : {nb_meta}")

conn.close()

# ── Étape 2 : Réinsérer les sites ───────────────────────────
print("\n" + "=" * 60)
print("CORRECTION : Insertion des sites")
print("=" * 60)

SITES = {
    "presse": [
        {"name": "Seneweb",       "url": "https://www.seneweb.com",     "domain": "seneweb.com"},
        {"name": "Dakaractu",     "url": "https://www.dakaractu.com",   "domain": "dakaractu.com"},
        {"name": "Senenews",      "url": "https://www.senenews.com",    "domain": "senenews.com"},
        {"name": "Rewmi",         "url": "https://www.rewmi.com",       "domain": "rewmi.com"},
        {"name": "Leral",         "url": "https://www.leral.net",       "domain": "leral.net"},
        {"name": "Pressafrik",    "url": "https://www.pressafrik.com",  "domain": "pressafrik.com"},
        {"name": "Actusen",       "url": "https://actusen.sn",          "domain": "actusen.sn"},
        {"name": "Senego",        "url": "https://senego.com",          "domain": "senego.com"},
        {"name": "Sud Quotidien", "url": "https://www.sudquotidien.sn", "domain": "sudquotidien.sn"},
        {"name": "Xibaaru",       "url": "https://xibaaru.com",         "domain": "xibaaru.com"},
        {"name": "Dakarmatin",    "url": "https://www.dakarmatin.com",  "domain": "dakarmatin.com"},
        {"name": "L'Observateur", "url": "https://www.lobservateur.sn", "domain": "lobservateur.sn"},
    ],
    "ecommerce": [
        {"name": "Jumia Sénégal", "url": "https://www.jumia.sn",        "domain": "jumia.sn"},
        {"name": "Expat Dakar",   "url": "https://www.expat-dakar.com", "domain": "expat-dakar.com"},
        {"name": "CoinAfrique",   "url": "https://sn.coinafrique.com",  "domain": "sn.coinafrique.com"},
        {"name": "Afrikrea",      "url": "https://www.afrikrea.com",    "domain": "afrikrea.com"},
        {"name": "Dakar Deal",    "url": "https://www.dakardeal.com",   "domain": "dakardeal.com"},
    ],
    "telephonie": [
        {"name": "Orange Sénégal","url": "https://www.orange.sn",           "domain": "orange.sn"},
        {"name": "Free Sénégal",  "url": "https://www.free.sn",             "domain": "free.sn"},
        {"name": "Expresso",      "url": "https://www.expressotelecom.sn",  "domain": "expressotelecom.sn"},
        {"name": "Sonatel",       "url": "https://www.sonatel.com",         "domain": "sonatel.com"},
    ],
    "banque_finance": [
        {"name": "CBAO",         "url": "https://www.cbao.sn",         "domain": "cbao.sn"},
        {"name": "Ecobank",      "url": "https://ecobank.com/sn",      "domain": "ecobank.com"},
        {"name": "Wave",         "url": "https://www.wave.com/fr/sen", "domain": "wave.com"},
        {"name": "Orange Money", "url": "https://www.orangemoney.sn",  "domain": "orangemoney.sn"},
    ],
    "emploi": [
        {"name": "Senjob",    "url": "https://www.senjob.com",  "domain": "senjob.com"},
        {"name": "Emploi.sn", "url": "https://www.emploi.sn",   "domain": "emploi.sn"},
        {"name": "Rekrute",   "url": "https://www.rekrute.com", "domain": "rekrute.com"},
    ],
}

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

inserted = 0
for category, sites in SITES.items():
    for site in sites:
        cursor.execute(
            "INSERT OR IGNORE INTO sites (domain, name, url, category) VALUES (?, ?, ?, ?)",
            (site["domain"], site["name"], site["url"], category)
        )
        if cursor.rowcount > 0:
            inserted += 1

conn.commit()

cursor.execute("SELECT COUNT(*) FROM sites")
total = cursor.fetchone()[0]
print(f"✅ {inserted} nouveaux sites insérés. Total en base : {total}")

# ── Étape 3 : Re-scraper et sauvegarder avec les bons IDs ────
print("\n" + "=" * 60)
print("RÉCUPÉRATION : Association données → sites")
print("=" * 60)

# Les URLs qu'on a déjà crawlées avec succès
resultats_connus = {
    "dakaractu.com": {"title": "DAKARACTU.COM", "status_code": 200, "response_time_ms": 1130.06,
                      "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                      "internal_links_count": 577, "external_links_count": 7},
    "leral.net":     {"title": "Leral.net - Sénégal", "status_code": 200, "response_time_ms": 895.03,
                      "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                      "internal_links_count": 172, "external_links_count": 0},
    "pressafrik.com":{"title": "PRESSAFRIK.COM, Premier média certifié JTI au Sénégal",
                      "status_code": 200, "response_time_ms": 2027.18,
                      "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                      "internal_links_count": 273, "external_links_count": 6},
    "sudquotidien.sn":{"title": "Accueil - Sud Quotidien", "status_code": 200, "response_time_ms": 813.72,
                       "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                       "internal_links_count": 508, "external_links_count": 15},
    "xibaaru.com":   {"title": "Accueil - Xibaaru", "status_code": 200, "response_time_ms": 3077.47,
                      "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                      "internal_links_count": 0, "external_links_count": 253},
    "dakarmatin.com":{"title": None, "status_code": 200, "response_time_ms": 1671.15,
                      "has_ssl": 1, "has_sitemap": 1, "has_robots_txt": 0,
                      "internal_links_count": 0, "external_links_count": 0},
    "seneweb.com":   {"title": None, "status_code": 200, "response_time_ms": 634.35,
                      "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                      "internal_links_count": 0, "external_links_count": 0},
    "senenews.com":  {"title": None, "status_code": 200, "response_time_ms": 596.33,
                      "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                      "internal_links_count": 0, "external_links_count": 0},
    "rewmi.com":     {"title": None, "status_code": 200, "response_time_ms": 2432.65,
                      "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                      "internal_links_count": 0, "external_links_count": 0},
    "actusen.sn":    {"title": None, "status_code": 200, "response_time_ms": 3026.46,
                      "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                      "internal_links_count": 0, "external_links_count": 0},
    "senego.com":    {"title": None, "status_code": 200, "response_time_ms": 738.46,
                      "has_ssl": 1, "has_sitemap": 0, "has_robots_txt": 0,
                      "internal_links_count": 0, "external_links_count": 0},
}

saved = 0
for domain, data in resultats_connus.items():
    cursor.execute("SELECT id FROM sites WHERE domain = ?", (domain,))
    row = cursor.fetchone()
    if not row:
        print(f"  ⚠️  Site non trouvé en base : {domain}")
        continue
    site_id = row[0]

    # Vérifier si déjà une entrée metadata pour ce site
    cursor.execute("SELECT COUNT(*) FROM site_metadata WHERE site_id = ?", (site_id,))
    if cursor.fetchone()[0] > 0:
        print(f"  ℹ️  Déjà des données pour {domain}, ignoré")
        continue

    cursor.execute("""
        INSERT INTO site_metadata (
            site_id, title, status_code, response_time_ms,
            has_ssl, has_sitemap, has_robots_txt,
            internal_links_count, external_links_count,
            h1_count, h2_count, images_count, images_with_alt, word_count
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, 0, 0, 0, 0)
    """, (
        site_id,
        data.get("title"),
        data.get("status_code"),
        data.get("response_time_ms"),
        data.get("has_ssl", 1),
        data.get("has_sitemap", 0),
        data.get("has_robots_txt", 0),
        data.get("internal_links_count", 0),
        data.get("external_links_count", 0),
    ))
    saved += 1
    print(f"  ✅ {domain}")

conn.commit()

# ── Étape 4 : Rapport final ──────────────────────────────────
print("\n" + "=" * 60)
print("ÉTAT FINAL DE LA BASE")
print("=" * 60)

cursor.execute("SELECT category, COUNT(*) FROM sites GROUP BY category")
print("\nSites par catégorie :")
for cat, count in cursor.fetchall():
    print(f"  {cat:<20} {count} sites")

cursor.execute("SELECT COUNT(*) FROM site_metadata")
print(f"\nMétadonnées enregistrées : {cursor.fetchone()[0]}")

cursor.execute("""
    SELECT s.name, sm.status_code, sm.response_time_ms, sm.has_ssl, sm.has_sitemap,
           sm.internal_links_count, sm.external_links_count
    FROM site_metadata sm
    JOIN sites s ON s.id = sm.site_id
    ORDER BY s.name
""")
rows = cursor.fetchall()
if rows:
    print(f"\n{'Site':<25} {'Status':<8} {'Temps(ms)':<12} {'SSL':<5} {'Sitemap':<9} {'Liens int.':<12} {'Liens ext.'}")
    print("-" * 85)
    for name, status, rt, ssl, sitemap, lint, lext in rows:
        print(f"{name:<25} {str(status):<8} {str(round(rt or 0)):<12} "
              f"{'Oui' if ssl else 'Non':<5} {'Oui' if sitemap else 'Non':<9} "
              f"{str(lint):<12} {str(lext)}")

conn.close()

print("\n" + "=" * 60)
print("✅ CORRECTION TERMINÉE !")
print("\nRelance maintenant Streamlit :")
print("   streamlit run app/streamlit_app.py")
print("=" * 60)
