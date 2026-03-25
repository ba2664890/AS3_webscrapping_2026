"""
SenWebStats — Observatory v7 · Masterclass Design
Dark sidebar · Premium KPIs · Treemap · Scatter · Donut · Radar · Violin
"""
import sys, os, io, json, sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))
except ImportError:
    pass

try:
    from models.ctr_model import compute_ctr_scores, SerperDevClient, CATEGORY_BASE, CATEGORY_LABELS
    _CTR_OK = True
except Exception:
    _CTR_OK = False
    CATEGORY_BASE = {"presse":250000,"ecommerce":80000,"telephonie":120000,"banque_finance":60000,"emploi":40000}
    CATEGORY_LABELS = {"presse":"Presse & Medias","ecommerce":"E-commerce","telephonie":"Telephonie","banque_finance":"Banque & Finance","emploi":"Emploi"}

st.set_page_config(
    page_title="SenWebStats · Observatory",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — MASTERCLASS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Inter:wght@300;400;500;600;700&display=swap');

:root {
  --navy:         #0d1117;
  --navy-2:       #161b22;
  --navy-3:       #21262d;
  --emerald:      #10B981;
  --emerald-dim:  rgba(16,185,129,0.10);
  --blue:         #0EA5E9;
  --surface:      #f5f6f8;
  --card:         #ffffff;
  --alt:          #f3f4f6;
  --border:       rgba(0,0,0,0.055);
  --txt:          #111827;
  --txt-2:        #4B5563;
  --txt-3:        #9CA3AF;
  --shadow-md:    0 2px 8px rgba(0,0,0,0.05), 0 1px 2px rgba(0,0,0,0.04);
  --shadow-lg:    0 8px 24px rgba(0,0,0,0.07), 0 2px 6px rgba(0,0,0,0.04);
}

/* ── RESET ── */
#MainMenu,footer,header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display:none !important; }

html,body,[data-testid="stAppViewContainer"] {
  background:var(--surface) !important;
  font-family:'Inter',sans-serif !important;
  color:var(--txt) !important;
}
.block-container { padding:0 !important; max-width:100% !important; }

/* ── SIDEBAR LIGHT GLASS ── */
[data-testid="stSidebar"] {
  background: rgba(255,255,255,0.92) !important;
  backdrop-filter: blur(24px) !important;
  -webkit-backdrop-filter: blur(24px) !important;
  border-right: 1px solid rgba(14,165,233,0.10) !important;
  box-shadow: 4px 0 32px rgba(14,165,233,0.07), 1px 0 0 rgba(0,0,0,0.04) !important;
}
[data-testid="stSidebarContent"] { padding:0 !important; }

/* ── NAV ACTIVE DIV ── */
.nav-active {
  display:flex; align-items:center; gap:10px;
  padding:10px 14px; border-radius:10px; margin:0 0 3px;
  background: linear-gradient(135deg, rgba(14,165,233,0.10) 0%, rgba(99,102,241,0.06) 100%);
  color:#0369a1; font-weight:600; font-size:.8125rem;
  font-family:'Inter',sans-serif; letter-spacing:.01em;
  box-shadow: inset 3px 0 0 #0EA5E9, 0 2px 8px rgba(14,165,233,0.12);
  position:relative;
}
.nav-active::after {
  content:''; position:absolute; right:12px; top:50%; transform:translateY(-50%);
  width:6px; height:6px; border-radius:50%;
  background:#0EA5E9;
  box-shadow:0 0 6px 2px rgba(14,165,233,0.5);
}

/* ── NAV BUTTONS (inactive) ── */
[data-testid="stSidebar"] .stButton > button {
  background:transparent !important;
  color:rgba(55,65,81,0.55) !important;
  border:none !important; border-radius:10px !important;
  text-align:left !important; justify-content:flex-start !important;
  padding:10px 14px !important; margin:0 0 3px !important;
  font-size:.8125rem !important; font-weight:400 !important;
  font-family:'Inter',sans-serif !important; letter-spacing:.01em !important;
  width:100% !important; transition:all .18s cubic-bezier(.4,0,.2,1) !important;
  box-shadow:none !important; min-height:0 !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background:rgba(14,165,233,0.06) !important;
  color:#0369a1 !important;
}
[data-testid="stSidebar"] .stButton > button:focus { box-shadow:none !important; }

/* ── SIDEBAR SELECTBOX ── */
[data-testid="stSidebar"] [data-testid="stSelectbox"] > div > div,
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background:rgba(241,245,249,0.8) !important;
  border:1px solid rgba(14,165,233,0.15) !important; border-radius:8px !important;
  color:#374151 !important; font-size:.8125rem !important;
}

/* ── MAIN INPUTS ── */
[data-testid="stMultiSelect"] > div {
  background:var(--card) !important;
  border:1px solid var(--border) !important; border-radius:8px !important;
}
[data-testid="stMultiSelect"] span {
  background:#dbeafe !important; color:#1e40af !important;
  border:none !important; border-radius:6px !important;
  font-size:.6875rem !important; font-weight:500 !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
  background:var(--emerald) !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] { border-radius:12px !important; overflow:hidden !important; }
[data-testid="stDataFrame"] th {
  background:var(--alt) !important; color:var(--txt-2) !important;
  font-size:.6875rem !important; letter-spacing:.08em !important;
  text-transform:uppercase !important; font-weight:600 !important;
}
[data-testid="stDataFrame"] td {
  color:var(--txt) !important; font-size:.875rem !important; background:var(--card) !important;
}

/* ── BUTTONS ── */
.stButton > button {
  background:var(--navy) !important; color:#fff !important;
  border:none !important; border-radius:8px !important;
  font-weight:500 !important; font-size:.875rem !important;
  padding:10px 20px !important; transition:opacity .18s !important;
}
.stButton > button:hover { opacity:.82 !important; }
[data-testid="stDownloadButton"] > button {
  background:var(--emerald) !important; color:#fff !important;
  border:none !important; border-radius:8px !important; font-weight:500 !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width:3px; height:3px; }
::-webkit-scrollbar-track { background:rgba(241,245,249,0.6); }
::-webkit-scrollbar-thumb { background:rgba(14,165,233,0.28); border-radius:3px; }

/* ── LAYOUT ── */
.mwrap { padding:2.5rem 3rem 6rem; }

/* ── ANIMATIONS ── */
@keyframes fade-up {
  from { opacity:0; transform:translateY(14px); }
  to   { opacity:1; transform:translateY(0); }
}
.anim-0 { animation:fade-up .45s ease both; }
.anim-1 { animation:fade-up .45s .07s ease both; }
.anim-2 { animation:fade-up .45s .14s ease both; }
.anim-3 { animation:fade-up .45s .21s ease both; }
.anim-4 { animation:fade-up .45s .28s ease both; }

/* ── PAGE HEADER ── */
.ph-wrap { margin-bottom:2.5rem; animation:fade-up .5s ease both; }
.ph-eyebrow {
  font-family:'Inter',sans-serif; font-size:.625rem; font-weight:700;
  color:var(--emerald); letter-spacing:.16em; text-transform:uppercase;
  margin-bottom:10px; display:flex; align-items:center; gap:8px;
}
.ph-dot {
  width:6px; height:6px; border-radius:50%;
  background:var(--emerald); display:inline-block;
  animation:pulse-dot 2.4s ease infinite;
}
@keyframes pulse-dot {
  0%,100% { opacity:1; transform:scale(1); }
  50%      { opacity:.35; transform:scale(.7); }
}
.ph-title {
  font-family:'Manrope',sans-serif; font-size:2.25rem; font-weight:800;
  color:var(--txt); line-height:1.1; letter-spacing:-.03em; margin:0 0 10px;
}
.ph-title .acc { color:var(--emerald); }
.ph-sub {
  font-family:'Inter',sans-serif; font-size:.9375rem;
  color:var(--txt-2); margin:0; line-height:1.65; font-weight:400;
}

