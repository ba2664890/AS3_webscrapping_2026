"""
SenWebStats — Dashboard Ultra-Moderne
Design : Cubisme africain × Data journalism × Luxury editorial
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sqlite3
import os
import json

# ── Config page ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SenWebStats",
    page_icon="🇸🇳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS — Design Cubisme Africain × Editorial Luxury ─────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,700;0,900;1,700&family=Space+Mono:wght@400;700&family=Syne:wght@400;600;800&display=swap');

:root {
    --noir:     #0a0a0a;
    --or:       #C9A84C;
    --or-pale:  #F0D080;
    --terre:    #8B3A2A;
    --sable:    #E8DCC8;
    --vert:     #1B4D3E;
    --vert-vif: #2ECC71;
    --gris:     #1a1a1a;
    --gris-mid: #2d2d2d;
    --blanc:    #FAF8F4;
}

* { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"] {
    background: var(--noir) !important;
    color: var(--sable) !important;
    font-family: 'Syne', sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background:
        radial-gradient(ellipse at 10% 20%, rgba(201,168,76,0.06) 0%, transparent 50%),
        radial-gradient(ellipse at 90% 80%, rgba(139,58,42,0.08) 0%, transparent 50%),
        radial-gradient(ellipse at 50% 50%, rgba(27,77,62,0.04) 0%, transparent 70%),
        var(--noir) !important;
}

/* Cacher les éléments Streamlit par défaut */
#MainMenu, footer, header, [data-testid="stToolbar"] { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 0 2rem 4rem 2rem !important; max-width: 100% !important; }

/* ── HERO HEADER ──────────────────────────────────────────────────────────── */
.hero {
    position: relative;
    padding: 5rem 4rem 4rem;
    margin: 0 -2rem 3rem -2rem;
    overflow: hidden;
    border-bottom: 1px solid rgba(201,168,76,0.2);
}

.hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0; bottom: 0;
    background:
        linear-gradient(135deg, rgba(201,168,76,0.03) 0%, transparent 60%),
        repeating-linear-gradient(
            -45deg,
            transparent,
            transparent 80px,
            rgba(201,168,76,0.015) 80px,
            rgba(201,168,76,0.015) 81px
        );
}

.hero-eyebrow {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.4em;
    color: var(--or);
    text-transform: uppercase;
    margin-bottom: 1.5rem;
    opacity: 0.8;
}

.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(3.5rem, 8vw, 7rem);
    font-weight: 900;
    line-height: 0.9;
    margin: 0 0 1.5rem 0;
    letter-spacing: -0.03em;
}

.hero-title .line1 { color: var(--blanc); display: block; }
.hero-title .line2 {
    color: transparent;
    -webkit-text-stroke: 1px var(--or);
    display: block;
    margin-left: 3rem;
}
.hero-title .line3 { color: var(--or); display: block; margin-left: 6rem; }

.hero-sub {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    color: rgba(232,220,200,0.5);
    max-width: 500px;
    margin-top: 2rem;
    line-height: 1.7;
    font-weight: 400;
}

.hero-flag {
    position: absolute;
    right: 4rem;
    top: 50%;
    transform: translateY(-50%);
    font-size: 8rem;
    opacity: 0.15;
    filter: grayscale(100%);
}

.hero-tag {
    display: inline-block;
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    padding: 0.3rem 0.8rem;
    border: 1px solid var(--or);
    color: var(--or);
    letter-spacing: 0.2em;
    text-transform: uppercase;
    margin-top: 2rem;
    opacity: 0.7;
}

/* ── KPI CARDS ────────────────────────────────────────────────────────────── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1px;
    background: rgba(201,168,76,0.1);
    border: 1px solid rgba(201,168,76,0.1);
    margin-bottom: 3rem;
}

.kpi-card {
    background: var(--gris);
    padding: 2rem 1.5rem;
    position: relative;
    overflow: hidden;
    transition: background 0.3s;
}

.kpi-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0;
    height: 2px;
    width: 0;
    background: var(--or);
    transition: width 0.4s ease;
}

.kpi-card:hover { background: var(--gris-mid); }
.kpi-card:hover::after { width: 100%; }

.kpi-icon {
    font-size: 1.2rem;
    margin-bottom: 1rem;
    opacity: 0.6;
}

.kpi-value {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem;
    font-weight: 700;
    color: var(--or);
    line-height: 1;
    margin-bottom: 0.5rem;
}

.kpi-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: rgba(232,220,200,0.4);
}

/* ── SECTION HEADERS ──────────────────────────────────────────────────────── */
.section-header {
    display: flex;
    align-items: baseline;
    gap: 1.5rem;
    margin: 3rem 0 1.5rem 0;
    padding-bottom: 1rem;
    border-bottom: 1px solid rgba(201,168,76,0.15);
}

.section-number {
    font-family: 'Playfair Display', serif;
    font-size: 4rem;
    font-weight: 900;
    color: transparent;
    -webkit-text-stroke: 1px rgba(201,168,76,0.2);
    line-height: 1;
}

.section-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--blanc);
}

.section-tag {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.3em;
    color: var(--or);
    text-transform: uppercase;
    margin-left: auto;
    opacity: 0.6;
}

/* ── TABS ─────────────────────────────────────────────────────────────────── */
[data-testid="stTabs"] { margin-top: 0; }

[data-testid="stTabContent"] { padding-top: 2rem; }

button[data-baseweb="tab"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.65rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    color: rgba(232,220,200,0.4) !important;
    padding: 1rem 1.5rem !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid transparent !important;
    transition: all 0.3s !important;
}

button[data-baseweb="tab"]:hover {
    color: var(--or) !important;
}

button[data-baseweb="tab"][aria-selected="true"] {
    color: var(--or) !important;
    border-bottom: 1px solid var(--or) !important;
}

[data-testid="stTabList"] {
    background: transparent !important;
    border-bottom: 1px solid rgba(201,168,76,0.1) !important;
    gap: 0 !important;
}

/* ── FILTER BAR ───────────────────────────────────────────────────────────── */
.filter-bar {
    display: flex;
    gap: 0.5rem;
    margin-bottom: 2rem;
    flex-wrap: wrap;
}

.filter-pill {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    letter-spacing: 0.15em;
    padding: 0.4rem 1rem;
    border: 1px solid rgba(201,168,76,0.3);
    color: rgba(232,220,200,0.5);
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s;
    background: transparent;
}

.filter-pill.active, .filter-pill:hover {
    border-color: var(--or);
    color: var(--or);
    background: rgba(201,168,76,0.05);
}

/* ── DATA TABLE ───────────────────────────────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(201,168,76,0.1) !important;
}

[data-testid="stDataFrame"] table {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
}

[data-testid="stDataFrame"] th {
    background: var(--gris) !important;
    color: var(--or) !important;
    font-size: 0.6rem !important;
    letter-spacing: 0.2em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid rgba(201,168,76,0.2) !important;
}

[data-testid="stDataFrame"] td {
    color: var(--sable) !important;
    border-bottom: 1px solid rgba(255,255,255,0.03) !important;
}

/* ── SELECTBOX ────────────────────────────────────────────────────────────── */
[data-testid="stSelectbox"] > div {
    background: var(--gris) !important;
    border: 1px solid rgba(201,168,76,0.2) !important;
    color: var(--sable) !important;
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
}

[data-testid="stMultiSelect"] > div {
    background: var(--gris) !important;
    border: 1px solid rgba(201,168,76,0.2) !important;
}

/* ── ALERT BOX ────────────────────────────────────────────────────────────── */
.custom-alert {
    border: 1px solid rgba(201,168,76,0.2);
    padding: 1.5rem 2rem;
    background: rgba(201,168,76,0.03);
    font-family: 'Space Mono', monospace;
    font-size: 0.75rem;
    color: rgba(232,220,200,0.5);
    margin: 1rem 0;
}

.custom-alert span { color: var(--or); }

/* ── SCROLLBAR ────────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--noir); }
::-webkit-scrollbar-thumb { background: rgba(201,168,76,0.3); }

/* ── RANK TABLE ───────────────────────────────────────────────────────────── */
.rank-row {
    display: flex;
    align-items: center;
    padding: 1rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    gap: 1.5rem;
}

.rank-num {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 900;
    color: rgba(201,168,76,0.2);
    width: 2.5rem;
    text-align: right;
}

.rank-name {
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    color: var(--blanc);
    flex: 1;
}

.rank-cat {
    font-family: 'Space Mono', monospace;
    font-size: 0.55rem;
    letter-spacing: 0.2em;
    color: var(--or);
    text-transform: uppercase;
    opacity: 0.6;
}

.rank-bar-container {
    width: 200px;
    height: 3px;
    background: rgba(255,255,255,0.05);
    position: relative;
}

.rank-bar-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--vert), var(--or));
    transition: width 1s ease;
}

.rank-value {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    color: var(--or);
    width: 3rem;
    text-align: right;
}

/* ── STAT BADGE ───────────────────────────────────────────────────────────── */
.badge-good   { color: #2ECC71; font-family:'Space Mono',monospace; font-size:0.75rem; }
.badge-medium { color: #F39C12; font-family:'Space Mono',monospace; font-size:0.75rem; }
.badge-bad    { color: #E74C3C; font-family:'Space Mono',monospace; font-size:0.75rem; }

/* ── DIVIDER ──────────────────────────────────────────────────────────────── */
.gold-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--or), transparent);
    margin: 2rem 0;
    opacity: 0.3;
}

/* ── FOOTER ───────────────────────────────────────────────────────────────── */
.footer {
    margin-top: 5rem;
    padding: 3rem 0 2rem 0;
    border-top: 1px solid rgba(201,168,76,0.1);
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.footer-logo {
    font-family: 'Playfair Display', serif;
    font-size: 1.5rem;
    font-weight: 900;
    color: var(--or);
}

.footer-info {
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    color: rgba(232,220,200,0.2);
    letter-spacing: 0.1em;
    text-align: right;
    line-height: 2;
}
</style>
""", unsafe_allow_html=True)

