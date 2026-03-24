"""
SenWebStats — Dashboard v5 · "The Informed Monolith"
Design : Navy #00113a + Emerald #006d36 · Manrope + Inter · Fond clair
"""
import sys, os, io, json, sqlite3
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
    CATEGORY_LABELS = {"presse":"Presse & Médias","ecommerce":"E-commerce","telephonie":"Téléphonie","banque_finance":"Banque & Finance","emploi":"Emploi"}

st.set_page_config(
    page_title="SenWebStats · Observatory",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — "THE INFORMED MONOLITH"
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@700;800&family=Inter:wght@400;500;600;700&display=swap');

/* ── TOKENS ── */
:root {
  --primary:                #00113a;
  --primary-container:      #002366;
  --primary-fixed-dim:      #b3c5ff;
  --on-primary-fixed:       #00174a;
  --secondary:              #006d36;
  --secondary-container:    #83fba5;
  --on-secondary-container: #00743a;
  --surface:                #f8f9fa;
  --surface-low:            #f3f4f5;
  --surface-card:           #ffffff;
  --surface-high:           #e7e8e9;
  --on-surface:             #191c1d;
  --on-surface-var:         #444650;
  --error:                  #ba1a1a;
  --error-container:        #ffdad6;
  --on-error-container:     #93000a;
}

/* ── RESET STREAMLIT ── */
#MainMenu,footer,header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display:none !important; }

html,body,[data-testid="stAppViewContainer"] {
  background: var(--surface) !important;
  font-family: 'Inter',sans-serif !important;
  color: var(--on-surface) !important;
}
.block-container { padding:0 !important; max-width:100% !important; }

/* ── SIDEBAR ── */
[data-testid="stSidebar"] { background: var(--surface-card) !important; }
[data-testid="stSidebarContent"] { padding:0 !important; }

[data-testid="stRadio"] > label { display:none !important; }
[data-testid="stRadio"] > div   { gap:0 !important; }
[data-testid="stRadio"] [type="radio"] { display:none !important; }
[data-testid="stRadio"] label {
  display:flex !important; align-items:center !important;
  gap:10px !important; padding:10px 16px !important;
  border-radius:8px !important; margin:2px 8px !important;
  font-family:'Inter',sans-serif !important; font-size:.875rem !important;
  font-weight:400 !important; color:var(--on-surface-var) !important;
  cursor:pointer !important; transition:all .15s !important;
}
[data-testid="stRadio"] label:hover {
  background:var(--surface-low) !important; color:var(--on-surface) !important;
}
[data-testid="stRadio"] label[data-checked="true"],
[data-testid="stRadio"] label[aria-checked="true"] {
  background:var(--primary-fixed-dim) !important;
  color:var(--primary) !important; font-weight:600 !important;
}

/* ── INPUTS ── */
[data-testid="stSelectbox"] > div > div,
[data-baseweb="select"] > div {
  background:var(--surface-high) !important;
  border:1px solid rgba(197,198,210,.1) !important;
  border-radius:8px !important;
  font-family:'Inter',sans-serif !important; font-size:.875rem !important;
}
[data-testid="stMultiSelect"] > div {
  background:var(--surface-high) !important;
  border:1px solid rgba(197,198,210,.1) !important; border-radius:8px !important;
}
[data-testid="stMultiSelect"] span {
  background:#dbe1ff !important; color:#00174a !important;
  border:none !important; border-radius:999px !important;
  font-size:.6875rem !important; font-weight:500 !important;
}

/* ── DATAFRAME ── */
[data-testid="stDataFrame"] { border-radius:12px !important; overflow:hidden !important; }
[data-testid="stDataFrame"] th {
  background:var(--surface-low) !important; color:var(--on-surface-var) !important;
  font-family:'Inter',sans-serif !important; font-size:.6875rem !important;
  letter-spacing:.08em !important; text-transform:uppercase !important; font-weight:600 !important;
}
[data-testid="stDataFrame"] td {
  color:var(--on-surface) !important; font-family:'Inter',sans-serif !important;
  font-size:.875rem !important; background:var(--surface-card) !important;
}

/* ── BUTTONS ── */
.stButton > button {
  background:var(--primary) !important; color:#fff !important;
  border:none !important; border-radius:12px !important;
  font-family:'Inter',sans-serif !important; font-weight:600 !important;
  font-size:.875rem !important; padding:10px 20px !important;
  transition:opacity .2s !important;
}
.stButton > button:hover { opacity:.88 !important; }
[data-testid="stDownloadButton"] > button {
  background:var(--secondary-container) !important;
  color:var(--on-secondary-container) !important;
  border:none !important; border-radius:12px !important;
  font-family:'Inter',sans-serif !important; font-weight:600 !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:var(--surface-low); }
::-webkit-scrollbar-thumb { background:#c5c6d2; border-radius:4px; }

/* ── LAYOUT ── */
.mwrap { padding:2.5rem 3rem 6rem; background:var(--surface); }

/* ── PAGE HEADER ── */
.ph-live { display:flex; align-items:center; gap:8px; margin-bottom:12px; }
.ph-dot {
  width:8px; height:8px; border-radius:50%;
  background:var(--secondary); flex-shrink:0;
  animation:pulse-dot 2s infinite;
}
@keyframes pulse-dot {
  0%,100% { opacity:1; transform:scale(1); }
  50%      { opacity:.6; transform:scale(.85); }
}
.ph-eye {
  font-family:'Inter',sans-serif; font-size:.6875rem; font-weight:700;
  color:var(--secondary); letter-spacing:.1em; text-transform:uppercase;
}
.ph-title {
  font-family:'Manrope',sans-serif; font-size:2.6rem; font-weight:800;
  color:var(--on-surface); line-height:1.05; letter-spacing:-.02em; margin:0 0 8px;
}
.ph-title .acc { color:var(--secondary); }
.ph-sub { font-family:'Inter',sans-serif; font-size:.875rem; color:var(--on-surface-var); margin:0; line-height:1.6; }

/* ── KPI ── */
.kpi-card { background:var(--surface-card); border-radius:12px; padding:20px 24px; box-shadow:0 8px 32px rgba(25,28,29,.04); }
.kpi-top  { display:flex; justify-content:space-between; align-items:center; margin-bottom:4px; }
.kpi-lbl  { font-family:'Inter',sans-serif; font-size:.6875rem; font-weight:500; color:var(--on-surface-var); letter-spacing:.08em; text-transform:uppercase; }
.kpi-val  { font-family:'Manrope',sans-serif; font-size:2.6rem; font-weight:800; color:var(--on-surface); line-height:1; letter-spacing:-.02em; margin:6px 0 4px; }
.kpi-sub  { font-family:'Inter',sans-serif; font-size:.6875rem; color:var(--on-surface-var); margin-bottom:12px; }
.kpi-chip { border-radius:999px; padding:2px 8px; font-family:'Inter',sans-serif; font-size:.6875rem; font-weight:700; display:inline-block; }
.chip-g   { background:#83fba5; color:#00210c; }
.chip-r   { background:#ffdad6; color:#93000a; }
.chip-n   { background:var(--surface-high); color:var(--on-surface-var); }
.kpi-bar-track { height:3px; background:var(--surface-high); border-radius:2px; overflow:hidden; }
.kpi-bar-fill  { height:100%; border-radius:2px; }

/* ── SECTION LABEL ── */
.sec { font-family:'Inter',sans-serif; font-size:.6875rem; font-weight:700; color:var(--on-surface-var); letter-spacing:.1em; text-transform:uppercase; margin:2rem 0 1rem; }

/* ── RANK ROW ── */
.rrow { display:grid; grid-template-columns:2rem 1fr auto auto; align-items:center; padding:12px 20px; gap:12px; transition:background .12s; }
.rrow:hover { background:var(--surface-low); }
.rn   { font-family:'Inter',sans-serif; font-size:.6875rem; color:var(--on-surface-var); text-align:right; font-weight:500; }
.rname{ font-size:.875rem; font-weight:600; color:var(--on-surface); }
.rcat { font-size:.6875rem; color:var(--on-surface-var); margin-top:2px; }
.rbar-w { height:3px; border-radius:2px; background:var(--surface-high); margin-top:5px; overflow:hidden; }
.rbar   { height:100%; border-radius:2px; }
.rscr { font-family:'Manrope',sans-serif; font-size:.875rem; font-weight:700; text-align:right; }
.rtrf { font-family:'Inter',sans-serif; font-size:.75rem; color:var(--secondary); text-align:right; white-space:nowrap; }

/* ── CARD ── */
.crd { background:var(--surface-card); border-radius:12px; overflow:hidden; box-shadow:0 8px 32px rgba(25,28,29,.04); }
.crd-hd { padding:12px 20px; background:var(--surface-low); font-family:'Inter',sans-serif; font-size:.6875rem; font-weight:600; color:var(--on-surface-var); letter-spacing:.08em; text-transform:uppercase; display:flex; justify-content:space-between; }

/* ── CHIPS ── */
.ch { border-radius:999px; padding:3px 10px; font-family:'Inter',sans-serif; font-size:.6875rem; font-weight:700; white-space:nowrap; display:inline-block; }
.ch-p { background:#dbe1ff; color:#00174a; }
.ch-s { background:#83fba5; color:#00210c; }
.ch-e { background:#ffdad6; color:#93000a; }
.ch-n { background:var(--surface-high); color:var(--on-surface-var); }

/* ── INFO BOX ── */
.ibox { background:#dbe1ff; color:#00174a; border-radius:12px; padding:16px 20px; font-family:'Inter',sans-serif; font-size:.875rem; margin:1rem 0; }

/* ── DARK CARD ── */
.dark-crd { background:linear-gradient(135deg,#00113a,#002366); border-radius:12px; padding:24px; color:#fff; }

/* ── STATUS PILLS ── */
.pills { display:flex; gap:.5rem; flex-wrap:wrap; margin-bottom:1.5rem; }
.pill  { display:inline-flex; align-items:center; gap:.35rem; padding:.3rem .75rem; border-radius:20px; font-size:.6875rem; font-weight:500; font-family:'Inter',sans-serif; }
.pill-ok   { background:#f0fdf4; color:#006d36; border:1px solid rgba(0,109,54,.2); }
.pill-warn { background:#fffbeb; color:#d97706; border:1px solid rgba(217,119,6,.2); }
.pill-gray { background:var(--surface-low); color:var(--on-surface-var); border:1px solid var(--surface-high); }

</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# BASE DE DONNÉES
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

    # Remplissage robuste — sans df.get()
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

    # Scores composites
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

    # Trafic : CTR model si disponible, sinon loi de puissance
    if _CTR_OK:
        try:
            df = compute_ctr_scores(df)
            df["trafic_estime"] = df["trafic_ctr"]
        except Exception:
            df["trafic_estime"] = df.apply(
                lambda r: int(CATEGORY_BASE.get(r["category"], 50000) * (r["score_global"] / 100) ** 1.5),
                axis=1,
            )
            df["trafic_ctr"] = df["trafic_estime"]
            df["position_estimee"] = 10
    else:
        df["trafic_estime"] = df.apply(
            lambda r: int(CATEGORY_BASE.get(r["category"], 50000) * (r["score_global"] / 100) ** 1.5),
            axis=1,
        )
        df["trafic_ctr"] = df["trafic_estime"]
        df["position_estimee"] = 10

    return df.sort_values("score_global", ascending=False).reset_index(drop=True)


# ══════════════════════════════════════════════════════════════════════════════
# THÈME PLOTLY — PREMIUM
# ══════════════════════════════════════════════════════════════════════════════
CAT_COLORS = {
    "presse":         "#0EA5E9",
    "ecommerce":      "#10B981",
    "telephonie":     "#8B5CF6",
    "banque_finance": "#F59E0B",
    "emploi":         "#EF4444",
}
CHART_PAL = ["#0EA5E9","#10B981","#F59E0B","#8B5CF6","#EF4444","#06B6D4","#F472B6","#84CC16"]
AREA_FILLS = [
    "rgba(14,165,233,0.15)","rgba(16,185,129,0.12)",
    "rgba(245,158,11,0.12)","rgba(139,92,246,0.10)",
    "rgba(239,68,68,0.10)","rgba(6,182,212,0.10)",
]

_GX = dict(showgrid=True, gridcolor="rgba(107,114,128,0.08)", gridwidth=1,
           linecolor="rgba(0,0,0,0)", zeroline=False, showline=False,
           tickfont=dict(size=10, color="#9CA3AF", family="Inter"))
_GY = dict(**_GX)

def hex_alpha(color, alpha=0.13):
    c = color.lstrip("#")
    r, g, b = int(c[0:2],16), int(c[2:4],16), int(c[4:6],16)
    return f"rgba({r},{g},{b},{alpha})"

def base_layout(title="", height=420, margin=None):
    m = margin or dict(l=0, r=0, t=(48 if title else 16), b=0)
    layout = dict(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        font=dict(family="Inter, sans-serif", color="#6B7280", size=11),
        margin=m,
        xaxis=dict(**_GX),
        yaxis=dict(**_GY),
        legend=dict(
            orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=11, color="#6B7280", family="Inter"),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(17,24,39,0.92)", bordercolor="rgba(0,0,0,0)",
            font=dict(family="Inter", size=12, color="#ffffff"),
        ),
    )
    if title:
        layout["title"] = dict(
            text=title,
            font=dict(family="Manrope, sans-serif", size=14, color="#191c1d"),
            x=0, pad=dict(l=0, b=12),
        )
    return layout

# Ancien PT maintenu pour compatibilité rétro (pages non encore migrées)
PT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, sans-serif", color="#6B7280", size=11),
    margin=dict(l=0, r=0, t=36, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=10, color="#6B7280", family="Inter")),
)
def xa(**kw): return {**_GX, **kw}
def ya(**kw): return {**_GY, **kw}


# ══════════════════════════════════════════════════════════════════════════════
# UTILITAIRES
# ══════════════════════════════════════════════════════════════════════════════
def fmt(n):
    try:
        return f"{int(n):,}".replace(",", "\u202f")
    except Exception:
        return "—"

def sc_color(v):
    if v is None:
        return "#444650"
    if v >= 60:
        return "#006d36"
    if v >= 40:
        return "#d97706"
    return "#ba1a1a"

def page_header(eyebrow, title_html, subtitle, right_meta=None):
    right = f'<div style="font-family:Inter,sans-serif;font-size:.6875rem;color:#444650;text-align:right;line-height:2">{right_meta}</div>' if right_meta else ""
    st.markdown(f"""
    <div style="display:flex;justify-content:space-between;align-items:flex-start;padding:0 0 2rem">
      <div>
        <div class="ph-live">
          <div class="ph-dot"></div>
          <span class="ph-eye">{eyebrow}</span>
        </div>
        <div class="ph-title">{title_html}</div>
        <p class="ph-sub">{subtitle}</p>
      </div>
      {right}
    </div>
    """, unsafe_allow_html=True)

def kpi_card(label, value, delta, delta_pos, subtext, progress=0.5, color="#006d36"):
    chip_cls = "chip-g" if delta_pos else ("chip-r" if delta_pos is False else "chip-n")
    bar_pct = int(min(max(progress, 0), 1) * 100)
    return f"""
    <div class="kpi-card">
      <div class="kpi-top">
        <span class="kpi-lbl">{label}</span>
        <span class="kpi-chip {chip_cls}">{delta}</span>
      </div>
      <div class="kpi-val">{value}</div>
      <div class="kpi-sub">{subtext}</div>
      <div class="kpi-bar-track">
        <div class="kpi-bar-fill" style="width:{bar_pct}%;background:{color}"></div>
      </div>
    </div>"""

def section_label(text):
    st.markdown(f'<div class="sec">{text}</div>', unsafe_allow_html=True)

def chip(text, variant="p"):
    return f'<span class="ch ch-{variant}">{text}</span>'


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
df_all = compute_scores()

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
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # Brand
    api_pill = (
        '<span style="background:#83fba5;color:#00210c;border-radius:999px;padding:2px 8px;font-size:.6rem;font-weight:700">SERPER ACTIF</span>'
        if serper_ok else
        '<span style="background:#e7e8e9;color:#444650;border-radius:999px;padding:2px 8px;font-size:.6rem;font-weight:600">PROXY CTR</span>'
    )
    st.markdown(f"""
    <div style="padding:1.8rem 1.4rem 1.2rem">
      <div style="font-family:Manrope,sans-serif;font-size:1.35rem;font-weight:800;
                  color:#00113a;letter-spacing:-.02em">
        Sen<span style="color:#006d36">Web</span>Stats
      </div>
      <div style="font-family:Inter,sans-serif;font-size:.6rem;color:#444650;
                  text-transform:uppercase;letter-spacing:.12em;margin-top:.2rem">
        National Digital Narrative
      </div>
      <div style="margin-top:.6rem">{api_pill}</div>
    </div>
    """, unsafe_allow_html=True)

    # Nav
    st.markdown('<div style="padding:.4rem 1.4rem;font-family:Inter,sans-serif;font-size:.6rem;font-weight:700;color:#444650;letter-spacing:.12em;text-transform:uppercase">Navigation</div>', unsafe_allow_html=True)

    page = st.radio("nav", [
        "📊  Dashboard",
        "🏆  Scoring & Trafic",
        "🌐  Métadonnées",
        "⚡  Performance",
        "🔗  Backlinks",
        "⚖️  Comparaison",
        "📡  Veille & Tendances",
        "📄  Rapports & Export",
    ], label_visibility="collapsed")

    st.markdown('<div style="height:1rem"></div>', unsafe_allow_html=True)
    st.markdown('<div style="padding:.4rem 1.4rem;font-family:Inter,sans-serif;font-size:.6rem;font-weight:700;color:#444650;letter-spacing:.12em;text-transform:uppercase">Filtre secteur</div>', unsafe_allow_html=True)

    cats_df = q("SELECT DISTINCT category FROM sites ORDER BY category")
    cat_opts = ["Tous secteurs"] + (list(cats_df["category"].values) if not cats_df.empty else [])
    cat_f = st.selectbox("cat", cat_opts, label_visibility="collapsed")

    # Upgrade button
    st.markdown('<div style="height:1.5rem"></div>', unsafe_allow_html=True)
    st.markdown("""
    <div style="padding:0 1rem">
      <div style="background:linear-gradient(135deg,#00113a,#002366);
                  border-radius:12px;padding:12px 16px;text-align:center;cursor:pointer">
        <div style="font-family:Inter,sans-serif;font-size:.75rem;font-weight:600;
                    color:#fff">⬆ Upgrade Access</div>
        <div style="font-family:Inter,sans-serif;font-size:.6rem;color:rgba(255,255,255,.6);
                    margin-top:2px">API Complète · Temps réel</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div style="position:absolute;bottom:0;left:0;right:0;padding:1rem 1.4rem;
                background:#f3f4f5">
      <div style="font-family:Inter,sans-serif;font-size:.6rem;color:#444650;line-height:2">
        {n_sites} sites · 5 secteurs<br>{now}
      </div>
    </div>
    """, unsafe_allow_html=True)

# ── Filtre ──
df_f = df_all if cat_f == "Tous secteurs" else df_all[df_all["category"] == cat_f]
cat_sql = "" if cat_f == "Tous secteurs" else f"AND s.category = '{cat_f}'"


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊  Dashboard":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "LIVE · OBSERVATOIRE NATIONAL",
        'Observatoire Web <span class="acc">Sénégalais</span>',
        f"Analyse de {n_sites} sites · presse, e-commerce, telecom, finance, emploi",
        f"{now}<br>Dakar · Sénégal",
    )

    # Status
    p1 = "pill-ok" if n_crawled > 0 else "pill-gray"
    p2 = "pill-ok" if n_perf > 0 else "pill-warn"
    p3 = "pill-ok" if n_bl > 0 else "pill-warn"
    p4 = "pill-ok" if not df_all.empty else "pill-warn"
    st.markdown(f"""
    <div class="pills">
      <div class="pill {p1}"><div style="width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0"></div>
        Métadonnées {"collectées" if n_crawled > 0 else "en attente"}
      </div>
      <div class="pill {p2}"><div style="width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0"></div>
        PageSpeed {"disponible" if n_perf > 0 else "en attente"}
      </div>
      <div class="pill {p3}"><div style="width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0"></div>
        Backlinks {"collectés" if n_bl > 0 else "en attente"}
      </div>
      <div class="pill {p4}"><div style="width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0"></div>
        Scoring {"calculé" if not df_all.empty else "en cours"}
      </div>
      <div class="pill {"pill-ok" if serper_ok else "pill-gray"}"><div style="width:6px;height:6px;border-radius:50%;background:currentColor;flex-shrink:0"></div>
        Serper.dev {"actif" if serper_ok else "proxy CTR"}
      </div>
    </div>
    """, unsafe_allow_html=True)

    # KPIs
    k1, k2, k3, k4, k5 = st.columns(5, gap="medium")
    kpi_data = [
        ("Sites suivis",       str(n_sites),      "5 secteurs",    None,  "presse · e-comm · telecom",  1.0,   "#00113a"),
        ("Trafic estimé total", fmt(total_tr),     "/mois",         True,  "CTR model AWR 2023",          0.72,  "#006d36"),
        ("Score moyen",        f"{avg_sc}",        "/100",          None,  "sur tous les sites",          avg_sc/100, "#435b9f"),
        ("Avec PageSpeed",     str(n_perf),        "sites analysés",True,  "Google Lighthouse",           n_perf/max(n_sites,1), "#d97706"),
        ("Backlinks indexés",  str(n_bl),          "sites tracés",  True,  "CommonCrawl Index",           n_bl/max(n_sites,1),   "#7c3aed"),
    ]
    for col, (lbl, val, sub, pos, info, prog, color) in zip([k1,k2,k3,k4,k5], kpi_data):
        delta_txt = "↑ actif" if pos is True else ("↓ partiel" if pos is False else "stable")
        col.markdown(kpi_card(lbl, val, delta_txt, pos, f"{sub} · {info}", prog, color), unsafe_allow_html=True)

    st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        section_label("Classement global — Top 15")
        st.markdown('<div class="crd"><div class="crd-hd"><span>Site · Secteur</span><span>Score · Trafic/mois</span></div>', unsafe_allow_html=True)
        if not df_all.empty:
            mx = df_all["score_global"].max()
            for rank, row in df_all.head(15).iterrows():
                pct   = int(row["score_global"] / mx * 100) if mx > 0 else 0
                color = sc_color(row["score_global"])
                cat_c = CAT_COLORS.get(row["category"], "#888")
                st.markdown(f"""
                <div class="rrow">
                  <div class="rn">{rank+1:02d}</div>
                  <div>
                    <div class="rname">{row['name']}</div>
                    <div class="rcat" style="color:{cat_c}">{row['category']}</div>
                    <div class="rbar-w"><div class="rbar" style="width:{pct}%;background:{color}"></div></div>
                  </div>
                  <div class="rscr" style="color:{color}">{row['score_global']:.1f}<span style="font-size:.65rem;color:#444650">/100</span></div>
                  <div class="rtrf">{fmt(row['trafic_estime'])}<span style="color:#444650;font-size:.6rem"> /mois</span></div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.markdown('<div style="padding:1.5rem"><div class="ibox">Base de données introuvable. Vérifier le chemin vers senwebstats.db</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        if not df_all.empty:
            section_label("Trafic estimé par secteur")
            cat_sum = df_all.groupby("category")["trafic_estime"].sum().reset_index().sort_values("trafic_estime")
            colors_bar = [CAT_COLORS.get(c, "#888") for c in cat_sum["category"]]
            max_v = cat_sum["trafic_estime"].max() * 1.08
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=cat_sum["category"], x=[max_v]*len(cat_sum), orientation="h",
                marker=dict(color="#F3F4F5", line=dict(width=0)),
                showlegend=False, hoverinfo="skip",
            ))
            fig.add_trace(go.Bar(
                y=cat_sum["category"], x=cat_sum["trafic_estime"], orientation="h",
                marker=dict(color=colors_bar, line=dict(width=0), opacity=0.88),
                text=[f"{v/1000:.0f}k" for v in cat_sum["trafic_estime"]],
                textposition="outside", textfont=dict(size=10, color="#374151", family="Inter"),
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} visites/mois<extra></extra>",
                showlegend=False,
            ))
            lay = base_layout("Trafic estimé / mois par secteur", height=220,
                              margin=dict(l=8, r=60, t=48, b=8))
            lay["barmode"] = "overlay"
            lay["xaxis"]["showgrid"] = False
            lay["yaxis"]["tickfont"] = dict(size=11, color="#374151", family="Inter")
            fig.update_layout(**lay)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

            section_label("Parts de trafic — Top 8")
            top8 = df_all.head(8)
            fig2 = go.Figure(go.Pie(
                labels=top8["name"], values=top8["trafic_estime"],
                marker=dict(colors=[CAT_COLORS.get(c, CHART_PAL[i % len(CHART_PAL)]) for i, c in enumerate(top8["category"])],
                            line=dict(color="#fff", width=2)),
                hole=0.6, textfont=dict(family="Inter", size=9, color="#191c1d"),
                hovertemplate="<b>%{label}</b><br>%{value:,.0f} vis./mois<br>%{percent}<extra></extra>",
            ))
            fig2.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=240, showlegend=False, margin=dict(l=0, r=0, t=16, b=0),
                hoverlabel=dict(bgcolor="rgba(17,24,39,0.92)", bordercolor="rgba(0,0,0,0)",
                                font=dict(family="Inter", size=12, color="#fff")),
            )
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

            section_label("Distribution des scores par secteur")
            fig3 = go.Figure()
            for cat in df_all["category"].unique():
                dc = df_all[df_all["category"] == cat]
                c = CAT_COLORS.get(cat, "#888")
                fig3.add_trace(go.Box(
                    y=dc["score_global"], name=cat,
                    marker=dict(color=c, size=5),
                    line=dict(color=c, width=2),
                    fillcolor=hex_alpha(c, 0.12),
                    boxmean=True,
                    hovertemplate="<b>%{x}</b><br>Score: %{y:.1f}<extra></extra>",
                ))
            lay3 = base_layout("Distribution des scores globaux", height=240)
            lay3["showlegend"] = False
            lay3["yaxis"]["range"] = [0, 100]
            fig3.update_layout(**lay3)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — SCORING & TRAFIC
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🏆  Scoring & Trafic":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "MODÈLE ANALYTIQUE · CALCUL AUTOMATIQUE",
        'Scoring & <span class="acc">Trafic Estimé</span>',
        "Autorité (45%) · Qualité (35%) · Technique (20%) · Modèle CTR AWR 2023",
    )
    if df_f.empty:
        st.markdown('<div class="ibox">Aucune donnée disponible. Vérifier que la base senwebstats.db est accessible.</div>', unsafe_allow_html=True)
    else:
        k1, k2, k3, k4 = st.columns(4, gap="medium")
        best  = df_f["score_global"].max()
        above = int((df_f["score_global"] >= 50).sum())
        pos_m = round(df_f["position_estimee"].mean(), 1) if "position_estimee" in df_f.columns else "—"
        for col, (lbl, val, delta, pos, sub, prog, color) in zip([k1,k2,k3,k4],[
            ("Meilleur score",   f"{best:.1f}",    "top site",  True, f"{df_f.loc[df_f['score_global'].idxmax(),'name']}", best/100, "#00113a"),
            ("Total trafic",     fmt(df_f['trafic_estime'].sum()), "/mois", True, "CTR model",  0.75, "#006d36"),
            ("Position moy.",    f"#{pos_m}",      "SERP est.", None, "score→position proxy", 0.5, "#435b9f"),
            ("Sites > 50 pts",   str(above),       f"/{len(df_f)} sites", True, "seuil de compétitivité", above/max(len(df_f),1), "#d97706"),
        ]):
            col.markdown(kpi_card(lbl, val, delta, pos, sub, prog, color), unsafe_allow_html=True)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        # ── Hero : Bubble chart pleine largeur
        section_label("Autorité vs Trafic — bubble chart")
        fig_bubble = go.Figure()
        for cat in df_f["category"].unique():
            dc = df_f[df_f["category"] == cat]
            c = CAT_COLORS.get(cat, "#0EA5E9")
            fig_bubble.add_trace(go.Scatter(
                x=dc["score_autorite"], y=dc["trafic_estime"],
                mode="markers+text", name=cat,
                text=dc["name"], textposition="top center",
                textfont=dict(size=9, color="#6B7280", family="Inter"),
                marker=dict(
                    size=dc["score_global"] / df_f["score_global"].max() * 46 + 10,
                    color=c, opacity=0.82,
                    line=dict(width=2, color="#ffffff"),
                    sizemode="diameter",
                ),
                hovertemplate="<b>%{text}</b><br>Autorité: %{x:.1f}<br>Trafic: %{y:,.0f}/mois<extra></extra>",
            ))
        lay_b = base_layout("Autorité vs Trafic estimé  (taille = score global)", height=480)
        lay_b["xaxis"]["title"] = dict(text="Score Autorité", font=dict(size=11, color="#9CA3AF"))
        lay_b["yaxis"]["title"] = dict(text="Trafic estimé / mois", font=dict(size=11, color="#9CA3AF"))
        fig_bubble.update_layout(**lay_b)
        st.plotly_chart(fig_bubble, use_container_width=True, config={"displayModeBar": False})

        col1, col2 = st.columns(2, gap="large")

        with col1:
            top12 = df_f.nlargest(12, "trafic_estime")
            clrs = [CAT_COLORS.get(c, "#0EA5E9") for c in top12["category"]]
            max_t = top12["trafic_estime"].max() * 1.1
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                y=top12["name"], x=[max_t]*len(top12), orientation="h",
                marker=dict(color="#F3F4F5", line=dict(width=0)),
                showlegend=False, hoverinfo="skip",
            ))
            fig2.add_trace(go.Bar(
                y=top12["name"], x=top12["trafic_estime"], orientation="h",
                marker=dict(color=clrs, line=dict(width=0), opacity=0.88),
                text=[f"{v/1000:.0f}k" for v in top12["trafic_estime"]],
                textposition="outside", textfont=dict(size=10, color="#374151", family="Inter"),
                hovertemplate="<b>%{y}</b><br>%{x:,.0f} visites/mois<extra></extra>",
                showlegend=False,
            ))
            lay2 = base_layout("Top 12 — Trafic estimé / mois", height=440,
                               margin=dict(l=8, r=70, t=48, b=8))
            lay2["barmode"] = "overlay"
            lay2["xaxis"]["showgrid"] = False
            lay2["yaxis"]["categoryorder"] = "total ascending"
            lay2["yaxis"]["tickfont"] = dict(size=10, color="#374151", family="Inter")
            fig2.update_layout(**lay2)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        with col2:
            dh = df_f.set_index("name")[["score_autorite","score_qualite","score_technique","score_global"]]
            dh.columns = ["Autorité","Qualité","Technique","Global"]
            fig3 = go.Figure(go.Heatmap(
                z=dh.values.T, x=dh.index.tolist(), y=dh.columns.tolist(),
                colorscale=[
                    [0.0, "#EFF6FF"], [0.35, "#93C5FD"],
                    [0.65, "#3B82F6"], [0.85, "#1D4ED8"], [1.0, "#1E3A8A"],
                ],
                hovertemplate="<b>%{x}</b><br>%{y}: <b>%{z:.1f}</b><extra></extra>",
                showscale=True, xgap=2, ygap=2,
                colorbar=dict(thickness=10, len=0.85, outlinewidth=0,
                              tickfont=dict(size=9, color="#9CA3AF", family="Inter")),
            ))
            lay3 = base_layout("Scores par dimension — tous les sites", height=440,
                               margin=dict(l=80, r=80, t=48, b=60))
            lay3["xaxis"]["tickangle"] = -35
            lay3["xaxis"]["tickfont"] = dict(size=9, color="#9CA3AF", family="Inter")
            lay3["yaxis"]["showgrid"] = False
            fig3.update_layout(**lay3)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

        section_label("Tableau complet des scores")
        d = df_f[["name","category","score_global","score_autorite","score_qualite","score_technique","trafic_estime"]].copy()
        d.columns = ["Site","Secteur","Global","Autorité","Qualité","Technique","Trafic/mois"]
        st.dataframe(d.round(1), use_container_width=True, hide_index=True, height=400)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — MÉTADONNÉES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🌐  Métadonnées":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "COLLECTE HTML · CRAWL AUTOMATIQUE",
        'Métadonnées <span class="acc">Techniques</span>',
        "Structure · Liens · Vitesse · Conformité SEO",
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
        st.markdown('<div class="ibox">Métadonnées non collectées. Lance : <code>python main.py crawl</code></div>', unsafe_allow_html=True)
    else:
        # KPIs
        k1,k2,k3,k4 = st.columns(4, gap="medium")
        ssl_ok  = int(df_meta["has_ssl"].fillna(0).sum())
        sit_ok  = int(df_meta["has_sitemap"].fillna(0).sum())
        rob_ok  = int(df_meta["has_robots_txt"].fillna(0).sum()) if "has_robots_txt" in df_meta else 0
        avg_rt  = round(df_meta["response_time_ms"].dropna().mean(), 0) if not df_meta["response_time_ms"].dropna().empty else 0
        for col,(lbl,val,delta,pos,sub,prog,color) in zip([k1,k2,k3,k4],[
            ("SSL activé",     f"{ssl_ok}/{len(df_meta)}", f"{ssl_ok} sites", ssl_ok==len(df_meta), "HTTPS requis",  ssl_ok/max(len(df_meta),1), "#006d36"),
            ("Sitemaps",       f"{sit_ok}/{len(df_meta)}", f"{sit_ok} sites", sit_ok>=len(df_meta)*0.7, "SEO essentiel", sit_ok/max(len(df_meta),1), "#435b9f"),
            ("Robots.txt",     f"{rob_ok}/{len(df_meta)}", f"{rob_ok} sites", True, "Crawl control", rob_ok/max(len(df_meta),1), "#d97706"),
            ("Temps moy.",     f"{int(avg_rt)} ms",        "réponse",         avg_rt<2000, "<2s = bon", max(0,1-avg_rt/5000), "#7c3aed"),
        ]):
            col.markdown(kpi_card(lbl,val,delta,pos,sub,prog,color), unsafe_allow_html=True)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        # ── Hero pleine largeur : temps de réponse
        df_rt = df_meta.dropna(subset=["response_time_ms"]).sort_values("response_time_ms")
        rt_colors = ["#10B981" if v < 1000 else "#F59E0B" if v < 2500 else "#EF4444"
                     for v in df_rt["response_time_ms"]]
        max_rt = df_rt["response_time_ms"].max() * 1.1
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df_rt["name"], x=[max_rt]*len(df_rt), orientation="h",
            marker=dict(color="#F3F4F5", line=dict(width=0)),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Bar(
            y=df_rt["name"], x=df_rt["response_time_ms"], orientation="h",
            marker=dict(color=rt_colors, line=dict(width=0), opacity=0.88),
            text=[f"{v:.0f} ms" for v in df_rt["response_time_ms"]],
            textposition="outside", textfont=dict(size=10, color="#374151", family="Inter"),
            hovertemplate="<b>%{y}</b><br>%{x:.0f} ms<extra></extra>",
            showlegend=False,
        ))
        lay_rt = base_layout("Temps de réponse  vert < 1s · amber < 2.5s · rouge > 2.5s",
                             height=max(340, len(df_rt)*28),
                             margin=dict(l=8, r=80, t=48, b=8))
        lay_rt["barmode"] = "overlay"
        lay_rt["xaxis"]["showgrid"] = False
        lay_rt["yaxis"]["categoryorder"] = "total ascending"
        lay_rt["yaxis"]["tickfont"] = dict(size=10, color="#374151", family="Inter")
        fig.update_layout(**lay_rt)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        col1, col2 = st.columns(2, gap="large")
        with col1:
            df_lk = df_meta.dropna(subset=["internal_links_count"]).sort_values("internal_links_count", ascending=False).head(14)
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                x=df_lk["name"], y=df_lk["internal_links_count"],
                marker=dict(
                    color=df_lk["internal_links_count"],
                    colorscale=[[0,"#BAE6FD"],[0.5,"#0EA5E9"],[1,"#0369A1"]],
                    line=dict(width=0), opacity=0.9,
                ),
                hovertemplate="<b>%{x}</b><br>%{y} liens internes<extra></extra>",
            ))
            lay2 = base_layout("Liens internes par site", height=320)
            lay2["xaxis"]["tickangle"] = -35
            lay2["xaxis"]["tickfont"] = dict(size=9, color="#9CA3AF", family="Inter")
            fig2.update_layout(**lay2)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        with col2:
            total_m = len(df_meta)
            labels_c = ["SSL activé","Sitemap","Robots.txt"]
            vals_c   = [ssl_ok, sit_ok, rob_ok]
            fig3 = go.Figure(go.Bar(
                x=labels_c, y=vals_c,
                marker=dict(color=["#10B981","#8B5CF6","#0EA5E9"], line=dict(width=0), opacity=0.88),
                text=[f"{v}/{total_m}" for v in vals_c],
                textposition="outside", textfont=dict(size=13, color="#374151", family="Manrope", weight=700),
                hovertemplate="<b>%{x}</b><br>%{y} sites<extra></extra>",
            ))
            lay3 = base_layout("Conformité technique", height=320)
            lay3["yaxis"]["range"] = [0, total_m + 4]
            lay3["xaxis"]["showgrid"] = False
            fig3.update_layout(**lay3)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

        section_label("Tableau complet")
        d = df_meta[["name","category","response_time_ms","word_count","has_ssl","has_sitemap"]].copy()
        d.columns = ["Site","Secteur","Temps(ms)","Mots","SSL","Sitemap"]
        d["SSL"]     = d["SSL"].apply(lambda x: "✓" if x==1 else "✗")
        d["Sitemap"] = d["Sitemap"].apply(lambda x: "✓" if x==1 else "✗")
        st.dataframe(d, use_container_width=True, hide_index=True, height=300)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 4 — PERFORMANCE
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚡  Performance":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "PAGESPEED INSIGHTS · GOOGLE LIGHTHOUSE",
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
        st.markdown('<div class="ibox">Scores PageSpeed non collectés. Lance : <code>python main.py perf</code></div>', unsafe_allow_html=True)
    else:
        # KPIs
        k1,k2,k3,k4 = st.columns(4, gap="medium")
        avg_p = round(df_perf["performance_score"].mean(),1)
        avg_s = round(df_perf["seo_score"].mean(),1)
        avg_a = round(df_perf["accessibility_score"].mean(),1)
        above90 = int((df_perf["performance_score"]>=90).sum())
        for col,(lbl,val,delta,pos,sub,prog,color) in zip([k1,k2,k3,k4],[
            ("Perf. moyenne",  f"{avg_p}",    "/100",   avg_p>=50,  "Lighthouse score", avg_p/100,       "#00113a"),
            ("SEO moyen",      f"{avg_s}",    "/100",   avg_s>=70,  "Optimisation",     avg_s/100,       "#006d36"),
            ("Accessibilité",  f"{avg_a}",    "/100",   avg_a>=70,  "WCAG",             avg_a/100,       "#435b9f"),
            ("Score ≥ 90",     str(above90),  "sites",  above90>0,  "Excellents",       above90/max(len(df_perf),1), "#d97706"),
        ]):
            col.markdown(kpi_card(lbl,val,delta,pos,sub,prog,color), unsafe_allow_html=True)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        # ── Hero : scores performances classés
        top = df_perf.sort_values("performance_score")
        p_colors = ["#10B981" if v>=90 else "#F59E0B" if v>=50 else "#EF4444"
                    for v in top["performance_score"]]
        max_p = 105
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=top["name"], x=[max_p]*len(top), orientation="h",
            marker=dict(color="#F3F4F5", line=dict(width=0)),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Bar(
            y=top["name"], x=top["performance_score"], orientation="h",
            marker=dict(color=p_colors, line=dict(width=0), opacity=0.88),
            text=[f"{v:.0f}" for v in top["performance_score"]],
            textposition="outside", textfont=dict(size=11, color="#374151", family="Manrope", weight=700),
            hovertemplate="<b>%{y}</b><br>%{x:.0f}/100<extra></extra>",
            showlegend=False,
        ))
        lay_p = base_layout("Score Performance Lighthouse  vert ≥ 90 · amber ≥ 50 · rouge < 50",
                            height=max(380, len(top)*30),
                            margin=dict(l=8, r=60, t=48, b=8))
        lay_p["barmode"] = "overlay"
        lay_p["xaxis"]["range"] = [0, max_p + 5]
        lay_p["xaxis"]["showgrid"] = False
        lay_p["yaxis"]["tickfont"] = dict(size=10, color="#374151", family="Inter")
        fig.update_layout(**lay_p)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        col1, col2 = st.columns(2, gap="large")
        with col1:
            # Scatter Performance vs SEO
            fig2 = go.Figure()
            for cat in df_perf["category"].unique():
                dc = df_perf[df_perf["category"] == cat]
                c = CAT_COLORS.get(cat, "#0EA5E9")
                fig2.add_trace(go.Scatter(
                    x=dc["performance_score"], y=dc["seo_score"],
                    mode="markers+text", name=cat,
                    text=dc["name"], textposition="top center",
                    textfont=dict(size=8, color="#6B7280", family="Inter"),
                    marker=dict(size=12, color=c, opacity=0.85,
                                line=dict(width=2, color="#ffffff")),
                    hovertemplate="<b>%{text}</b><br>Perf: %{x:.0f} · SEO: %{y:.0f}<extra></extra>",
                ))
            lay2 = base_layout("Performance vs SEO", height=380)
            lay2["xaxis"]["title"] = dict(text="Performance", font=dict(size=11, color="#9CA3AF"))
            lay2["xaxis"]["range"] = [0, 100]
            lay2["yaxis"]["title"] = dict(text="SEO", font=dict(size=11, color="#9CA3AF"))
            lay2["yaxis"]["range"] = [0, 100]
            fig2.update_layout(**lay2)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        with col2:
            # Accessibilité classée
            df_acc = df_perf.sort_values("accessibility_score")
            acc_colors = ["#10B981" if v >= 90 else "#F59E0B" if v >= 60 else "#EF4444"
                          for v in df_acc["accessibility_score"]]
            fig3 = go.Figure()
            fig3.add_trace(go.Bar(
                y=df_acc["name"], x=[105]*len(df_acc), orientation="h",
                marker=dict(color="#F3F4F5", line=dict(width=0)),
                showlegend=False, hoverinfo="skip",
            ))
            fig3.add_trace(go.Bar(
                y=df_acc["name"], x=df_acc["accessibility_score"], orientation="h",
                marker=dict(color=acc_colors, line=dict(width=0), opacity=0.88),
                text=[f"{v:.0f}" for v in df_acc["accessibility_score"]],
                textposition="outside", textfont=dict(size=10, color="#374151", family="Inter"),
                hovertemplate="<b>%{y}</b><br>Accessibilité: %{x:.0f}/100<extra></extra>",
                showlegend=False,
            ))
            lay3 = base_layout("Accessibilité (WCAG)", height=380,
                               margin=dict(l=8, r=60, t=48, b=8))
            lay3["barmode"] = "overlay"
            lay3["xaxis"]["range"] = [0, 110]
            lay3["xaxis"]["showgrid"] = False
            lay3["yaxis"]["tickfont"] = dict(size=10, color="#374151", family="Inter")
            fig3.update_layout(**lay3)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

        section_label("Core Web Vitals — tableau complet")
        cwv = df_perf[["name","performance_score","lcp_ms","fcp_ms","ttfb_ms","cls_score","accessibility_score","best_practices_score"]].copy()
        cwv.columns = ["Site","Perf","LCP(ms)","FCP(ms)","TTFB(ms)","CLS","Accessibilité","Best Practices"]
        st.dataframe(cwv.round(1), use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 5 — BACKLINKS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "🔗  Backlinks":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "COMMONCRAWL INDEX · AUTORITÉ DE DOMAINE",
        'Autorité & <span class="acc">Backlinks</span>',
        "Pages indexées · Domaines référents · Variation mensuelle",
    )

    df_bl = q(f"""
        SELECT s.name, s.category, s.domain,
               sb.total_backlinks, sb.referring_domains, sb.backlinks_change
        FROM site_backlinks sb JOIN sites s ON s.id=sb.site_id
        WHERE sb.collected_at=(SELECT MAX(collected_at) FROM site_backlinks WHERE site_id=sb.site_id)
        {cat_sql} ORDER BY sb.total_backlinks DESC
    """)

    if df_bl.empty:
        st.markdown('<div class="ibox">Backlinks non collectés. Lance : <code>python main.py backlinks</code></div>', unsafe_allow_html=True)
    else:
        # KPIs
        k1,k2,k3,k4 = st.columns(4, gap="medium")
        total_bl = int(df_bl["total_backlinks"].sum())
        total_rd = int(df_bl["referring_domains"].sum())
        best_bl  = df_bl.loc[df_bl["total_backlinks"].idxmax(), "name"] if not df_bl.empty else "—"
        avg_rd   = round(df_bl["referring_domains"].mean(), 0)
        for col,(lbl,val,delta,pos,sub,prog,color) in zip([k1,k2,k3,k4],[
            ("Total backlinks",  fmt(total_bl), "pages indexées", True, "CommonCrawl",    0.8, "#00113a"),
            ("Dom. référents",   fmt(total_rd), "domaines uniq.", True, "Link diversity", 0.7, "#006d36"),
            ("Leader",           best_bl[:12],  "autorité max",  True, "Top site",       1.0, "#435b9f"),
            ("Moy. dom. réf.",   str(int(avg_rd)), "par site",   None, "Distribution",  0.5, "#d97706"),
        ]):
            col.markdown(kpi_card(lbl,val,delta,pos,sub,prog,color), unsafe_allow_html=True)

        st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

        # ── Hero pleine largeur : backlinks
        df_bl_s = df_bl.sort_values("total_backlinks")
        bl_colors = [CAT_COLORS.get(c, "#0EA5E9") for c in df_bl_s["category"]]
        max_bl = df_bl_s["total_backlinks"].max() * 1.1
        fig = go.Figure()
        fig.add_trace(go.Bar(
            y=df_bl_s["name"], x=[max_bl]*len(df_bl_s), orientation="h",
            marker=dict(color="#F3F4F5", line=dict(width=0)),
            showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Bar(
            y=df_bl_s["name"], x=df_bl_s["total_backlinks"], orientation="h",
            marker=dict(color=bl_colors, line=dict(width=0), opacity=0.88),
            text=[f"{int(v):,}" for v in df_bl_s["total_backlinks"]],
            textposition="outside", textfont=dict(size=10, color="#374151", family="Inter"),
            hovertemplate="<b>%{y}</b><br>%{x:,} pages indexées<extra></extra>",
            showlegend=False,
        ))
        lay_bl = base_layout("Pages indexées — CommonCrawl",
                             height=max(380, len(df_bl_s)*30),
                             margin=dict(l=8, r=80, t=48, b=8))
        lay_bl["barmode"] = "overlay"
        lay_bl["xaxis"]["showgrid"] = False
        lay_bl["yaxis"]["tickfont"] = dict(size=10, color="#374151", family="Inter")
        fig.update_layout(**lay_bl)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

        col1, col2 = st.columns(2, gap="large")
        with col1:
            top_rd = df_bl.sort_values("referring_domains")
            max_rd = top_rd["referring_domains"].max() * 1.1
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(
                y=top_rd["name"], x=[max_rd]*len(top_rd), orientation="h",
                marker=dict(color="#F3F4F5", line=dict(width=0)),
                showlegend=False, hoverinfo="skip",
            ))
            fig2.add_trace(go.Bar(
                y=top_rd["name"], x=top_rd["referring_domains"], orientation="h",
                marker=dict(color="#10B981", line=dict(width=0), opacity=0.88),
                text=[f"{int(v):,}" for v in top_rd["referring_domains"]],
                textposition="outside", textfont=dict(size=10, color="#374151", family="Inter"),
                hovertemplate="<b>%{y}</b><br>%{x:,} domaines référents<extra></extra>",
                showlegend=False,
            ))
            lay2 = base_layout("Domaines référents", height=380,
                               margin=dict(l=8, r=70, t=48, b=8))
            lay2["barmode"] = "overlay"
            lay2["xaxis"]["showgrid"] = False
            lay2["yaxis"]["categoryorder"] = "total ascending"
            lay2["yaxis"]["tickfont"] = dict(size=10, color="#374151", family="Inter")
            fig2.update_layout(**lay2)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

        with col2:
            # Backlinks vs domaines scatter
            fig3 = go.Figure()
            for cat in df_bl["category"].unique():
                dc = df_bl[df_bl["category"] == cat]
                c = CAT_COLORS.get(cat, "#0EA5E9")
                fig3.add_trace(go.Scatter(
                    x=dc["referring_domains"], y=dc["total_backlinks"],
                    mode="markers+text", name=cat,
                    text=dc["name"], textposition="top center",
                    textfont=dict(size=8, color="#6B7280", family="Inter"),
                    marker=dict(size=14, color=c, opacity=0.85,
                                line=dict(width=2, color="#fff")),
                    hovertemplate="<b>%{text}</b><br>Dom. réf: %{x:,}<br>Pages: %{y:,}<extra></extra>",
                ))
            lay3 = base_layout("Domaines référents vs Pages indexées", height=380)
            lay3["xaxis"]["title"] = dict(text="Domaines référents", font=dict(size=11, color="#9CA3AF"))
            lay3["yaxis"]["title"] = dict(text="Pages indexées", font=dict(size=11, color="#9CA3AF"))
            fig3.update_layout(**lay3)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})

        section_label("Tableau complet")
        d = df_bl[["name","category","domain","total_backlinks","referring_domains","backlinks_change"]].copy()
        d.columns = ["Site","Secteur","Domaine","Pages indexées","Dom. référents","Variation"]
        d["Variation"] = d["Variation"].fillna(0)
        st.dataframe(d, use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 6 — COMPARAISON
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚖️  Comparaison":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "ANALYSE CONCURRENTIELLE · MULTI-SITES",
        'Comparaison <span class="acc">Directe</span>',
        "Sélectionnez jusqu'à 8 sites pour comparer toutes leurs dimensions",
    )

    sl = q("SELECT name FROM sites ORDER BY name")
    if sl.empty or df_all.empty:
        st.markdown('<div class="ibox">Données insuffisantes pour la comparaison.</div>', unsafe_allow_html=True)
    else:
        selected = st.multiselect(
            "Sites à comparer",
            options=sl["name"].tolist(),
            default=sl["name"].tolist()[:6],
            max_selections=8,
        )
        if selected:
            ds = df_all[df_all["name"].isin(selected)]
            if not ds.empty:
                PALETTE = ["#0EA5E9","#10B981","#F59E0B","#8B5CF6","#EF4444","#06B6D4","#F472B6","#84CC16"]

                # ── Hero : radar pleine largeur
                dims = ["Autorité","Qualité","Technique","Score global"]
                fig = go.Figure()
                for j, (_, row) in enumerate(ds.iterrows()):
                    c = PALETTE[j % len(PALETTE)]
                    vals = [row["score_autorite"], row["score_qualite"],
                            row["score_technique"], row["score_global"]]
                    vals += [vals[0]]
                    fig.add_trace(go.Scatterpolar(
                        r=vals, theta=dims+[dims[0]],
                        fill="toself", name=row["name"],
                        line=dict(color=c, width=2.5),
                        fillcolor=hex_alpha(c, 0.12),
                        hovertemplate="%{theta}: <b>%{r:.1f}</b><extra>" + row["name"] + "</extra>",
                    ))
                fig.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    height=500,
                    polar=dict(
                        bgcolor="rgba(0,0,0,0)",
                        radialaxis=dict(visible=True, range=[0,100],
                                        gridcolor="rgba(107,114,128,0.12)",
                                        tickfont=dict(size=9, color="#9CA3AF", family="Inter")),
                        angularaxis=dict(gridcolor="rgba(107,114,128,0.12)",
                                         tickfont=dict(size=12, color="#374151", family="Inter")),
                    ),
                    title=dict(text="Profil comparatif — radar",
                               font=dict(family="Manrope, sans-serif", size=14, color="#191c1d"), x=0),
                    legend=dict(font=dict(size=11, color="#374151", family="Inter"),
                                bgcolor="rgba(0,0,0,0)", orientation="h", y=-0.08),
                    margin=dict(l=60, r=60, t=60, b=60),
                    hoverlabel=dict(bgcolor="rgba(17,24,39,0.92)", bordercolor="rgba(0,0,0,0)",
                                    font=dict(family="Inter", size=12, color="#fff")),
                )
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

                # ── Barres groupées pleine largeur
                metrics = ["score_autorite","score_qualite","score_technique","score_global"]
                labels  = ["Autorité","Qualité","Technique","Global"]
                fig2 = go.Figure()
                for j, (_, row) in enumerate(ds.iterrows()):
                    c = PALETTE[j % len(PALETTE)]
                    fig2.add_trace(go.Bar(
                        name=row["name"], x=labels, y=[row[m] for m in metrics],
                        marker=dict(color=c, line=dict(width=0), opacity=0.88),
                        hovertemplate="<b>" + row["name"] + "</b><br>%{x}: %{y:.1f}<extra></extra>",
                    ))
                lay2 = base_layout("Comparaison par dimension", height=420)
                lay2["barmode"] = "group"
                lay2["bargap"] = 0.25
                lay2["bargroupgap"] = 0.08
                lay2["yaxis"]["range"] = [0, 100]
                lay2["xaxis"]["showgrid"] = False
                fig2.update_layout(**lay2)
                st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})

                section_label("Tableau récapitulatif")
                dt = ds[["name","category","score_global","score_autorite","score_qualite","score_technique","trafic_estime"]].copy()
                dt.columns = ["Site","Secteur","Global","Autorité","Qualité","Technique","Trafic/mois"]
                st.dataframe(dt.round(1).sort_values("Global",ascending=False), use_container_width=True, hide_index=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 7 — VEILLE & TENDANCES
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📡  Veille & Tendances":
    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "INTELLIGENCE STRATÉGIQUE · SIMULATION · RISQUES",
        'Veille & <span class="acc">Tendances</span>',
        "Simulateur d'impact · Opportunités de croissance · Sites à risque",
    )

    if df_all.empty:
        st.markdown('<div class="ibox">Données insuffisantes pour l\'analyse de tendances.</div>', unsafe_allow_html=True)
    else:
        # ── SIMULATEUR
        section_label("Simulateur d'impact SEO")
        st.markdown("""
        <div class="crd" style="padding:1.5rem 1.8rem;margin-bottom:1.5rem">
          <div style="font-family:Inter,sans-serif;font-size:.6875rem;font-weight:700;color:#006d36;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.6rem">Projection de trafic</div>
          <div style="font-size:.875rem;color:#444650;line-height:1.6">Simulez l'effet d'une amélioration des scores Lighthouse sur le trafic estimé.</div>
        </div>
        """, unsafe_allow_html=True)

        sim_col1, sim_col2, sim_col3 = st.columns([1.5,1,1], gap="large")
        with sim_col1:
            sim_site = st.selectbox("Site à simuler", df_all["name"].tolist(), key="sim_site")
        with sim_col2:
            delta_seo = st.slider("Gain SEO (points)", 0, 40, 10, key="delta_seo")
        with sim_col3:
            delta_perf = st.slider("Gain Performance (points)", 0, 40, 10, key="delta_perf")

        row_sim = df_all[df_all["name"] == sim_site].iloc[0]
        new_seo  = min(100, float(row_sim.get("seo_score") or 50) + delta_seo)
        new_perf = min(100, float(row_sim.get("performance_score") or 50) + delta_perf)
        new_acc  = float(row_sim.get("accessibility_score") or 50)
        new_qualite = round(new_seo*0.40 + new_perf*0.35 + new_acc*0.25, 1)
        new_global  = round(row_sim["score_autorite"]*0.45 + new_qualite*0.35 + row_sim["score_technique"]*0.20, 1)
        new_traffic = int(CATEGORY_BASE.get(row_sim["category"],50000) * (new_global/100)**1.5)
        delta_traffic = new_traffic - row_sim["trafic_estime"]
        delta_global  = round(new_global - row_sim["score_global"], 1)

        s1,s2,s3,s4 = st.columns(4, gap="medium")
        for col,(lbl,val,delta,pos,sub,prog,color) in zip([s1,s2,s3,s4],[
            ("Score actuel",  f"{row_sim['score_global']:.1f}", "actuel", None, "Global/100", row_sim["score_global"]/100, "#444650"),
            ("Score projeté", f"{new_global:.1f}", f"+{delta_global} pts", delta_global>0, "Projection", new_global/100, "#006d36"),
            ("Trafic actuel", fmt(row_sim["trafic_estime"]), "vis./mois", None, "Base",  0.5, "#444650"),
            ("Trafic projeté",fmt(new_traffic), f"+{fmt(delta_traffic)}", delta_traffic>0, "Gain estimé", min(new_traffic/max(row_sim["trafic_estime"],1)*0.5,1), "#006d36"),
        ]):
            col.markdown(kpi_card(lbl,val,delta,pos,sub,prog,color), unsafe_allow_html=True)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        # ── OPPORTUNITÉS
        section_label("Carte des opportunités de croissance")
        df_opp = df_all.copy()
        df_opp["score_qualite_proj"]  = df_opp["score_qualite"].apply(lambda x: min(90, x+30))
        df_opp["score_global_proj"]   = (df_opp["score_autorite"]*0.45 + df_opp["score_qualite_proj"]*0.35 + df_opp["score_technique"]*0.20).round(1)
        df_opp["trafic_potentiel"]    = df_opp.apply(lambda r: int(CATEGORY_BASE.get(r["category"],50000)*(r["score_global_proj"]/100)**1.5), axis=1)
        df_opp["gap_trafic"]          = df_opp["trafic_potentiel"] - df_opp["trafic_estime"]
        df_top_opp = df_opp.nlargest(12, "gap_trafic")

        opp_colors = [CAT_COLORS.get(c, "#0EA5E9") for c in df_top_opp["category"]]
        max_gap = df_top_opp["gap_trafic"].max() * 1.1
        fig_opp = go.Figure()
        fig_opp.add_trace(go.Bar(
            y=df_top_opp["name"], x=[max_gap]*len(df_top_opp), orientation="h",
            marker=dict(color="#F3F4F5", line=dict(width=0)),
            showlegend=False, hoverinfo="skip",
        ))
        fig_opp.add_trace(go.Bar(
            y=df_top_opp["name"], x=df_top_opp["gap_trafic"], orientation="h",
            marker=dict(color=opp_colors, opacity=0.88, line=dict(width=0)),
            text=[f"+{fmt(v)}" for v in df_top_opp["gap_trafic"]],
            textposition="outside", textfont=dict(size=10, color="#374151", family="Inter"),
            hovertemplate="<b>%{y}</b><br>Gain potentiel : +%{x:,.0f} visites/mois<extra></extra>",
            showlegend=False,
        ))
        lay_opp = base_layout("Gain potentiel si le score qualité montait à 90", height=420,
                              margin=dict(l=8, r=90, t=48, b=8))
        lay_opp["barmode"] = "overlay"
        lay_opp["xaxis"]["showgrid"] = False
        lay_opp["yaxis"]["categoryorder"] = "total ascending"
        lay_opp["yaxis"]["tickfont"] = dict(size=10, color="#374151", family="Inter")
        fig_opp.update_layout(**lay_opp)
        st.plotly_chart(fig_opp, use_container_width=True, config={"displayModeBar": False})

        # ── RISQUES
        section_label("Radar des sites à risque technique")
        df_risk = df_all.copy()
        risk = pd.Series(0.0, index=df_risk.index)

        rt_col = df_risk["response_time_ms"] if "response_time_ms" in df_risk.columns else pd.Series([1000]*len(df_risk), index=df_risk.index)
        rt_filled = rt_col.fillna(1000)
        risk += (rt_filled > 3000).astype(float) * 30
        risk += (rt_filled > 5000).astype(float) * 20

        ssl_col = df_risk["has_ssl"] if "has_ssl" in df_risk.columns else pd.Series([1]*len(df_risk), index=df_risk.index)
        risk += (ssl_col.fillna(1) == 0).astype(float) * 25

        sit_col = df_risk["has_sitemap"] if "has_sitemap" in df_risk.columns else pd.Series([1]*len(df_risk), index=df_risk.index)
        risk += (sit_col.fillna(1) == 0).astype(float) * 15
        risk += (df_risk["score_qualite"] < 40).astype(float) * 20
        risk += (df_risk["score_autorite"] < 20).astype(float) * 10

        df_risk["score_risque"] = risk.clip(0, 100).round(0).astype(int)
        df_risk_sorted = df_risk.sort_values("score_risque", ascending=False).head(12)

        r1, r2 = st.columns(2, gap="large")
        with r1:
            risk_colors = ["#EF4444" if v>=60 else "#F59E0B" if v>=30 else "#10B981"
                           for v in df_risk_sorted["score_risque"]]
            max_r = 120
            fig_risk = go.Figure()
            fig_risk.add_trace(go.Bar(
                y=df_risk_sorted["name"], x=[max_r]*len(df_risk_sorted), orientation="h",
                marker=dict(color="#F3F4F5", line=dict(width=0)),
                showlegend=False, hoverinfo="skip",
            ))
            fig_risk.add_trace(go.Bar(
                y=df_risk_sorted["name"], x=df_risk_sorted["score_risque"], orientation="h",
                marker=dict(color=risk_colors, opacity=0.88, line=dict(width=0)),
                text=df_risk_sorted["score_risque"].astype(str),
                textposition="outside", textfont=dict(size=11, color="#374151", family="Manrope", weight=700),
                hovertemplate="<b>%{y}</b><br>Risque: %{x}/100<extra></extra>",
                showlegend=False,
            ))
            lay_r = base_layout("Score de risque  rouge ≥ 60 · amber ≥ 30 · vert < 30",
                                height=400, margin=dict(l=8, r=60, t=48, b=8))
            lay_r["barmode"] = "overlay"
            lay_r["xaxis"]["range"] = [0, max_r + 10]
            lay_r["xaxis"]["showgrid"] = False
            lay_r["yaxis"]["categoryorder"] = "total ascending"
            lay_r["yaxis"]["tickfont"] = dict(size=10, color="#374151", family="Inter")
            fig_risk.update_layout(**lay_r)
            st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar": False})

        with r2:
            section_label("Facteurs de risque détectés")
            rt_tab = df_risk_sorted[["name","category","score_risque"]].copy()
            rt_tab["Temps rép."] = rt_filled.reindex(df_risk_sorted.index).apply(lambda x: "LENT" if x>3000 else "OK")
            rt_tab["SSL"]     = ssl_col.reindex(df_risk_sorted.index).fillna(0).apply(lambda x: "OK" if x==1 else "MANQUANT")
            rt_tab["Sitemap"] = sit_col.reindex(df_risk_sorted.index).fillna(0).apply(lambda x: "OK" if x==1 else "MANQUANT")
            rt_tab["Qualité"] = df_risk_sorted["score_qualite"].apply(lambda x: "FAIBLE" if x<40 else "OK")
            rt_tab = rt_tab.rename(columns={"name":"Site","category":"Secteur","score_risque":"Risque/100"})
            st.dataframe(rt_tab, use_container_width=True, hide_index=True, height=380)

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 8 — RAPPORTS & EXPORT
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📄  Rapports & Export":
    import base64 as _b64

    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "EXPORT · RAPPORT EXÉCUTIF · FICHE SITE",
        'Rapports & <span class="acc">Export</span>',
        "Télécharge les données · Génère un rapport HTML imprimable",
        f"{now}<br>{n_sites} sites · {len(df_all)} scores calculés",
    )

    if df_all.empty:
        st.markdown('<div class="ibox">Aucune donnée disponible pour l\'export.</div>', unsafe_allow_html=True)
    else:
        section_label("Exports rapides")
        exp1, exp2, exp3 = st.columns(3, gap="large")

        # ── CSV
        with exp1:
            st.markdown("""
            <div class="crd" style="padding:1.4rem 1.6rem;min-height:130px">
              <div style="font-family:Inter,sans-serif;font-size:.6875rem;font-weight:700;color:#006d36;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.5rem">CSV · Scores complets</div>
              <div style="font-size:.8rem;color:#444650;line-height:1.6">Tous les scores pour les 28 sites. Compatible Excel, Google Sheets, Power BI.</div>
            </div>
            """, unsafe_allow_html=True)
            csv_cols = ["name","domain","category","score_global","score_autorite","score_qualite","score_technique","trafic_estime","total_backlinks","referring_domains","performance_score","seo_score","accessibility_score","response_time_ms","has_ssl","has_sitemap"]
            csv_df = df_all[[c for c in csv_cols if c in df_all.columns]].copy()
            csv_df.columns = [c.replace("_"," ").title() for c in csv_df.columns]
            csv_bytes = csv_df.round(1).to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
            st.download_button("⬇ Télécharger CSV", data=csv_bytes,
                file_name=f"senwebstats_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv", use_container_width=True)

        # ── JSON
        with exp2:
            st.markdown("""
            <div class="crd" style="padding:1.4rem 1.6rem;min-height:130px">
              <div style="font-family:Inter,sans-serif;font-size:.6875rem;font-weight:700;color:#435b9f;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.5rem">JSON · API-ready</div>
              <div style="font-size:.8rem;color:#444650;line-height:1.6">Format structuré pour intégrations Power BI, Tableau, dashboards custom.</div>
            </div>
            """, unsafe_allow_html=True)
            json_data = df_all[["name","domain","category","score_global","score_autorite","score_qualite","score_technique","trafic_estime"]].round(1).to_dict(orient="records")
            json_bytes = json.dumps({"generated_at": now, "sites": json_data}, ensure_ascii=False, indent=2).encode("utf-8")
            st.download_button("⬇ Télécharger JSON", data=json_bytes,
                file_name=f"senwebstats_{datetime.now().strftime('%Y%m%d')}.json",
                mime="application/json", use_container_width=True)

        # ── HTML
        with exp3:
            st.markdown("""
            <div class="crd" style="padding:1.4rem 1.6rem;min-height:130px">
              <div style="font-family:Inter,sans-serif;font-size:.6875rem;font-weight:700;color:#00113a;letter-spacing:.1em;text-transform:uppercase;margin-bottom:.5rem">HTML · Rapport exécutif</div>
              <div style="font-size:.8rem;color:#444650;line-height:1.6">Rapport complet imprimable en PDF depuis le navigateur.</div>
            </div>
            """, unsafe_allow_html=True)

            all_rows = "".join([
                f"<tr><td>{i+1}</td><td><b>{r['name']}</b></td><td>{r['category']}</td>"
                f"<td style='text-align:right'>{r['score_global']:.1f}</td>"
                f"<td style='text-align:right'>{r['score_autorite']:.1f}</td>"
                f"<td style='text-align:right'>{r['score_qualite']:.1f}</td>"
                f"<td style='text-align:right'>{r['score_technique']:.1f}</td>"
                f"<td style='text-align:right'>{fmt(r['trafic_estime'])}</td></tr>"
                for i,(_, r) in enumerate(df_all.iterrows())
            ])
            html_report = f"""<!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
<title>SenWebStats — Rapport {datetime.now().strftime('%B %Y')}</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Manrope:wght@700;800&family=Inter:wght@400;600&display=swap');
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Inter',sans-serif;background:#f8f9fa;color:#191c1d;font-size:13px}}
.page{{max-width:960px;margin:0 auto;padding:48px 40px}}
h1{{font-family:'Manrope',sans-serif;font-size:2rem;font-weight:800;color:#00113a;margin-bottom:.2rem}}
h1 em{{color:#006d36;font-style:normal}}
h2{{font-family:'Inter',sans-serif;font-size:.6rem;font-weight:700;letter-spacing:.15em;text-transform:uppercase;color:#444650;margin:2rem 0 .8rem;padding-bottom:.4rem;border-bottom:1px solid #e7e8e9}}
.meta{{font-family:'Inter',sans-serif;font-size:.65rem;color:#444650;margin-bottom:2rem}}
.kpi-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:1rem 0 2rem}}
.kpi{{background:#fff;border-radius:10px;padding:1rem 1.2rem;box-shadow:0 4px 16px rgba(25,28,29,.04)}}
.kpi-lbl{{font-family:'Inter',sans-serif;font-size:.55rem;letter-spacing:.15em;text-transform:uppercase;color:#444650;margin-bottom:.4rem}}
.kpi-val{{font-family:'Manrope',sans-serif;font-size:1.6rem;font-weight:800;color:#00113a}}
.kpi-sub{{font-size:.65rem;color:#444650;margin-top:.2rem}}
table{{width:100%;border-collapse:collapse;font-size:.82rem}}
th{{background:#f3f4f5;color:#444650;font-family:'Inter',sans-serif;font-size:.55rem;letter-spacing:.1em;text-transform:uppercase;padding:.5rem .7rem;text-align:left}}
td{{padding:.55rem .7rem;border-bottom:1px solid #e7e8e9;color:#191c1d}}
tr:last-child td{{border-bottom:none}}
.footer{{margin-top:3rem;padding-top:1rem;border-top:1px solid #e7e8e9;font-size:.58rem;color:#444650;text-align:center}}
@media print{{body{{background:#fff}}.page{{padding:20px}}}}
</style></head><body><div class="page">
<h1>Observatoire Web <em>Sénégalais</em></h1>
<div class="meta">SenWebStats · Rapport exécutif · {datetime.now().strftime('%d %B %Y')} · {n_sites} sites surveillés</div>
<div class="kpi-grid">
  <div class="kpi"><div class="kpi-lbl">Sites suivis</div><div class="kpi-val">{n_sites}</div><div class="kpi-sub">5 secteurs</div></div>
  <div class="kpi"><div class="kpi-lbl">Trafic total estimé</div><div class="kpi-val">{fmt(total_tr)}</div><div class="kpi-sub">visites/mois</div></div>
  <div class="kpi"><div class="kpi-lbl">Score moyen</div><div class="kpi-val">{avg_sc}</div><div class="kpi-sub">/100</div></div>
  <div class="kpi"><div class="kpi-lbl">Avec PageSpeed</div><div class="kpi-val">{n_perf}</div><div class="kpi-sub">sites analysés</div></div>
</div>
<h2>Classement complet</h2>
<table><thead><tr><th>#</th><th>Site</th><th>Secteur</th><th>Global</th><th>Autorité</th><th>Qualité</th><th>Technique</th><th>Trafic/mois</th></tr></thead>
<tbody>{all_rows}</tbody></table>
<div class="footer">SenWebStats · Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')} · Données: CommonCrawl + PageSpeed + CTR Model AWR 2023</div>
</div></body></html>"""

            st.download_button("⬇ Télécharger HTML", data=html_report.encode("utf-8"),
                file_name=f"senwebstats_rapport_{datetime.now().strftime('%Y%m%d')}.html",
                mime="text/html", use_container_width=True)

        # ── FICHE SITE
        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)
        section_label("Fiche individuelle par site")
        site_sel = st.selectbox("Choisir un site", df_all["name"].tolist(), key="fiche_sel")
        fs = df_all[df_all["name"] == site_sel].iloc[0]

        fc1, fc2, fc3, fc4 = st.columns(4, gap="medium")
        for col,(lbl,val,color) in zip([fc1,fc2,fc3,fc4],[
            ("Score global",   f"{fs['score_global']:.1f}",    sc_color(fs["score_global"])),
            ("Autorité",       f"{fs['score_autorite']:.1f}",  sc_color(fs["score_autorite"])),
            ("Qualité",        f"{fs['score_qualite']:.1f}",   sc_color(fs["score_qualite"])),
            ("Trafic estimé",  fmt(fs["trafic_estime"]),        "#006d36"),
        ]):
            col.markdown(f"""
            <div class="kpi-card">
              <div class="kpi-lbl">{lbl}</div>
              <div class="kpi-val" style="color:{color}">{val}</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

        fd1, fd2 = st.columns(2, gap="large")
        with fd1:
            st.markdown(f"""
            <div class="crd" style="padding:1.4rem 1.6rem">
              <div class="crd-hd" style="margin:-1.4rem -1.6rem 1rem;padding:12px 20px">Informations</div>
              <div style="font-family:Inter,sans-serif;font-size:.875rem;color:#191c1d;line-height:2.2">
                <b>Domaine :</b> {fs.get('domain','—')}<br>
                <b>Secteur :</b> {fs.get('category','—')}<br>
                <b>Score technique :</b> {fs.get('score_technique','—'):.1f}/100<br>
                <b>Position estimée :</b> #{int(fs.get('position_estimee',10))}<br>
                <b>SSL :</b> {'✓ actif' if fs.get('has_ssl',0)==1 else '✗ inactif'}<br>
                <b>Sitemap :</b> {'✓ présent' if fs.get('has_sitemap',0)==1 else '✗ absent'}
              </div>
            </div>
            """, unsafe_allow_html=True)

        with fd2:
            dims = ["Autorité","Qualité","Technique","Global"]
            vals = [fs["score_autorite"],fs["score_qualite"],fs["score_technique"],fs["score_global"]]
            bar_colors = ["#10B981" if v>=60 else "#F59E0B" if v>=40 else "#EF4444" for v in vals]
            fig_f = go.Figure()
            fig_f.add_trace(go.Bar(
                y=dims, x=[105]*4, orientation="h",
                marker=dict(color="#F3F4F5", line=dict(width=0)),
                showlegend=False, hoverinfo="skip",
            ))
            fig_f.add_trace(go.Bar(
                y=dims, x=vals, orientation="h",
                marker=dict(color=bar_colors, line=dict(width=0), opacity=0.9),
                text=[f"{v:.1f}" for v in vals],
                textposition="outside", textfont=dict(size=13, color="#374151", family="Manrope", weight=700),
                hovertemplate="%{y}: %{x:.1f}/100<extra></extra>",
                showlegend=False,
            ))
            lay_f = base_layout(f"Profil — {site_sel}", height=220,
                                margin=dict(l=8, r=60, t=48, b=8))
            lay_f["barmode"] = "overlay"
            lay_f["xaxis"]["range"] = [0, 115]
            lay_f["xaxis"]["showgrid"] = False
            lay_f["yaxis"]["tickfont"] = dict(size=11, color="#374151", family="Inter")
            fig_f.update_layout(**lay_f)
            st.plotly_chart(fig_f, use_container_width=True, config={"displayModeBar": False})

    st.markdown('</div>', unsafe_allow_html=True)
