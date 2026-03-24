"""
SenWebStats — Test de connexion aux APIs
=========================================
Lance depuis senwebstats/ :
    python test_apis.py

Ce script vérifie :
  1. Chargement du fichier .env
  2. Connexion DataForSEO (si configuré)
  3. Connexion Semrush (si configuré)
  4. Fallback proxy CTR (toujours disponible)
"""

import sys
import os

sys.stdout.reconfigure(encoding="utf-8")

# Charger .env si python-dotenv est disponible
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("[.env] Chargé avec succès")
except ImportError:
    print("[.env] python-dotenv non installé — variables lues depuis l'environnement système")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models.ctr_model import (
    DataForSEOClient,
    SemrushClient,
    SerperDevClient,
    AWR_2023,
    score_to_position,
    ctr_at_position,
    compute_ctr_scores,
    CATEGORY_BASE,
)

SEP = "─" * 60

# ─────────────────────────────────────────────────────────────
# TEST 0 : SERPER.DEV  (priorité 1 — accepte Gmail)
# ─────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  TEST 0 — Serper.dev (Google Search API — RECOMMANDÉ)")
print(SEP)

serper = SerperDevClient()

if not serper.is_configured():
    print("  ⚠  Non configuré.")
    print("     → Inscription GRATUITE avec Gmail : https://serper.dev")
    print("     → Cliquer 'Sign up with Google' → copier la clé API")
    print("     → Ajouter dans .env : SERPER_API_KEY=ta_cle")
    print("     → 2 500 recherches gratuites/mois (sans carte bancaire)")
else:
    print(f"  Clé API  : {serper.api_key[:8]}...")
    print()
    print("  Test — position de senenews.com sur 'actualite senegal' (gl=sn) ...")
    try:
        pos = serper.get_domain_position("senenews.com", "actualite senegal", country="sn")
        print(f"  ✓ Connexion OK")
        print(f"    Position de senenews.com : #{pos}")
        print()
        print("  Test complet — estimation trafic presse (5 mots-clés) ...")
        result = serper.estimate_traffic_from_serp("senenews.com", "presse", max_keywords=5)
        if "error" in result:
            print(f"  ✗ Erreur : {result['error']}")
        else:
            print(f"  ✓ Trafic estimé        : {result.get('trafic_ctr', 0):,} visites/mois")
            print(f"    Position moyenne      : #{result.get('position_moyenne', '?')}")
            print(f"    Mots-clés analysés    : {result.get('keywords_checked', 0)}")
            print(f"    Source                : {result.get('source')}")
    except Exception as e:
        print(f"  ✗ Exception : {e}")

# ─────────────────────────────────────────────────────────────
# TEST 1 : DATAFORSEO
# ─────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  TEST 1 — DataForSEO")
print(SEP)

dfs = DataForSEOClient()

if not dfs.is_configured():
    print("  ⚠  Non configuré.")
    print("     → Remplis DATAFORSEO_LOGIN et DATAFORSEO_PASSWORD dans .env")
    print("     → Inscription gratuite : https://app.dataforseo.com/register")
    print("     → Crédit offert : $1 sans carte bancaire")
else:
    print(f"  Login    : {dfs.login}")
    print(f"  Password : {'*' * len(dfs.password)}")
    print()
    print("  Test avec senenews.com ...")
    try:
        result = dfs.get_domain_metrics("senenews.com")
        if "error" in result:
            print(f"  ✗ Erreur : {result['error']}")
            print("    → Vérifie tes identifiants sur https://app.dataforseo.com/")
        else:
            print(f"  ✓ Connexion OK")
            print(f"    Trafic organique estimé : {result.get('organic_traffic', 0):,}")
            print(f"    Mots-clés classés       : {result.get('organic_count', 0):,}")
            print(f"    Source                  : {result.get('source')}")
    except Exception as e:
        print(f"  ✗ Exception : {e}")

# ─────────────────────────────────────────────────────────────
# TEST 2 : SEMRUSH
# ─────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  TEST 2 — Semrush")
print(SEP)

sem = SemrushClient()

if not sem.is_configured():
    print("  ⚠  Non configuré.")
    print("     → Remplis SEMRUSH_API_KEY dans .env")
    print("     → Essai gratuit 7 jours : https://www.semrush.com/")
    print("     → Clé API disponible dans : Mon compte > Profil > API")
else:
    print(f"  Clé API  : {sem.api_key[:8]}...")
    print()
    print("  Test avec senenews.com ...")
    try:
        result = sem.get_domain_traffic("senenews.com", database="ww")
        if "error" in result:
            print(f"  ✗ Erreur : {result['error']}")
            print("    → Vérifie ta clé sur https://www.semrush.com/api/")
        else:
            print(f"  ✓ Connexion OK")
            print(f"    Mots-clés organiques : {result.get('organic_keywords', 0):,}")
            print(f"    Trafic organique     : {result.get('organic_traffic', 0):,}")
    except Exception as e:
        print(f"  ✗ Exception : {e}")