# ── DB ────────────────────────────────────────────────────────────────────────
DB_PATH = os.path.join(os.path.dirname(__file__), "senwebstats", "data", "senwebstats.db")

@st.cache_resource
def get_conn():
    if not os.path.exists(DB_PATH):
        return None
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def q(sql, params=()):
    conn = get_conn()
    if conn is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(sql, conn, params=params)
    except Exception:
        return pd.DataFrame()

# ── Plotly theme ──────────────────────────────────────────────────────────────
PLOT_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Space Mono, monospace", color="#E8DCC8", size=10),
    xaxis=dict(gridcolor="rgba(201,168,76,0.08)", linecolor="rgba(201,168,76,0.1)",
               tickfont=dict(size=9, color="rgba(232,220,200,0.4)")),
    yaxis=dict(gridcolor="rgba(201,168,76,0.08)", linecolor="rgba(201,168,76,0.1)",
               tickfont=dict(size=9, color="rgba(232,220,200,0.4)")),
    margin=dict(l=20, r=20, t=40, b=20),
)

GOLD_SCALE  = ["#1B4D3E", "#2d6e55", "#C9A84C", "#F0D080", "#FAF8F4"]
CAT_PALETTE = {
    "presse":        "#C9A84C",
    "ecommerce":     "#E74C3C",
    "telephonie":    "#3498DB",
    "banque_finance":"#9B59B6",
    "emploi":        "#2ECC71",
}

