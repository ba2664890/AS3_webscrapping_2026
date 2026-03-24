"""
SenWebStats — Dashboard v5 (Dash)
==================================
Lancer depuis le dossier senwebstats/ :
    python app/dashboard.py
Ou avec rechargement automatique :
    python app/dashboard.py  (debug=True en bas du fichier)
URL : http://localhost:8050
"""

import sys
import os
import json
import math
import io
from datetime import datetime
from functools import lru_cache

import pandas as pd
import sqlite3

import dash
from dash import dcc, html, Input, Output, State, callback, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px

# ── Chemin vers le module models ──────────────────────────────
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)

from models.ctr_model import (
    compute_ctr_scores,
    CTR_CURVES,
    DEFAULT_CURVE,
    CATEGORY_BASE,
    CATEGORY_LABELS,
    AWR_2023,
    score_to_position,
    ctr_at_position,
    SemrushClient,
    DataForSEOClient,
)

# ─────────────────────────────────────────────────────────────
# INITIALISATION APP
# ─────────────────────────────────────────────────────────────
GOOGLE_FONTS = (
    "https://fonts.googleapis.com/css2?"
    "family=Inter:wght@300;400;500;600;700;800"
    "&family=DM+Mono:wght@400;500"
    "&family=Sora:wght@400;600;700;800"
    "&display=swap"
)

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP, GOOGLE_FONTS],
    suppress_callback_exceptions=True,
    title="SenWebStats — Observatoire Web Sénégal",
    meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}],
)
server = app.server  # pour déploiement Gunicorn / cloud

# ─────────────────────────────────────────────────────────────
# CONSTANTES VISUELLES
# ─────────────────────────────────────────────────────────────
COLORS = {
    "presse":        "#00dc82",
    "ecommerce":     "#4f8ef7",
    "telephonie":    "#fbbf24",
    "banque_finance":"#a78bfa",
    "emploi":        "#34d399",
}

SCORE_COLOR = lambda v: "#00dc82" if v >= 60 else "#fbbf24" if v >= 40 else "#ef4444"

# Thème Plotly — dark navy
PT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Mono, monospace", color="#6b88a8", size=10),
    margin=dict(l=8, r=8, t=40, b=8),
    hoverlabel=dict(
        bgcolor="#132338",
        font_size=12,
        font_family="DM Mono, monospace",
        bordercolor="#1e3049",
    ),
)
PT_AXIS = dict(
    gridcolor="#172335",
    linecolor="#172335",
    tickfont=dict(size=9, color="#6b88a8"),
    zeroline=False,
)
PT_TITLE = lambda t: dict(text=t, font=dict(size=9, color="#6b88a8", family="DM Mono"), x=0)

# ─────────────────────────────────────────────────────────────
# BASE DE DONNÉES
# ─────────────────────────────────────────────────────────────
def find_db(name: str) -> str | None:
    base = os.path.dirname(os.path.abspath(__file__))
    for p in [
        os.path.join(base, "..", "data", name),
        os.path.join(base, "data", name),
        os.path.join(os.getcwd(), "data", name),
        os.path.join(os.getcwd(), "senwebstats", "data", name),
        os.path.join(_ROOT, "data", name),
    ]:
        full = os.path.abspath(p)
        if os.path.exists(full):
            return full
    return None


def get_conn() -> sqlite3.Connection | None:
    p = find_db("senwebstats.db")
    if not p:
        return None
    c = sqlite3.connect(p, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c


def qry(sql: str, params=()) -> pd.DataFrame:
    conn = get_conn()
    if conn is None:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    except Exception:
        conn.close()
        return pd.DataFrame()


# ─────────────────────────────────────────────────────────────
# MODÈLE DE SCORING
# ─────────────────────────────────────────────────────────────
def normalize(s: pd.Series, invert: bool = False) -> pd.Series:
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series([50.0] * len(s), index=s.index)
    n = (s - mn) / (mx - mn) * 100
    return (100 - n) if invert else n


@lru_cache(maxsize=1)
def compute_scores_cached() -> pd.DataFrame:
    """Chargement + scoring complet — mis en cache au démarrage."""
    sites = qry("SELECT id, name, domain, category FROM sites ORDER BY category, name")
    if sites.empty:
        return pd.DataFrame()

    meta = qry("""
        SELECT site_id, response_time_ms, word_count,
               internal_links_count, external_links_count,
               images_count, has_ssl, has_sitemap, has_robots_txt, status_code
        FROM site_metadata sm
        WHERE crawled_at = (
            SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = sm.site_id
        )
    """)

    perf = qry("""
        SELECT site_id, performance_score, seo_score, accessibility_score,
               best_practices_score, lcp_ms, fcp_ms, ttfb_ms, cls_score
        FROM site_performance sp
        WHERE measured_at = (
            SELECT MAX(measured_at) FROM site_performance WHERE site_id = sp.site_id
        )
    """)

    bl = qry("""
        SELECT site_id, total_backlinks, referring_domains, backlinks_change
        FROM site_backlinks sb
        WHERE collected_at = (
            SELECT MAX(collected_at) FROM site_backlinks WHERE site_id = sb.site_id
        )
    """)

    df = sites.copy()
    for other, key in [(meta, "site_id"), (perf, "site_id"), (bl, "site_id")]:
        if not other.empty:
            df = df.merge(other, left_on="id", right_on=key, how="left")
            df = df.drop(columns=[c for c in ["site_id"] if c in df.columns])

    # Fillna robuste
    fill = {
        "total_backlinks": 0, "referring_domains": 0, "backlinks_change": 0,
        "seo_score": 50, "performance_score": 50, "accessibility_score": 50,
        "best_practices_score": 50, "response_time_ms": 3000,
        "has_ssl": 0, "has_sitemap": 0, "has_robots_txt": 0,
        "word_count": 0, "internal_links_count": 0, "external_links_count": 0,
        "lcp_ms": 0, "fcp_ms": 0, "ttfb_ms": 0, "cls_score": 0,
    }
    for col, val in fill.items():
        if col in df.columns:
            df[col] = df[col].fillna(val)
        else:
            df[col] = val

    # Scores
    df["score_autorite"]  = (
        normalize(df["total_backlinks"]) * 0.6 +
        normalize(df["referring_domains"]) * 0.4
    ).round(1)

    df["score_qualite"] = (
        df["seo_score"] * 0.40 +
        df["performance_score"] * 0.35 +
        df["accessibility_score"] * 0.25
    ).round(1)

    df["score_technique"] = (
        normalize(df["response_time_ms"], invert=True) * 0.40 +
        df["has_ssl"] * 100 * 0.20 +
        df["has_sitemap"] * 100 * 0.15 +
        normalize(df["word_count"]) * 0.25
    ).round(1)

    df["score_global"] = (
        df["score_autorite"]  * 0.45 +
        df["score_qualite"]   * 0.35 +
        df["score_technique"] * 0.20
    ).round(1)

    # Trafic score-based (modèle de base, conservé pour comparaison)
    def trafic_score(row):
        base = CATEGORY_BASE.get(row["category"], 50000)
        return int(base * (row["score_global"] / 100) ** 1.5)
    df["trafic_score"] = df.apply(trafic_score, axis=1)

    # Modèle CTR (proxy scientifique)
    df = compute_ctr_scores(df, DEFAULT_CURVE)

    # Trafic final = on expose les deux pour comparaison
    df["trafic_estime"] = df["trafic_ctr"]

    return df.sort_values("score_global", ascending=False).reset_index(drop=True)


# ─────────────────────────────────────────────────────────────
# DONNÉES GLOBALES (chargées une fois au démarrage)
# ─────────────────────────────────────────────────────────────
df_all = compute_scores_cached()

n_sites   = int(qry("SELECT COUNT(*) as n FROM sites")["n"].iloc[0]) if not qry("SELECT COUNT(*) as n FROM sites").empty else 0
n_crawled = int(qry("SELECT COUNT(DISTINCT site_id) as n FROM site_metadata")["n"].iloc[0]) if not qry("SELECT COUNT(DISTINCT site_id) as n FROM site_metadata").empty else 0
n_perf    = int(qry("SELECT COUNT(DISTINCT site_id) as n FROM site_performance")["n"].iloc[0]) if not qry("SELECT COUNT(DISTINCT site_id) as n FROM site_performance").empty else 0
n_bl      = int(qry("SELECT COUNT(DISTINCT site_id) as n FROM site_backlinks")["n"].iloc[0]) if not qry("SELECT COUNT(DISTINCT site_id) as n FROM site_backlinks").empty else 0
total_tr  = int(df_all["trafic_estime"].sum()) if not df_all.empty else 0
avg_sc    = round(df_all["score_global"].mean(), 1) if not df_all.empty else 0
now       = datetime.now().strftime("%d %b %Y · %H:%M")
categories = sorted(df_all["category"].unique().tolist()) if not df_all.empty else []

# Semrush / DataForSEO configurés ?
_sem_ok = SemrushClient().is_configured()
_dfs_ok = DataForSEOClient().is_configured()


# ─────────────────────────────────────────────────────────────
# HELPERS VISUELS
# ─────────────────────────────────────────────────────────────
def fmt(n) -> str:
    try:
        return f"{int(n):,}".replace(",", "\u202f")
    except Exception:
        return "—"


def kpi_card(label: str, value: str, sub: str, color: str) -> html.Div:
    return html.Div([
        html.Div(className="kpi-bar", style={
            "background": f"linear-gradient(90deg, {color} 0%, transparent 100%)"
        }),
        html.Div(label, className="kpi-label"),
        html.Div(value, className="kpi-value", style={"color": color}),
        html.Div(sub, className="kpi-sub"),
    ], className="kpi")


def pill(text: str, style: str = "gray") -> html.Div:
    return html.Div([
        html.Div(className="pill-dot"),
        text,
    ], className=f"pill pill-{style}")


def section_label(text: str) -> html.Div:
    return html.Div(text, className="section-label")


def page_header(eyebrow: str, title_parts: list, subtitle: str, right_meta: str = "") -> html.Div:
    """
    eyebrow    : texte monospace vert caps
    title_parts: liste alternée de (texte, est_accentué)
                 ex: [("Scoring & ", False), ("Trafic CTR", True)]
    subtitle   : sous-titre grisé
    right_meta : texte meta aligné à droite
    """
    title_children = []
    for part, accented in title_parts:
        if accented:
            title_children.append(html.Em(part))
        else:
            title_children.append(part)

    right_block = html.Div([
        html.Div(right_meta, className="ph-meta") if right_meta else None,
    ], className="ph-right") if right_meta else html.Span()

    return html.Div([
        html.Div([
            html.Div(eyebrow, className="ph-eyebrow"),
            html.Div(title_children, className="ph-title"),
            html.Div(subtitle, className="ph-subtitle"),
        ]),
        right_block,
    ], className="page-header")


def empty_state(msg: str) -> html.Div:
    return html.Div(msg, className="info-box")


# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("/",           "Vue d'ensemble"),
    ("/scoring",    "Scoring & Trafic CTR"),
    ("/metadata",   "Métadonnées"),
    ("/performance","Performance PageSpeed"),
    ("/backlinks",  "Backlinks & Autorité"),
    ("/comparison", "Comparaison"),
    ("/trends",     "Veille & Tendances"),
    ("/export",     "Rapport & Export"),
]

