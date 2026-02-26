"""
SenWebStats — Modèle de scoring sans SERP
==========================================
Calcule un score d'autorité et estime le trafic
à partir des données déjà collectées :
  - Backlinks CommonCrawl
  - Scores PageSpeed / SEO
  - Métadonnées HTML

Lance depuis senwebstats/ :
  python scoring_model.py
"""

import sqlite3
import os
import json
import pandas as pd

# Chemins vers les deux bases
DB_PHASE1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "senwebstats.db")
DB_PHASE2 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "phase2", "data", "phase2.db")

# ── Coefficients de trafic par catégorie ─────────────────────
# Basés sur les données SimilarWeb Africa 2024
# (trafic moyen observé pour ce type de site en Afrique de l'Ouest)
CATEGORY_TRAFFIC_BASE = {
    "presse":        250000,   # Sites de news : fort trafic
    "ecommerce":     80000,    # E-commerce : trafic modéré
    "telephonie":    120000,   # Télécom : fort trafic marque
    "banque_finance":60000,    # Finance : trafic ciblé
    "emploi":        40000,    # Emploi : trafic spécialisé
}


def get_connection(db_path):
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def load_all_data() -> pd.DataFrame:
    """
    Charge et fusionne toutes les données disponibles
    depuis la base Phase 1.
    """
    conn = get_connection(DB_PHASE1)
    if conn is None:
        print(f"ERREUR : Base introuvable à {DB_PHASE1}")
        return pd.DataFrame()

    # Sites de base
    sites = pd.read_sql_query(
        "SELECT id, name, domain, category FROM sites ORDER BY category, name",
        conn
    )

    # Métadonnées HTML (dernière collecte)
    meta = pd.read_sql_query("""
        SELECT site_id,
               response_time_ms,
               word_count,
               internal_links_count,
               external_links_count,
               images_count,
               has_ssl,
               has_sitemap,
               has_robots_txt,
               status_code
        FROM site_metadata sm
        WHERE crawled_at = (
            SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = sm.site_id
        )
    """, conn)

    # Performance PageSpeed (dernière collecte)
    perf = pd.read_sql_query("""
        SELECT site_id,
               performance_score,
               seo_score,
               accessibility_score,
               best_practices_score,
               lcp_ms,
               ttfb_ms,
               fcp_ms
        FROM site_performance sp
        WHERE measured_at = (
            SELECT MAX(measured_at) FROM site_performance WHERE site_id = sp.site_id
        )
    """, conn)

    # Backlinks CommonCrawl (dernière collecte)
    backlinks = pd.read_sql_query("""
        SELECT site_id,
               total_backlinks,
               referring_domains
        FROM site_backlinks sb
        WHERE collected_at = (
            SELECT MAX(collected_at) FROM site_backlinks WHERE site_id = sb.site_id
        )
    """, conn)

    conn.close()

    # Fusionner tout sur site_id
    df = sites.copy()
    df = df.merge(meta,      left_on="id", right_on="site_id", how="left").drop(columns=["site_id"], errors="ignore")
    df = df.merge(perf,      left_on="id", right_on="site_id", how="left").drop(columns=["site_id"], errors="ignore")
    df = df.merge(backlinks, left_on="id", right_on="site_id", how="left").drop(columns=["site_id"], errors="ignore")

    return df


def normalize(series: pd.Series, invert: bool = False) -> pd.Series:
    """Normalise une série entre 0 et 100."""
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series([50.0] * len(series), index=series.index)
    normalized = (series - mn) / (mx - mn) * 100
    return (100 - normalized) if invert else normalized