/* ── KPI MASTERCLASS ── */
.kpi-wrap {
  background:var(--card); border-radius:16px;
  padding:24px 24px 20px; box-shadow:var(--shadow-lg);
  position:relative; overflow:hidden;
}
.kpi-wrap::before {
  content:''; position:absolute; top:0; left:0; right:0; height:3px;
  background:var(--kpi-c,var(--emerald)); border-radius:16px 16px 0 0;
}
.kpi-wrap::after {
  content:''; position:absolute; top:-20px; right:-20px;
  width:100px; height:100px; border-radius:50%;
  background:var(--kpi-c,var(--emerald)); opacity:.04;
}
.kpi-label {
  font-family:'Inter',sans-serif; font-size:.625rem; font-weight:700;
  color:var(--txt-3); letter-spacing:.14em; text-transform:uppercase; margin-bottom:12px;
}
.kpi-value {
  font-family:'Manrope',sans-serif; font-size:2.6rem; font-weight:800;
  color:var(--txt); line-height:1; letter-spacing:-.04em; margin-bottom:4px;
}
.kpi-sub {
  font-family:'Inter',sans-serif; font-size:.75rem;
  color:var(--txt-3); line-height:1.4; margin-bottom:14px;
}
.kpi-badge {
  display:inline-flex; align-items:center; gap:4px;
  padding:3px 9px; border-radius:6px;
  font-family:'Inter',sans-serif; font-size:.625rem; font-weight:700;
  letter-spacing:.06em; text-transform:uppercase;
}
.badge-up   { background:#dcfce7; color:#15803d; }
.badge-down { background:#fee2e2; color:#b91c1c; }
.badge-flat { background:var(--alt); color:var(--txt-3); }
.kpi-track { height:2px; background:var(--alt); border-radius:2px; overflow:hidden; margin-top:14px; }
.kpi-fill  { height:100%; border-radius:2px; background:var(--kpi-c,var(--emerald)); }

/* ── SECTION LABEL ── */
.sec {
  font-family:'Inter',sans-serif; font-size:.625rem; font-weight:700;
  color:var(--txt-3); letter-spacing:.14em; text-transform:uppercase;
  margin:2.5rem 0 1.25rem; display:flex; align-items:center; gap:12px;
}
.sec::after { content:''; flex:1; height:1px; background:var(--border); }

/* ── CARD ── */
.crd { background:var(--card); border-radius:16px; overflow:hidden; box-shadow:var(--shadow-md); }
.crd-hd {
  padding:14px 20px; background:var(--alt);
  font-family:'Inter',sans-serif; font-size:.625rem; font-weight:700;
  color:var(--txt-3); letter-spacing:.1em; text-transform:uppercase;
  display:flex; justify-content:space-between; border-bottom:1px solid var(--border);
}

/* ── RANK ROW ── */
.rrow { display:grid; grid-template-columns:2rem 1fr auto auto; align-items:center; padding:11px 20px; gap:12px; transition:background .12s; }
.rrow:hover { background:var(--alt); }
.rn   { font-family:'Manrope',sans-serif; font-size:.75rem; color:var(--txt-3); text-align:right; font-weight:700; }
.rname{ font-size:.875rem; font-weight:600; color:var(--txt); font-family:'Inter',sans-serif; }
.rcat { font-size:.6875rem; color:var(--txt-3); margin-top:2px; font-family:'Inter',sans-serif; }
.rbar-w { height:2px; border-radius:2px; background:var(--alt); margin-top:6px; overflow:hidden; }
.rbar   { height:100%; border-radius:2px; }
.rscr { font-family:'Manrope',sans-serif; font-size:.9375rem; font-weight:800; text-align:right; }
.rtrf { font-family:'Inter',sans-serif; font-size:.75rem; color:var(--emerald); text-align:right; white-space:nowrap; font-weight:500; }

/* ── INFO BOX ── */
.ibox { background:#eff6ff; color:#1e40af; border-radius:12px; padding:16px 20px; font-size:.875rem; margin:1rem 0; border:1px solid #bfdbfe; }

/* ── PILLS ── */
.pills { display:flex; gap:.5rem; flex-wrap:wrap; margin-bottom:2rem; }
.pill  { display:inline-flex; align-items:center; gap:.4rem; padding:.3rem .8rem; border-radius:6px; font-size:.6875rem; font-weight:500; font-family:'Inter',sans-serif; }
.pill-ok   { background:#f0fdf4; color:#15803d; border:1px solid #bbf7d0; }
.pill-warn { background:#fffbeb; color:#b45309; border:1px solid #fde68a; }
.pill-gray { background:var(--alt); color:var(--txt-3); border:1px solid var(--border); }

/* ── DARK CARD ── */
.dark-crd { background:linear-gradient(135deg,#0d1117,#1a2332); border-radius:16px; padding:24px; color:#fff; }

/* ── CHART CARD ── */
.chart-card { background:var(--card); border-radius:16px; padding:8px 8px 4px; box-shadow:var(--shadow-md); overflow:hidden; margin-bottom:1.5rem; }

/* ── GAUGE ROW ── */
.gauge-lbl {
  font-family:'Manrope',sans-serif; font-size:1.5rem; font-weight:800;
  color:var(--txt); text-align:center; line-height:1; margin-bottom:2px;
}
.gauge-sub { font-family:'Inter',sans-serif; font-size:.6875rem; color:var(--txt-3); text-align:center; }

/* ══════════════════════════════════════════════════════════
   PREMIUM DATA TABLE  —  SaaS Analytics style
   ══════════════════════════════════════════════════════════ */
.ptbl-outer {
  background: rgba(255,255,255,0.92);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 32px rgba(14,165,233,0.09), 0 1px 4px rgba(0,0,0,0.04);
  border: 1px solid rgba(14,165,233,0.10);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  margin-bottom: 1.5rem;
  overflow-x: auto;
}
.ptbl-outer table {
  width: 100%; border-collapse: collapse;
  font-family: 'Inter', sans-serif;
}
.ptbl-outer thead {
  position: sticky; top: 0; z-index: 2;
}
.ptbl-outer thead tr {
  background: linear-gradient(135deg,rgba(14,165,233,0.07) 0%,rgba(99,102,241,0.05) 100%);
  border-bottom: 1.5px solid rgba(14,165,233,0.12);
}
.ptbl-outer th {
  padding: 13px 18px;
  font-size: .5625rem; font-weight: 700;
  letter-spacing: .13em; text-transform: uppercase;
  color: #64748b; text-align: left; white-space: nowrap;
  font-family: 'Inter', sans-serif;
}
.ptbl-outer td {
  padding: 11px 18px;
  font-size: .8125rem; color: #1e293b;
  border-bottom: 1px solid rgba(14,165,233,0.05);
  font-family: 'Inter', sans-serif;
  white-space: nowrap;
}
.ptbl-outer tbody tr { transition: background .14s ease; }
.ptbl-outer tbody tr:hover td {
  background: rgba(14,165,233,0.05);
  box-shadow: inset 3px 0 0 rgba(14,165,233,0.30);
}
.ptbl-outer tbody tr:last-child td { border-bottom: none; }
.ptbl-outer .td-num {
  font-family: 'Manrope', sans-serif;
  font-weight: 700; color: #0f172a;
  font-variant-numeric: tabular-nums;
}
.ptbl-outer .td-score {
  font-family: 'Manrope', sans-serif;
  font-weight: 800; font-size: .875rem;
}
.ptbl-outer .td-chip {
  display: inline-flex; align-items: center;
  padding: 3px 9px; border-radius: 5px;
  font-size: .625rem; font-weight: 600; letter-spacing: .05em;
  white-space: nowrap;
}
.ptbl-outer .chip-blue   { background:rgba(14,165,233,0.10); color:#0369a1; }
.ptbl-outer .chip-green  { background:rgba(16,185,129,0.10); color:#047857; }
.ptbl-outer .chip-purple { background:rgba(139,92,246,0.10); color:#6d28d9; }
.ptbl-outer .chip-amber  { background:rgba(245,158,11,0.10); color:#b45309; }
.ptbl-outer .chip-red    { background:rgba(239,68,68,0.10);  color:#b91c1c; }
.ptbl-outer .chip-gray   { background:rgba(107,114,128,0.10);color:#374151; }
.ptbl-outer .td-bar-wrap { display:flex; align-items:center; gap:8px; min-width:90px; }
.ptbl-outer .td-bar-bg   { flex:1; height:3px; background:rgba(14,165,233,0.10); border-radius:3px; overflow:hidden; }
.ptbl-outer .td-bar-fill { height:100%; border-radius:3px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNEES
# ══════════════════════════════════════════════════════════════════════════════
def find_db(name="senwebstats.db"):
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
def get_conn():
    p = find_db()
    if not p:
        return None
    c = sqlite3.connect(p, check_same_thread=False)
    c.row_factory = sqlite3.Row
    return c

def q(sql, params=()):
    c = get_conn()
    if c is None:
        return pd.DataFrame()
    try:
        return pd.read_sql_query(sql, c, params=params)
    except Exception:
        return pd.DataFrame()

def sv(sql, col="n", default=0):
    try:
        df = q(sql)
        if df.empty or col not in df.columns:
            return default
        v = df[col].values[0]
        return v if v is not None else default
    except Exception:
        return default


# ══════════════════════════════════════════════════════════════════════════════
# CALCUL DES SCORES
# ══════════════════════════════════════════════════════════════════════════════
def _normalize(s, invert=False):
    mn, mx = s.min(), s.max()
    if mx == mn:
        return pd.Series([50.0] * len(s), index=s.index)
    n = (s - mn) / (mx - mn) * 100
    return (100 - n) if invert else n

@st.cache_data(ttl=300)
def compute_scores():
    sites = q("SELECT id, name, domain, category FROM sites ORDER BY category, name")
    if sites.empty:
        return pd.DataFrame()

    meta = q("""SELECT site_id, response_time_ms, word_count,
                       internal_links_count, external_links_count,
                       images_count, has_ssl, has_sitemap, has_robots_txt, status_code
               FROM site_metadata sm
               WHERE crawled_at=(SELECT MAX(crawled_at) FROM site_metadata WHERE site_id=sm.site_id)""")

    perf = q("""SELECT site_id, performance_score, seo_score, accessibility_score,
                       best_practices_score, lcp_ms, fcp_ms, ttfb_ms, cls_score
               FROM site_performance sp
               WHERE measured_at=(SELECT MAX(measured_at) FROM site_performance WHERE site_id=sp.site_id)""")

    bl = q("""SELECT site_id, total_backlinks, referring_domains, backlinks_change
              FROM site_backlinks sb
              WHERE collected_at=(SELECT MAX(collected_at) FROM site_backlinks WHERE site_id=sb.site_id)""")

    df = sites.copy()
    for other in [meta, perf, bl]:
        if not other.empty:
            df = df.merge(other, left_on="id", right_on="site_id", how="left")
            if "site_id" in df.columns:
                df = df.drop(columns=["site_id"])

    fills = {
        "total_backlinks": 0, "referring_domains": 0, "backlinks_change": 0,
        "seo_score": 50, "performance_score": 50, "accessibility_score": 50,
        "best_practices_score": 50, "lcp_ms": 3000, "fcp_ms": 2000,
        "ttfb_ms": 1000, "cls_score": 0.1,
        "response_time_ms": 3000, "has_ssl": 0, "has_sitemap": 0,
        "has_robots_txt": 0, "word_count": 0, "internal_links_count": 0,
        "external_links_count": 0, "images_count": 0, "status_code": 200,
    }
    for col, val in fills.items():
        if col not in df.columns:
            df[col] = val
        else:
            df[col] = df[col].fillna(val)

    df["score_autorite"]  = (_normalize(df["total_backlinks"]) * 0.6 +
                              _normalize(df["referring_domains"]) * 0.4).round(1)
    df["score_qualite"]   = (df["seo_score"] * 0.40 +
                              df["performance_score"] * 0.35 +
                              df["accessibility_score"] * 0.25).round(1)
    df["score_technique"] = (_normalize(df["response_time_ms"], invert=True) * 0.40 +
                              df["has_ssl"] * 100 * 0.20 +
                              df["has_sitemap"] * 100 * 0.15 +
                              _normalize(df["word_count"]) * 0.25).round(1)
    df["score_global"]    = (df["score_autorite"] * 0.45 +
                              df["score_qualite"] * 0.35 +
                              df["score_technique"] * 0.20).round(1)

    if _CTR_OK:
        try:
            df = compute_ctr_scores(df)
            df["trafic_estime"] = df["trafic_ctr"]
        except Exception:
            df["trafic_estime"] = df.apply(
                lambda r: int(CATEGORY_BASE.get(r["category"], 50000) * (r["score_global"] / 100) ** 1.5), axis=1)
            df["trafic_ctr"] = df["trafic_estime"]
            df["position_estimee"] = 10
    else:
        df["trafic_estime"] = df.apply(
            lambda r: int(CATEGORY_BASE.get(r["category"], 50000) * (r["score_global"] / 100) ** 1.5), axis=1)
        df["trafic_ctr"] = df["trafic_estime"]
        df["position_estimee"] = 10

    return df.sort_values("score_global", ascending=False).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# THEME PLOTLY + HELPERS GRAPHIQUES
# ══════════════════════════════════════════════════════════════════════════════
CAT_COLORS = {
    "presse":         "#0EA5E9",
    "ecommerce":      "#10B981",
    "telephonie":     "#8B5CF6",
    "banque_finance": "#F59E0B",
    "emploi":         "#EF4444",
}
CHART_PAL = ["#0EA5E9","#10B981","#F59E0B","#8B5CF6","#EF4444","#06B6D4","#F472B6","#84CC16"]
CAT_LABEL = {
    "presse": "Presse", "ecommerce": "E-commerce",
    "telephonie": "Telecom", "banque_finance": "Finance", "emploi": "Emploi",
}

_HOVER = dict(bgcolor="rgba(15,20,30,0.92)", bordercolor="rgba(0,0,0,0)",
              font=dict(family="Inter", size=12, color="#ffffff"))
_GX = dict(showgrid=True, gridcolor="rgba(107,114,128,0.08)", gridwidth=1,
           linecolor="rgba(0,0,0,0)", zeroline=False, showline=False,
           tickfont=dict(size=10, color="#9CA3AF", family="Inter"))
_GY = dict(**_GX)


def hex_alpha(color, alpha=0.13):
    c = color.lstrip("#")
    r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def base_layout(title="", height=420, margin=None):
    m = margin or dict(l=0, r=0, t=(52 if title else 16), b=0)
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(family="Inter, sans-serif", color="#6B7280", size=11),
        margin=m,
        xaxis=dict(**_GX),
        yaxis=dict(**_GY),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                    bgcolor="rgba(0,0,0,0)",
                    font=dict(size=11, color="#4B5563", family="Inter")),
        hovermode="closest",
        hoverlabel=dict(**_HOVER),
        transition=dict(duration=400, easing="cubic-in-out"),
    )
    if title:
        layout["title"] = dict(
            text=title,
            font=dict(family="Manrope, sans-serif", size=14, color="#111827"),
            x=0, pad=dict(l=0, b=16),
        )
    return layout


def donut_gauge(value, max_val=100, title="", color="auto", height=200):
    """Donut gauge premium pour un score."""
    pct = min(max(float(value) / max_val, 0), 1)
    if color == "auto":
        color = "#10B981" if pct >= 0.7 else "#F59E0B" if pct >= 0.4 else "#EF4444"
    fig = go.Figure(go.Pie(
        values=[pct, 1 - pct], hole=0.74,
        marker=dict(colors=[color, "#F3F4F6"], line=dict(color="rgba(0,0,0,0)", width=0)),
        direction="clockwise", sort=False,
        showlegend=False, hoverinfo="skip", textinfo="none",
    ))
    fig.add_annotation(
        text=f"<b>{value:.1f}</b>",
        x=0.5, y=0.56, showarrow=False, xref="paper", yref="paper",
        font=dict(family="Manrope, sans-serif", size=24, color="#111827"),
    )
    fig.add_annotation(
        text=title,
        x=0.5, y=0.36, showarrow=False, xref="paper", yref="paper",
        font=dict(family="Inter, sans-serif", size=10, color="#9CA3AF"),
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        height=height, margin=dict(l=10, r=10, t=10, b=10),
        hoverlabel=dict(**_HOVER),
    )
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES UI
# ══════════════════════════════════════════════════════════════════════════════
def fmt(n):
    try:
        return f"{int(n):,}".replace(",", "\u202f")
    except Exception:
        return "—"

def sc_color(v):
    if v is None: return "#9CA3AF"
    if v >= 60: return "#10B981"
    if v >= 40: return "#F59E0B"
    return "#EF4444"

def page_header(eyebrow, title_html, subtitle):
    st.markdown(f"""
    <div class="ph-wrap">
      <div class="ph-eyebrow"><div class="ph-dot"></div>{eyebrow}</div>
      <div class="ph-title">{title_html}</div>
      <p class="ph-sub">{subtitle}</p>
    </div>
    """, unsafe_allow_html=True)

def kpi_master(label, value, subtext, badge_txt, badge_cls, progress, color, delay=0):
    bar_pct = int(min(max(progress, 0), 1) * 100)
    return f"""
    <div class="kpi-wrap anim-{delay}" style="--kpi-c:{color}">
      <div class="kpi-label">{label}</div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub">{subtext}</div>
      <div class="kpi-badge {badge_cls}">{badge_txt}</div>
      <div class="kpi-track"><div class="kpi-fill" style="width:{bar_pct}%"></div></div>
    </div>"""

def section_label(text):
    st.markdown(f'<div class="sec">{text}</div>', unsafe_allow_html=True)


_CAT_CHIP = {
    "presse":         "chip-blue",
    "ecommerce":      "chip-green",
    "telephonie":     "chip-purple",
    "banque_finance": "chip-amber",
    "emploi":         "chip-red",
}

def _cell(val, col_name, df_ref=None):
    """Render a single table cell as HTML."""
    num_cols = {"global","autorite","qualite","technique","score","performance","seo",
                "accessibilite","best practices","lcp(ms)","fcp(ms)","ttfb(ms)","cls",
                "trafic/mois","pages indexees","dom. referents","variation","risque/100",
                "temps(ms)","mots","score global"}
    key = col_name.lower().strip()
    # Score columns — colored number
    if key in {"global","autorite","qualite","technique","score global","score"}:
        try:
            v = float(val)
            c = sc_color(v)
            return f'<td class="td-score" style="color:{c}">{v:.1f}</td>'
        except Exception:
            pass
    # Numeric columns
    if key in num_cols:
        try:
            v = float(val)
            if v == int(v):
                return f'<td class="td-num">{int(v):,}</td>'
            return f'<td class="td-num">{v:.1f}</td>'
        except Exception:
            pass
    # Secteur chip
    if key == "secteur":
        raw = str(val).lower().replace(" ","_").replace("&","").replace("-","_").strip("_")
        chip = _CAT_CHIP.get(raw, "chip-gray")
        label = CAT_LABEL.get(raw, str(val))
        return f'<td><span class="td-chip {chip}">{label}</span></td>'
    # Boolean-like
    if str(val).lower() in {"oui","yes","1"}:
        return '<td><span class="td-chip chip-green">Oui</span></td>'
    if str(val).lower() in {"non","no","0"}:
        return '<td><span class="td-chip chip-red">Non</span></td>'
    # Default
    return f'<td>{val}</td>'


def html_table(df, max_rows=50):
    """Generate a premium SaaS-style HTML data table."""
    if df is None or df.empty:
        return '<div class="ibox">Aucune donnee.</div>'
    df = df.head(max_rows)
    # Header
    ths = "".join(f"<th>{c}</th>" for c in df.columns)
    # Rows
    rows_html = []
    for _, row in df.iterrows():
        cells = "".join(_cell(row[c], c, df) for c in df.columns)
        rows_html.append(f"<tr>{cells}</tr>")
    body = "".join(rows_html)
    return f'<div class="ptbl-outer"><table><thead><tr>{ths}</tr></thead><tbody>{body}</tbody></table></div>'


def make_treemap(df, value_col, color_col=None, label_col="name", cat_col="category",
                 title="", height=420):
    """Build a go.Treemap with proper parent node ids (avoids silent render failure)."""
    cats = df[cat_col].unique()
    ids     = [f"__c__{c}" for c in cats] + list(df[label_col])
    labels  = [CAT_LABEL.get(c, c) for c in cats] + list(df[label_col])
    parents = [""] * len(cats) + [f"__c__{c}" for c in df[cat_col]]
    values  = [0] * len(cats) + list(df[value_col].clip(lower=0))
    if color_col and color_col in df.columns:
        # numeric color scale — assign category average for parent
        cat_avg = {c: df[df[cat_col]==c][color_col].mean() for c in cats}
        colors  = [cat_avg[c] for c in cats] + list(df[color_col])
        marker  = dict(
            colors=colors,
            colorscale=[[0,"#EFF6FF"],[0.35,"#93C5FD"],[0.65,"#3B82F6"],[1,"#1E3A8A"]],
            showscale=True,
            colorbar=dict(thickness=8, len=0.6, outlinewidth=0,
                          tickfont=dict(size=9, color="#9CA3AF")),
            line=dict(width=2, color="#f5f6f8"), pad=dict(t=4,l=4,r=4,b=4),
        )
    else:
        cat_colors = [CAT_COLORS.get(c, "#0EA5E9") for c in cats]
        site_colors = [CAT_COLORS.get(c, "#0EA5E9") for c in df[cat_col]]
        marker = dict(
            colors=cat_colors + site_colors,
            line=dict(width=2, color="#f5f6f8"), pad=dict(t=4,l=4,r=4,b=4),
        )
    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values,
        textfont=dict(family="Inter", size=11, color="white"),
        hovertemplate="<b>%{label}</b><br>%{value:,.1f}<extra></extra>",
        marker=marker,
    ))
    lay = base_layout(title, height)
    lay["margin"] = dict(l=0, r=0, t=(40 if title else 0), b=0)
    fig.update_layout(**lay)
    return fig


def make_sunburst(df, value_col, label_col="name", cat_col="category", height=420):
    """Build a go.Sunburst with proper parent node ids."""
    cats    = df[cat_col].unique()
    ids     = [f"__c__{c}" for c in cats] + list(df[label_col])
    labels  = [CAT_LABEL.get(c, c) for c in cats] + list(df[label_col])
    parents = [""] * len(cats) + [f"__c__{c}" for c in df[cat_col]]
    values  = [0] * len(cats) + list(df[value_col].clip(lower=1))
    cat_col_colors  = [CAT_COLORS.get(c, "#0EA5E9") for c in cats]
    site_colors = [CAT_COLORS.get(c, "#0EA5E9") for c in df[cat_col]]
    fig = go.Figure(go.Sunburst(
        ids=ids, labels=labels, parents=parents, values=values,
        marker=dict(colors=cat_col_colors + site_colors, line=dict(width=1.5, color="#f5f6f8")),
        textfont=dict(family="Inter", size=11),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>",
    ))
    lay = base_layout(height=height)
    lay["margin"] = dict(l=0, r=0, t=0, b=0)
    fig.update_layout(**lay)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
df_all    = compute_scores()
n_sites   = sv("SELECT COUNT(*) as n FROM sites")
n_crawled = sv("SELECT COUNT(DISTINCT site_id) as n FROM site_metadata")
n_perf    = sv("SELECT COUNT(DISTINCT site_id) as n FROM site_performance")
n_bl      = sv("SELECT COUNT(DISTINCT site_id) as n FROM site_backlinks")
total_tr  = int(df_all["trafic_estime"].sum()) if not df_all.empty else 0
avg_sc    = round(df_all["score_global"].mean(), 1) if not df_all.empty else 0
now       = datetime.now().strftime("%d %b %Y · %H:%M")

try:
    serper_ok = SerperDevClient().is_configured()
except Exception:
    serper_ok = False


# ══════════════════════════════════════════════════════════════════════════════
# NAVIGATION STATE
# ══════════════════════════════════════════════════════════════════════════════
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

NAV = [
    ("dashboard",  "Dashboard"),
    ("scoring",    "Scoring & Trafic"),
    ("meta",       "Metadonnees"),
    ("perf",       "Performance"),
    ("backlinks",  "Backlinks"),
    ("compare",    "Comparaison"),
    ("veille",     "Veille & Tendances"),
    ("export",     "Rapports & Export"),
]


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    api_pill = (
        '<span style="background:rgba(16,185,129,0.12);color:#059669;'
        'border:1px solid rgba(16,185,129,0.25);'
        'border-radius:6px;padding:2px 8px;font-size:.6rem;font-weight:700;'
        'letter-spacing:.08em;text-transform:uppercase">Serper actif</span>'
        if serper_ok else
        '<span style="background:rgba(14,165,233,0.08);color:#0369a1;'
        'border:1px solid rgba(14,165,233,0.18);'
        'border-radius:6px;padding:2px 8px;font-size:.6rem;font-weight:600;'
        'letter-spacing:.08em;text-transform:uppercase">Proxy CTR</span>'
    )
    st.markdown(f"""
    <div style="padding:2rem 1.5rem 1.5rem">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:.35rem">
        <div style="width:30px;height:30px;border-radius:8px;
                    background:linear-gradient(135deg,#0EA5E9,#6366F1);
                    display:flex;align-items:center;justify-content:center;
                    box-shadow:0 4px 12px rgba(14,165,233,0.35)">
          <span style="font-family:Manrope,sans-serif;font-size:.85rem;font-weight:800;color:#fff">S</span>
        </div>
        <div style="font-family:Manrope,sans-serif;font-size:1.15rem;font-weight:800;
                    color:#0f172a;letter-spacing:-.025em;line-height:1">
          Sen<span style="background:linear-gradient(135deg,#0EA5E9,#6366F1);
                          -webkit-background-clip:text;-webkit-text-fill-color:transparent">Web</span>Stats
        </div>
      </div>
      <div style="font-family:Inter,sans-serif;font-size:.5625rem;font-weight:600;
                  color:rgba(15,23,42,0.35);letter-spacing:.18em;
                  text-transform:uppercase;margin-bottom:.75rem">
        National Observatory
      </div>
      <div>{api_pill}</div>
    </div>
    <div style="height:1px;background:rgba(14,165,233,0.10);margin:0 1.5rem .5rem"></div>
    <div style="padding:.5rem 1.5rem .25rem;font-family:Inter,sans-serif;font-size:.5625rem;
                font-weight:700;color:rgba(15,23,42,0.28);letter-spacing:.18em;
                text-transform:uppercase">Navigation</div>
    <div style="padding:0 .75rem">
    """, unsafe_allow_html=True)

    for pid, label in NAV:
        if st.session_state.page == pid:
            st.markdown(f'<div class="nav-active">{label}</div>', unsafe_allow_html=True)
        else:
            if st.button(label, key=f"nav_{pid}", use_container_width=True):
                st.session_state.page = pid
                st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

    # Filtre secteur
    st.markdown("""
    <div style="height:1px;background:rgba(14,165,233,0.10);margin:1rem 1.5rem .75rem"></div>
    <div style="padding:.25rem 1.5rem .5rem;font-family:Inter,sans-serif;font-size:.5625rem;
                font-weight:700;color:rgba(15,23,42,0.28);letter-spacing:.18em;
                text-transform:uppercase">Secteur</div>
    <div style="padding:0 .75rem">
    """, unsafe_allow_html=True)
    cats_df  = q("SELECT DISTINCT category FROM sites ORDER BY category")
    cat_opts = ["Tous secteurs"] + (list(cats_df["category"].values) if not cats_df.empty else [])
    cat_f    = st.selectbox("cat", cat_opts, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div style="position:absolute;bottom:0;left:0;right:0;
                padding:1rem 1.5rem;
                border-top:1px solid rgba(14,165,233,0.10);
                background:rgba(248,250,252,0.8)">
      <div style="font-family:Inter,sans-serif;font-size:.5625rem;
                  color:rgba(15,23,42,0.35);line-height:2;letter-spacing:.04em">
        {n_sites} sites · 5 secteurs<br>{now}
      </div>
    </div>
    """, unsafe_allow_html=True)

page    = st.session_state.page
df_f    = df_all if cat_f == "Tous secteurs" else df_all[df_all["category"] == cat_f]
cat_sql = "" if cat_f == "Tous secteurs" else f"AND s.category = '{cat_f}'"


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "dashboard":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "Live · Observatoire National",
        'Observatoire Web <span class="acc">Senegalais</span>',
        f"Analyse continue de {n_sites} sites — presse, e-commerce, telecom, finance, emploi",
    )

    p1 = "pill-ok" if n_crawled > 0 else "pill-gray"
    p2 = "pill-ok" if n_perf > 0 else "pill-warn"
    p3 = "pill-ok" if n_bl > 0 else "pill-warn"
    st.markdown(f"""
    <div class="pills">
      <div class="pill {p1}"><div style="width:5px;height:5px;border-radius:50%;background:currentColor"></div>
        Metadonnees {"OK" if n_crawled>0 else "en attente"}
      </div>
      <div class="pill {p2}"><div style="width:5px;height:5px;border-radius:50%;background:currentColor"></div>
        PageSpeed {"OK" if n_perf>0 else "en attente"}
      </div>
      <div class="pill {p3}"><div style="width:5px;height:5px;border-radius:50%;background:currentColor"></div>
        Backlinks {"OK" if n_bl>0 else "en attente"}
      </div>
      <div class="pill {"pill-ok" if serper_ok else "pill-gray"}">
        <div style="width:5px;height:5px;border-radius:50%;background:currentColor"></div>
        Serper.dev {"actif" if serper_ok else "proxy CTR"}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # KPI row
    k1, k2, k3, k4, k5 = st.columns(5, gap="medium")
    kpi_data = [
        ("Sites suivis",       str(n_sites),    "5 secteurs · Senegal",     "Actif",     "badge-up",   1.0,        "#0EA5E9", 0),
        ("Trafic total",       fmt(total_tr),   "visites estimees / mois",  "CTR model", "badge-flat", 0.75,       "#10B981", 1),
        ("Score moyen",        f"{avg_sc}",     "sur 100 pts",              "Composite", "badge-flat", avg_sc/100, "#8B5CF6", 2),
        ("PageSpeed",          str(n_perf),     "sites analyses",           "Lighthouse","badge-up",   n_perf/max(n_sites,1), "#F59E0B", 3),
        ("Backlinks",          str(n_bl),       "sites avec donnees",       "CommonCrawl","badge-up",  n_bl/max(n_sites,1),   "#EF4444", 4),
    ]
    for col, (lbl, val, sub, badge, bcls, prog, color, delay) in zip([k1,k2,k3,k4,k5], kpi_data):
        col.markdown(kpi_master(lbl, val, sub, badge, bcls, prog, color, delay), unsafe_allow_html=True)

    st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)

    # ── TOP 15 pleine largeur ──────────────────────────────────────────────────
    section_label("Classement global — Top 15")
    st.markdown('<div class="crd"><div class="crd-hd"><span>Site · Secteur</span><span>Score · Trafic / mois</span></div>', unsafe_allow_html=True)
    if not df_all.empty:
        top15 = df_all.head(15)
        mx = df_all["score_global"].max()
        # Affichage en 3 colonnes pour occuper toute la largeur
        chunk = [top15.iloc[i:i+5] for i in range(0, 15, 5)]
        rank_cols = st.columns(3, gap="large")
        for ci, (col, grp) in enumerate(zip(rank_cols, chunk)):
            with col:
                st.markdown('<div class="crd" style="overflow:hidden">', unsafe_allow_html=True)
                for i, (_, row) in enumerate(grp.iterrows()):
                    abs_rank = ci * 5 + i + 1
                    pct   = int(row["score_global"] / mx * 100) if mx > 0 else 0
                    color = sc_color(row["score_global"])
                    cat_c = CAT_COLORS.get(row["category"], "#9CA3AF")
                    st.markdown(f"""
                    <div class="rrow">
                      <div class="rn">{abs_rank:02d}</div>
                      <div>
                        <div class="rname">{row['name']}</div>
                        <div class="rcat" style="color:{cat_c}">{CAT_LABEL.get(row['category'], row['category'])}</div>
                        <div class="rbar-w"><div class="rbar" style="width:{pct}%;background:{color}"></div></div>
                      </div>
                      <div class="rscr" style="color:{color}">{row['score_global']:.1f}<span style="font-size:.65rem;color:#9CA3AF">/100</span></div>
                      <div class="rtrf">{fmt(row['trafic_estime'])}<span style="color:#9CA3AF;font-size:.6rem"> /mois</span></div>
                    </div>""", unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="ibox">Base de donnees introuvable.</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── Graphiques en bas ─────────────────────────────────────────────────────
    if not df_all.empty:
        ch1, ch2 = st.columns(2, gap="large")

        with ch1:
            section_label("Treemap — trafic par site et secteur")
            st.plotly_chart(
                make_treemap(df_all, "trafic_estime", height=380),
                use_container_width=True, config={"displayModeBar": False}
            )

        with ch2:
            section_label("Distribution des scores par secteur")
            fig_vio = go.Figure()
            for cat in df_all["category"].unique():
                dc = df_all[df_all["category"] == cat]
                c = CAT_COLORS.get(cat, "#0EA5E9")
                fig_vio.add_trace(go.Violin(
                    y=dc["score_global"],
                    name=CAT_LABEL.get(cat, cat),
                    line_color=c, fillcolor=hex_alpha(c, 0.18),
                    box_visible=True, meanline_visible=True,
                    points="all",
                    marker=dict(color=c, size=5, opacity=0.65),
                    hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<extra></extra>",
                ))
            lay_vio = base_layout(height=380)
            lay_vio["showlegend"] = False
            lay_vio["yaxis"]["range"] = [0, 105]
            lay_vio["yaxis"]["title"] = dict(text="Score global", font=dict(size=11, color="#9CA3AF"))
            fig_vio.update_layout(**lay_vio)
            st.plotly_chart(fig_vio, use_container_width=True, config={"displayModeBar": False})

        # ── Sunburst secteur + Scatter trafic ─────────────────────────────────
        ch3, ch4 = st.columns(2, gap="large")

        with ch3:
            section_label("Sunburst — hierarchie secteur par trafic")
            st.plotly_chart(
                make_sunburst(df_all, "trafic_estime", height=400),
                use_container_width=True, config={"displayModeBar": False}
            )

        with ch4:
            section_label("Positionnement — autorite vs trafic estime")
            fig_pos = go.Figure()
            for cat in df_all["category"].unique():
                dc = df_all[df_all["category"] == cat]
                c  = CAT_COLORS.get(cat, "#0EA5E9")
                fig_pos.add_trace(go.Scatter(
                    x=dc["score_autorite"], y=dc["trafic_estime"],
                    mode="markers+text", name=CAT_LABEL.get(cat, cat),
                    text=dc["name"], textposition="top center",
                    textfont=dict(size=8, color="#6B7280", family="Inter"),
                    marker=dict(
                        size=dc["score_global"] / df_all["score_global"].max() * 40 + 8,
                        color=c, opacity=0.82,
                        line=dict(width=2, color="#ffffff"),
                        sizemode="diameter",
                    ),
                    hovertemplate="<b>%{text}</b><br>Autorite: %{x:.1f}<br>Trafic: %{y:,.0f}/mois<extra></extra>",
                ))
            lay_pos = base_layout("", height=400)
            lay_pos["xaxis"]["title"] = dict(text="Score Autorite", font=dict(size=11, color="#9CA3AF"))
            lay_pos["yaxis"]["title"] = dict(text="Trafic estime / mois", font=dict(size=11, color="#9CA3AF"))
            fig_pos.update_layout(**lay_pos)
            st.plotly_chart(fig_pos, use_container_width=True, config={"displayModeBar": False})

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : SCORING & TRAFIC
# ══════════════════════════════════════════════════════════════════════════════
elif page == "scoring":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "Modele Analytique · Calcul Automatique",
        'Scoring & <span class="acc">Trafic Estime</span>',
        "Autorite (45%) · Qualite (35%) · Technique (20%) · Modele CTR AWR 2023",
    )
    if df_f.empty:
        st.markdown('<div class="ibox">Aucune donnee disponible.</div>', unsafe_allow_html=True)
    else:
        k1, k2, k3, k4 = st.columns(4, gap="medium")
        best  = df_f["score_global"].max()
        above = int((df_f["score_global"] >= 50).sum())
        pos_m = round(df_f["position_estimee"].mean(), 1) if "position_estimee" in df_f.columns else 10
        kpis  = [
            ("Meilleur score",  f"{best:.1f}",  df_f.loc[df_f['score_global'].idxmax(),'name'][:16], "Top", "badge-up", best/100, "#0EA5E9", 0),
            ("Total trafic",    fmt(df_f['trafic_estime'].sum()), "visites / mois", "CTR model", "badge-flat", 0.78, "#10B981", 1),
            ("Position moy.",   f"#{pos_m}", "SERP estimee", "Proxy", "badge-flat", 0.5, "#8B5CF6", 2),
            ("Sites > 50 pts",  str(above), f"sur {len(df_f)} sites", "Competitifs", "badge-up", above/max(len(df_f),1), "#F59E0B", 3),
        ]
        for col, (lbl, val, sub, badge, bcls, prog, color, delay) in zip([k1,k2,k3,k4], kpis):
            col.markdown(kpi_master(lbl, val, sub, badge, bcls, prog, color, delay), unsafe_allow_html=True)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        # Hero : Bubble chart Autorite vs Trafic
        section_label("Autorite vs Trafic — carte de positionnement")
        fig_b = go.Figure()
        for cat in df_f["category"].unique():
            dc = df_f[df_f["category"] == cat]
            c  = CAT_COLORS.get(cat, "#0EA5E9")
            fig_b.add_trace(go.Scatter(
                x=dc["score_autorite"], y=dc["trafic_estime"],
                mode="markers+text", name=CAT_LABEL.get(cat, cat),
                text=dc["name"], textposition="top center",
                textfont=dict(size=9, color="#6B7280", family="Inter"),
                marker=dict(
                    size=dc["score_global"] / df_f["score_global"].max() * 48 + 10,
                    color=c, opacity=0.82,
                    line=dict(width=2.5, color="#ffffff"),
                    sizemode="diameter",
                ),
                hovertemplate="<b>%{text}</b><br>Autorite: %{x:.1f}<br>Trafic: %{y:,.0f}/mois<extra></extra>",
            ))
        lay_b = base_layout("", height=500)
        lay_b["xaxis"]["title"] = dict(text="Score Autorite", font=dict(size=11, color="#9CA3AF"))
        lay_b["yaxis"]["title"] = dict(text="Trafic estime / mois", font=dict(size=11, color="#9CA3AF"))
        lay_b["hovermode"] = "closest"
        fig_b.update_layout(**lay_b)
        st.plotly_chart(fig_b, use_container_width=True, config={"displayModeBar": False})

        col1, col2 = st.columns(2, gap="large")
        with col1:
            section_label("Treemap — poids des sites par score global")
            _df_tm = df_f.copy()
            _df_tm["score_global_clipped"] = _df_tm["score_global"].clip(lower=1)
            st.plotly_chart(
                make_treemap(_df_tm, "score_global_clipped", color_col="score_global", height=440),
                use_container_width=True, config={"displayModeBar": False}
            )

        with col2:
            section_label("Heatmap — scores par dimension")
            dh = df_f.set_index("name")[["score_autorite","score_qualite","score_technique","score_global"]]
            dh.columns = ["Autorite","Qualite","Technique","Global"]
            fig_hm = go.Figure(go.Heatmap(
                z=dh.values.T, x=dh.index.tolist(), y=dh.columns.tolist(),
                colorscale=[[0,"#F0F9FF"],[0.35,"#BAE6FD"],[0.65,"#0EA5E9"],[1,"#0C4A6E"]],
                hovertemplate="<b>%{x}</b><br>%{y}: <b>%{z:.1f}</b><extra></extra>",
                showscale=True, xgap=2, ygap=2,
                colorbar=dict(thickness=8, len=0.7, outlinewidth=0,
                              tickfont=dict(size=9, color="#9CA3AF")),
            ))
            lay_hm = base_layout(height=440, margin=dict(l=70, r=60, t=10, b=80))
            lay_hm["xaxis"]["tickangle"] = -40
            lay_hm["xaxis"]["tickfont"]  = dict(size=9, color="#9CA3AF")
            lay_hm["yaxis"]["showgrid"]  = False
            fig_hm.update_layout(**lay_hm)
            st.plotly_chart(fig_hm, use_container_width=True, config={"displayModeBar": False})

        section_label("Tableau complet des scores")
        d = df_f[["name","category","score_global","score_autorite","score_qualite","score_technique","trafic_estime"]].copy()
        d.columns = ["Site","Secteur","Global","Autorite","Qualite","Technique","Trafic/mois"]
        st.markdown(html_table(d.round(1)), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : METADONNEES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "meta":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "Collecte HTML · Crawl Automatique",
        'Metadonnees <span class="acc">Techniques</span>',
        "Structure · Liens · Vitesse · Conformite SEO",
    )

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
        st.markdown('<div class="ibox">Metadonnees non collectees. Lance : <code>python main.py crawl</code></div>', unsafe_allow_html=True)
    else:
        ssl_ok  = int(df_meta["has_ssl"].fillna(0).sum())
        sit_ok  = int(df_meta["has_sitemap"].fillna(0).sum())
        rob_ok  = int(df_meta["has_robots_txt"].fillna(0).sum()) if "has_robots_txt" in df_meta else 0
        avg_rt  = round(df_meta["response_time_ms"].dropna().mean(), 0) if not df_meta["response_time_ms"].dropna().empty else 0
        total_m = len(df_meta)

        k1, k2, k3, k4 = st.columns(4, gap="medium")
        for col, (lbl, val, sub, badge, bcls, prog, color, delay) in zip([k1,k2,k3,k4], [
            ("SSL actif",   f"{ssl_ok}/{total_m}", "sites HTTPS",  "Securite",  "badge-up",   ssl_ok/max(total_m,1),   "#10B981", 0),
            ("Sitemaps",    f"{sit_ok}/{total_m}", "sitemap.xml",  "SEO",       "badge-flat",  sit_ok/max(total_m,1),  "#0EA5E9", 1),
            ("Robots.txt",  f"{rob_ok}/{total_m}", "fichiers",     "Crawl",     "badge-flat",  rob_ok/max(total_m,1),  "#8B5CF6", 2),
            ("Temps moyen", f"{int(avg_rt)} ms",   "de reponse",   "Perf",      "badge-up" if avg_rt<2000 else "badge-down",
             max(0,1-avg_rt/5000), "#F59E0B", 3),
        ]):
            col.markdown(kpi_master(lbl, val, sub, badge, bcls, prog, color, delay), unsafe_allow_html=True)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        # Hero : scatter Temps de reponse vs Mots
        section_label("Carte de sante — temps de reponse vs contenu")
        df_sc = df_meta.dropna(subset=["response_time_ms","word_count"])
        fig_sc = go.Figure()
        for cat in df_sc["category"].unique():
            dc  = df_sc[df_sc["category"] == cat]
            c   = CAT_COLORS.get(cat, "#0EA5E9")
            fig_sc.add_trace(go.Scatter(
                x=dc["response_time_ms"], y=dc["word_count"],
                mode="markers+text", name=CAT_LABEL.get(cat, cat),
                text=dc["name"], textposition="top center",
                textfont=dict(size=8, color="#6B7280", family="Inter"),
                marker=dict(
                    size=14,
                    color=["#10B981" if s == 1 else "#EF4444" for s in dc["has_ssl"].fillna(0)],
                    symbol=["circle" if s == 1 else "x" for s in dc["has_ssl"].fillna(0)],
                    opacity=0.85,
                    line=dict(width=2, color=c),
                ),
                hovertemplate="<b>%{text}</b><br>Reponse: %{x:.0f}ms<br>Mots: %{y:,}<extra></extra>",
            ))
        lay_sc = base_layout("Temps de reponse vs volume de contenu (cercle=SSL OK, croix=SSL absent)", height=460)
        lay_sc["xaxis"]["title"] = dict(text="Temps de reponse (ms)", font=dict(size=11, color="#9CA3AF"))
        lay_sc["yaxis"]["title"] = dict(text="Nombre de mots", font=dict(size=11, color="#9CA3AF"))
        # Reference line
        fig_sc.add_vline(x=2000, line=dict(color="#F59E0B", width=1.5, dash="dash"))
        fig_sc.add_annotation(x=2000, y=0, text="Seuil 2s", showarrow=False,
                              font=dict(size=9, color="#F59E0B"), yref="paper", yshift=10)
        fig_sc.update_layout(**lay_sc)
        st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

        col1, col2, col3 = st.columns(3, gap="large")
        with col1:
            section_label("Conformite SSL")
            fig_ssl = donut_gauge(ssl_ok / total_m * 100, 100, f"{ssl_ok} / {total_m} sites", "#10B981", 220)
            st.plotly_chart(fig_ssl, use_container_width=True, config={"displayModeBar": False})
        with col2:
            section_label("Sitemaps")
            fig_sit = donut_gauge(sit_ok / total_m * 100, 100, f"{sit_ok} / {total_m} sites", "#0EA5E9", 220)
            st.plotly_chart(fig_sit, use_container_width=True, config={"displayModeBar": False})
        with col3:
            section_label("Robots.txt")
            fig_rob = donut_gauge(rob_ok / total_m * 100, 100, f"{rob_ok} / {total_m} sites", "#8B5CF6", 220)
            st.plotly_chart(fig_rob, use_container_width=True, config={"displayModeBar": False})

        section_label("Tableau complet")
        d = df_meta[["name","category","response_time_ms","word_count","has_ssl","has_sitemap"]].copy()
        d.columns = ["Site","Secteur","Temps(ms)","Mots","SSL","Sitemap"]
        d["SSL"]     = d["SSL"].apply(lambda x: "Oui" if x == 1 else "Non")
        d["Sitemap"] = d["Sitemap"].apply(lambda x: "Oui" if x == 1 else "Non")
        st.markdown(html_table(d), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "perf":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "PageSpeed Insights · Google Lighthouse",
        'Performance <span class="acc">Lighthouse</span>',
        "Core Web Vitals · LCP · FCP · TTFB · Mobile first",
    )

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
        st.markdown('<div class="ibox">Scores PageSpeed non collectes. Lance : <code>python main.py perf</code></div>', unsafe_allow_html=True)
    else:
        avg_p  = round(df_perf["performance_score"].mean(), 1)
        avg_s  = round(df_perf["seo_score"].mean(), 1)
        avg_a  = round(df_perf["accessibility_score"].mean(), 1)
        avg_bp = round(df_perf["best_practices_score"].mean(), 1) if "best_practices_score" in df_perf else 50.0
        above90 = int((df_perf["performance_score"] >= 90).sum())

        k1, k2, k3, k4, k5 = st.columns(5, gap="medium")
        for col, (lbl, val, sub, badge, bcls, prog, color, delay) in zip([k1,k2,k3,k4,k5], [
            ("Perf. moyenne",  f"{avg_p}",    "/100",    "Lighthouse", "badge-flat", avg_p/100,         "#0EA5E9", 0),
            ("SEO moyen",      f"{avg_s}",    "/100",    "Optimise",   "badge-flat", avg_s/100,         "#10B981", 1),
            ("Accessibilite",  f"{avg_a}",    "/100",    "WCAG",       "badge-flat", avg_a/100,         "#8B5CF6", 2),
            ("Best Practices", f"{avg_bp}",   "/100",    "Standards",  "badge-flat", avg_bp/100,        "#F59E0B", 3),
            ("Score >= 90",    str(above90),  "sites",   "Excellents", "badge-up" if above90>0 else "badge-flat",
             above90/max(len(df_perf),1), "#EF4444", 4),
        ]):
            col.markdown(kpi_master(lbl, val, sub, badge, bcls, prog, color, delay), unsafe_allow_html=True)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        # 4 donut gauges en rangee
        section_label("Scores moyens Lighthouse")
        g1, g2, g3, g4 = st.columns(4, gap="medium")
        for col, (val, lbl, color) in zip([g1,g2,g3,g4], [
            (avg_p,  "Performance",    "auto"),
            (avg_s,  "SEO",            "auto"),
            (avg_a,  "Accessibilite",  "auto"),
            (avg_bp, "Best Practices", "auto"),
        ]):
            col.plotly_chart(donut_gauge(val, 100, lbl, color, 200),
                             use_container_width=True, config={"displayModeBar": False})

        # Scatter Perf vs SEO (hero)
        section_label("Cartographie Performance vs SEO")
        fig_sc = go.Figure()
        for cat in df_perf["category"].unique():
            dc = df_perf[df_perf["category"] == cat]
            c  = CAT_COLORS.get(cat, "#0EA5E9")
            fig_sc.add_trace(go.Scatter(
                x=dc["performance_score"], y=dc["seo_score"],
                mode="markers+text", name=CAT_LABEL.get(cat, cat),
                text=dc["name"], textposition="top center",
                textfont=dict(size=9, color="#6B7280", family="Inter"),
                marker=dict(
                    size=dc["accessibility_score"] / 100 * 30 + 8,
                    color=c, opacity=0.85,
                    line=dict(width=2.5, color="#ffffff"),
                    sizemode="diameter",
                ),
                hovertemplate="<b>%{text}</b><br>Performance: %{x:.0f}<br>SEO: %{y:.0f}<extra></extra>",
            ))
        lay_sc = base_layout("Performance vs SEO  (taille = score accessibilite)", height=480)
        lay_sc["xaxis"]["title"] = dict(text="Performance", font=dict(size=11, color="#9CA3AF"))
        lay_sc["xaxis"]["range"] = [0, 105]
        lay_sc["yaxis"]["title"] = dict(text="SEO", font=dict(size=11, color="#9CA3AF"))
        lay_sc["yaxis"]["range"] = [0, 105]
        fig_sc.add_vline(x=50, line=dict(color="#F59E0B", width=1, dash="dot"))
        fig_sc.add_hline(y=70, line=dict(color="#F59E0B", width=1, dash="dot"))
        fig_sc.update_layout(**lay_sc)
        st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

        # Violin distribution des 4 scores
        section_label("Distribution des scores — violon")
        fig_vio = go.Figure()
        score_cols = [("performance_score","Performance","#0EA5E9"),
                      ("seo_score","SEO","#10B981"),
                      ("accessibility_score","Accessibilite","#8B5CF6"),
                      ("best_practices_score","Best Practices","#F59E0B")]
        for col_name, lbl, c in score_cols:
            if col_name in df_perf.columns:
                fig_vio.add_trace(go.Violin(
                    y=df_perf[col_name], name=lbl,
                    line_color=c, fillcolor=hex_alpha(c, 0.18),
                    box_visible=True, meanline_visible=True,
                    points="all",
                    marker=dict(color=c, size=4, opacity=0.55),
                    hovertemplate=f"<b>{lbl}</b><br>Score: %{{y:.1f}}<extra></extra>",
                ))
        lay_vio = base_layout(height=380)
        lay_vio["showlegend"] = False
        lay_vio["yaxis"]["range"] = [0, 105]
        fig_vio.update_layout(**lay_vio)
        st.plotly_chart(fig_vio, use_container_width=True, config={"displayModeBar": False})

        section_label("Core Web Vitals — tableau")
        cwv = df_perf[["name","performance_score","lcp_ms","fcp_ms","ttfb_ms","cls_score","accessibility_score"]].copy()
        cwv.columns = ["Site","Performance","LCP(ms)","FCP(ms)","TTFB(ms)","CLS","Accessibilite"]
        st.markdown(html_table(cwv.round(1)), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : BACKLINKS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "backlinks":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "CommonCrawl Index · Autorite de Domaine",
        'Autorite & <span class="acc">Backlinks</span>',
        "Pages indexees · Domaines referents · Variation mensuelle",
    )

    df_bl = q(f"""
        SELECT s.name, s.category, s.domain,
               sb.total_backlinks, sb.referring_domains, sb.backlinks_change
        FROM site_backlinks sb JOIN sites s ON s.id=sb.site_id
        WHERE sb.collected_at=(SELECT MAX(collected_at) FROM site_backlinks WHERE site_id=sb.site_id)
        {cat_sql} ORDER BY sb.total_backlinks DESC
    """)

    if df_bl.empty:
        st.markdown('<div class="ibox">Backlinks non collectes. Lance : <code>python main.py backlinks</code></div>', unsafe_allow_html=True)
    else:
        total_bl = int(df_bl["total_backlinks"].sum())
        total_rd = int(df_bl["referring_domains"].sum())
        best_bl  = df_bl.loc[df_bl["total_backlinks"].idxmax(), "name"] if not df_bl.empty else "—"
        avg_rd   = round(df_bl["referring_domains"].mean(), 0)

        k1, k2, k3, k4 = st.columns(4, gap="medium")
        for col, (lbl, val, sub, badge, bcls, prog, color, delay) in zip([k1,k2,k3,k4], [
            ("Total backlinks", fmt(total_bl), "pages indexees",  "CommonCrawl", "badge-flat", 0.8,  "#0EA5E9", 0),
            ("Dom. referents",  fmt(total_rd), "domaines uniques","Diversite",   "badge-flat", 0.7,  "#10B981", 1),
            ("Leader autorite", best_bl[:14],  "top site",        "Max",         "badge-up",   1.0,  "#8B5CF6", 2),
            ("Moy. dom. ref.",  str(int(avg_rd)),"par site",       "Distribution","badge-flat", 0.5,  "#F59E0B", 3),
        ]):
            col.markdown(kpi_master(lbl, val, sub, badge, bcls, prog, color, delay), unsafe_allow_html=True)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        # Hero : Treemap backlinks
        section_label("Treemap — poids de l'autorite par site")
        st.plotly_chart(
            make_treemap(df_bl, "total_backlinks", height=400),
            use_container_width=True, config={"displayModeBar": False}
        )

        col1, col2 = st.columns(2, gap="large")
        with col1:
            section_label("Domaines referents vs Pages indexees")
            fig_sc = go.Figure()
            for cat in df_bl["category"].unique():
                dc = df_bl[df_bl["category"] == cat]
                c  = CAT_COLORS.get(cat, "#0EA5E9")
                fig_sc.add_trace(go.Scatter(
                    x=dc["referring_domains"], y=dc["total_backlinks"],
                    mode="markers+text", name=CAT_LABEL.get(cat, cat),
                    text=dc["name"], textposition="top center",
                    textfont=dict(size=8, color="#6B7280", family="Inter"),
                    marker=dict(size=14, color=c, opacity=0.85,
                                line=dict(width=2.5, color="#fff")),
                    hovertemplate="<b>%{text}</b><br>Dom. ref: %{x:,}<br>Pages: %{y:,}<extra></extra>",
                ))
            lay_sc = base_layout(height=420)
            lay_sc["xaxis"]["title"] = dict(text="Domaines referents", font=dict(size=11, color="#9CA3AF"))
            lay_sc["yaxis"]["title"] = dict(text="Pages indexees", font=dict(size=11, color="#9CA3AF"))
            fig_sc.update_layout(**lay_sc)
            st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

        with col2:
            section_label("Sunburst — hierarchie secteur > site")
            st.plotly_chart(
                make_sunburst(df_bl, "total_backlinks", height=420),
                use_container_width=True, config={"displayModeBar": False}
            )

        section_label("Tableau complet")
        d = df_bl[["name","category","domain","total_backlinks","referring_domains","backlinks_change"]].copy()
        d.columns = ["Site","Secteur","Domaine","Pages indexees","Dom. referents","Variation"]
        d["Variation"] = d["Variation"].fillna(0)
        st.markdown(html_table(d), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : COMPARAISON
# ══════════════════════════════════════════════════════════════════════════════
elif page == "compare":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "Analyse Concurrentielle · Multi-Sites",
        'Comparaison <span class="acc">Directe</span>',
        "Selectionnez jusqu'a 8 sites pour comparer toutes leurs dimensions",
    )

    sl = q("SELECT name FROM sites ORDER BY name")
    if sl.empty or df_all.empty:
        st.markdown('<div class="ibox">Donnees insuffisantes.</div>', unsafe_allow_html=True)
    else:
        selected = st.multiselect(
            "Sites a comparer", options=sl["name"].tolist(),
            default=sl["name"].tolist()[:6], max_selections=8,
        )
        if selected:
            ds = df_all[df_all["name"].isin(selected)]
            if not ds.empty:
                PAL = ["#0EA5E9","#10B981","#F59E0B","#8B5CF6","#EF4444","#06B6D4","#F472B6","#84CC16"]

                # Hero : Radar pleine largeur
                section_label("Radar — profil comparatif")
                dims = ["Autorite","Qualite","Technique","Score global"]
                fig_r = go.Figure()
                for j, (_, row) in enumerate(ds.iterrows()):
                    c    = PAL[j % len(PAL)]
                    vals = [row["score_autorite"], row["score_qualite"],
                            row["score_technique"], row["score_global"], row["score_autorite"]]
                    fig_r.add_trace(go.Scatterpolar(
                        r=vals, theta=dims+[dims[0]],
                        fill="toself", name=row["name"],
                        line=dict(color=c, width=2.5),
                        fillcolor=hex_alpha(c, 0.12),
                        hovertemplate="%{theta}: <b>%{r:.1f}</b><extra>" + row["name"] + "</extra>",
                    ))
                fig_r.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    height=520, margin=dict(l=70, r=70, t=40, b=70),
                    polar=dict(
                        bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(visible=True, range=[0,100],
                                        gridcolor="rgba(107,114,128,0.12)",
                                        tickfont=dict(size=9, color="#9CA3AF")),
                        angularaxis=dict(gridcolor="rgba(107,114,128,0.12)",
                                         tickfont=dict(size=13, color="#374151", family="Manrope")),
                    ),
                    legend=dict(font=dict(size=11, color="#4B5563", family="Inter"),
                                bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.12),
                    hoverlabel=dict(**_HOVER),
                    transition=dict(duration=400, easing="cubic-in-out"),
                )
                st.plotly_chart(fig_r, use_container_width=True, config={"displayModeBar": False})

                # Scatter parallele — chaque site comme une serie de points
                section_label("Profils paralleles — scores par dimension")
                metrics = ["score_autorite","score_qualite","score_technique","score_global"]
                labels  = ["Autorite","Qualite","Technique","Global"]
                fig_sc = go.Figure()
                for j, (_, row) in enumerate(ds.iterrows()):
                    c = PAL[j % len(PAL)]
                    y_vals = [row[m] for m in metrics]
                    fig_sc.add_trace(go.Scatter(
                        x=labels, y=y_vals,
                        mode="lines+markers", name=row["name"],
                        line=dict(color=c, width=2.5, shape="spline", smoothing=0.8),
                        marker=dict(size=10, color="#ffffff", line=dict(color=c, width=2.5)),
                        fill="tozeroy", fillcolor=hex_alpha(c, 0.04),
                        hovertemplate="<b>" + row["name"] + "</b><br>%{x}: %{y:.1f}<extra></extra>",
                    ))
                lay_sc = base_layout("", height=400)
                lay_sc["yaxis"]["range"] = [0, 105]
                lay_sc["hovermode"]      = "x unified"
                lay_sc["xaxis"]["showgrid"] = False
                fig_sc.update_layout(**lay_sc)
                st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

                section_label("Tableau recapitulatif")
                dt = ds[["name","category","score_global","score_autorite","score_qualite",
                          "score_technique","trafic_estime"]].copy()
                dt.columns = ["Site","Secteur","Global","Autorite","Qualite","Technique","Trafic/mois"]
                st.markdown(html_table(dt.round(1).sort_values("Global", ascending=False)), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : VEILLE & TENDANCES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "veille":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "Intelligence Strategique · Simulation · Risques",
        'Veille & <span class="acc">Tendances</span>',
        "Simulateur d'impact · Opportunites de croissance · Sites a risque",
    )

    if df_all.empty:
        st.markdown('<div class="ibox">Donnees insuffisantes.</div>', unsafe_allow_html=True)
    else:
        # Simulateur
        section_label("Simulateur d'impact SEO")
        sim_col1, sim_col2, sim_col3 = st.columns([1.5,1,1], gap="large")
        with sim_col1:
            sim_site = st.selectbox("Site a simuler", df_all["name"].tolist(), key="sim_site")
        with sim_col2:
            delta_seo = st.slider("Gain SEO (points)", 0, 40, 10, key="delta_seo")
        with sim_col3:
            delta_perf = st.slider("Gain Performance (points)", 0, 40, 10, key="delta_perf")

        row_sim = df_all[df_all["name"] == sim_site].iloc[0]
        new_seo     = min(100, float(row_sim.get("seo_score") or 50) + delta_seo)
        new_perf    = min(100, float(row_sim.get("performance_score") or 50) + delta_perf)
        new_acc     = float(row_sim.get("accessibility_score") or 50)
        new_qualite = round(new_seo*0.40 + new_perf*0.35 + new_acc*0.25, 1)
        new_global  = round(row_sim["score_autorite"]*0.45 + new_qualite*0.35 + row_sim["score_technique"]*0.20, 1)
        new_traffic = int(CATEGORY_BASE.get(row_sim["category"],50000) * (new_global/100)**1.5)
        delta_tr    = new_traffic - int(row_sim["trafic_estime"])
        delta_g     = round(new_global - row_sim["score_global"], 1)

        s1,s2,s3,s4 = st.columns(4, gap="medium")
        for col, (lbl,val,sub,badge,bcls,prog,color,delay) in zip([s1,s2,s3,s4],[
            ("Score actuel",   f"{row_sim['score_global']:.1f}", "Actuel / 100", "Base",   "badge-flat", row_sim["score_global"]/100, "#6B7280", 0),
            ("Score projete",  f"{new_global:.1f}",             f"+{delta_g} pts","Gain",  "badge-up",   new_global/100, "#10B981", 1),
            ("Trafic actuel",  fmt(row_sim["trafic_estime"]),   "vis./mois",     "Base",   "badge-flat", 0.5, "#6B7280", 2),
            ("Trafic projete", fmt(new_traffic),                f"+{fmt(delta_tr)}","Gain", "badge-up",  min(new_traffic/max(int(row_sim["trafic_estime"]),1)*0.5,1), "#10B981", 3),
        ]):
            col.markdown(kpi_master(lbl,val,sub,badge,bcls,prog,color,delay), unsafe_allow_html=True)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        # Carte des risques — scatter bubble
        section_label("Carte des risques — score global vs risque technique")
        df_risk = df_all.copy()
        rt_col  = df_risk["response_time_ms"] if "response_time_ms" in df_risk.columns else pd.Series([1000]*len(df_risk), index=df_risk.index)
        ssl_col = df_risk["has_ssl"] if "has_ssl" in df_risk.columns else pd.Series([1]*len(df_risk), index=df_risk.index)
        sit_col = df_risk["has_sitemap"] if "has_sitemap" in df_risk.columns else pd.Series([1]*len(df_risk), index=df_risk.index)
        risk    = pd.Series(0.0, index=df_risk.index)
        risk   += (rt_col.fillna(1000) > 3000).astype(float) * 35
        risk   += (rt_col.fillna(1000) > 5000).astype(float) * 20
        risk   += (ssl_col.fillna(1) == 0).astype(float) * 25
        risk   += (sit_col.fillna(1) == 0).astype(float) * 15
        risk   += (df_risk["score_qualite"] < 40).astype(float) * 20
        df_risk["score_risque"] = risk.clip(0, 100).round(0).astype(int)

        fig_rb = go.Figure()
        for cat in df_risk["category"].unique():
            dc = df_risk[df_risk["category"] == cat]
            c  = CAT_COLORS.get(cat, "#0EA5E9")
            fig_rb.add_trace(go.Scatter(
                x=dc["score_global"], y=dc["score_risque"],
                mode="markers+text", name=CAT_LABEL.get(cat, cat),
                text=dc["name"], textposition="top center",
                textfont=dict(size=9, color="#6B7280", family="Inter"),
                marker=dict(
                    size=dc["trafic_estime"] / df_risk["trafic_estime"].max() * 50 + 10,
                    color=["#EF4444" if v >= 60 else "#F59E0B" if v >= 30 else "#10B981"
                           for v in dc["score_risque"]],
                    opacity=0.82,
                    line=dict(width=2.5, color=c),
                    sizemode="diameter",
                ),
                hovertemplate="<b>%{text}</b><br>Score: %{x:.1f}<br>Risque: %{y}<extra></extra>",
            ))
        lay_rb = base_layout("Score global vs Risque technique  (taille = trafic estime)", height=500)
        lay_rb["xaxis"]["title"] = dict(text="Score global (plus grand = meilleur)", font=dict(size=11, color="#9CA3AF"))
        lay_rb["yaxis"]["title"] = dict(text="Score de risque (plus grand = plus risque)", font=dict(size=11, color="#9CA3AF"))
        lay_rb["xaxis"]["range"] = [0, 105]
        lay_rb["yaxis"]["range"] = [-5, 110]
        fig_rb.add_hrect(y0=60, y1=110, fillcolor="#fee2e2", opacity=0.07, line_width=0)
        fig_rb.add_hrect(y0=30, y1=60,  fillcolor="#fef3c7", opacity=0.10, line_width=0)
        fig_rb.add_hrect(y0=0,  y1=30,  fillcolor="#dcfce7", opacity=0.10, line_width=0)
        fig_rb.update_layout(**lay_rb)
        st.plotly_chart(fig_rb, use_container_width=True, config={"displayModeBar": False})

        # Opportunites — funnel
        section_label("Pipeline d'opportunites de croissance")
        df_opp = df_all.copy()
        df_opp["score_qualite_proj"] = df_opp["score_qualite"].apply(lambda x: min(90, x+30))
        df_opp["score_global_proj"]  = (df_opp["score_autorite"]*0.45 + df_opp["score_qualite_proj"]*0.35 + df_opp["score_technique"]*0.20).round(1)
        df_opp["trafic_potentiel"]   = df_opp.apply(lambda r: int(CATEGORY_BASE.get(r["category"],50000)*(r["score_global_proj"]/100)**1.5), axis=1)
        df_opp["gap_trafic"]         = df_opp["trafic_potentiel"] - df_opp["trafic_estime"]
        top_opp = df_opp.nlargest(10, "gap_trafic")

        fig_fn = go.Figure(go.Funnel(
            y=top_opp["name"],
            x=top_opp["gap_trafic"],
            textinfo="value+percent initial",
            textfont=dict(family="Inter", size=10, color="white"),
            marker=dict(
                color=[CAT_COLORS.get(c,"#0EA5E9") for c in top_opp["category"]],
                line=dict(width=1.5, color="#fff"),
            ),
            connector=dict(line=dict(color="#e5e7eb", width=1)),
            hovertemplate="<b>%{y}</b><br>Gain potentiel: +%{x:,.0f} vis/mois<extra></extra>",
        ))
        lay_fn = base_layout("Gain de trafic potentiel si score qualite monte a 90", height=420,
                             margin=dict(l=140, r=0, t=52, b=0))
        lay_fn["yaxis"]["tickfont"] = dict(size=10, color="#374151", family="Inter")
        fig_fn.update_layout(**lay_fn)
        st.plotly_chart(fig_fn, use_container_width=True, config={"displayModeBar": False})

        section_label("Facteurs de risque detectes")
        rt_tab = df_risk.sort_values("score_risque", ascending=False).head(12)[
            ["name","category","score_risque","score_global","trafic_estime"]].copy()
        rt_tab.columns = ["Site","Secteur","Risque/100","Score Global","Trafic/mois"]
        st.markdown(html_table(rt_tab.round(1)), unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : RAPPORTS & EXPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "export":
    import base64 as _b64

    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "Export · Rapport Executif · Fiche Site",
        'Rapports & <span class="acc">Export</span>',
        f"Telecharge les donnees · Genere un rapport HTML imprimable · {n_sites} sites · {now}",
    )

    if df_all.empty:
        st.markdown('<div class="ibox">Aucune donnee disponible pour l\'export.</div>', unsafe_allow_html=True)
    else:
        section_label("Exports rapides")
        exp1, exp2, exp3 = st.columns(3, gap="large")

        with exp1:
            st.markdown("""
            <div class="crd" style="padding:1.4rem 1.6rem;min-height:120px">
              <div style="font-family:Inter,sans-serif;font-size:.625rem;font-weight:700;
                          color:#10B981;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.5rem">
                CSV · Scores complets
              </div>
              <div style="font-size:.8125rem;color:#4B5563;line-height:1.65">
                Tous les scores pour les 28 sites. Compatible Excel, Google Sheets, Power BI.
              </div>
            </div>
            """, unsafe_allow_html=True)
            csv_cols = ["name","domain","category","score_global","score_autorite","score_qualite",
                        "score_technique","trafic_estime","total_backlinks","referring_domains",
                        "performance_score","seo_score","accessibility_score","response_time_ms","has_ssl","has_sitemap"]
            csv_df    = df_all[[c for c in csv_cols if c in df_all.columns]].copy()
            csv_df.columns = [c.replace("_"," ").title() for c in csv_df.columns]
            csv_bytes = csv_df.round(1).to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("Telecharger CSV", data=csv_bytes,
                file_name=f"senwebstats_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True)

        with exp2:
            st.markdown("""
            <div class="crd" style="padding:1.4rem 1.6rem;min-height:120px">
              <div style="font-family:Inter,sans-serif;font-size:.625rem;font-weight:700;
                          color:#0EA5E9;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.5rem">
                JSON · API-ready
              </div>
              <div style="font-size:.8125rem;color:#4B5563;line-height:1.65">
                Format structure pour integrations Power BI, Tableau, dashboards custom.
              </div>
            </div>
            """, unsafe_allow_html=True)
            json_data  = df_all[["name","domain","category","score_global","score_autorite",
                                  "score_qualite","score_technique","trafic_estime"]].round(1).to_dict(orient="records")
            json_bytes = json.dumps({"generated_at": now, "sites": json_data},
                                    ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button("Telecharger JSON", data=json_bytes,
                file_name=f"senwebstats_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json", use_container_width=True)

        with exp3:
            st.markdown("""
            <div class="crd" style="padding:1.4rem 1.6rem;min-height:120px">
              <div style="font-family:Inter,sans-serif;font-size:.625rem;font-weight:700;
                          color:#8B5CF6;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.5rem">
                HTML · Rapport executif
              </div>
              <div style="font-size:.8125rem;color:#4B5563;line-height:1.65">
                Rapport complet imprimable en PDF depuis le navigateur.
              </div>
            </div>
            """, unsafe_allow_html=True)
            all_rows = "".join([
                f"<tr><td>{i+1}</td><td><b>{r['name']}</b></td><td>{r['category']}</td>"
                f"<td style='text-align:right'>{r['score_global']:.1f}</td>"
                f"<td style='text-align:right'>{r['score_autorite']:.1f}</td>"
                f"<td style='text-align:right'>{r['score_qualite']:.1f}</td>"
                f"<td style='text-align:right'>{r['score_technique']:.1f}</td>"
                f"<td style='text-align:right'>{fmt(r['trafic_estime'])}</td></tr>"
                for i, (_, r) in enumerate(df_all.iterrows())
            ])
            html_report = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<title>SenWebStats — Rapport {datetime.now().strftime('%B %Y')}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@700;800&family=Inter:wght@400;600&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',sans-serif;background:#f9fafb;color:#111827;font-size:13px}}
.page{{max-width:960px;margin:0 auto;padding:48px 40px}}
h1{{font-family:'Manrope',sans-serif;font-size:2rem;font-weight:800;color:#0d1117;margin-bottom:.2rem}}
h1 em{{color:#10B981;font-style:normal}}
h2{{font-family:'Inter',sans-serif;font-size:.6rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#6B7280;margin:2rem 0 .8rem;padding-bottom:.4rem;border-bottom:1px solid #e5e7eb}}
.meta{{font-size:.65rem;color:#6B7280;margin-bottom:2rem}}
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:1rem 0 2rem}}
.kpi{{background:#fff;border-radius:10px;padding:1rem 1.2rem;box-shadow:0 2px 8px rgba(0,0,0,.05)}}
.kpi-lbl{{font-size:.55rem;letter-spacing:.15em;text-transform:uppercase;color:#6B7280;margin-bottom:.4rem}}
.kpi-val{{font-family:'Manrope',sans-serif;font-size:1.6rem;font-weight:800;color:#0d1117}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th{{background:#f3f4f6;color:#6B7280;font-size:.55rem;letter-spacing:.1em;text-transform:uppercase;padding:.5rem .7rem;text-align:left}}
td{{padding:.55rem .7rem;border-bottom:1px solid #e5e7eb;color:#111827}}
.footer{{margin-top:3rem;padding-top:1rem;border-top:1px solid #e5e7eb;font-size:.58rem;color:#6B7280;text-align:center}}
</style></head><body><div class="page">
<h1>Observatoire Web <em>Senegalais</em></h1>
<div class="meta">SenWebStats · {datetime.now().strftime('%d %B %Y')} · {n_sites} sites</div>
<div class="kpi-grid">
  <div class="kpi"><div class="kpi-lbl">Sites suivis</div><div class="kpi-val">{n_sites}</div></div>
  <div class="kpi"><div class="kpi-lbl">Trafic total</div><div class="kpi-val">{fmt(total_tr)}</div></div>
  <div class="kpi"><div class="kpi-lbl">Score moyen</div><div class="kpi-val">{avg_sc}</div></div>
  <div class="kpi"><div class="kpi-lbl">PageSpeed</div><div class="kpi-val">{n_perf}</div></div>
</div>
<h2>Classement complet</h2>
<table><thead><tr><th>#</th><th>Site</th><th>Secteur</th><th>Global</th><th>Autorite</th><th>Qualite</th><th>Technique</th><th>Trafic/mois</th></tr></thead>
<tbody>{all_rows}</tbody></table>
<div class="footer">SenWebStats · {datetime.now().strftime('%d/%m/%Y %H:%M')} · CommonCrawl + PageSpeed + CTR Model AWR 2023</div>
</div></body></html>"""
            st.download_button("Telecharger HTML", data=html_report.encode("utf-8"),
                file_name=f"senwebstats_rapport_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html", use_container_width=True)

        # Fiche individuelle
        st.markdown("<div style='height:2.5rem'></div>", unsafe_allow_html=True)
        section_label("Fiche individuelle par site")
        site_sel = st.selectbox("Choisir un site", df_all["name"].tolist(), key="fiche_sel")
        fs = df_all[df_all["name"] == site_sel].iloc[0]

        fc1, fc2, fc3, fc4 = st.columns(4, gap="medium")
        for col, (lbl, val, color, delay) in zip([fc1,fc2,fc3,fc4],[
            ("Score global",   f"{fs['score_global']:.1f}", sc_color(fs["score_global"]),   0),
            ("Autorite",       f"{fs['score_autorite']:.1f}", sc_color(fs["score_autorite"]), 1),
            ("Qualite",        f"{fs['score_qualite']:.1f}", sc_color(fs["score_qualite"]),  2),
            ("Trafic estime",  fmt(fs["trafic_estime"]),     "#10B981",                       3),
        ]):
            col.markdown(f"""
            <div class="kpi-wrap anim-{delay}" style="--kpi-c:{color}">
              <div class="kpi-label">{lbl}</div>
              <div class="kpi-value">{val}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
        fd1, fd2 = st.columns(2, gap="large")

        with fd1:
            st.markdown(f"""
            <div class="crd" style="padding:1.4rem 1.6rem">
              <div class="crd-hd" style="margin:-1.4rem -1.6rem 1rem;padding:14px 20px">Informations</div>
              <div style="font-family:Inter,sans-serif;font-size:.875rem;color:#111827;line-height:2.4">
                <b style="color:#9CA3AF;font-size:.6875rem;letter-spacing:.08em;text-transform:uppercase">Domaine</b><br>
                {fs.get('domain','—')}<br>
                <b style="color:#9CA3AF;font-size:.6875rem;letter-spacing:.08em;text-transform:uppercase">Secteur</b><br>
                {CAT_LABEL.get(fs.get('category',''),'—')}<br>
                <b style="color:#9CA3AF;font-size:.6875rem;letter-spacing:.08em;text-transform:uppercase">Technique</b><br>
                {fs.get('score_technique','—'):.1f} / 100<br>
                <b style="color:#9CA3AF;font-size:.6875rem;letter-spacing:.08em;text-transform:uppercase">SSL</b><br>
                {'Actif' if fs.get('has_ssl',0)==1 else 'Inactif'} &nbsp;·&nbsp;
                Sitemap {'present' if fs.get('has_sitemap',0)==1 else 'absent'}
              </div>
            </div>
            """, unsafe_allow_html=True)

        with fd2:
            # 4 donut gauges pour la fiche
            dims_g = [
                (fs["score_autorite"],  "Autorite",  "#0EA5E9"),
                (fs["score_qualite"],   "Qualite",   "#10B981"),
                (fs["score_technique"], "Technique", "#8B5CF6"),
                (fs["score_global"],    "Global",    sc_color(fs["score_global"])),
            ]
            g1, g2 = st.columns(2, gap="small")
            with g1:
                st.plotly_chart(donut_gauge(dims_g[0][0], 100, dims_g[0][1], dims_g[0][2], 150),
                                use_container_width=True, config={"displayModeBar": False})
                st.plotly_chart(donut_gauge(dims_g[2][0], 100, dims_g[2][1], dims_g[2][2], 150),
                                use_container_width=True, config={"displayModeBar": False})
            with g2:
                st.plotly_chart(donut_gauge(dims_g[1][0], 100, dims_g[1][1], dims_g[1][2], 150),
                                use_container_width=True, config={"displayModeBar": False})
                st.plotly_chart(donut_gauge(dims_g[3][0], 100, dims_g[3][1], dims_g[3][2], 150),
                                use_container_width=True, config={"displayModeBar": False})

    st.markdown('</div>', unsafe_allow_html=True)