api_status = []
if _sem_ok:
    api_status.append(pill("Semrush API actif", "teal"))
if _dfs_ok:
    api_status.append(pill("DataForSEO actif", "green"))
if not _sem_ok and not _dfs_ok:
    api_status.append(pill("APIs non config. — proxy CTR", "amber"))


def build_sidebar() -> html.Div:
    nav_links = [
        dcc.Link(
            label,
            href=href,
            id=f"nav-{i}",
            className="nav-item",
        )
        for i, (href, label) in enumerate(NAV_ITEMS)
    ]

    cat_options = [{"label": "Toutes catégories", "value": "Toutes"}] + [
        {"label": CATEGORY_LABELS.get(c, c), "value": c} for c in categories
    ]

    api_badge = pill("Semrush actif", "green") if _sem_ok else (
        pill("DataForSEO actif", "teal") if _dfs_ok else
        pill("Proxy CTR · AWR 2023", "amber")
    )

    return html.Div([
        # ── Marque ──────────────────────────────────────────
        html.Div([
            html.Div([
                "Sen", html.Span("Web", style={"color": "#00dc82"}), "Stats"
            ], className="brand-name"),
            html.Div([
                "The Observatory",
                html.Br(),
                "National Digital Narrative",
            ], className="brand-sub"),
        ], className="sidebar-brand"),

        # ── Navigation ──────────────────────────────────────
        html.Div("Navigation", className="sidebar-section-label"),
        html.Div(nav_links, className="sidebar-nav"),

        html.Div(className="sidebar-divider"),

        # ── Filtre ──────────────────────────────────────────
        html.Div([
            html.Label("Secteur", className="filter-label"),
            dcc.Dropdown(
                id="cat-dropdown",
                options=cat_options,
                value="Toutes",
                clearable=False,
            ),
        ], className="sidebar-filter"),

        # ── Upgrade ─────────────────────────────────────────
        html.A("Upgrade Access", href="#", className="btn-upgrade"),

        html.Div(className="sidebar-divider"),

        # ── API status ──────────────────────────────────────
        html.Div("Data Sources", className="sidebar-section-label"),
        html.Div([api_badge], style={"padding": "0 0.8rem 0.8rem"}),

        # ── Footer ──────────────────────────────────────────
        html.Div([
            html.Div(f"{n_sites} sites · 5 secteurs", className="sidebar-footer-line"),
            html.Div("Modèle CTR · AWR 2023", className="sidebar-footer-line"),
            html.Div(now, className="sidebar-footer-line"),
        ], className="sidebar-footer"),
    ], className="sidebar")


# ─────────────────────────────────────────────────────────────
# LAYOUT PRINCIPAL
# ─────────────────────────────────────────────────────────────
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    dcc.Store(id="cat-store", data="Toutes"),
    build_sidebar(),
    html.Div(id="page-content", className="main-content"),
], className="app-wrapper")


# ─────────────────────────────────────────────────────────────
# CALLBACKS — Navigation active state
# ─────────────────────────────────────────────────────────────
@app.callback(
    [Output(f"nav-{i}", "className") for i in range(len(NAV_ITEMS))],
    Input("url", "pathname"),
)
def update_nav_active(pathname):
    pathname = pathname or "/"
    return [
        "nav-item active" if pathname == href else "nav-item"
        for href, _ in NAV_ITEMS
    ]


@app.callback(
    Output("cat-store", "data"),
    Input("cat-dropdown", "value"),
)
def update_cat(val):
    return val or "Toutes"


# ─────────────────────────────────────────────────────────────
# CALLBACK — Routing
# ─────────────────────────────────────────────────────────────
@app.callback(
    Output("page-content", "children"),
    [Input("url", "pathname"), Input("cat-store", "data")],
)
def route(pathname, cat):
    pathname = pathname or "/"
    df_f = df_all if cat == "Toutes" else df_all[df_all["category"] == cat]

    routes = {
        "/":           lambda: page_overview(df_all, df_f, cat),
        "/scoring":    lambda: page_scoring(df_all, df_f, cat),
        "/metadata":   lambda: page_metadata(df_f, cat),
        "/performance":lambda: page_performance(df_f, cat),
        "/backlinks":  lambda: page_backlinks(df_f, cat),
        "/comparison": lambda: page_comparison(df_all),
        "/trends":     lambda: page_trends(df_all, df_f),
        "/export":     lambda: page_export(df_all),
    }
    fn = routes.get(pathname, routes["/"])
    return fn()


# ═════════════════════════════════════════════════════════════
# PAGE 1 — VUE D'ENSEMBLE
# ═════════════════════════════════════════════════════════════
def page_overview(df_all: pd.DataFrame, df_f: pd.DataFrame, cat: str) -> html.Div:
    if df_all.empty:
        return html.Div([empty_state("Base de données introuvable. Vérifier le chemin vers senwebstats.db")])

    # ── KPIs ──────────────────────────────────────────────────
    kpis = html.Div([
        kpi_card("Sites suivis",        str(n_sites),    "5 catégories · Sénégal", "#0d9488"),
        kpi_card("Trafic CTR estimé",   fmt(total_tr),   "visites / mois",          "#2563eb"),
        kpi_card("Score moyen",         f"{avg_sc}",     "/ 100 pts · score global","#16a34a"),
        kpi_card("Avec PageSpeed",      str(n_perf),     "sites analysés Lighthouse","#d97706"),
        kpi_card("Avec backlinks",      str(n_bl),       "sites CommonCrawl",        "#7c3aed"),
    ], className="kpi-grid")

    # ── Status pills ──────────────────────────────────────────
    pills = html.Div([
        pill("Métadonnées collectées" if n_crawled > 0 else "Métadonnées en attente",
             "green" if n_crawled > 0 else "gray"),
        pill("PageSpeed disponible" if n_perf > 0 else "PageSpeed en attente",
             "teal" if n_perf > 0 else "gray"),
        pill("Backlinks disponibles" if n_bl > 0 else "Backlinks en attente",
             "green" if n_bl > 0 else "gray"),
        pill("Scoring CTR calculé" if not df_all.empty else "Scoring en cours",
             "teal" if not df_all.empty else "amber"),
        pill("Semrush API" if _sem_ok else "Semrush non configuré",
             "blue" if _sem_ok else "gray"),
        pill("DataForSEO API" if _dfs_ok else "DataForSEO non configuré",
             "purple" if _dfs_ok else "gray"),
    ], className="status-row")

    # ── Classement Top 15 ─────────────────────────────────────
    mx = df_all["score_global"].max() or 1
    rank_rows = []
    for rank, row in df_all.head(15).iterrows():
        pct   = int(row["score_global"] / mx * 100)
        color = SCORE_COLOR(row["score_global"])
        cat_c = COLORS.get(row["category"], "#888")
        rank_rows.append(html.Div([
            html.Div(f"{rank+1:02d}", className="rank-num"),
            html.Div([
                html.Div(row["name"], className="rank-name"),
                html.Div(row["category"], className="rank-cat", style={"color": cat_c}),
                html.Div(html.Div(className="rank-bar",
                    style={"width": f"{pct}%", "background": color}),
                    className="rank-bar-wrap"),
            ]),
            html.Div([
                html.Span(f"{row['score_global']:.1f}", style={"color": color}),
                html.Span("/100", style={"color": "#9ca3af", "fontSize": "0.58rem"}),
            ], className="rank-score"),
            html.Div([
                fmt(row["trafic_estime"]),
                html.Span(" /mois", style={"color": "#9ca3af", "fontSize": "0.58rem"}),
            ], className="rank-traffic"),
        ], className="rank-row"))

    ranking_card = html.Div([
        html.Div([
            html.Span("Site · Catégorie"),
            html.Span("Score · Trafic/mois"),
        ], className="card-header"),
        html.Div(rank_rows),
    ], className="card")

    # ── Graphiques droite ─────────────────────────────────────
    # Trafic par catégorie
    cat_sum = df_all.groupby("category")["trafic_estime"].sum().reset_index().sort_values("trafic_estime")
    fig_cat = go.Figure(go.Bar(
        x=cat_sum["trafic_estime"], y=cat_sum["category"], orientation="h",
        marker=dict(color=[COLORS.get(c, "#888") for c in cat_sum["category"]],
                    opacity=0.85, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>%{x:,.0f} visites/mois<extra></extra>",
    ))
    fig_cat.update_layout(**PT, height=190,
        title=PT_TITLE("TRAFIC CTR ESTIMÉ PAR CATÉGORIE"),
        yaxis=dict(**PT_AXIS, tickfont=dict(size=9)),
        xaxis=dict(**PT_AXIS),
    )

    # Donut Top 8
    top8 = df_all.head(8)
    fig_donut = go.Figure(go.Pie(
        labels=top8["name"], values=top8["trafic_estime"],
        marker=dict(colors=[COLORS.get(c, "#888") for c in top8["category"]],
                    line=dict(color="#fff", width=2)),
        hole=0.55,
        textfont=dict(family="DM Mono", size=8),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f} visites<br>%{percent}<extra></extra>",
    ))
    fig_donut.update_layout(**PT, height=230, showlegend=False, margin=dict(l=0, r=0, t=28, b=0),
        title=PT_TITLE("PART DE TRAFIC — TOP 8 SITES"))

    # Boxplot scores par catégorie
    fig_box = go.Figure()
    for cat_k in df_all["category"].unique():
        dc = df_all[df_all["category"] == cat_k]
        fig_box.add_trace(go.Box(
            y=dc["score_global"], name=cat_k,
            marker_color=COLORS.get(cat_k, "#888"),
            line=dict(width=1.5),
            fillcolor=COLORS.get(cat_k, "#888") + "22",
            hovertemplate="%{y:.1f}<extra>" + cat_k + "</extra>",
        ))
    fig_box.update_layout(**PT, height=230, showlegend=False,
        title=PT_TITLE("DISTRIBUTION SCORES GLOBAUX PAR CATÉGORIE"),
        yaxis=dict(**PT_AXIS, range=[0, 100]),
        xaxis=dict(**PT_AXIS),
    )

    right_col = html.Div([
        section_label("Trafic estimé par catégorie"),
        dcc.Graph(figure=fig_cat, config={"displayModeBar": False}),
        section_label("Part de marché — Top 8"),
        dcc.Graph(figure=fig_donut, config={"displayModeBar": False}),
        section_label("Distribution des scores"),
        dcc.Graph(figure=fig_box, config={"displayModeBar": False}),
    ])

    return html.Div([
        page_header(
            "Live Observatory · Sénégal",
            [("National ", False), ("Narrative", True)],
            f"Analyse de {n_sites} sites · presse · e-commerce · télécom · finance · emploi",
            f"Dakar · Sénégal\nModèle CTR AWR 2023\n{now}",
        ),
        pills,
        kpis,
        section_label("Classement global — Top 15"),
        dbc.Row([
            dbc.Col(ranking_card, width=7),
            dbc.Col(right_col, width=5),
        ], className="g-4"),
    ], className="page-wrap")