# ─────────────────────────────────────────────────────────────
# TEST 3 : PROXY CTR (toujours disponible)
# ─────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  TEST 3 — Proxy CTR (AWR 2023) — toujours actif")
print(SEP)

import sqlite3, pandas as pd

db_path = os.path.join(os.path.dirname(__file__), "data", "senwebstats.db")
if not os.path.exists(db_path):
    print("  ✗ Base senwebstats.db introuvable")
else:
    conn = sqlite3.connect(db_path)
    df = pd.read_sql("SELECT id, name, domain, category FROM sites ORDER BY category, name", conn)

    meta = pd.read_sql("""
        SELECT site_id, response_time_ms, word_count, has_ssl, has_sitemap
        FROM site_metadata sm
        WHERE crawled_at=(SELECT MAX(crawled_at) FROM site_metadata WHERE site_id=sm.site_id)
    """, conn)
    perf = pd.read_sql("""
        SELECT site_id, performance_score, seo_score, accessibility_score
        FROM site_performance sp
        WHERE measured_at=(SELECT MAX(measured_at) FROM site_performance WHERE site_id=sp.site_id)
    """, conn)
    bl = pd.read_sql("""
        SELECT site_id, total_backlinks, referring_domains
        FROM site_backlinks sb
        WHERE collected_at=(SELECT MAX(collected_at) FROM site_backlinks WHERE site_id=sb.site_id)
    """, conn)
    conn.close()

    for other, key in [(meta, "site_id"), (perf, "site_id"), (bl, "site_id")]:
        if not other.empty:
            df = df.merge(other, left_on="id", right_on=key, how="left")
            df = df.drop(columns=["site_id"], errors="ignore")

    fills = {
        "total_backlinks": 0, "referring_domains": 0, "seo_score": 50,
        "performance_score": 50, "accessibility_score": 50,
        "response_time_ms": 3000, "has_ssl": 0, "has_sitemap": 0, "word_count": 0,
    }
    for col, val in fills.items():
        if col not in df.columns:
            df[col] = val
        df[col] = df[col].fillna(val)

    # Calcul rapide scores
    def normalize(s):
        mn, mx = s.min(), s.max()
        if mx == mn: return pd.Series([50.0]*len(s), index=s.index)
        return (s - mn) / (mx - mn) * 100

    df["score_autorite"]  = (normalize(df["total_backlinks"])*0.6 + normalize(df["referring_domains"])*0.4).round(1)
    df["score_qualite"]   = (df["seo_score"]*0.4 + df["performance_score"]*0.35 + df["accessibility_score"]*0.25).round(1)
    df["score_technique"] = (normalize(df["response_time_ms"][::-1].values)*0.4 + df["has_ssl"]*20 + df["has_sitemap"]*15 + normalize(df["word_count"])*0.25).round(1)
    df["score_global"]    = (df["score_autorite"]*0.45 + df["score_qualite"]*0.35 + df["score_technique"]*0.2).round(1)

    df_ctr = compute_ctr_scores(df)

    print(f"  ✓ Proxy CTR calculé pour {len(df_ctr)} sites\n")
    print(f"  {'Site':<22} {'Score':>6}  {'Position':>9}  {'Trafic CTR/mois':>16}")
    print("  " + "─"*58)
    for _, row in df_ctr.sort_values("trafic_ctr", ascending=False).head(10).iterrows():
        print(f"  {row['name']:<22} {row['score_global']:>6.1f}  #{int(row['position_estimee']):>8}  {int(row['trafic_ctr']):>16,}")

    total = df_ctr["trafic_ctr"].sum()
    print(f"\n  Total trafic CTR estimé : {int(total):,} visites/mois")

# ─────────────────────────────────────────────────────────────
# RÉSUMÉ
# ─────────────────────────────────────────────────────────────
print(f"\n{SEP}")
print("  RÉSUMÉ")
print(SEP)
print(f"  Serper.dev   : {'OK' if serper.is_configured() else 'Non configuré  <- RECOMMANDÉ (Gmail OK)'}")
print(f"  DataForSEO   : {'OK' if dfs.is_configured() else 'Non configuré'}")
print(f"  Semrush      : {'OK' if sem.is_configured() else 'Non configuré'}")
print(f"  Proxy CTR    : Toujours actif (AWR 2023)")
print()
print("  Pour configurer Serper.dev (option la plus simple) :")
print("  1. Aller sur https://serper.dev → 'Sign up with Google'")
print("  2. Copier : cp .env.example .env")
print("  3. Coller la cle : SERPER_API_KEY=ta_cle dans .env")
print("  4. Relancer : python test_apis.py")
print(f"{SEP}\n")
