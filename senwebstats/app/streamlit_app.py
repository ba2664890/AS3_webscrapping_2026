"""
SenWebStats — Dashboard v4
Thème : Clair · Lumineux · Professionnel
Tout est calculé automatiquement au chargement — aucune commande manuelle.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
import json
from datetime import datetime

st.set_page_config(
    page_title="SenWebStats",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# CSS — THÈME CLAIR MODERNE
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&family=Lora:ital,wght@0,500;0,700;1,400;1,600&display=swap');

:root {
    --bg:       #f7f8fc;
    --bg2:      #ffffff;
    --bg3:      #f0f2f8;
    --border:   #e4e7f0;
    --border2:  #d0d5e8;
    --text:     #1a1d2e;
    --muted:    #6b7280;
    --muted2:   #9ca3af;
    --teal:     #0d9488;
    --teal-lt:  #e6f7f5;
    --amber:    #d97706;
    --amber-lt: #fef3c7;
    --blue:     #2563eb;
    --blue-lt:  #eff6ff;
    --red:      #dc2626;
    --red-lt:   #fef2f2;
    --purple:   #7c3aed;
    --purple-lt:#f5f3ff;
    --green:    #16a34a;
    --green-lt: #f0fdf4;
    --font:     'Plus Jakarta Sans', sans-serif;
    --mono:     'DM Mono', monospace;
    --serif:    'Lora', serif;
}

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: var(--bg) !important;
    font-family: var(--font) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

.block-container { padding: 0 !important; max-width: 100% !important; }

/* ── SIDEBAR ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--bg2) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebarContent"] { padding: 0 !important; }

[data-testid="stRadio"] > label { display: none !important; }
[data-testid="stRadio"] > div { gap: 0 !important; }
[data-testid="stRadio"] [type="radio"] { display: none !important; }
[data-testid="stRadio"] label {
    display: flex !important;
    align-items: center !important;
    padding: 0.65rem 1.4rem !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    color: var(--muted) !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    border-left: 2px solid transparent !important;
    border-radius: 0 !important;
    margin: 0 !important;
}
[data-testid="stRadio"] label:hover {
    color: var(--text) !important;
    background: var(--bg3) !important;
}
[data-testid="stRadio"] label[data-checked="true"],
[data-testid="stRadio"] label[aria-checked="true"] {
    color: var(--teal) !important;
    border-left-color: var(--teal) !important;
    background: var(--teal-lt) !important;
    font-weight: 600 !important;
}

/* ── SELECT ──────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div > div,
[data-baseweb="select"] > div {
    background: var(--bg2) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-family: var(--font) !important;
    font-size: 0.82rem !important;
}
[data-testid="stMultiSelect"] > div {
    background: var(--bg2) !important;
    border: 1px solid var(--border2) !important;
    border-radius: 8px !important;
}
[data-testid="stMultiSelect"] span {
    background: var(--teal-lt) !important;
    color: var(--teal) !important;
    border: 1px solid rgba(13,148,136,0.2) !important;
    border-radius: 5px !important;
    font-size: 0.72rem !important;
}

/* ── DATAFRAME ───────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04) !important;
}
[data-testid="stDataFrame"] th {
    background: var(--bg3) !important;
    color: var(--muted) !important;
    font-family: var(--mono) !important;
    font-size: 0.64rem !important;
    letter-spacing: 0.06em !important;
    text-transform: uppercase !important;
    font-weight: 500 !important;
}
[data-testid="stDataFrame"] td {
    color: var(--text) !important;
    font-size: 0.82rem !important;
    background: var(--bg2) !important;
}

/* ── SCROLLBAR ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg3); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }

/* ── LAYOUT ──────────────────────────────────────────────── */
.wrap { padding: 2rem 2.5rem 5rem; }

/* PAGE HEADER */
.ph {
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}
.ph-left {}
.ph-eyebrow {
    font-family: var(--mono);
    font-size: 0.6rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--teal);
    margin-bottom: 0.4rem;
}
.ph-title {
    font-family: var(--serif);
    font-size: 1.85rem;
    font-weight: 500;
    color: var(--text);
    line-height: 1.2;
    letter-spacing: -0.01em;
}
.ph-title em { font-style: italic; color: var(--teal); font-weight: 400; }
.ph-sub {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 0.3rem;
    font-weight: 400;
}
.ph-right {
    font-family: var(--mono);
    font-size: 0.6rem;
    color: var(--muted2);
    text-align: right;
    line-height: 2;
}

/* STATUS PILLS */
.status-row {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    margin-bottom: 1.5rem;
}
.pill {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    padding: 0.3rem 0.75rem;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 500;
    font-family: var(--mono);
}
.pill-green  { background: var(--green-lt);  color: var(--green);  border: 1px solid rgba(22,163,74,0.2); }
.pill-teal   { background: var(--teal-lt);   color: var(--teal);   border: 1px solid rgba(13,148,136,0.2); }
.pill-amber  { background: var(--amber-lt);  color: var(--amber);  border: 1px solid rgba(217,119,6,0.2); }
.pill-gray   { background: var(--bg3);       color: var(--muted);  border: 1px solid var(--border); }
.pill-dot { width:6px; height:6px; border-radius:50%; background:currentColor; }

/* KPI */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1rem;
    margin-bottom: 2rem;
}
.kpi {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.4rem 1.5rem;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    position: relative;
    overflow: hidden;
    transition: box-shadow 0.2s, transform 0.2s;
}
.kpi:hover {
    box-shadow: 0 4px 16px rgba(0,0,0,0.08);
    transform: translateY(-1px);
}
.kpi-accent-bar {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 12px 12px 0 0;
}
.kpi-lbl {
    font-family: var(--mono);
    font-size: 0.58rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    color: var(--muted2);
    margin-bottom: 0.8rem;
}
.kpi-val {
    font-family: var(--serif);
    font-size: 2.1rem;
    font-weight: 700;
    line-height: 1;
    letter-spacing: -0.02em;
}
.kpi-sub {
    font-size: 0.7rem;
    color: var(--muted);
    margin-top: 0.4rem;
    font-weight: 400;
}

/* SECTION LABEL */
.sec {
    font-family: var(--mono);
    font-size: 0.58rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: var(--muted2);
    margin-bottom: 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.8rem;
}
.sec::after { content:''; flex:1; height:1px; background:var(--border); }

/* CARD */
.card {
    background: var(--bg2);
    border: 1px solid var(--border);
    border-radius: 12px;
    overflow: hidden;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
}
.card-hd {
    padding: 0.9rem 1.2rem;
    border-bottom: 1px solid var(--border);
    font-family: var(--mono);
    font-size: 0.58rem;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted2);
    display: flex;
    justify-content: space-between;
    background: var(--bg3);
}

/* RANK ROW */
.rrow {
    display: grid;
    grid-template-columns: 2.2rem 1fr auto auto;
    align-items: center;
    padding: 0.8rem 1.2rem;
    gap: 1rem;
    border-bottom: 1px solid var(--border);
    transition: background 0.12s;
}
.rrow:hover { background: var(--bg); }
.rrow:last-child { border-bottom: none; }
.rn { font-family:var(--mono); font-size:0.68rem; color:var(--muted2); text-align:right; font-weight:500; }
.rname { font-size:0.84rem; font-weight:600; color:var(--text); }
.rcat { font-family:var(--mono); font-size:0.58rem; color:var(--muted2); margin-top:0.1rem; }
.rbar-wrap { height:3px; border-radius:2px; background:var(--border); margin-top:0.4rem; overflow:hidden; }
.rbar { height:100%; border-radius:2px; }
.rscore { font-family:var(--mono); font-size:0.75rem; text-align:right; font-weight:500; }
.rtraffic { font-family:var(--mono); font-size:0.7rem; color:var(--teal); text-align:right; white-space:nowrap; font-weight:500; }

/* INFO BOX */
.info-box {
    background: var(--amber-lt);
    border: 1px solid rgba(217,119,6,0.2);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    font-size: 0.82rem;
    color: var(--amber);
    margin: 1rem 0;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES — Connexions automatiques
# ══════════════════════════════════════════════════════════════════════════════
def find_db(name):
    base = os.path.dirname(os.path.abspath(__file__))
    for p in [
        os.path.join(base, "..", "data", name),
        os.path.join(base, "data", name),
        os.path.join(os.getcwd(), "data", name),
        os.path.join(os.getcwd(), "senwebstats", "data", name),
    ]:
        full = os.path.abspath(p)
        if os.path.exists(full):
            return full
    return None

@st.cache_resource
def db1():
    p = find_db("senwebstats.db")
    if not p: return None
    c = sqlite3.connect(p, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def q(sql, params=(), db="main"):
    c = db1()
    if c is None: return pd.DataFrame()
    try: return pd.read_sql_query(sql, c, params=params)
    except: return pd.DataFrame()

def sv(sql, col="n", default=0):
    try:
        df = q(sql)
        if df.empty or col not in df.columns: return default
        v = df[col].values[0]
        return v if v is not None else default
    except: return default

# ══════════════════════════════════════════════════════════════════════════════
# CALCUL AUTOMATIQUE DU SCORING (intégré — pas de script séparé)
# ══════════════════════════════════════════════════════════════════════════════
CATEGORY_BASE = {
    "presse": 250000, "ecommerce": 80000,
    "telephonie": 120000, "banque_finance": 60000, "emploi": 40000,
}
CTR = {1:0.285,2:0.157,3:0.110,4:0.080,5:0.072,6:0.051,
       7:0.040,8:0.032,9:0.028,10:0.025}

def normalize(s, invert=False):
    mn, mx = s.min(), s.max()
    if mx == mn: return pd.Series([50.0]*len(s), index=s.index)
    n = (s - mn) / (mx - mn) * 100
    return (100 - n) if invert else n

@st.cache_data(ttl=300)
def compute_scores():
    """Calcule les scores directement depuis la DB — auto au chargement."""
    sites = q("SELECT id, name, domain, category FROM sites ORDER BY category, name")
    if sites.empty: return pd.DataFrame()

    meta = q("""SELECT site_id, response_time_ms, word_count,
                       internal_links_count, has_ssl, has_sitemap, status_code
               FROM site_metadata sm
               WHERE crawled_at=(SELECT MAX(crawled_at) FROM site_metadata WHERE site_id=sm.site_id)""")

    perf = q("""SELECT site_id, performance_score, seo_score, accessibility_score
               FROM site_performance sp
               WHERE measured_at=(SELECT MAX(measured_at) FROM site_performance WHERE site_id=sp.site_id)""")

    bl = q("""SELECT site_id, total_backlinks, referring_domains
              FROM site_backlinks sb
              WHERE collected_at=(SELECT MAX(collected_at) FROM site_backlinks WHERE site_id=sb.site_id)""")

    df = sites.copy()
    for other, key in [(meta,"site_id"),(perf,"site_id"),(bl,"site_id")]:
        if not other.empty:
            df = df.merge(other, left_on="id", right_on=key, how="left")
            if "site_id" in df.columns:
                df = df.drop(columns=["site_id"])

    # Remplir valeurs manquantes
    df["total_backlinks"]    = df.get("total_backlinks", pd.Series([0]*len(df))).fillna(0)
    df["referring_domains"]  = df.get("referring_domains", pd.Series([0]*len(df))).fillna(0)
    df["seo_score"]          = df.get("seo_score", pd.Series([50]*len(df))).fillna(50)
    df["performance_score"]  = df.get("performance_score", pd.Series([50]*len(df))).fillna(50)
    df["accessibility_score"]= df.get("accessibility_score", pd.Series([50]*len(df))).fillna(50)
    df["response_time_ms"]   = df.get("response_time_ms", pd.Series([3000]*len(df))).fillna(3000)
    df["has_ssl"]            = df.get("has_ssl", pd.Series([0]*len(df))).fillna(0)
    df["has_sitemap"]        = df.get("has_sitemap", pd.Series([0]*len(df))).fillna(0)
    df["word_count"]         = df.get("word_count", pd.Series([0]*len(df))).fillna(0)

    # Scores
    df["score_autorite"]  = (normalize(df["total_backlinks"])*0.6 + normalize(df["referring_domains"])*0.4).round(1)
    df["score_qualite"]   = (df["seo_score"]*0.40 + df["performance_score"]*0.35 + df["accessibility_score"]*0.25).round(1)
    df["score_technique"] = (normalize(df["response_time_ms"], invert=True)*0.40 +
                             df["has_ssl"]*100*0.20 +
                             df["has_sitemap"]*100*0.15 +
                             normalize(df["word_count"])*0.25).round(1)
    df["score_global"]    = (df["score_autorite"]*0.45 + df["score_qualite"]*0.35 + df["score_technique"]*0.20).round(1)

    def trafic(row):
        base = CATEGORY_BASE.get(row["category"], 50000)
        return int(base * (row["score_global"]/100) ** 1.5)
    df["trafic_estime"] = df.apply(trafic, axis=1)

    return df.sort_values("score_global", ascending=False).reset_index(drop=True)

# ══════════════════════════════════════════════════════════════════════════════
# PLOTLY THEME CLAIR
# ══════════════════════════════════════════════════════════════════════════════
PT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Mono, monospace", color="#6b7280", size=10),
    margin=dict(l=8, r=8, t=38, b=8),
    xaxis=dict(gridcolor="#f0f2f8", linecolor="#e4e7f0",
               tickfont=dict(size=9, color="#9ca3af")),
    yaxis=dict(gridcolor="#f0f2f8", linecolor="#e4e7f0",
               tickfont=dict(size=9, color="#9ca3af")),
)

COLORS = {
    "presse":         "#0d9488",
    "ecommerce":      "#2563eb",
    "telephonie":     "#d97706",
    "banque_finance": "#7c3aed",
    "emploi":         "#16a34a",
}

def sc(v):
    if v is None: return "#0d9488"
    if v >= 60: return "#16a34a"
    if v >= 40: return "#d97706"
    return "#dc2626"

def fmt(n):
    try: return f"{int(n):,}".replace(",", "\u202f")
    except: return "—"

# ══════════════════════════════════════════════════════════════════════════════
# DONNÉES
# ══════════════════════════════════════════════════════════════════════════════
df_all = compute_scores()

n_sites   = sv("SELECT COUNT(*) as n FROM sites")
n_crawled = sv("SELECT COUNT(DISTINCT site_id) as n FROM site_metadata")
n_perf    = sv("SELECT COUNT(DISTINCT site_id) as n FROM site_performance")
n_bl      = sv("SELECT COUNT(DISTINCT site_id) as n FROM site_backlinks")
total_tr  = int(df_all["trafic_estime"].sum()) if not df_all.empty else 0
avg_sc    = round(df_all["score_global"].mean(), 1) if not df_all.empty else 0

now = datetime.now().strftime("%d %b %Y · %H:%M")

# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="padding:1.8rem 1.4rem 1.4rem;border-bottom:1px solid #e4e7f0">
        <div style="font-family:'Lora',serif;font-size:1.3rem;font-weight:700;color:#1a1d2e;letter-spacing:-0.01em">
            SenWebStats
        </div>
        <div style="font-family:'DM Mono',monospace;font-size:0.55rem;letter-spacing:0.18em;
                    color:#9ca3af;margin-top:0.3rem;text-transform:uppercase">
            Observatoire · Web · Senegal
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)
    st.markdown("<div style='padding:0.5rem 1.4rem;font-family:DM Mono,monospace;font-size:0.52rem;letter-spacing:0.2em;text-transform:uppercase;color:#9ca3af'>Vues</div>", unsafe_allow_html=True)

    page = st.radio("nav", [
        "Vue d'ensemble",
        "Scoring & Trafic",
        "Metadonnees",
        "Performance",
        "Backlinks",
        "Comparaison",
    ], label_visibility="collapsed")

    st.markdown("<div style='height:1rem;border-top:1px solid #e4e7f0;margin:0.8rem 0 0'></div>", unsafe_allow_html=True)
    st.markdown("<div style='padding:0.5rem 1.4rem;font-family:DM Mono,monospace;font-size:0.52rem;letter-spacing:0.2em;text-transform:uppercase;color:#9ca3af'>Filtre</div>", unsafe_allow_html=True)

    cats_raw = q("SELECT DISTINCT category FROM sites ORDER BY category")
    cat_opts = ["Toutes"] + list(cats_raw["category"].values) if not cats_raw.empty else ["Toutes"]
    cat_f = st.selectbox("cat", cat_opts, label_visibility="collapsed")

    st.markdown(f"""
    <div style="position:absolute;bottom:0;left:0;right:0;padding:1rem 1.4rem;
                border-top:1px solid #e4e7f0;background:#f7f8fc">
        <div style="font-family:'DM Mono',monospace;font-size:0.58rem;color:#9ca3af;line-height:2.1">
            {n_sites} sites · 5 categories<br>
            Scoring : calcul automatique<br>
            {now}
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# FILTRE
# ══════════════════════════════════════════════════════════════════════════════
df_f = df_all if cat_f == "Toutes" else df_all[df_all["category"] == cat_f]
cat_sql = "" if cat_f == "Toutes" else f"AND s.category = '{cat_f}'"

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : VUE D'ENSEMBLE
# ══════════════════════════════════════════════════════════════════════════════
if page == "Vue d'ensemble":
    st.markdown('<div class="wrap">', unsafe_allow_html=True)

    # Status auto
    phase1_ok = n_crawled > 0
    perf_ok   = n_perf > 0
    bl_ok     = n_bl > 0
    score_ok  = not df_all.empty

    st.markdown(f"""
    <div class="ph">
        <div class="ph-left">
            <div class="ph-eyebrow">Tableau de bord</div>
            <div class="ph-title">Observatoire web <em>senegalais</em></div>
            <div class="ph-sub">Analyse de {n_sites} sites · presse, e-commerce, telecom, finance, emploi</div>
        </div>
        <div class="ph-right">{now}<br>Dakar · Senegal<br>Phase 1 complete · Scoring actif</div>
    </div>

    <div class="status-row">
        <div class="pill {'pill-green' if phase1_ok else 'pill-gray'}">
            <div class="pill-dot"></div>
            Metadonnees {"collectees" if phase1_ok else "en attente"}
        </div>
        <div class="pill {'pill-teal' if perf_ok else 'pill-gray'}">
            <div class="pill-dot"></div>
            Performance {"disponible" if perf_ok else "en attente"}
        </div>
        <div class="pill {'pill-green' if bl_ok else 'pill-gray'}">
            <div class="pill-dot"></div>
            Backlinks {"collectes" if bl_ok else "en attente"}
        </div>
        <div class="pill {'pill-teal' if score_ok else 'pill-amber'}">
            <div class="pill-dot"></div>
            Scoring {"calcule" if score_ok else "en cours"}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    st.markdown(f"""
    <div class="kpi-grid">
        <div class="kpi">
            <div class="kpi-accent-bar" style="background:#0d9488"></div>
            <div class="kpi-lbl">Sites suivis</div>
            <div class="kpi-val" style="color:#0d9488">{n_sites}</div>
            <div class="kpi-sub">5 categories</div>
        </div>
        <div class="kpi">
            <div class="kpi-accent-bar" style="background:#2563eb"></div>
            <div class="kpi-lbl">Trafic estime total</div>
            <div class="kpi-val" style="color:#2563eb">{fmt(total_tr)}</div>
            <div class="kpi-sub">visites / mois</div>
        </div>
        <div class="kpi">
            <div class="kpi-accent-bar" style="background:#16a34a"></div>
            <div class="kpi-lbl">Score moyen</div>
            <div class="kpi-val" style="color:#16a34a">{avg_sc}<small style="font-size:1rem;color:#9ca3af">/100</small></div>
            <div class="kpi-sub">sur 28 sites</div>
        </div>
        <div class="kpi">
            <div class="kpi-accent-bar" style="background:#d97706"></div>
            <div class="kpi-lbl">Avec PageSpeed</div>
            <div class="kpi-val" style="color:#d97706">{n_perf}</div>
            <div class="kpi-sub">scores collectes</div>
        </div>
        <div class="kpi">
            <div class="kpi-accent-bar" style="background:#7c3aed"></div>
            <div class="kpi-lbl">Backlinks</div>
            <div class="kpi-val" style="color:#7c3aed">{n_bl}</div>
            <div class="kpi-sub">sites avec donnees</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        st.markdown('<div class="sec">Classement global — Top 15</div>', unsafe_allow_html=True)
        st.markdown('<div class="card"><div class="card-hd"><span>Site · Categorie</span><span>Score · Trafic/mois</span></div>', unsafe_allow_html=True)

        if not df_all.empty:
            mx = df_all["score_global"].max()
            for rank, row in df_all.head(15).iterrows():
                pct   = int(row["score_global"] / mx * 100)
                color = sc(row["score_global"])
                cat_c = COLORS.get(row["category"], "#888")
                st.markdown(f"""
                <div class="rrow">
                    <div class="rn">{rank+1:02d}</div>
                    <div>
                        <div class="rname">{row['name']}</div>
                        <div class="rcat" style="color:{cat_c}">{row['category']}</div>
                        <div class="rbar-wrap">
                            <div class="rbar" style="width:{pct}%;background:{color}"></div>
                        </div>
                    </div>
                    <div class="rscore" style="color:{color}">{row['score_global']:.1f}<span style="color:#9ca3af;font-size:0.58rem">/100</span></div>
                    <div class="rtraffic">{fmt(row['trafic_estime'])}<span style="color:#9ca3af;font-size:0.58rem"> /mois</span></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="padding:1.5rem"><div class="info-box">Base de donnees non trouvee. Verifie le chemin vers senwebstats.db</div></div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if not df_all.empty:
            # Trafic par catégorie
            st.markdown('<div class="sec">Trafic estime par categorie</div>', unsafe_allow_html=True)
            cat_sum = df_all.groupby("category")["trafic_estime"].sum().reset_index().sort_values("trafic_estime")
            fig = go.Figure(go.Bar(
                x=cat_sum["trafic_estime"], y=cat_sum["category"],
                orientation="h",
                marker=dict(color=[COLORS.get(c,"#888") for c in cat_sum["category"]],
                           line=dict(width=0), opacity=0.85),
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} visites/mois<extra></extra>",
            ))
            fig.update_layout(**PT, height=200,
                title=dict(text="VISITES ESTIMEES / MOIS",
                          font=dict(size=9, color="#9ca3af"), x=0),
                yaxis=dict(**PT["yaxis"], tickfont=dict(size=9, color="#6b7280")))
            st.plotly_chart(fig, use_container_width=True)

            # Part de marché donut
            st.markdown('<div class="sec">Part de trafic · Top 8</div>', unsafe_allow_html=True)
            top8 = df_all.head(8)
            fig2 = go.Figure(go.Pie(
                labels=top8["name"], values=top8["trafic_estime"],
                marker=dict(colors=[COLORS.get(c,"#888") for c in top8["category"]],
                           line=dict(color="#ffffff", width=2)),
                hole=0.52,
                textfont=dict(family="DM Mono", size=8, color="#1a1d2e"),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} visites/mois<br>%{percent}<extra></extra>",
            ))
            fig2.update_layout(**PT, height=230, showlegend=False,
                margin=dict(l=0,r=0,t=28,b=0),
                title=dict(text="PART DE TRAFIC ESTIMEE · TOP 8",
                          font=dict(size=9, color="#9ca3af"), x=0))
            st.plotly_chart(fig2, use_container_width=True)

            # Score distribution
            st.markdown('<div class="sec">Distribution des scores</div>', unsafe_allow_html=True)
            fig3 = go.Figure()
            for cat in df_all["category"].unique():
                dc = df_all[df_all["category"] == cat]
                fig3.add_trace(go.Box(
                    y=dc["score_global"], name=cat,
                    marker_color=COLORS.get(cat, "#888"),
                    line=dict(width=1.5),
                    fillcolor=COLORS.get(cat, "#888") + "22",
                    hovertemplate="%{y:.1f}<extra>" + cat + "</extra>",
                ))
            fig3.update_layout(**PT, height=230, showlegend=False,
                title=dict(text="SCORES GLOBAUX PAR CATEGORIE",
                          font=dict(size=9, color="#9ca3af"), x=0),
                yaxis=dict(**PT["yaxis"], range=[0,100]))
            st.plotly_chart(fig3, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : SCORING & TRAFIC
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Scoring & Trafic":
    st.markdown('<div class="wrap">', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="ph">
        <div class="ph-left">
            <div class="ph-eyebrow">Modele analytique · calcul automatique</div>
            <div class="ph-title">Scoring & <em>Trafic estime</em></div>
            <div class="ph-sub">Autorite (45%) · Qualite (35%) · Technique (20%) · Loi de puissance par categorie</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if df_f.empty:
        st.markdown('<div class="info-box">Aucune donnee disponible. Verifie que la base senwebstats.db est accessible.</div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            fig = go.Figure()
            for cat in df_f["category"].unique():
                dc = df_f[df_f["category"] == cat]
                fig.add_trace(go.Scatter(
                    x=dc["score_autorite"], y=dc["trafic_estime"],
                    mode="markers+text", name=cat,
                    text=dc["name"],
                    textposition="top center",
                    textfont=dict(size=8, color="#6b7280"),
                    marker=dict(
                        size=dc["score_global"] / 4 + 7,
                        color=COLORS.get(cat, "#888"),
                        opacity=0.8,
                        line=dict(width=1.5, color="#ffffff"),
                    ),
                    hovertemplate="<b>%{text}</b><br>Autorite: %{x:.0f}<br>Trafic: %{y:,.0f}/mois<extra></extra>",
                ))
            fig.update_layout(**PT, height=400, showlegend=True,
                title=dict(text="AUTORITE vs TRAFIC  (taille = score global)",
                          font=dict(size=9, color="#9ca3af"), x=0),
                legend=dict(font=dict(size=9, color="#6b7280"), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(**PT["xaxis"], title=dict(text="Score Autorite", font=dict(size=9, color="#9ca3af"))),
                yaxis=dict(**PT["yaxis"], title=dict(text="Trafic estime / mois", font=dict(size=9, color="#9ca3af"))))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            top12 = df_f.nlargest(12, "trafic_estime")
            fig2 = go.Figure(go.Bar(
                x=top12["trafic_estime"], y=top12["name"],
                orientation="h",
                marker=dict(color=[COLORS.get(c,"#888") for c in top12["category"]],
                           line=dict(width=0), opacity=0.82),
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} visites/mois<extra></extra>",
            ))
            fig2.update_layout(**PT, height=400,
                title=dict(text="TOP TRAFIC ESTIME / MOIS",
                          font=dict(size=9, color="#9ca3af"), x=0),
                yaxis=dict(**PT["yaxis"], categoryorder="total ascending", tickfont=dict(size=9)))
            st.plotly_chart(fig2, use_container_width=True)

        # Heatmap
        st.markdown('<div class="sec">Heatmap des sous-scores</div>', unsafe_allow_html=True)
        dh = df_f.set_index("name")[["score_autorite","score_qualite","score_technique","score_global"]]
        dh.columns = ["Autorite","Qualite","Technique","Global"]
        fig3 = go.Figure(go.Heatmap(
            z=dh.values.T, x=dh.index.tolist(), y=dh.columns.tolist(),
            colorscale=[[0,"#f0fdf4"],[0.4,"#6ee7b7"],[0.7,"#059669"],[1,"#064e3b"]],
            hovertemplate="<b>%{x}</b><br>%{y}: %{z:.1f}<extra></extra>",
            showscale=True,
            colorbar=dict(tickfont=dict(size=8, color="#6b7280"), thickness=10, len=0.9),
        ))
        fig3.update_layout(**PT, height=200,
            title=dict(text="SCORES PAR DIMENSION — TOUS LES SITES",
                      font=dict(size=9, color="#9ca3af"), x=0),
            xaxis=dict(**PT["xaxis"], tickangle=-35, tickfont=dict(size=8)),
            margin=dict(l=70, r=70, t=38, b=60))
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown('<div class="sec">Detail complet</div>', unsafe_allow_html=True)
        d = df_f[["name","category","score_global","score_autorite","score_qualite","score_technique","trafic_estime"]].copy()
        d.columns = ["Site","Categorie","Global","Autorite","Qualite","Technique","Trafic/mois"]
        st.dataframe(d.round(1), use_container_width=True, hide_index=True, height=400)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : METADONNEES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Metadonnees":
    st.markdown('<div class="wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="ph">
        <div class="ph-left">
            <div class="ph-eyebrow">Collecte HTML automatique</div>
            <div class="ph-title">Metadonnees <em>techniques</em></div>
            <div class="ph-sub">Structure · Liens · Vitesse · Conformite SEO</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_meta = q(f"""
        SELECT s.name, s.domain, s.category,
               sm.status_code, sm.response_time_ms, sm.word_count,
               sm.internal_links_count, sm.external_links_count,
               sm.images_count, sm.has_ssl, sm.has_sitemap, sm.has_robots_txt
        FROM sites s
        LEFT JOIN site_metadata sm ON sm.site_id=s.id
            AND sm.crawled_at=(SELECT MAX(crawled_at) FROM site_metadata WHERE site_id=s.id)
        WHERE 1=1 {cat_sql} ORDER BY s.category, s.name
    """)

    if df_meta.empty or df_meta["status_code"].isna().all():
        st.markdown('<div class="info-box">Metadonnees non collectees. Lance : python main.py crawl</div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            df_rt = df_meta.dropna(subset=["response_time_ms"]).sort_values("response_time_ms")
            fig = go.Figure(go.Bar(
                x=df_rt["response_time_ms"], y=df_rt["name"], orientation="h",
                marker=dict(
                    color=["#16a34a" if v<1000 else "#d97706" if v<2500 else "#dc2626"
                           for v in df_rt["response_time_ms"]],
                    line=dict(width=0), opacity=0.82),
                hovertemplate="<b>%{y}</b><br>%{x:.0f} ms<extra></extra>",
            ))
            fig.update_layout(**PT, height=400,
                title=dict(text="TEMPS DE REPONSE (ms)  vert<1s · jaune<2.5s · rouge>2.5s",
                          font=dict(size=9, color="#9ca3af"), x=0),
                yaxis=dict(**PT["yaxis"], categoryorder="total ascending", tickfont=dict(size=8)))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            df_lk = df_meta.dropna(subset=["internal_links_count"]).sort_values("internal_links_count", ascending=False).head(14)
            fig2 = go.Figure(go.Bar(
                x=df_lk["name"], y=df_lk["internal_links_count"],
                marker=dict(color="#2563eb", line=dict(width=0), opacity=0.75),
                hovertemplate="<b>%{x}</b><br>%{y} liens internes<extra></extra>",
            ))
            fig2.update_layout(**PT, height=400,
                title=dict(text="LIENS INTERNES PAR SITE",
                          font=dict(size=9, color="#9ca3af"), x=0),
                xaxis=dict(**PT["xaxis"], tickangle=-35, tickfont=dict(size=8)))
            st.plotly_chart(fig2, use_container_width=True)

        col3, col4 = st.columns(2, gap="large")
        with col3:
            ssl_ok  = int(df_meta["has_ssl"].fillna(0).sum())
            site_ok = int(df_meta["has_sitemap"].fillna(0).sum())
            rob_ok  = int(df_meta["has_robots_txt"].fillna(0).sum()) if "has_robots_txt" in df_meta else 0
            total_m = len(df_meta)
            fig3 = go.Figure(go.Bar(
                x=["SSL","Sitemap","Robots.txt"],
                y=[ssl_ok, site_ok, rob_ok],
                marker=dict(color=["#0d9488","#2563eb","#7c3aed"], line=dict(width=0), opacity=0.82),
                text=[f"{v}/{total_m}" for v in [ssl_ok, site_ok, rob_ok]],
                textposition="outside",
                textfont=dict(size=11, color="#6b7280", family="DM Mono"),
            ))
            fig3.update_layout(**PT, height=260,
                title=dict(text="CONFORMITE TECHNIQUE",
                          font=dict(size=9, color="#9ca3af"), x=0),
                yaxis=dict(**PT["yaxis"], range=[0, total_m + 3]))
            st.plotly_chart(fig3, use_container_width=True)

        with col4:
            st.markdown('<div class="sec" style="margin-top:0.3rem">Tableau complet</div>', unsafe_allow_html=True)
            d = df_meta[["name","category","response_time_ms","word_count","has_ssl","has_sitemap"]].copy()
            d.columns = ["Site","Cat.","Temps(ms)","Mots","SSL","Sitemap"]
            d["SSL"]     = d["SSL"].apply(lambda x: "oui" if x==1 else "non")
            d["Sitemap"] = d["Sitemap"].apply(lambda x: "oui" if x==1 else "non")
            st.dataframe(d, use_container_width=True, hide_index=True, height=260)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Performance":
    st.markdown('<div class="wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="ph">
        <div class="ph-left">
            <div class="ph-eyebrow">PageSpeed Insights · Google</div>
            <div class="ph-title">Scores de <em>performance</em></div>
            <div class="ph-sub">Core Web Vitals · Lighthouse · Mobile first</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_perf = q(f"""
        SELECT s.name, s.category,
               sp.performance_score, sp.seo_score,
               sp.accessibility_score, sp.best_practices_score,
               sp.lcp_ms, sp.fcp_ms, sp.ttfb_ms, sp.cls_score
        FROM site_performance sp JOIN sites s ON s.id=sp.site_id
        WHERE sp.measured_at=(SELECT MAX(measured_at) FROM site_performance WHERE site_id=sp.site_id)
        {cat_sql} ORDER BY sp.performance_score DESC
    """)

    if df_perf.empty:
        st.markdown('<div class="info-box">Scores PageSpeed non collectes. Lance : python main.py perf</div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            top = df_perf.nlargest(12, "performance_score")
            fig = go.Figure(go.Bar(
                x=top["performance_score"], y=top["name"], orientation="h",
                marker=dict(
                    color=["#16a34a" if v>=90 else "#d97706" if v>=50 else "#dc2626"
                           for v in top["performance_score"]],
                    line=dict(width=0), opacity=0.82),
                hovertemplate="<b>%{y}</b><br>%{x:.0f}/100<extra></extra>",
            ))
            fig.update_layout(**PT, height=360,
                title=dict(text="SCORE PERFORMANCE / 100",
                          font=dict(size=9, color="#9ca3af"), x=0),
                xaxis=dict(**PT["xaxis"], range=[0,100]),
                yaxis=dict(**PT["yaxis"], categoryorder="total ascending", tickfont=dict(size=8)))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            fig2 = px.scatter(df_perf, x="performance_score", y="seo_score",
                color="category", text="name", color_discrete_map=COLORS,
                labels={"performance_score":"Performance","seo_score":"SEO"})
            fig2.update_traces(
                textposition="top center",
                textfont=dict(size=8, color="#6b7280"),
                marker=dict(size=10, opacity=0.8, line=dict(width=1.5, color="#ffffff")))
            fig2.update_layout(**PT, height=360,
                title=dict(text="PERFORMANCE vs SEO",
                          font=dict(size=9, color="#9ca3af"), x=0),
                legend=dict(font=dict(size=9, color="#6b7280"), bgcolor="rgba(0,0,0,0)"),
                xaxis=dict(**PT["xaxis"], range=[0,100]),
                yaxis=dict(**PT["yaxis"], range=[0,100]))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="sec">Core Web Vitals</div>', unsafe_allow_html=True)
        cwv = df_perf[["name","lcp_ms","fcp_ms","ttfb_ms","cls_score","accessibility_score","best_practices_score"]].copy()
        cwv.columns = ["Site","LCP (ms)","FCP (ms)","TTFB (ms)","CLS","Accessibilite","Best Practices"]
        st.dataframe(cwv.round(1), use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : BACKLINKS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Backlinks":
    st.markdown('<div class="wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="ph">
        <div class="ph-left">
            <div class="ph-eyebrow">CommonCrawl Index</div>
            <div class="ph-title">Autorite & <em>Backlinks</em></div>
            <div class="ph-sub">Pages indexees · Domaines referents · Variation mensuelle</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    df_bl = q(f"""
        SELECT s.name, s.category, s.domain,
               sb.total_backlinks, sb.referring_domains, sb.backlinks_change
        FROM site_backlinks sb JOIN sites s ON s.id=sb.site_id
        WHERE sb.collected_at=(SELECT MAX(collected_at) FROM site_backlinks WHERE site_id=sb.site_id)
        {cat_sql} ORDER BY sb.total_backlinks DESC
    """)

    if df_bl.empty:
        st.markdown('<div class="info-box">Backlinks non collectes. Lance : python main.py backlinks</div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2, gap="large")
        with col1:
            fig = go.Figure(go.Bar(
                x=df_bl["total_backlinks"], y=df_bl["name"], orientation="h",
                marker=dict(color=[COLORS.get(c,"#888") for c in df_bl["category"]],
                           line=dict(width=0), opacity=0.82),
                hovertemplate="<b>%{y}</b><br>%{x} pages indexees<extra></extra>",
            ))
            fig.update_layout(**PT, height=420,
                title=dict(text="PAGES INDEXEES — CommonCrawl",
                          font=dict(size=9, color="#9ca3af"), x=0),
                yaxis=dict(**PT["yaxis"], categoryorder="total ascending", tickfont=dict(size=8)))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            top_rd = df_bl.nlargest(14,"referring_domains")
            fig2 = go.Figure(go.Bar(
                x=top_rd["referring_domains"], y=top_rd["name"], orientation="h",
                marker=dict(color="#0d9488", line=dict(width=0), opacity=0.75),
                hovertemplate="<b>%{y}</b><br>%{x} domaines referents<extra></extra>",
            ))
            fig2.update_layout(**PT, height=420,
                title=dict(text="DOMAINES REFERENTS",
                          font=dict(size=9, color="#9ca3af"), x=0),
                yaxis=dict(**PT["yaxis"], categoryorder="total ascending", tickfont=dict(size=8)))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="sec">Tableau complet</div>', unsafe_allow_html=True)
        d = df_bl[["name","category","domain","total_backlinks","referring_domains"]].copy()
        d.columns = ["Site","Categorie","Domaine","Pages indexees","Dom. referents"]
        st.dataframe(d, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE : COMPARAISON
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Comparaison":
    st.markdown('<div class="wrap">', unsafe_allow_html=True)
    st.markdown("""
    <div class="ph">
        <div class="ph-left">
            <div class="ph-eyebrow">Analyse concurrentielle</div>
            <div class="ph-title">Comparaison <em>directe</em></div>
            <div class="ph-sub">Selectionnez jusqu'a 8 sites pour comparer toutes leurs dimensions</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sl = q("SELECT name FROM sites ORDER BY name")
    if not sl.empty and not df_all.empty:
        selected = st.multiselect(
            "Sites a comparer",
            options=sl["name"].tolist(),
            default=sl["name"].tolist()[:6],
            max_selections=8,
        )
        if selected:
            ds = df_all[df_all["name"].isin(selected)]
            if not ds.empty:
                PALETTE = ["#0d9488","#2563eb","#d97706","#7c3aed","#16a34a","#dc2626","#ea580c","#0891b2"]

                col1, col2 = st.columns(2, gap="large")
                with col1:
                    dims = ["Autorite","Qualite","Technique","Score global"]
                    fig = go.Figure()
                    for j, (_, row) in enumerate(ds.iterrows()):
                        vals = [row["score_autorite"],row["score_qualite"],
                                row["score_technique"],row["score_global"]]
                        vals += [vals[0]]
                        fig.add_trace(go.Scatterpolar(
                            r=vals, theta=dims+[dims[0]],
                            fill="toself", name=row["name"],
                            line=dict(color=PALETTE[j%len(PALETTE)], width=2),
                            fillcolor=PALETTE[j%len(PALETTE)]+"22",
                            hovertemplate="%{theta}: %{r:.1f}<extra>"+row["name"]+"</extra>",
                        ))
                    fig.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        font=dict(family="DM Mono, monospace", color="#6b7280", size=10),
                        height=420,
                        polar=dict(
                            bgcolor="rgba(0,0,0,0)",
                            radialaxis=dict(visible=True, range=[0,100],
                                          gridcolor="#e4e7f0",
                                          tickfont=dict(size=7, color="#9ca3af")),
                            angularaxis=dict(gridcolor="#e4e7f0",
                                            tickfont=dict(size=9, color="#6b7280"))
                        ),
                        title=dict(text="RADAR — PROFIL COMPARATIF",
                                  font=dict(size=9, color="#9ca3af"), x=0),
                        legend=dict(font=dict(size=9, color="#6b7280"), bgcolor="rgba(0,0,0,0)"),
                        margin=dict(l=40, r=40, t=38, b=20),
                    )
                    st.plotly_chart(fig, use_container_width=True)

                with col2:
                    metrics = ["score_autorite","score_qualite","score_technique","score_global"]
                    labels  = ["Autorite","Qualite","Technique","Global"]
                    fig2 = go.Figure()
                    for j, (_, row) in enumerate(ds.iterrows()):
                        fig2.add_trace(go.Bar(
                            name=row["name"], x=labels,
                            y=[row[m] for m in metrics],
                            marker=dict(color=PALETTE[j%len(PALETTE)], line=dict(width=0), opacity=0.82),
                            hovertemplate="<b>"+row["name"]+"</b><br>%{x}: %{y:.1f}<extra></extra>",
                        ))
                    fig2.update_layout(**PT, height=420, barmode="group",
                        title=dict(text="COMPARAISON PAR DIMENSION",
                                  font=dict(size=9, color="#9ca3af"), x=0),
                        yaxis=dict(**PT["yaxis"], range=[0,100]),
                        legend=dict(font=dict(size=9, color="#6b7280"), bgcolor="rgba(0,0,0,0)"))
                    st.plotly_chart(fig2, use_container_width=True)

                st.markdown('<div class="sec">Tableau recapitulatif</div>', unsafe_allow_html=True)
                dt = ds[["name","category","score_global","score_autorite",
                         "score_qualite","score_technique","trafic_estime"]].copy()
                dt.columns = ["Site","Categorie","Global","Autorite","Qualite","Technique","Trafic/mois"]
                st.dataframe(dt.round(1).sort_values("Global", ascending=False),
                            use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)