# ═════════════════════════════════════════════════════════════
# PAGE 2 — SCORING & TRAFIC CTR
# ═════════════════════════════════════════════════════════════
def page_scoring(df_all: pd.DataFrame, df_f: pd.DataFrame, cat: str) -> html.Div:
    if df_f.empty:
        return html.Div([empty_state("Aucune donnée.")], className="page-wrap")

    # ── Explication du modèle CTR ────────────────────────────
    ctr_info = html.Div([
        html.Div("Modèle de trafic CTR", className="ctr-callout-label"),
        html.Div([
            html.Strong("Comment c'est calculé : "),
            "Pour chaque site, le modèle mappe son score global sur une position SERP estimée ",
            "via une courbe exponentielle calibrée. Le trafic est la somme : ",
            html.Code("Σ volume_kw × CTR(position)"),
            " sur le pool de mots-clés de sa catégorie. Les requêtes navigationnelles ",
            "(marque du site) bénéficient d'un multiplicateur ×2.8. ",
            html.Strong("Source CTR : AWR 2023 (blended desktop+mobile)."),
        ], className="ctr-callout-text"),
    ], className="ctr-callout", style={"marginBottom": "1.5rem"})

    # ── Scatter autorité vs trafic ───────────────────────────
    fig_scatter = go.Figure()
    for cat_k in df_f["category"].unique():
        dc = df_f[df_f["category"] == cat_k]
        fig_scatter.add_trace(go.Scatter(
            x=dc["score_autorite"], y=dc["trafic_estime"],
            mode="markers+text", name=cat_k,
            text=dc["name"],
            textposition="top center",
            textfont=dict(size=8, color="#6b7280"),
            marker=dict(
                size=dc["score_global"] / 4 + 8,
                color=COLORS.get(cat_k, "#888"),
                opacity=0.82,
                line=dict(width=1.5, color="#fff"),
            ),
            hovertemplate=(
                "<b>%{text}</b><br>"
                "Autorité : %{x:.0f}<br>"
                "Trafic CTR : %{y:,.0f}/mois<extra></extra>"
            ),
        ))
    fig_scatter.update_layout(**PT, height=400, showlegend=True,
        title=PT_TITLE("AUTORITÉ vs TRAFIC CTR  (taille = score global)"),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(**PT_AXIS, title=dict(text="Score Autorité", font=dict(size=9, color="#9ca3af"))),
        yaxis=dict(**PT_AXIS, title=dict(text="Trafic CTR / mois", font=dict(size=9, color="#9ca3af"))),
    )

    # ── Comparaison trafic CTR vs trafic score ───────────────
    cmp = df_f[["name", "trafic_ctr", "trafic_score"]].copy().sort_values("trafic_ctr", ascending=True).tail(14)
    fig_cmp = go.Figure()
    fig_cmp.add_trace(go.Bar(
        name="CTR (AWR 2023)",
        x=cmp["trafic_ctr"], y=cmp["name"], orientation="h",
        marker=dict(color="#0d9488", opacity=0.85, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>CTR : %{x:,.0f}<extra></extra>",
    ))
    fig_cmp.add_trace(go.Bar(
        name="Score-based",
        x=cmp["trafic_score"], y=cmp["name"], orientation="h",
        marker=dict(color="#e4e7f0", opacity=1, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>Score-based : %{x:,.0f}<extra></extra>",
    ))
    fig_cmp.update_layout(**PT, height=400, barmode="overlay",
        title=PT_TITLE("TRAFIC CTR vs MODÈLE SCORE-BASED (Top 14)"),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)", orientation="h", y=1.08),
        yaxis=dict(**PT_AXIS, tickfont=dict(size=9)),
        xaxis=dict(**PT_AXIS),
    )

    # ── Positions estimées ───────────────────────────────────
    df_pos = df_f[["name", "category", "score_global", "position_estimee", "trafic_ctr"]].copy()
    df_pos = df_pos.sort_values("position_estimee")
    fig_pos = go.Figure(go.Bar(
        x=df_pos["name"], y=df_pos["position_estimee"],
        marker=dict(
            color=[COLORS.get(c, "#888") for c in df_pos["category"]],
            opacity=0.82, line=dict(width=0)
        ),
        text=df_pos["position_estimee"],
        textposition="outside",
        textfont=dict(size=9, family="DM Mono", color="#6b7280"),
        hovertemplate="<b>%{x}</b><br>Position estimée : #%{y}<extra></extra>",
    ))
    fig_pos.update_layout(**PT, height=280,
        title=PT_TITLE("POSITION SERP ESTIMÉE (proxy score → position via courbe exponentielle)"),
        xaxis=dict(**PT_AXIS, tickangle=-35, tickfont=dict(size=8)),
        yaxis=dict(**PT_AXIS, autorange="reversed",
                   title=dict(text="Position", font=dict(size=9, color="#9ca3af"))),
    )

    # ── Heatmap des sous-scores ──────────────────────────────
    dh = df_f.set_index("name")[["score_autorite", "score_qualite", "score_technique", "score_global"]]
    dh.columns = ["Autorité", "Qualité", "Technique", "Global"]
    fig_hm = go.Figure(go.Heatmap(
        z=dh.values.T, x=dh.index.tolist(), y=dh.columns.tolist(),
        colorscale=[[0, "#f0fdf4"], [0.4, "#6ee7b7"], [0.7, "#059669"], [1, "#064e3b"]],
        hovertemplate="<b>%{x}</b><br>%{y} : %{z:.1f}<extra></extra>",
        showscale=True,
        colorbar=dict(tickfont=dict(size=8, color="#6b7280"), thickness=10, len=0.9),
    ))
    fig_hm.update_layout(**PT, height=200,
        title=PT_TITLE("HEATMAP DES SCORES — TOUS LES SITES"),
        xaxis=dict(**PT_AXIS, tickangle=-35, tickfont=dict(size=8)),
        margin=dict(l=70, r=70, t=38, b=60),
    )

    # ── Tableau détaillé ─────────────────────────────────────
    tbl_df = df_f[[
        "name", "category", "score_global", "score_autorite",
        "score_qualite", "score_technique", "position_estimee",
        "trafic_ctr", "trafic_score"
    ]].copy().round(1)
    tbl_df.columns = [
        "Site", "Catégorie", "Global", "Autorité",
        "Qualité", "Technique", "Position est.",
        "Trafic CTR", "Trafic Score"
    ]

    return html.Div([
        page_header(
            "Modèle analytique · CTR × Pool mots-clés",
            [("Scoring & ", False), ("Trafic CTR", True)],
            "AWR 2023 · Sistrix 2020 · Score-to-Position proxy · Sénégal",
        ),
        ctr_info,
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_scatter, config={"displayModeBar": False}), width=6),
            dbc.Col(dcc.Graph(figure=fig_cmp, config={"displayModeBar": False}), width=6),
        ], className="g-4"),
        html.Div(style={"height": "1.5rem"}),
        dcc.Graph(figure=fig_pos, config={"displayModeBar": False}),
        html.Div(style={"height": "1rem"}),
        section_label("Heatmap des sous-scores"),
        dcc.Graph(figure=fig_hm, config={"displayModeBar": False}),
        html.Div(style={"height": "1rem"}),
        section_label("Tableau complet"),
        dash_table.DataTable(
            data=tbl_df.to_dict("records"),
            columns=[{"name": c, "id": c} for c in tbl_df.columns],
            sort_action="native",
            filter_action="native",
            page_size=20,
            style_table={"overflowX": "auto", "borderRadius": "10px", "border": "1px solid #e4e7f0"},
            style_header={"backgroundColor": "#f0f2f8", "color": "#9ca3af",
                          "fontFamily": "DM Mono, monospace", "fontSize": "0.6rem",
                          "letterSpacing": "0.1em", "textTransform": "uppercase",
                          "border": "none", "fontWeight": "500"},
            style_cell={"fontFamily": "Plus Jakarta Sans, sans-serif", "fontSize": "0.8rem",
                        "color": "#1a1d2e", "border": "none",
                        "borderBottom": "1px solid #f0f2f8", "padding": "0.6rem 0.8rem"},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#fafbfe"},
            ],
        ),
    ], className="page-wrap")