# ── Check DB ──────────────────────────────────────────────────────────────────
if get_conn() is None:
    st.markdown("""
    <div class="hero">
        <div class="hero-eyebrow">⚠ Erreur système</div>
        <h1 class="hero-title">
            <span class="line1">BASE DE</span>
            <span class="line2">DONNÉES</span>
            <span class="line3">ABSENTE</span>
        </h1>
        <p class="hero-sub">Lance d'abord : <code>python main.py init</code> puis <code>python main.py crawl</code></p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
n_sites   = q("SELECT COUNT(*) as n FROM sites")["n"].values[0]
n_crawled = q("SELECT COUNT(DISTINCT site_id) as n FROM site_metadata")["n"].values[0]
n_perf    = q("SELECT COUNT(DISTINCT site_id) as n FROM site_performance")["n"].values[0]
n_bl      = q("SELECT COUNT(DISTINCT site_id) as n FROM site_backlinks")["n"].values[0]
avg_seo   = q("SELECT ROUND(AVG(seo_score),0) as v FROM site_performance")["v"].values[0]

# ── HERO ──────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hero">
    <div class="hero-eyebrow">◆ Observatoire Web · Dakar · {pd.Timestamp.now().strftime("%B %Y")}</div>
    <h1 class="hero-title">
        <span class="line1">SEN</span>
        <span class="line2">WEB</span>
        <span class="line3">STATS</span>
    </h1>
    <p class="hero-sub">
        Intelligence numérique pour les sites web sénégalais.
        Presse, e-commerce, télécom & finance — analysés en temps réel.
    </p>
    <div class="hero-tag">Phase 1 · Collecte active · {n_crawled} sites analysés</div>
    <div class="hero-flag">🇸🇳</div>
</div>
""", unsafe_allow_html=True)