def calculate_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule 4 scores pour chaque site :

    1. Score Autorité  (0-100) : backlinks + domaines référents
    2. Score Qualité   (0-100) : SEO + performance + accessibilité
    3. Score Technique (0-100) : SSL + sitemap + vitesse + taille
    4. Score Global    (0-100) : moyenne pondérée des 3 scores
    """
    df = df.copy()

    # Remplir les valeurs manquantes
    df["total_backlinks"]    = df["total_backlinks"].fillna(0)
    df["referring_domains"]  = df["referring_domains"].fillna(0)
    df["seo_score"]          = df["seo_score"].fillna(50)
    df["performance_score"]  = df["performance_score"].fillna(50)
    df["accessibility_score"]= df["accessibility_score"].fillna(50)
    df["response_time_ms"]   = df["response_time_ms"].fillna(3000)
    df["has_ssl"]            = df["has_ssl"].fillna(0)
    df["has_sitemap"]        = df["has_sitemap"].fillna(0)
    df["word_count"]         = df["word_count"].fillna(0)

    # ── Score Autorité ────────────────────────────────────────
    # Backlinks (60%) + Domaines référents (40%)
    bl_norm  = normalize(df["total_backlinks"])
    rd_norm  = normalize(df["referring_domains"])
    df["score_autorite"] = (bl_norm * 0.6 + rd_norm * 0.4).round(1)

    # ── Score Qualité ─────────────────────────────────────────
    # SEO (40%) + Performance (35%) + Accessibilité (25%)
    has_perf = df["seo_score"].notna() & df["performance_score"].notna()
    df["score_qualite"] = (
        df["seo_score"]          * 0.40 +
        df["performance_score"]  * 0.35 +
        df["accessibility_score"]* 0.25
    ).round(1)
    # Si pas de données PageSpeed, score qualité = 40 (neutre)
    df.loc[~has_perf, "score_qualite"] = 40.0

    # ── Score Technique ───────────────────────────────────────
    # Vitesse (40%) + SSL (20%) + Sitemap (15%) + Contenu (25%)
    vitesse_norm = normalize(df["response_time_ms"], invert=True)  # Inverser : moins = mieux
    contenu_norm = normalize(df["word_count"])

    df["score_technique"] = (
        vitesse_norm             * 0.40 +
        df["has_ssl"]   * 100   * 0.20 +
        df["has_sitemap"] * 100 * 0.15 +
        contenu_norm             * 0.25
    ).round(1)

    # ── Score Global ──────────────────────────────────────────
    # Autorité (45%) + Qualité (35%) + Technique (20%)
    df["score_global"] = (
        df["score_autorite"]  * 0.45 +
        df["score_qualite"]   * 0.35 +
        df["score_technique"] * 0.20
    ).round(1)

    return df


def estimate_traffic(df: pd.DataFrame) -> pd.DataFrame:
    """
    Estime le trafic mensuel basé sur le score global
    et le coefficient de la catégorie.

    Formule :
        trafic = base_catégorie × (score_global / 100) ^ 1.5

    L'exposant 1.5 crée un effet de domination :
    les meilleurs sites captent beaucoup plus de trafic
    (comme dans la réalité — la loi de puissance du web).
    """
    df = df.copy()

    def calc_traffic(row):
        base = CATEGORY_TRAFFIC_BASE.get(row["category"], 50000)
        score = row["score_global"] / 100
        # Loi de puissance : les meilleurs sites écrasent les autres
        traffic = int(base * (score ** 1.5))
        return traffic

    df["trafic_estime"] = df.apply(calc_traffic, axis=1)
    return df


def print_report(df: pd.DataFrame):
    """Affiche le rapport complet dans le terminal."""

    print("\n" + "="*70)
    print("  SENWEBSTATS — RAPPORT DE SCORING & ESTIMATION DE TRAFIC")
    print("="*70)

    # ── Par catégorie ─────────────────────────────────────────
    categories = df["category"].unique()
    for cat in sorted(categories):
        df_cat = df[df["category"] == cat].sort_values("score_global", ascending=False)
        base = CATEGORY_TRAFFIC_BASE.get(cat, 50000)

        print(f"\n  ━━━ {cat.upper()} (base trafic: {base:,}/mois) ━━━")
        print(f"  {'Site':<22} {'Global':>7} {'Autorité':>9} {'Qualité':>8} {'Technique':>10} {'Trafic/mois':>13}")
        print("  " + "-"*72)

        for _, row in df_cat.iterrows():
            name = row["name"][:22]
            print(f"  {name:<22} "
                  f"{row['score_global']:>6.1f} "
                  f"{row['score_autorite']:>9.1f} "
                  f"{row['score_qualite']:>8.1f} "
                  f"{row['score_technique']:>10.1f} "
                  f"{row['trafic_estime']:>12,}")

    # ── Classement global ─────────────────────────────────────
    print(f"\n\n  {'='*70}")
    print(f"  CLASSEMENT GÉNÉRAL — TOP 20 SITES")
    print(f"  {'='*70}")
    print(f"  {'#':<4} {'Site':<22} {'Catégorie':<16} {'Score':>6} {'Trafic estimé':>14}")
    print("  " + "-"*65)

    df_sorted = df.sort_values("score_global", ascending=False).head(20)
    for i, (_, row) in enumerate(df_sorted.iterrows(), 1):
        print(f"  {i:<4} {row['name'][:22]:<22} {row['category']:<16} "
              f"{row['score_global']:>5.1f}  {row['trafic_estime']:>13,}")

    # ── Stats globales ────────────────────────────────────────
    total_trafic = df["trafic_estime"].sum()
    print(f"\n  TOTAL trafic estimé : {total_trafic:,} visites/mois")
    print(f"  Score moyen global  : {df['score_global'].mean():.1f}/100")
    print(f"  Sites analysés      : {len(df)}")
    print(f"{'='*70}\n")


def save_to_phase2_db(df: pd.DataFrame):
    """Sauvegarde les scores dans la base Phase 2 pour le dashboard."""
    os.makedirs(os.path.dirname(DB_PHASE2), exist_ok=True)
    conn = sqlite3.connect(DB_PHASE2)
    c = conn.cursor()

    # Créer la table si elle n'existe pas
    c.execute("""
        CREATE TABLE IF NOT EXISTS site_scores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            domain TEXT NOT NULL,
            name TEXT,
            category TEXT,
            score_global REAL,
            score_autorite REAL,
            score_qualite REAL,
            score_technique REAL,
            trafic_estime INTEGER,
            calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Supprimer les anciens scores
    c.execute("DELETE FROM site_scores")

    # Insérer les nouveaux
    for _, row in df.iterrows():
        c.execute("""
            INSERT INTO site_scores
            (domain, name, category, score_global, score_autorite,
             score_qualite, score_technique, trafic_estime)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            row["domain"], row["name"], row["category"],
            row["score_global"], row["score_autorite"],
            row["score_qualite"], row["score_technique"],
            row["trafic_estime"],
        ))

    conn.commit()
    conn.close()
    print(f"  Scores sauvegardés dans : {DB_PHASE2}")


def run():
    print("\nChargement des données...")
    df = load_all_data()

    if df.empty:
        print("Aucune donnée trouvée. Vérifie que la base senwebstats.db existe.")
        return

    print(f"  {len(df)} sites chargés")

    print("Calcul des scores...")
    df = calculate_scores(df)

    print("Estimation du trafic...")
    df = estimate_traffic(df)

    print_report(df)
    save_to_phase2_db(df)

    # Sauvegarder en CSV aussi
    csv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "scores_export.csv")
    df[["name","domain","category","score_global","score_autorite",
        "score_qualite","score_technique","trafic_estime"]].to_csv(csv_path, index=False)
    print(f"  Export CSV : {csv_path}")


if __name__ == "__main__":
    run()