# ═════════════════════════════════════════════════════════════
# PAGE 3 — MÉTADONNÉES
# ═════════════════════════════════════════════════════════════
def page_metadata(df_f: pd.DataFrame, cat: str) -> html.Div:
    cat_clause = "" if cat == "Toutes" else f"AND s.category = '{cat}'"
    df_meta = qry(f"""
        SELECT s.name, s.domain, s.category,
               sm.status_code, sm.response_time_ms, sm.word_count,
               sm.internal_links_count, sm.external_links_count,
               sm.images_count, sm.has_ssl, sm.has_sitemap, sm.has_robots_txt
        FROM sites s
        LEFT JOIN site_metadata sm ON sm.site_id = s.id
            AND sm.crawled_at = (
                SELECT MAX(crawled_at) FROM site_metadata WHERE site_id = s.id
            )
        WHERE 1=1 {cat_clause}
        ORDER BY s.category, s.name
    """)

    header = page_header(
        "Collecte HTML automatique",
        [("Métadonnées ", False), ("techniques", True)],
        "Structure · Liens · Vitesse de réponse · Conformité SEO",
    )

    if df_meta.empty or df_meta["status_code"].isna().all():
        return html.Div([header, empty_state("Métadonnées non disponibles.")], className="page-wrap")

    # Temps de réponse
    df_rt = df_meta.dropna(subset=["response_time_ms"]).sort_values("response_time_ms")
    fig_rt = go.Figure(go.Bar(
        x=df_rt["response_time_ms"], y=df_rt["name"], orientation="h",
        marker=dict(
            color=["#16a34a" if v < 1000 else "#d97706" if v < 2500 else "#dc2626"
                   for v in df_rt["response_time_ms"]],
            opacity=0.82, line=dict(width=0)
        ),
        hovertemplate="<b>%{y}</b><br>%{x:.0f} ms<extra></extra>",
    ))
    fig_rt.update_layout(**PT, height=380,
        title=PT_TITLE("TEMPS DE RÉPONSE (ms) — vert<1s · amber<2.5s · rouge>2.5s"),
        yaxis=dict(**PT_AXIS, categoryorder="total ascending", tickfont=dict(size=8)),
        xaxis=dict(**PT_AXIS),
    )

    # Liens internes
    df_lk = df_meta.dropna(subset=["internal_links_count"]).sort_values("internal_links_count", ascending=False).head(14)
    fig_lk = go.Figure(go.Bar(
        x=df_lk["name"], y=df_lk["internal_links_count"],
        marker=dict(color="#2563eb", opacity=0.75, line=dict(width=0)),
        hovertemplate="<b>%{x}</b><br>%{y} liens internes<extra></extra>",
    ))
    fig_lk.update_layout(**PT, height=380,
        title=PT_TITLE("LIENS INTERNES PAR SITE"),
        xaxis=dict(**PT_AXIS, tickangle=-35, tickfont=dict(size=8)),
        yaxis=dict(**PT_AXIS),
    )

    # Conformité technique
    ssl_ok  = int(df_meta["has_ssl"].fillna(0).sum())
    sit_ok  = int(df_meta["has_sitemap"].fillna(0).sum())
    rob_ok  = int(df_meta["has_robots_txt"].fillna(0).sum()) if "has_robots_txt" in df_meta else 0
    total_m = len(df_meta)
    fig_conf = go.Figure(go.Bar(
        x=["SSL", "Sitemap", "Robots.txt"],
        y=[ssl_ok, sit_ok, rob_ok],
        marker=dict(color=["#0d9488", "#2563eb", "#7c3aed"], opacity=0.82, line=dict(width=0)),
        text=[f"{v}/{total_m}" for v in [ssl_ok, sit_ok, rob_ok]],
        textposition="outside",
        textfont=dict(size=11, color="#6b7280", family="DM Mono"),
    ))
    fig_conf.update_layout(**PT, height=260,
        title=PT_TITLE("CONFORMITÉ TECHNIQUE SEO"),
        yaxis=dict(**PT_AXIS, range=[0, total_m + 3]),
        xaxis=dict(**PT_AXIS),
    )

    # Tableau
    tbl = df_meta[["name", "category", "response_time_ms", "word_count",
                   "internal_links_count", "has_ssl", "has_sitemap", "has_robots_txt"]].copy()
    tbl["has_ssl"]       = tbl["has_ssl"].apply(lambda x: "Oui" if x == 1 else "Non")
    tbl["has_sitemap"]   = tbl["has_sitemap"].apply(lambda x: "Oui" if x == 1 else "Non")
    tbl["has_robots_txt"]= tbl["has_robots_txt"].apply(lambda x: "Oui" if x == 1 else "Non")
    tbl.columns = ["Site", "Catégorie", "Temps ms", "Mots", "Liens int.", "SSL", "Sitemap", "Robots"]

    return html.Div([
        header,
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_rt, config={"displayModeBar": False}), width=6),
            dbc.Col(dcc.Graph(figure=fig_lk, config={"displayModeBar": False}), width=6),
        ], className="g-4"),
        html.Div(style={"height": "1rem"}),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_conf, config={"displayModeBar": False}), width=5),
            dbc.Col([
                section_label("Tableau complet"),
                dash_table.DataTable(
                    data=tbl.fillna("—").to_dict("records"),
                    columns=[{"name": c, "id": c} for c in tbl.columns],
                    sort_action="native",
                    page_size=15,
                    style_table={"overflowX": "auto", "border": "1px solid #e4e7f0", "borderRadius": "10px"},
                    style_header={"backgroundColor": "#f0f2f8", "color": "#9ca3af",
                                  "fontFamily": "DM Mono, monospace", "fontSize": "0.58rem",
                                  "textTransform": "uppercase", "border": "none"},
                    style_cell={"fontFamily": "Plus Jakarta Sans", "fontSize": "0.78rem",
                                "color": "#1a1d2e", "border": "none",
                                "borderBottom": "1px solid #f0f2f8", "padding": "0.55rem 0.7rem"},
                ),
            ], width=7),
        ], className="g-4"),
    ], className="page-wrap")


# ═════════════════════════════════════════════════════════════
# PAGE 4 — PERFORMANCE PAGESPEED
# ═════════════════════════════════════════════════════════════
def page_performance(df_f: pd.DataFrame, cat: str) -> html.Div:
    cat_clause = "" if cat == "Toutes" else f"AND s.category = '{cat}'"
    df_perf = qry(f"""
        SELECT s.name, s.category,
               sp.performance_score, sp.seo_score,
               sp.accessibility_score, sp.best_practices_score,
               sp.lcp_ms, sp.fcp_ms, sp.ttfb_ms, sp.cls_score
        FROM site_performance sp
        JOIN sites s ON s.id = sp.site_id
        WHERE sp.measured_at = (
            SELECT MAX(measured_at) FROM site_performance WHERE site_id = sp.site_id
        ) {cat_clause}
        ORDER BY sp.performance_score DESC NULLS LAST
    """)

    header = page_header(
        "PageSpeed Insights · Google Lighthouse",
        [("Performance ", False), ("web", True)],
        "Core Web Vitals · LCP · FCP · TTFB · CLS · Mobile first",
    )

    if df_perf.empty:
        return html.Div([header, empty_state("Scores PageSpeed non disponibles.")], className="page-wrap")

    # Barres performance
    fig_perf = go.Figure(go.Bar(
        x=df_perf["performance_score"], y=df_perf["name"], orientation="h",
        marker=dict(
            color=["#16a34a" if v >= 90 else "#d97706" if v >= 50 else "#dc2626"
                   for v in df_perf["performance_score"].fillna(0)],
            opacity=0.82, line=dict(width=0)
        ),
        hovertemplate="<b>%{y}</b><br>Performance : %{x:.0f}/100<extra></extra>",
    ))
    fig_perf.update_layout(**PT, height=380,
        title=PT_TITLE("SCORE PERFORMANCE LIGHTHOUSE / 100"),
        xaxis=dict(**PT_AXIS, range=[0, 100]),
        yaxis=dict(**PT_AXIS, categoryorder="total ascending", tickfont=dict(size=8)),
    )

    # Scatter performance vs SEO
    fig_seo = px.scatter(
        df_perf.dropna(subset=["performance_score", "seo_score"]),
        x="performance_score", y="seo_score",
        color="category", text="name",
        color_discrete_map=COLORS,
    )
    fig_seo.update_traces(
        textposition="top center",
        textfont=dict(size=8, color="#6b7280"),
        marker=dict(size=10, opacity=0.82, line=dict(width=1.5, color="#fff")),
    )
    fig_seo.update_layout(**PT, height=380,
        title=PT_TITLE("PERFORMANCE vs SEO (coloré par catégorie)"),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
        xaxis=dict(**PT_AXIS, range=[0, 100]),
        yaxis=dict(**PT_AXIS, range=[0, 100]),
    )

    # Tableau CWV
    cwv = df_perf[["name", "lcp_ms", "fcp_ms", "ttfb_ms", "cls_score",
                   "accessibility_score", "best_practices_score"]].copy()
    cwv.columns = ["Site", "LCP (ms)", "FCP (ms)", "TTFB (ms)", "CLS", "Accessibilité", "Best Practices"]

    # Score moyen par catégorie
    cat_avg = df_perf.groupby("category")[["performance_score", "seo_score", "accessibility_score"]].mean().round(1).reset_index()
    fig_cat_bar = go.Figure()
    for col, color in [("performance_score", "#0d9488"), ("seo_score", "#2563eb"), ("accessibility_score", "#7c3aed")]:
        fig_cat_bar.add_trace(go.Bar(
            name=col.replace("_score", "").capitalize(),
            x=cat_avg["category"], y=cat_avg[col],
            marker=dict(color=color, opacity=0.82, line=dict(width=0)),
        ))
    fig_cat_bar.update_layout(**PT, height=260, barmode="group",
        title=PT_TITLE("SCORES MOYENS PAR CATÉGORIE"),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
        yaxis=dict(**PT_AXIS, range=[0, 100]),
        xaxis=dict(**PT_AXIS),
    )

    return html.Div([
        header,
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_perf, config={"displayModeBar": False}), width=6),
            dbc.Col(dcc.Graph(figure=fig_seo, config={"displayModeBar": False}), width=6),
        ], className="g-4"),
        html.Div(style={"height": "1rem"}),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_cat_bar, config={"displayModeBar": False}), width=5),
            dbc.Col([
                section_label("Core Web Vitals"),
                dash_table.DataTable(
                    data=cwv.fillna("—").round(1).to_dict("records"),
                    columns=[{"name": c, "id": c} for c in cwv.columns],
                    sort_action="native",
                    page_size=15,
                    style_table={"overflowX": "auto", "border": "1px solid #e4e7f0", "borderRadius": "10px"},
                    style_header={"backgroundColor": "#f0f2f8", "color": "#9ca3af",
                                  "fontFamily": "DM Mono, monospace", "fontSize": "0.58rem",
                                  "textTransform": "uppercase", "border": "none"},
                    style_cell={"fontFamily": "Plus Jakarta Sans", "fontSize": "0.78rem",
                                "color": "#1a1d2e", "border": "none",
                                "borderBottom": "1px solid #f0f2f8", "padding": "0.55rem 0.7rem"},
                ),
            ], width=7),
        ], className="g-4"),
    ], className="page-wrap")