# ── KPI CARDS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-grid">
    <div class="kpi-card">
        <div class="kpi-icon">◈</div>
        <div class="kpi-value">{n_sites}</div>
        <div class="kpi-label">Sites suivis</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">◉</div>
        <div class="kpi-value">{n_crawled}</div>
        <div class="kpi-label">Sites crawlés</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">◎</div>
        <div class="kpi-value">{n_perf}</div>
        <div class="kpi-label">Scores perf.</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">◐</div>
        <div class="kpi-value">{n_bl}</div>
        <div class="kpi-label">Backlinks col.</div>
    </div>
    <div class="kpi-card">
        <div class="kpi-icon">◑</div>
        <div class="kpi-value">{int(avg_seo) if avg_seo else "—"}</div>
        <div class="kpi-label">Score SEO moy.</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── TABS ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "01 · Métadonnées",
    "02 · Performance",
    "03 · Backlinks",
    "04 · Comparaison",
])

# ╔════════════════════════════════════════════════════════════════╗
# ║  TAB 1 — MÉTADONNÉES                                         ║
# ╚════════════════════════════════════════════════════════════════╝
with tab1:
    st.markdown("""
    <div class="section-header">
        <div class="section-number">01</div>
        <div class="section-title">Cartographie des sites</div>
        <div class="section-tag">HTML · Structure · SEO technique</div>
    </div>
    """, unsafe_allow_html=True)

    df_meta = q("""
        SELECT s.name, s.domain, s.category,
               sm.status_code, sm.response_time_ms, sm.word_count,
               sm.internal_links_count, sm.external_links_count,
               sm.images_count, sm.has_ssl, sm.has_sitemap, sm.has_robots_txt,
               sm.title, sm.meta_description
        FROM sites s
        LEFT JOIN site_metadata sm ON sm.site_id = s.id
            AND sm.crawled_at = (SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = s.id)
        ORDER BY s.category, s.name
    """)

    if df_meta.empty or df_meta["status_code"].isna().all():
        st.markdown('<div class="custom-alert"><span>Aucune donnée.</span> Lance : <span>python main.py crawl</span></div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([1, 1], gap="large")

        with col1:
            # Répartition catégories
            cat_df = df_meta["category"].value_counts().reset_index()
            cat_df.columns = ["Catégorie", "Sites"]
            colors = [CAT_PALETTE.get(c, "#888") for c in cat_df["Catégorie"]]

            fig = go.Figure(go.Pie(
                labels=cat_df["Catégorie"],
                values=cat_df["Sites"],
                marker=dict(colors=colors, line=dict(color="#0a0a0a", width=3)),
                hole=0.6,
                textfont=dict(family="Space Mono", size=9),
                hovertemplate="<b>%{label}</b><br>%{value} sites<extra></extra>",
            ))
            fig.add_annotation(
                text=f"<b>{n_sites}</b><br><span style='font-size:9px'>SITES</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(family="Playfair Display", size=22, color="#C9A84C"),
                align="center"
            )
            fig.update_layout(**PLOT_THEME, title=dict(
                text="RÉPARTITION PAR CATÉGORIE",
                font=dict(family="Space Mono", size=9, color="rgba(201,168,76,0.6)"),
                x=0, y=0.98
            ), showlegend=True,
            legend=dict(font=dict(family="Space Mono", size=8, color="#E8DCC8"),
                       bgcolor="rgba(0,0,0,0)"))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # Temps de réponse
            df_rt = df_meta.dropna(subset=["response_time_ms"]).copy()
            if not df_rt.empty:
                df_rt = df_rt.sort_values("response_time_ms")
                colors_rt = []
                for v in df_rt["response_time_ms"]:
                    if v < 1000:   colors_rt.append("#2ECC71")
                    elif v < 2000: colors_rt.append("#C9A84C")
                    else:          colors_rt.append("#E74C3C")

                fig2 = go.Figure(go.Bar(
                    x=df_rt["response_time_ms"],
                    y=df_rt["name"],
                    orientation="h",
                    marker=dict(color=colors_rt, line=dict(width=0)),
                    hovertemplate="<b>%{y}</b><br>%{x:.0f} ms<extra></extra>",
                ))
                fig2.update_layout(**PLOT_THEME, title=dict(
                    text="TEMPS DE RÉPONSE (ms)",
                    font=dict(family="Space Mono", size=9, color="rgba(201,168,76,0.6)"),
                    x=0, y=0.98
                ), yaxis=dict(categoryorder="total ascending", tickfont=dict(size=8)))
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

        # Classement liens internes
        st.markdown("""
        <div class="section-header" style="margin-top:1rem">
            <div class="section-number" style="font-size:2rem">↗</div>
            <div class="section-title" style="font-size:1.2rem">Densité de liens internes</div>
        </div>
        """, unsafe_allow_html=True)

        df_links = df_meta.dropna(subset=["internal_links_count"]).sort_values("internal_links_count", ascending=False).head(10)
        max_links = df_links["internal_links_count"].max() if not df_links.empty else 1

        for _, row in df_links.iterrows():
            pct = int(row["internal_links_count"] / max_links * 100) if max_links > 0 else 0
            cat_color = CAT_PALETTE.get(row["category"], "#888")
            st.markdown(f"""
            <div class="rank-row">
                <div class="rank-num">{list(df_links["name"]).index(row["name"]) + 1}</div>
                <div>
                    <div class="rank-name">{row["name"]}</div>
                    <div class="rank-cat" style="color:{cat_color}">{row["category"]}</div>
                </div>
                <div class="rank-bar-container">
                    <div class="rank-bar-fill" style="width:{pct}%"></div>
                </div>
                <div class="rank-value">{int(row["internal_links_count"])}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)

        # Tableau complet
        st.markdown('<p style="font-family:Space Mono,monospace;font-size:0.65rem;letter-spacing:0.2em;color:rgba(201,168,76,0.5);text-transform:uppercase;margin-bottom:1rem">TABLE COMPLÈTE DES DONNÉES</p>', unsafe_allow_html=True)

        df_show = df_meta[["name","category","status_code","response_time_ms",
                            "word_count","has_ssl","has_sitemap"]].copy()
        df_show.columns = ["Site","Catégorie","Status","Temps(ms)","Mots","SSL","Sitemap"]
        df_show["SSL"]     = df_show["SSL"].apply(lambda x: "✓" if x==1 else "✗")
        df_show["Sitemap"] = df_show["Sitemap"].apply(lambda x: "✓" if x==1 else "✗")
        st.dataframe(df_show, use_container_width=True, hide_index=True, height=300)


# ╔════════════════════════════════════════════════════════════════╗
# ║  TAB 2 — PERFORMANCE                                         ║
# ╚════════════════════════════════════════════════════════════════╝
with tab2:
    st.markdown("""
    <div class="section-header">
        <div class="section-number">02</div>
        <div class="section-title">Scores de performance</div>
        <div class="section-tag">PageSpeed · Core Web Vitals · Mobile</div>
    </div>
    """, unsafe_allow_html=True)

    df_perf = q("""
        SELECT s.name, s.category, sp.performance_score, sp.seo_score,
               sp.accessibility_score, sp.best_practices_score,
               sp.lcp_ms, sp.fcp_ms, sp.ttfb_ms, sp.cls_score, sp.device
        FROM site_performance sp JOIN sites s ON s.id = sp.site_id
        WHERE sp.measured_at = (SELECT MAX(measured_at) FROM site_performance WHERE site_id = sp.site_id)
        ORDER BY sp.performance_score DESC
    """)

    if df_perf.empty:
        st.markdown('<div class="custom-alert"><span>Aucune donnée.</span> Lance : <span>python main.py perf</span> ou <span>python local_performance_collector.py</span></div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2, gap="large")

        with col1:
            top10 = df_perf.nlargest(10, "performance_score")
            colors_p = []
            for v in top10["performance_score"]:
                if v >= 90:  colors_p.append("#2ECC71")
                elif v >= 50: colors_p.append("#C9A84C")
                else:         colors_p.append("#E74C3C")

            fig = go.Figure(go.Bar(
                x=top10["performance_score"],
                y=top10["name"],
                orientation="h",
                marker=dict(color=colors_p, line=dict(width=0)),
                hovertemplate="<b>%{y}</b><br>Score: %{x}<extra></extra>",
            ))
            fig.update_layout(**PLOT_THEME,
                title=dict(text="TOP 10 · PERFORMANCE",
                          font=dict(family="Space Mono", size=9, color="rgba(201,168,76,0.6)"),
                          x=0),
                xaxis=dict(**PLOT_THEME["xaxis"], range=[0, 100]),
                yaxis=dict(**PLOT_THEME["yaxis"], categoryorder="total ascending", tickfont=dict(size=8)))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            top10s = df_perf.nlargest(10, "seo_score")
            fig2 = go.Figure(go.Bar(
                x=top10s["seo_score"],
                y=top10s["name"],
                orientation="h",
                marker=dict(
                    color=top10s["seo_score"],
                    colorscale=[[0,"#E74C3C"],[0.5,"#C9A84C"],[1,"#2ECC71"]],
                    line=dict(width=0)
                ),
                hovertemplate="<b>%{y}</b><br>SEO: %{x}<extra></extra>",
            ))
            fig2.update_layout(**PLOT_THEME,
                title=dict(text="TOP 10 · SEO",
                          font=dict(family="Space Mono", size=9, color="rgba(201,168,76,0.6)"),
                          x=0),
                xaxis=dict(**PLOT_THEME["xaxis"], range=[0, 100]),
                yaxis=dict(**PLOT_THEME["yaxis"], categoryorder="total ascending", tickfont=dict(size=8)))
            st.plotly_chart(fig2, use_container_width=True)

        # Scatter performance vs SEO
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
        fig3 = px.scatter(
            df_perf, x="performance_score", y="seo_score",
            color="category", text="name", size_max=15,
            color_discrete_map=CAT_PALETTE,
            labels={"performance_score": "Score Performance", "seo_score": "Score SEO"},
        )
        fig3.update_traces(textposition="top center", textfont=dict(size=8, family="Space Mono"))
        fig3.update_layout(**PLOT_THEME,
            title=dict(text="MATRICE PERFORMANCE × SEO — Positionnement des sites",
                      font=dict(family="Space Mono", size=9, color="rgba(201,168,76,0.6)"), x=0),
            height=450)
        st.plotly_chart(fig3, use_container_width=True)

        # Core Web Vitals table
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
        st.markdown('<p style="font-family:Space Mono,monospace;font-size:0.65rem;letter-spacing:0.2em;color:rgba(201,168,76,0.5);text-transform:uppercase;margin-bottom:1rem">CORE WEB VITALS · Seuils : LCP &lt; 2500ms · FCP &lt; 1800ms · TTFB &lt; 800ms</p>', unsafe_allow_html=True)
        df_cwv = df_perf[["name","lcp_ms","fcp_ms","ttfb_ms","cls_score"]].copy()
        df_cwv.columns = ["Site","LCP (ms)","FCP (ms)","TTFB (ms)","CLS"]
        st.dataframe(df_cwv.round(1), use_container_width=True, hide_index=True)


# ╔════════════════════════════════════════════════════════════════╗
# ║  TAB 3 — BACKLINKS                                           ║
# ╚════════════════════════════════════════════════════════════════╝
with tab3:
    st.markdown("""
    <div class="section-header">
        <div class="section-number">03</div>
        <div class="section-title">Autorité & Backlinks</div>
        <div class="section-tag">CommonCrawl · Domaines référents · Indexation</div>
    </div>
    """, unsafe_allow_html=True)

    df_bl = q("""
        SELECT s.name, s.category, s.domain,
               sb.total_backlinks, sb.referring_domains, sb.backlinks_change
        FROM site_backlinks sb JOIN sites s ON s.id = sb.site_id
        WHERE sb.collected_at = (SELECT MAX(collected_at) FROM site_backlinks WHERE site_id = sb.site_id)
        ORDER BY sb.total_backlinks DESC
    """)

    if df_bl.empty:
        st.markdown('<div class="custom-alert"><span>Aucune donnée.</span> Lance : <span>python main.py backlinks</span></div>', unsafe_allow_html=True)
    else:
        col1, col2 = st.columns(2, gap="large")

        with col1:
            top_bl = df_bl.nlargest(10, "total_backlinks")
            fig = go.Figure(go.Bar(
                x=top_bl["total_backlinks"],
                y=top_bl["name"],
                orientation="h",
                marker=dict(
                    color=[CAT_PALETTE.get(c, "#888") for c in top_bl["category"]],
                    line=dict(width=0)
                ),
                hovertemplate="<b>%{y}</b><br>%{x} pages indexées<extra></extra>",
            ))
            fig.update_layout(**PLOT_THEME,
                title=dict(text="PAGES INDEXÉES (CommonCrawl)",
                          font=dict(family="Space Mono", size=9, color="rgba(201,168,76,0.6)"), x=0),
                yaxis=dict(**PLOT_THEME["yaxis"], categoryorder="total ascending", tickfont=dict(size=8)))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            top_rd = df_bl.nlargest(10, "referring_domains")
            fig2 = go.Figure(go.Bar(
                x=top_rd["referring_domains"],
                y=top_rd["name"],
                orientation="h",
                marker=dict(color="#C9A84C", line=dict(width=0),
                           opacity=[0.4 + 0.6 * (i / len(top_rd)) for i in range(len(top_rd))]),
                hovertemplate="<b>%{y}</b><br>%{x} domaines référents<extra></extra>",
            ))
            fig2.update_layout(**PLOT_THEME,
                title=dict(text="DOMAINES RÉFÉRENTS",
                          font=dict(family="Space Mono", size=9, color="rgba(201,168,76,0.6)"), x=0),
                yaxis=dict(**PLOT_THEME["yaxis"], categoryorder="total ascending", tickfont=dict(size=8)))
            st.plotly_chart(fig2, use_container_width=True)

        # Classement textuel élégant
        st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div class="section-header" style="margin-top:0">
            <div class="section-number" style="font-size:2rem">↗</div>
            <div class="section-title" style="font-size:1.2rem">Classement par autorité</div>
        </div>
        """, unsafe_allow_html=True)

        max_bl = df_bl["total_backlinks"].max() if not df_bl.empty else 1
        for i, (_, row) in enumerate(df_bl.head(10).iterrows(), 1):
            pct = int(row["total_backlinks"] / max_bl * 100) if max_bl > 0 else 0
            change = row["backlinks_change"]
            change_str = f"+{change}" if change > 0 else str(change)
            change_color = "#2ECC71" if change > 0 else ("#E74C3C" if change < 0 else "rgba(232,220,200,0.3)")
            cat_color = CAT_PALETTE.get(row["category"], "#888")
            st.markdown(f"""
            <div class="rank-row">
                <div class="rank-num">{i}</div>
                <div style="flex:1">
                    <div class="rank-name">{row["name"]}</div>
                    <div style="display:flex;gap:1rem;align-items:center;margin-top:0.2rem">
                        <div class="rank-cat" style="color:{cat_color}">{row["category"]}</div>
                        <div style="font-family:Space Mono,monospace;font-size:0.55rem;color:{change_color}">{change_str}</div>
                    </div>
                </div>
                <div class="rank-bar-container">
                    <div class="rank-bar-fill" style="width:{pct}%"></div>
                </div>
                <div class="rank-value">{int(row["total_backlinks"])}</div>
            </div>
            """, unsafe_allow_html=True)


# ╔════════════════════════════════════════════════════════════════╗
# ║  TAB 4 — COMPARAISON                                         ║
# ╚════════════════════════════════════════════════════════════════╝
with tab4:
    st.markdown("""
    <div class="section-header">
        <div class="section-number">04</div>
        <div class="section-title">Comparaison directe</div>
        <div class="section-tag">Multi-métriques · Radar · Analyse concurrentielle</div>
    </div>
    """, unsafe_allow_html=True)

    sites_list = q("SELECT name FROM sites ORDER BY name")
    if not sites_list.empty:
        col_sel, col_metric = st.columns([2, 1], gap="large")
        with col_sel:
            selected = st.multiselect(
                "Sélectionne jusqu'à 8 sites",
                options=sites_list["name"].tolist(),
                default=sites_list["name"].tolist()[:5],
                max_selections=8,
            )
        with col_metric:
            metric_map = {
                "Performance": "performance_score",
                "SEO": "seo_score",
                "Pages indexées": "total_backlinks",
                "Temps réponse": "response_time_ms",
                "Mots (page)": "word_count",
            }
            selected_metrics = st.multiselect(
                "Métriques",
                list(metric_map.keys()),
                default=["Performance", "SEO"],
            )

        if selected:
            ph = ",".join(["?" for _ in selected])
            df_cmp = q(f"""
                SELECT s.name, s.category,
                       sm.word_count, sm.response_time_ms,
                       sp.performance_score, sp.seo_score,
                       sb.total_backlinks, sb.referring_domains
                FROM sites s
                LEFT JOIN site_metadata sm ON sm.site_id = s.id
                    AND sm.crawled_at = (SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = s.id)
                LEFT JOIN site_performance sp ON sp.site_id = s.id
                    AND sp.measured_at = (SELECT MAX(measured_at) FROM site_performance WHERE site_id = s.id)
                LEFT JOIN site_backlinks sb ON sb.site_id = s.id
                    AND sb.collected_at = (SELECT MAX(collected_at) FROM site_backlinks WHERE site_id = s.id)
                WHERE s.name IN ({ph})
            """, tuple(selected))

            if not df_cmp.empty and selected_metrics:
                metric_cols = [metric_map[m] for m in selected_metrics]

                # Bar chart groupé
                fig = go.Figure()
                for m_label, m_col in zip(selected_metrics, metric_cols):
                    df_m = df_cmp[["name", m_col]].dropna()
                    fig.add_trace(go.Bar(
                        name=m_label,
                        x=df_m["name"],
                        y=df_m[m_col],
                        hovertemplate=f"<b>%{{x}}</b><br>{m_label}: %{{y:.1f}}<extra></extra>",
                    ))

                fig.update_layout(**PLOT_THEME,
                    barmode="group",
                    title=dict(text="COMPARAISON MULTI-MÉTRIQUES",
                              font=dict(family="Space Mono", size=9, color="rgba(201,168,76,0.6)"), x=0),
                    xaxis=dict(**PLOT_THEME["xaxis"], tickangle=-20, tickfont=dict(size=8)),
                    height=400,
                    legend=dict(font=dict(family="Space Mono", size=8, color="#E8DCC8"),
                               bgcolor="rgba(0,0,0,0)"))
                st.plotly_chart(fig, use_container_width=True)

                # Radar chart si performance + SEO disponibles
                df_radar = df_cmp.dropna(subset=["performance_score", "seo_score"])
                if not df_radar.empty and len(df_radar) > 1:
                    st.markdown('<div class="gold-divider"></div>', unsafe_allow_html=True)
                    radar_cats = ["Performance", "SEO", "Pages indexées (norm.)", "Vitesse (inv.)"]

                    def norm(series, invert=False):
                        mx = series.max()
                        mn = series.min()
                        if mx == mn: return [50] * len(series)
                        n = [(v - mn) / (mx - mn) * 100 for v in series]
                        return [100 - v for v in n] if invert else n

                    fig_r = go.Figure()
                    p_norm  = norm(df_radar["performance_score"])
                    s_norm  = norm(df_radar["seo_score"])
                    bl_norm = norm(df_radar["total_backlinks"].fillna(0))
                    rt_norm = norm(df_radar["response_time_ms"].fillna(3000), invert=True)

                    palette = ["#C9A84C","#E74C3C","#3498DB","#2ECC71","#9B59B6","#F39C12","#1ABC9C","#E67E22"]
                    for i, row in enumerate(df_radar.itertuples()):
                        vals = [p_norm[i], s_norm[i], bl_norm[i], rt_norm[i]]
                        vals.append(vals[0])
                        fig_r.add_trace(go.Scatterpolar(
                            r=vals,
                            theta=radar_cats + [radar_cats[0]],
                            fill="toself",
                            name=row.name,
                            line=dict(color=palette[i % len(palette)], width=2),
                            fillcolor=palette[i % len(palette)].replace("#", "rgba(") + ",0.08)",
                            opacity=0.8,
                        ))

                    fig_r.update_layout(
                        **PLOT_THEME,
                        polar=dict(
                            radialaxis=dict(visible=True, range=[0, 100],
                                          gridcolor="rgba(201,168,76,0.1)",
                                          tickfont=dict(size=7, color="rgba(232,220,200,0.3)")),
                            angularaxis=dict(gridcolor="rgba(201,168,76,0.1)",
                                           tickfont=dict(family="Space Mono", size=8, color="rgba(232,220,200,0.5)"))
                        ),
                        title=dict(text="RADAR — PROFIL COMPARATIF (normalisé)",
                                  font=dict(family="Space Mono", size=9, color="rgba(201,168,76,0.6)"), x=0),
                        legend=dict(font=dict(family="Space Mono", size=8, color="#E8DCC8"),
                                   bgcolor="rgba(0,0,0,0)"),
                        height=450,
                    )
                    st.plotly_chart(fig_r, use_container_width=True)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
    <div>
        <div class="footer-logo">SenWebStats</div>
        <div style="font-family:Space Mono,monospace;font-size:0.6rem;color:rgba(201,168,76,0.4);margin-top:0.5rem">
            L'observatoire numérique du Sénégal
        </div>
    </div>
    <div class="footer-info">
        Sources : Scraping HTML · Google PageSpeed API · CommonCrawl Index<br>
        Mise à jour : {pd.Timestamp.now().strftime("%d %B %Y · %H:%M")}<br>
        Phase 1 active · Phase 2 (estimation trafic) à venir
    </div>
</div>
""", unsafe_allow_html=True)