# ═════════════════════════════════════════════════════════════
# PAGE 5 — BACKLINKS
# ═════════════════════════════════════════════════════════════
def page_backlinks(df_f: pd.DataFrame, cat: str) -> html.Div:
    cat_clause = "" if cat == "Toutes" else f"AND s.category = '{cat}'"
    df_bl = qry(f"""
        SELECT s.name, s.category, s.domain,
               sb.total_backlinks, sb.referring_domains, sb.backlinks_change
        FROM site_backlinks sb
        JOIN sites s ON s.id = sb.site_id
        WHERE sb.collected_at = (
            SELECT MAX(collected_at) FROM site_backlinks WHERE site_id = sb.site_id
        ) {cat_clause}
        ORDER BY sb.total_backlinks DESC NULLS LAST
    """)

    header = page_header(
        "CommonCrawl Index",
        [("Autorité & ", False), ("Backlinks", True)],
        "Pages indexées · Domaines référents · Variation mensuelle",
    )

    if df_bl.empty:
        return html.Div([header, empty_state("Backlinks non disponibles.")], className="page-wrap")

    fig_bl = go.Figure(go.Bar(
        x=df_bl["total_backlinks"], y=df_bl["name"], orientation="h",
        marker=dict(color=[COLORS.get(c, "#888") for c in df_bl["category"]],
                    opacity=0.82, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>%{x} pages indexées<extra></extra>",
    ))
    fig_bl.update_layout(**PT, height=420,
        title=PT_TITLE("PAGES INDEXÉES — CommonCrawl"),
        yaxis=dict(**PT_AXIS, categoryorder="total ascending", tickfont=dict(size=8)),
        xaxis=dict(**PT_AXIS),
    )

    top_rd = df_bl.nlargest(14, "referring_domains")
    fig_rd = go.Figure(go.Bar(
        x=top_rd["referring_domains"], y=top_rd["name"], orientation="h",
        marker=dict(color="#0d9488", opacity=0.76, line=dict(width=0)),
        hovertemplate="<b>%{y}</b><br>%{x} domaines référents<extra></extra>",
    ))
    fig_rd.update_layout(**PT, height=420,
        title=PT_TITLE("DOMAINES RÉFÉRENTS (Top 14)"),
        yaxis=dict(**PT_AXIS, categoryorder="total ascending", tickfont=dict(size=8)),
        xaxis=dict(**PT_AXIS),
    )

    tbl = df_bl[["name", "category", "domain", "total_backlinks", "referring_domains", "backlinks_change"]].copy()
    tbl.columns = ["Site", "Catégorie", "Domaine", "Pages indexées", "Dom. référents", "Variation"]

    return html.Div([
        header,
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_bl, config={"displayModeBar": False}), width=6),
            dbc.Col(dcc.Graph(figure=fig_rd, config={"displayModeBar": False}), width=6),
        ], className="g-4"),
        html.Div(style={"height": "1rem"}),
        section_label("Tableau complet"),
        dash_table.DataTable(
            data=tbl.fillna("—").to_dict("records"),
            columns=[{"name": c, "id": c} for c in tbl.columns],
            sort_action="native",
            filter_action="native",
            page_size=20,
            style_table={"overflowX": "auto", "border": "1px solid #e4e7f0", "borderRadius": "10px"},
            style_header={"backgroundColor": "#f0f2f8", "color": "#9ca3af",
                          "fontFamily": "DM Mono, monospace", "fontSize": "0.58rem",
                          "textTransform": "uppercase", "border": "none"},
            style_cell={"fontFamily": "Plus Jakarta Sans", "fontSize": "0.8rem",
                        "color": "#1a1d2e", "border": "none",
                        "borderBottom": "1px solid #f0f2f8", "padding": "0.6rem 0.8rem"},
        ),
    ], className="page-wrap")


# ═════════════════════════════════════════════════════════════
# PAGE 6 — COMPARAISON
# ═════════════════════════════════════════════════════════════
def page_comparison(df_all: pd.DataFrame) -> html.Div:
    header = page_header(
        "Analyse concurrentielle",
        [("Comparaison ", False), ("directe", True)],
        "Sélectionnez jusqu'à 8 sites pour comparer toutes leurs dimensions",
    )

    if df_all.empty:
        return html.Div([header, empty_state("Données insuffisantes.")], className="page-wrap")

    site_opts = [{"label": n, "value": n} for n in sorted(df_all["name"].tolist())]
    default_sel = df_all["name"].tolist()[:6]

    return html.Div([
        header,
        html.Div([
            html.Label("Sites à comparer (max 8)", style={
                "fontFamily": "var(--mono)", "fontSize": "0.58rem",
                "letterSpacing": "0.15em", "textTransform": "uppercase",
                "color": "#9ca3af", "display": "block", "marginBottom": "0.5rem"
            }),
            dcc.Dropdown(
                id="comparison-selector",
                options=site_opts,
                value=default_sel,
                multi=True,
                placeholder="Sélectionner des sites...",
                style={"fontSize": "0.82rem"},
            ),
        ], style={"marginBottom": "1.5rem"}),
        html.Div(id="comparison-charts"),
    ], className="page-wrap")


@app.callback(
    Output("comparison-charts", "children"),
    Input("comparison-selector", "value"),
)
def update_comparison(selected):
    if not selected or df_all.empty:
        return empty_state("Sélectionnez des sites pour afficher la comparaison.")

    selected = selected[:8]
    ds = df_all[df_all["name"].isin(selected)]
    if ds.empty:
        return empty_state("Aucune donnée pour la sélection.")

    PALETTE = ["#0d9488", "#2563eb", "#d97706", "#7c3aed", "#16a34a", "#dc2626", "#ea580c", "#0891b2"]

    # Radar
    dims = ["Autorité", "Qualité", "Technique", "Score global"]
    fig_radar = go.Figure()
    for j, (_, row) in enumerate(ds.iterrows()):
        vals = [row["score_autorite"], row["score_qualite"], row["score_technique"], row["score_global"]]
        vals_closed = vals + [vals[0]]
        fig_radar.add_trace(go.Scatterpolar(
            r=vals_closed, theta=dims + [dims[0]],
            fill="toself", name=row["name"],
            line=dict(color=PALETTE[j % len(PALETTE)], width=2),
            fillcolor=PALETTE[j % len(PALETTE)] + "22",
            hovertemplate="%{theta}: %{r:.1f}<extra>" + row["name"] + "</extra>",
        ))
    fig_radar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="DM Mono, monospace", color="#9ca3af", size=10),
        height=420,
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(visible=True, range=[0, 100],
                            gridcolor="#e4e7f0",
                            tickfont=dict(size=7, color="#9ca3af")),
            angularaxis=dict(gridcolor="#e4e7f0",
                             tickfont=dict(size=9, color="#6b7280")),
        ),
        title=PT_TITLE("RADAR — PROFIL COMPARATIF"),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=40, r=40, t=38, b=20),
        hoverlabel=dict(bgcolor="#1a1d2e", font_size=12, font_family="DM Mono"),
    )

    # Barres groupées
    metrics = ["score_autorite", "score_qualite", "score_technique", "score_global"]
    labels  = ["Autorité", "Qualité", "Technique", "Global"]
    fig_bar = go.Figure()
    for j, (_, row) in enumerate(ds.iterrows()):
        fig_bar.add_trace(go.Bar(
            name=row["name"], x=labels,
            y=[row[m] for m in metrics],
            marker=dict(color=PALETTE[j % len(PALETTE)], opacity=0.82, line=dict(width=0)),
            hovertemplate="<b>" + row["name"] + "</b><br>%{x}: %{y:.1f}<extra></extra>",
        ))
    fig_bar.update_layout(**PT, height=420, barmode="group",
        title=PT_TITLE("COMPARAISON PAR DIMENSION"),
        yaxis=dict(**PT_AXIS, range=[0, 100]),
        xaxis=dict(**PT_AXIS),
        legend=dict(font=dict(size=9), bgcolor="rgba(0,0,0,0)"),
    )

    # Tableau
    tbl = ds[["name", "category", "score_global", "score_autorite",
              "score_qualite", "score_technique", "trafic_ctr", "position_estimee"]].copy()
    tbl.columns = ["Site", "Catégorie", "Global", "Autorité", "Qualité", "Technique", "Trafic CTR", "Position"]
    tbl = tbl.round(1).sort_values("Global", ascending=False)

    return html.Div([
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_radar, config={"displayModeBar": False}), width=6),
            dbc.Col(dcc.Graph(figure=fig_bar, config={"displayModeBar": False}), width=6),
        ], className="g-4"),
        html.Div(style={"height": "1rem"}),
        section_label("Tableau récapitulatif"),
        dash_table.DataTable(
            data=tbl.to_dict("records"),
            columns=[{"name": c, "id": c} for c in tbl.columns],
            sort_action="native",
            style_table={"overflowX": "auto", "border": "1px solid #e4e7f0", "borderRadius": "10px"},
            style_header={"backgroundColor": "#f0f2f8", "color": "#9ca3af",
                          "fontFamily": "DM Mono, monospace", "fontSize": "0.58rem",
                          "textTransform": "uppercase", "border": "none"},
            style_cell={"fontFamily": "Plus Jakarta Sans", "fontSize": "0.8rem",
                        "color": "#1a1d2e", "border": "none",
                        "borderBottom": "1px solid #f0f2f8", "padding": "0.6rem 0.8rem"},
        ),
    ])


# ═════════════════════════════════════════════════════════════
# PAGE 7 — VEILLE & TENDANCES
# ═════════════════════════════════════════════════════════════
def page_trends(df_all: pd.DataFrame, df_f: pd.DataFrame) -> html.Div:
    header = page_header(
        "Intelligence stratégique · simulation · risques",
        [("Veille & ", False), ("Tendances", True)],
        "Simulateur CTR · Carte des opportunités · Détection des sites à risque",
    )

    if df_all.empty:
        return html.Div([header, empty_state("Données insuffisantes.")], className="page-wrap")

    # ── Simulateur CTR ────────────────────────────────────────
    sim_intro = html.Div([
        html.Div("Simulateur d'impact SEO → Trafic CTR", className="ctr-callout-label"),
        html.Div(
            "Sélectionnez un site, ajustez les gains de score, et observez l'effet "
            "sur le trafic estimé via le modèle CTR. Le modèle recalcule la position "
            "SERP estimée et applique la courbe AWR 2023.",
            className="ctr-callout-text"
        ),
    ], className="ctr-callout", style={"marginBottom": "1.2rem"})

    site_opts = [{"label": n, "value": n} for n in df_all["name"].tolist()]

    sim_controls = html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Site à simuler", style={
                    "fontFamily": "DM Mono", "fontSize": "0.56rem", "letterSpacing": "0.15em",
                    "textTransform": "uppercase", "color": "#9ca3af", "display": "block", "marginBottom": "0.4rem"
                }),
                dcc.Dropdown(id="sim-site", options=site_opts,
                             value=df_all["name"].iloc[0] if not df_all.empty else None,
                             clearable=False, style={"fontSize": "0.82rem"}),
            ], width=4),
            dbc.Col([
                html.Label("Gain score SEO (pts)", style={
                    "fontFamily": "DM Mono", "fontSize": "0.56rem", "letterSpacing": "0.15em",
                    "textTransform": "uppercase", "color": "#9ca3af", "display": "block", "marginBottom": "0.4rem"
                }),
                dcc.Slider(id="sim-seo", min=0, max=40, step=1, value=10,
                           marks={0: "0", 10: "10", 20: "20", 30: "30", 40: "40"},
                           tooltip={"always_visible": False}),
            ], width=4),
            dbc.Col([
                html.Label("Gain Performance (pts)", style={
                    "fontFamily": "DM Mono", "fontSize": "0.56rem", "letterSpacing": "0.15em",
                    "textTransform": "uppercase", "color": "#9ca3af", "display": "block", "marginBottom": "0.4rem"
                }),
                dcc.Slider(id="sim-perf", min=0, max=40, step=1, value=10,
                           marks={0: "0", 10: "10", 20: "20", 30: "30", 40: "40"},
                           tooltip={"always_visible": False}),
            ], width=4),
        ], className="g-3"),
    ], style={"marginBottom": "1.2rem"})

    # ── Carte des opportunités ────────────────────────────────
    df_opp = df_all.copy()
    df_opp["score_qualite_proj"] = df_opp["score_qualite"].apply(lambda x: min(90, x + 30))
    df_opp["score_global_proj"]  = (
        df_opp["score_autorite"]     * 0.45 +
        df_opp["score_qualite_proj"] * 0.35 +
        df_opp["score_technique"]    * 0.20
    ).round(1)
    df_opp["trafic_potentiel"] = df_opp.apply(
        lambda r: int(CATEGORY_BASE.get(r["category"], 50000) *
                      (r["score_global_proj"] / 100) ** 1.5),
        axis=1
    )
    df_opp["gap_trafic"] = (df_opp["trafic_potentiel"] - df_opp["trafic_score"]).clip(lower=0)
    df_top_opp = df_opp.nlargest(12, "gap_trafic")

    fig_opp = go.Figure(go.Bar(
        x=df_top_opp["gap_trafic"], y=df_top_opp["name"], orientation="h",
        marker=dict(color=[COLORS.get(c, "#888") for c in df_top_opp["category"]],
                    opacity=0.82, line=dict(width=0)),
        text=[f"+{fmt(v)}" for v in df_top_opp["gap_trafic"]],
        textposition="outside",
        textfont=dict(size=9, color="#6b7280", family="DM Mono"),
        hovertemplate="<b>%{y}</b><br>Gain potentiel : +%{x:,.0f} visites/mois<extra></extra>",
    ))
    fig_opp.update_layout(**PT, height=360,
        title=PT_TITLE("GAIN DE TRAFIC POTENTIEL — si score qualité montait à 90"),
        yaxis=dict(**PT_AXIS, categoryorder="total ascending", tickfont=dict(size=9)),
        xaxis=dict(**PT_AXIS),
    )

    # ── Score de risque ───────────────────────────────────────
    df_risk = df_all.copy()
    risk = pd.Series(0.0, index=df_risk.index)
    risk += (df_risk["response_time_ms"].fillna(1000) > 3000).astype(float) * 30
    risk += (df_risk["response_time_ms"].fillna(1000) > 5000).astype(float) * 20
    risk += (df_risk["has_ssl"].fillna(1) == 0).astype(float) * 25
    risk += (df_risk["has_sitemap"].fillna(1) == 0).astype(float) * 15
    risk += (df_risk["score_qualite"] < 40).astype(float) * 20
    risk += (df_risk["score_autorite"] < 20).astype(float) * 10
    df_risk["score_risque"] = risk.clip(0, 100).round(0).astype(int)
    df_risk_sorted = df_risk.sort_values("score_risque", ascending=False).head(12)

    fig_risk = go.Figure(go.Bar(
        x=df_risk_sorted["score_risque"], y=df_risk_sorted["name"], orientation="h",
        marker=dict(
            color=["#dc2626" if v >= 60 else "#d97706" if v >= 30 else "#16a34a"
                   for v in df_risk_sorted["score_risque"]],
            opacity=0.85, line=dict(width=0)
        ),
        text=df_risk_sorted["score_risque"].astype(str),
        textposition="outside",
        textfont=dict(size=9, color="#6b7280", family="DM Mono"),
        hovertemplate="<b>%{y}</b><br>Score risque : %{x}/100<extra></extra>",
    ))
    fig_risk.update_layout(**PT, height=360,
        title=PT_TITLE("SCORE DE RISQUE TECHNIQUE — rouge≥60 · amber≥30"),
        xaxis=dict(**PT_AXIS, range=[0, 120]),
        yaxis=dict(**PT_AXIS, categoryorder="total ascending", tickfont=dict(size=9)),
    )

    risk_tbl = df_risk_sorted[["name", "category", "score_risque"]].copy()
    risk_tbl["Temps resp."] = df_risk_sorted["response_time_ms"].fillna(0).apply(
        lambda x: "LENT" if x > 3000 else "OK")
    risk_tbl["SSL"] = df_risk_sorted["has_ssl"].fillna(0).apply(
        lambda x: "OK" if x == 1 else "MANQUANT")
    risk_tbl["Sitemap"] = df_risk_sorted["has_sitemap"].fillna(0).apply(
        lambda x: "OK" if x == 1 else "MANQUANT")
    risk_tbl.columns = ["Site", "Catégorie", "Risque /100", "Temps resp.", "SSL", "Sitemap"]

    return html.Div([
        header,
        sim_intro,
        sim_controls,
        html.Div(id="sim-result"),
        html.Div(style={"height": "2rem"}),
        section_label("Carte des opportunités de croissance"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_opp, config={"displayModeBar": False}), width=12),
        ]),
        html.Div(style={"height": "1rem"}),
        section_label("Radar des sites à risque technique"),
        dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_risk, config={"displayModeBar": False}), width=6),
            dbc.Col([
                dash_table.DataTable(
                    data=risk_tbl.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in risk_tbl.columns],
                    sort_action="native",
                    style_table={"overflowX": "auto", "border": "1px solid #e4e7f0",
                                 "borderRadius": "10px", "marginTop": "0.5rem"},
                    style_header={"backgroundColor": "#f0f2f8", "color": "#9ca3af",
                                  "fontFamily": "DM Mono, monospace", "fontSize": "0.58rem",
                                  "textTransform": "uppercase", "border": "none"},
                    style_cell={"fontFamily": "Plus Jakarta Sans", "fontSize": "0.78rem",
                                "color": "#1a1d2e", "border": "none",
                                "borderBottom": "1px solid #f0f2f8", "padding": "0.55rem 0.7rem"},
                    style_data_conditional=[
                        {"if": {"filter_query": '{Risque /100} >= 60', "column_id": "Risque /100"},
                         "color": "#dc2626", "fontWeight": "700"},
                        {"if": {"filter_query": '{Risque /100} >= 30 && {Risque /100} < 60', "column_id": "Risque /100"},
                         "color": "#d97706", "fontWeight": "600"},
                        {"if": {"filter_query": '{SSL} = "MANQUANT"', "column_id": "SSL"},
                         "color": "#dc2626"},
                        {"if": {"filter_query": '{Sitemap} = "MANQUANT"', "column_id": "Sitemap"},
                         "color": "#dc2626"},
                        {"if": {"filter_query": '{Temps resp.} = "LENT"', "column_id": "Temps resp."},
                         "color": "#d97706"},
                    ],
                ),
            ], width=6),
        ], className="g-4"),
    ], className="page-wrap")


@app.callback(
    Output("sim-result", "children"),
    [Input("sim-site", "value"), Input("sim-seo", "value"), Input("sim-perf", "value")],
)
def update_simulator(site_name, delta_seo, delta_perf):
    if not site_name or df_all.empty:
        return html.Span()
    rows = df_all[df_all["name"] == site_name]
    if rows.empty:
        return html.Span()

    row = rows.iloc[0]
    new_seo  = min(100, float(row.get("seo_score", 50) or 50)  + (delta_seo or 0))
    new_perf = min(100, float(row.get("performance_score", 50) or 50) + (delta_perf or 0))
    new_acc  = float(row.get("accessibility_score", 50) or 50)

    new_qualite  = new_seo * 0.40 + new_perf * 0.35 + new_acc * 0.25
    new_global   = round(row["score_autorite"] * 0.45 + new_qualite * 0.35 + row["score_technique"] * 0.20, 1)
    new_pos      = score_to_position(new_global, row["score_autorite"])
    old_pos      = int(row.get("position_estimee", score_to_position(row["score_global"], row["score_autorite"])))

    base_cat     = CATEGORY_BASE.get(row["category"], 50000)
    new_traffic  = int(base_cat * (new_global / 100) ** 1.5)
    delta_tr     = new_traffic - int(row["trafic_estime"])
    delta_global = round(new_global - row["score_global"], 1)

    color_tr  = "#16a34a" if delta_tr > 0 else "#6b7280"
    color_sc  = "#0d9488" if delta_global > 0 else "#6b7280"

    return html.Div([
        html.Div([
            kpi_card("Score actuel",  f"{row['score_global']:.1f}", f"{row['category']}", "#6b7280"),
            kpi_card("Score projeté", f"{new_global:.1f}", f"+{delta_global} pts", color_sc),
            kpi_card("Position actuelle", f"#{old_pos}", "SERP estimée", "#6b7280"),
            kpi_card("Position projetée", f"#{new_pos}", f"{'mieux' if new_pos < old_pos else 'stable'}", color_sc),
            kpi_card("Trafic actuel",  fmt(row["trafic_estime"]), "visites/mois", "#6b7280"),
            kpi_card("Trafic projeté", fmt(new_traffic), f"+{fmt(delta_tr)} visites", color_tr),
        ], style={
            "display": "grid",
            "gridTemplateColumns": "repeat(6, 1fr)",
            "gap": "1rem",
            "marginBottom": "1rem",
        }),
    ])


# ═════════════════════════════════════════════════════════════
# PAGE 8 — RAPPORT & EXPORT
# ═════════════════════════════════════════════════════════════
def page_export(df_all: pd.DataFrame) -> html.Div:
    header = page_header(
        "Export · Rapport exécutif · Fiche site",
        [("Rapport & ", False), ("Export", True)],
        "Télécharge les données · Génère un rapport HTML imprimable en PDF",
        f"{now}\n{n_sites} sites · {len(df_all)} scores calculés",
    )

    if df_all.empty:
        return html.Div([header, empty_state("Aucune donnée disponible pour l'export.")], className="page-wrap")

    # ── Sélecteur de fiche ────────────────────────────────────
    site_opts = [{"label": n, "value": n} for n in df_all["name"].tolist()]

    # ── Export cards ──────────────────────────────────────────
    export_cards = dbc.Row([
        dbc.Col(html.Div([
            html.Div([
                html.Div("CSV · Scores complets", style={
                    "fontFamily": "DM Mono", "fontSize": "0.58rem", "letterSpacing": "0.15em",
                    "textTransform": "uppercase", "color": "#0d9488", "marginBottom": "0.6rem"
                }),
                html.Div(
                    "Tous les scores, métriques et trafic CTR pour les 28 sites. "
                    "Compatible Excel, Google Sheets, Power BI.",
                    style={"fontSize": "0.8rem", "color": "#6b7280", "lineHeight": "1.6",
                           "marginBottom": "1rem"}
                ),
                dcc.Download(id="download-csv"),
                html.Button("Télécharger CSV", id="btn-csv", n_clicks=0,
                            className="btn-download btn-teal"),
            ], className="card-body"),
        ], className="card"), width=4),

        dbc.Col(html.Div([
            html.Div([
                html.Div("HTML · Rapport exécutif", style={
                    "fontFamily": "DM Mono", "fontSize": "0.58rem", "letterSpacing": "0.15em",
                    "textTransform": "uppercase", "color": "#2563eb", "marginBottom": "0.6rem"
                }),
                html.Div(
                    "Rapport complet avec KPIs, classement et tableau. "
                    "Imprimable en PDF depuis le navigateur (Ctrl+P).",
                    style={"fontSize": "0.8rem", "color": "#6b7280", "lineHeight": "1.6",
                           "marginBottom": "1rem"}
                ),
                dcc.Download(id="download-html"),
                html.Button("Télécharger rapport HTML", id="btn-html", n_clicks=0,
                            className="btn-download btn-blue"),
            ], className="card-body"),
        ], className="card"), width=4),

        dbc.Col(html.Div([
            html.Div([
                html.Div("JSON · API-ready", style={
                    "fontFamily": "DM Mono", "fontSize": "0.58rem", "letterSpacing": "0.15em",
                    "textTransform": "uppercase", "color": "#7c3aed", "marginBottom": "0.6rem"
                }),
                html.Div(
                    "Export structuré pour intégration API, dashboards tiers "
                    "ou alimentation de bases de données.",
                    style={"fontSize": "0.8rem", "color": "#6b7280", "lineHeight": "1.6",
                           "marginBottom": "1rem"}
                ),
                dcc.Download(id="download-json"),
                html.Button("Télécharger JSON", id="btn-json", n_clicks=0,
                            className="btn-download btn-purple"),
            ], className="card-body"),
        ], className="card"), width=4),
    ], className="g-4", style={"marginBottom": "2rem"})

    fiche_section = html.Div([
        section_label("Fiche site individuelle"),
        html.Div([
            html.Label("Sélectionner un site", style={
                "fontFamily": "DM Mono", "fontSize": "0.58rem", "letterSpacing": "0.15em",
                "textTransform": "uppercase", "color": "#9ca3af", "display": "block", "marginBottom": "0.5rem"
            }),
            dcc.Dropdown(
                id="fiche-selector",
                options=site_opts,
                value=df_all["name"].iloc[0] if not df_all.empty else None,
                clearable=False,
                style={"fontSize": "0.82rem", "marginBottom": "1rem"},
            ),
        ]),
        html.Div(id="fiche-content"),
    ])

    return html.Div([
        header,
        section_label("Exports rapides"),
        export_cards,
        fiche_section,
    ], className="page-wrap")


# ── Callbacks export ──────────────────────────────────────────
@app.callback(Output("download-csv", "data"), Input("btn-csv", "n_clicks"), prevent_initial_call=True)
def export_csv(n):
    if not n or df_all.empty:
        return dash.no_update
    cols = ["name", "domain", "category", "score_global", "score_autorite", "score_qualite",
            "score_technique", "position_estimee", "trafic_ctr", "trafic_score",
            "total_backlinks", "referring_domains", "performance_score", "seo_score",
            "accessibility_score", "response_time_ms", "has_ssl", "has_sitemap"]
    ex = df_all[[c for c in cols if c in df_all.columns]].copy().round(1)
    ex.columns = [c.replace("_", " ").title() for c in ex.columns]
    return dcc.send_data_frame(ex.to_csv, f"senwebstats_{datetime.now().strftime('%Y%m%d')}.csv",
                               index=False, sep=";", encoding="utf-8-sig")


@app.callback(Output("download-json", "data"), Input("btn-json", "n_clicks"), prevent_initial_call=True)
def export_json(n):
    if not n or df_all.empty:
        return dash.no_update
    cols = ["name", "domain", "category", "score_global", "score_autorite",
            "score_qualite", "score_technique", "position_estimee", "trafic_ctr"]
    payload = {
        "generated_at": now,
        "n_sites": n_sites,
        "total_traffic_ctr": total_tr,
        "avg_score": float(avg_sc),
        "model": "CTR × Pool mots-clés Sénégal (AWR 2023)",
        "sites": df_all[[c for c in cols if c in df_all.columns]].round(1).to_dict("records"),
    }
    return dcc.send_string(
        json.dumps(payload, ensure_ascii=False, indent=2),
        f"senwebstats_{datetime.now().strftime('%Y%m%d')}.json",
        type="application/json"
    )


@app.callback(Output("download-html", "data"), Input("btn-html", "n_clicks"), prevent_initial_call=True)
def export_html(n):
    if not n or df_all.empty:
        return dash.no_update

    cat_stats = df_all.groupby("category").agg(
        sites=("name", "count"),
        score_moy=("score_global", "mean"),
        trafic_tot=("trafic_ctr", "sum"),
    ).reset_index()

    top_rows = "".join([
        f"<tr><td>{i+1}</td><td><b>{r['name']}</b></td><td>{r['category']}</td>"
        f"<td style='text-align:right'>{r['score_global']:.1f}</td>"
        f"<td style='text-align:right'>#{int(r['position_estimee'])}</td>"
        f"<td style='text-align:right'>{fmt(r['trafic_ctr'])}</td></tr>"
        for i, (_, r) in enumerate(df_all.head(15).iterrows())
    ])
    cat_rows = "".join([
        f"<tr><td>{r['category']}</td><td style='text-align:right'>{int(r['sites'])}</td>"
        f"<td style='text-align:right'>{r['score_moy']:.1f}</td>"
        f"<td style='text-align:right'>{fmt(r['trafic_tot'])}</td></tr>"
        for _, r in cat_stats.iterrows()
    ])

    html_str = f"""<!DOCTYPE html><html lang="fr">
<head><meta charset="UTF-8">
<title>SenWebStats — Rapport {datetime.now().strftime('%B %Y')}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,600;1,400&family=Plus+Jakarta+Sans:wght@400;600&family=DM+Mono:wght@400;500&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Plus Jakarta Sans',sans-serif;background:#f7f8fc;color:#1a1d2e;font-size:13px}}
.page{{max-width:960px;margin:0 auto;padding:48px 40px}}
h1{{font-family:'Lora',serif;font-size:2rem;font-weight:600}}
h1 em{{color:#0d9488;font-style:italic;font-weight:400}}
h2{{font-family:'DM Mono',monospace;font-size:0.56rem;letter-spacing:0.2em;text-transform:uppercase;color:#9ca3af;margin:2rem 0 0.8rem;border-bottom:1px solid #e4e7f0;padding-bottom:0.4rem}}
.meta{{font-family:'DM Mono',monospace;font-size:0.6rem;color:#9ca3af;margin-bottom:2rem}}
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:1.2rem 0 2rem}}
.kpi{{background:#fff;border:1px solid #e4e7f0;border-radius:10px;padding:1rem 1.2rem;position:relative;overflow:hidden}}
.kpi-bar{{position:absolute;top:0;left:0;right:0;height:3px}}
.kpi-lbl{{font-family:'DM Mono',monospace;font-size:0.5rem;letter-spacing:0.15em;text-transform:uppercase;color:#9ca3af;margin-bottom:0.4rem}}
.kpi-val{{font-family:'Lora',serif;font-size:1.6rem;font-weight:600;line-height:1}}
.kpi-sub{{font-size:0.68rem;color:#9ca3af;margin-top:0.3rem}}
table{{width:100%;border-collapse:collapse;font-size:0.82rem}}
th{{background:#f0f2f8;color:#9ca3af;font-family:'DM Mono',monospace;font-size:0.54rem;letter-spacing:0.1em;text-transform:uppercase;padding:0.5rem 0.7rem;text-align:left}}
td{{padding:0.55rem 0.7rem;border-bottom:1px solid #e4e7f0}}
tr:last-child td{{border-bottom:none}}
.footer{{margin-top:3rem;padding-top:1rem;border-top:1px solid #e4e7f0;font-family:'DM Mono',monospace;font-size:0.58rem;color:#9ca3af;text-align:center}}
@media print{{body{{background:#fff}}.page{{padding:20px}}}}
</style></head><body><div class="page">
<h1>Observatoire web <em>sénégalais</em></h1>
<div class="meta">SenWebStats · Rapport exécutif · {datetime.now().strftime('%d %B %Y')} · {n_sites} sites · Modèle CTR AWR 2023</div>
<h2>Indicateurs clés</h2>
<div class="kpi-grid">
  <div class="kpi"><div class="kpi-bar" style="background:#0d9488"></div><div class="kpi-lbl">Sites suivis</div><div class="kpi-val" style="color:#0d9488">{n_sites}</div><div class="kpi-sub">5 catégories · Sénégal</div></div>
  <div class="kpi"><div class="kpi-bar" style="background:#2563eb"></div><div class="kpi-lbl">Trafic CTR estimé</div><div class="kpi-val" style="color:#2563eb">{fmt(total_tr)}</div><div class="kpi-sub">visites / mois</div></div>
  <div class="kpi"><div class="kpi-bar" style="background:#16a34a"></div><div class="kpi-lbl">Score moyen</div><div class="kpi-val" style="color:#16a34a">{avg_sc}</div><div class="kpi-sub">/ 100 points</div></div>
  <div class="kpi"><div class="kpi-bar" style="background:#7c3aed"></div><div class="kpi-lbl">Sites avec backlinks</div><div class="kpi-val" style="color:#7c3aed">{n_bl}</div><div class="kpi-sub">CommonCrawl analysés</div></div>
</div>
<h2>Répartition par catégorie</h2>
<table><tr><th>Catégorie</th><th style="text-align:right">Sites</th><th style="text-align:right">Score moy.</th><th style="text-align:right">Trafic total</th></tr>{cat_rows}</table>
<h2>Top 15 — Classement global</h2>
<table><tr><th>#</th><th>Site</th><th>Catégorie</th><th style="text-align:right">Score</th><th style="text-align:right">Position est.</th><th style="text-align:right">Trafic CTR/mois</th></tr>{top_rows}</table>
<div class="footer">SenWebStats · Observatoire numérique Afrique de l'Ouest · {datetime.now().year} · Données : CommonCrawl · PageSpeed Insights · Modèle CTR (AWR 2023)</div>
</div></body></html>"""

    return dcc.send_string(html_str, f"senwebstats_rapport_{datetime.now().strftime('%Y%m%d')}.html", type="text/html")


@app.callback(
    Output("fiche-content", "children"),
    Input("fiche-selector", "value"),
)
def render_fiche(site_name):
    if not site_name or df_all.empty:
        return html.Span()

    rows = df_all[df_all["name"] == site_name]
    if rows.empty:
        return empty_state("Site introuvable.")

    frow = rows.iloc[0]
    cat_color   = COLORS.get(frow["category"], "#0d9488")
    score_color = SCORE_COLOR(frow["score_global"])
    rank_pos    = int(rows.index[0]) + 1

    # Données perf supplémentaires
    df_perf_f = qry(f"""
        SELECT sp.lcp_ms, sp.fcp_ms, sp.ttfb_ms, sp.cls_score,
               sp.best_practices_score
        FROM site_performance sp
        JOIN sites s ON s.id = sp.site_id
        WHERE s.name = ?
        ORDER BY sp.measured_at DESC LIMIT 1
    """, params=(site_name,))

    detail_items = [
        ("Score autorité",   f"{frow['score_autorite']:.1f}/100"),
        ("Score qualité",    f"{frow['score_qualite']:.1f}/100"),
        ("Score technique",  f"{frow['score_technique']:.1f}/100"),
        ("Position SERP est.", f"#{int(frow.get('position_estimee', 0))}"),
        ("Performance",      f"{frow.get('performance_score', '—'):.0f}/100" if pd.notna(frow.get('performance_score')) else "—"),
        ("SEO",              f"{frow.get('seo_score', '—'):.0f}/100" if pd.notna(frow.get('seo_score')) else "—"),
        ("Accessibilité",    f"{frow.get('accessibility_score', '—'):.0f}/100" if pd.notna(frow.get('accessibility_score')) else "—"),
        ("Temps réponse",    f"{frow.get('response_time_ms', 0) or 0:.0f} ms"),
        ("SSL",              "Oui" if frow.get("has_ssl") == 1 else "Non"),
        ("Sitemap",          "Oui" if frow.get("has_sitemap") == 1 else "Non"),
        ("Backlinks",        fmt(frow.get("total_backlinks", 0) or 0)),
        ("Dom. référents",   fmt(frow.get("referring_domains", 0) or 0)),
    ]
    if not df_perf_f.empty:
        pr = df_perf_f.iloc[0]
        detail_items += [
            ("LCP",  f"{pr.get('lcp_ms', 0) or 0:.0f} ms"),
            ("FCP",  f"{pr.get('fcp_ms', 0) or 0:.0f} ms"),
            ("TTFB", f"{pr.get('ttfb_ms', 0) or 0:.0f} ms"),
            ("CLS",  f"{pr.get('cls_score', 0) or 0:.3f}"),
        ]

    n_cols = 6
    detail_cells = [
        html.Div([
            html.Div(lbl, className="fiche-detail-cell-label"),
            html.Div(val, className="fiche-detail-cell-value"),
        ], className="fiche-detail-cell",
           style={"borderRight": "1px solid #e4e7f0" if (i + 1) % n_cols != 0 else "none"})
        for i, (lbl, val) in enumerate(detail_items)
    ]

    return html.Div([
        html.Div([
            html.Div(f"{frow['category']} · {frow['domain']}", className="fiche-header-eyebrow"),
            html.Div(frow["name"], className="fiche-header-name"),
        ], className="fiche-header", style={"background": cat_color}),
        html.Div([
            html.Div([
                html.Div("Score global",  className="fiche-metric-label"),
                html.Div([
                    html.Span(f"{frow['score_global']:.1f}", className="fiche-metric-value",
                              style={"color": score_color}),
                    html.Span("/100", style={"fontSize": "0.9rem", "color": "#9ca3af"}),
                ]),
            ], className="fiche-metric", style={"borderRight": "1px solid #e4e7f0"}),
            html.Div([
                html.Div("Trafic CTR/mois", className="fiche-metric-label"),
                html.Div(fmt(frow["trafic_ctr"]), className="fiche-metric-value",
                         style={"color": "#7c3aed"}),
            ], className="fiche-metric", style={"borderRight": "1px solid #e4e7f0"}),
            html.Div([
                html.Div("Position SERP est.", className="fiche-metric-label"),
                html.Div(f"#{int(frow.get('position_estimee', 0))}", className="fiche-metric-value",
                         style={"color": "#2563eb"}),
            ], className="fiche-metric", style={"borderRight": "1px solid #e4e7f0"}),
            html.Div([
                html.Div("Classement général", className="fiche-metric-label"),
                html.Div(f"#{rank_pos} / {n_sites}", className="fiche-metric-value",
                         style={"color": "#0d9488"}),
            ], className="fiche-metric"),
        ], className="fiche-metrics", style={"gridTemplateColumns": "repeat(4, 1fr)"}),
        html.Div(detail_cells,
                 className="fiche-detail-grid",
                 style={"gridTemplateColumns": f"repeat({n_cols}, 1fr)"}),
    ], style={
        "background": "#fff",
        "border": "1px solid #e4e7f0",
        "borderRadius": "12px",
        "overflow": "hidden",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.06)",
    })


# ─────────────────────────────────────────────────────────────
# POINT D'ENTRÉE
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8050))
    debug = os.environ.get("DASH_DEBUG", "false").lower() == "true"
    print(f"\n  SenWebStats Dashboard — http://localhost:{port}")
    print(f"  DB : {find_db('senwebstats.db')}")
    print(f"  Semrush API : {'configuré' if _sem_ok else 'non configuré (proxy CTR utilisé)'}")
    print(f"  DataForSEO  : {'configuré' if _dfs_ok else 'non configuré'}\n")
    app.run(debug=debug, port=port, host="0.0.0.0")
