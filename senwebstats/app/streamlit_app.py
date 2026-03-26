"""
SenWebStats — Observatory v7 · Masterclass Design
Dark sidebar · Premium KPIs · Treemap · Scatter · Donut · Radar · Violin
"""
import sys, os, io, json, sqlite3, base64
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

import streamlit as st
import streamlit.components.v1 as _stc
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

# ── Senegal map image (base64) ──────────────────────────────────────────────
@st.cache_resource
def _load_img_b64(fname: str) -> str:
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), fname)
    if os.path.exists(p):
        with open(p, "rb") as _f:
            ext = fname.rsplit(".", 1)[-1].lower()
            mime = "image/png" if ext == "png" else "image/jpeg"
            return f"data:{mime};base64,{base64.b64encode(_f.read()).decode()}"
    return ""

_SN_MAP_SRC = _load_img_b64("senegal_map.png")

st.set_page_config(
    page_title="SenWebStats · Observatory",
    page_icon="S",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
# DESIGN SYSTEM — NATIONAL DIGITAL OBSERVATORY (LIGHT THEME)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Inter:wght@300;400;500;600;700&family=Space+Mono:wght@400;700&display=swap');

/* ═══════════════════════════════════════
   DESIGN TOKENS — LIGHT GOLD THEME
═══════════════════════════════════════ */
:root {
  --bg:         #FFFFFF;
  --card:       #FFFFFF;
  --sidebar-bg: #FDFAF4;
  --text:       #1A1A2E;
  --text-sub:   #6B7280;
  --gold:       #C9A84C;
  --gold-dark:  #8B6914;
  --gold-light: #F0D080;
  --gold-glow:  rgba(201,168,76,0.35);
  --border:     rgba(0,0,0,0.08);
  --shadow-sm:  0 2px 12px rgba(0,0,0,0.06);
  --shadow-md:  0 4px 20px rgba(0,0,0,0.08);
  --shadow-lg:  0 8px 32px rgba(0,0,0,0.12);
  --green:      #16A34A;
  --red:        #DC2626;
  /* Legacy aliases for page content */
  --txt:        #1A1A2E;
  --txt-2:      #374151;
  --txt-3:      #6B7280;
  --blue:       #C9A84C;
  --emerald:    #16A34A;
  --amber:      #D97706;
  --grad-bp:    linear-gradient(135deg,#C9A84C 0%,#F0D080 100%);
  --grad-surface: linear-gradient(145deg,#FFFFFF 0%,#FAFAFA 50%,#FFFFFF 100%);
}

/* ═══════════════════════════════════════
   KEYFRAMES
═══════════════════════════════════════ */
@keyframes fadeInUp {
  from { opacity:0; transform:translateY(24px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes fadeInLeft {
  from { opacity:0; transform:translateX(-20px); }
  to   { opacity:1; transform:translateX(0); }
}
@keyframes pulse-glow {
  0%,100% { box-shadow:0 0 0 0 rgba(201,168,76,0); }
  50%     { box-shadow:0 0 20px 6px rgba(201,168,76,0.35); }
}
@keyframes node-ping {
  0%  { transform:scale(1);   opacity:1; }
  70% { transform:scale(2.5); opacity:0; }
  100%{ transform:scale(1);   opacity:0; }
}
@keyframes bar-grow {
  from { width:0%; }
  to   { width:var(--target-w,100%); }
}
@keyframes float-btn {
  0%,100% { transform:translateY(0); }
  50%     { transform:translateY(-6px); }
}
@keyframes fade-up {
  from { opacity:0; transform:translateY(16px); }
  to   { opacity:1; transform:translateY(0); }
}
@keyframes pulse-dot {
  0%,100% { opacity:1; transform:scale(1); }
  50%     { opacity:.3; transform:scale(.6); }
}
@keyframes gold-rush {
  0%   { transform:translateX(-120%) skewX(-18deg); opacity:0; }
  25%  { opacity:1; }
  100% { transform:translateX(280%) skewX(-18deg); opacity:0; }
}
@keyframes gold-particles {
  0%   { opacity:0; transform:translateY(0) scale(0); }
  30%  { opacity:1; }
  100% { opacity:0; transform:translateY(-18px) scale(1.6); }
}
@keyframes skeleton-shimmer {
  0%   { background-position: -400px 0; }
  100% { background-position: 400px 0; }
}
.skeleton {
  background: linear-gradient(90deg,#f0f0f0 25%,#e8e0d0 50%,#f0f0f0 75%);
  background-size: 400px 100%;
  animation: skeleton-shimmer 1.4s ease infinite;
  border-radius: 8px;
}

/* ═══════════════════════════════════════
   GLOBAL RESET + BACKGROUND
═══════════════════════════════════════ */
#MainMenu,footer,header,
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display:none !important; }

html,body {
  background: var(--bg) !important;
}
[data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  font-family:'Inter',sans-serif !important;
  color:var(--text) !important;
}
.block-container { padding:0 !important; max-width:100% !important; }

/* ═══════════════════════════════════════
   SIDEBAR — GOLD MAJESTIC PANEL
═══════════════════════════════════════ */
[data-testid="stSidebar"] {
  background: linear-gradient(160deg,#C9A84C 0%,#DFB84A 55%,#F0D080 100%) !important;
  border-right: 1px solid rgba(61,43,0,0.18) !important;
  box-shadow: 4px 0 32px rgba(139,105,20,0.25) !important;
  animation: fadeInLeft 0.4s ease both;
}
[data-testid="stSidebarContent"] { padding:0 !important; }

/* Brand block */
.brand-block {
  display:flex; align-items:center; gap:.75rem;
  padding:1.5rem 1.25rem 1.25rem;
  border-bottom:1px solid rgba(61,43,0,0.12);
  margin-bottom:.75rem;
}
.brand-icon {
  width:42px; height:42px; background:#3D2B00;
  border-radius:8px; display:flex; align-items:center;
  justify-content:center; color:#F0D080; font-weight:900;
  font-size:1.1rem; flex-shrink:0;
  box-shadow:0 4px 12px rgba(61,43,0,0.3);
}
.brand-name { font-weight:700; font-size:.95rem; color:#3D2B00; font-family:'Inter',sans-serif; }
.brand-sub  { font-size:.55rem; letter-spacing:.15em; color:rgba(61,43,0,0.6);
              text-transform:uppercase; font-family:'Inter',sans-serif; }

/* Nav section label */
.sb-section {
  font-family:'Inter',sans-serif; font-size:.5rem; font-weight:700;
  color:rgba(61,43,0,0.45); letter-spacing:.22em; text-transform:uppercase;
  padding:.5rem 1.25rem .3rem;
}

/* Active nav item (HTML div, not button) */
.nav-item {
  display:flex; align-items:center; gap:.75rem;
  padding:.7rem 1.25rem; font-size:.7rem; font-weight:600;
  letter-spacing:.1em; color:rgba(61,43,0,0.65);
  text-transform:uppercase; font-family:'Inter',sans-serif;
  border-left:3px solid transparent;
}
.nav-item.active {
  background:rgba(61,43,0,0.15);
  color:#3D2B00;
  border-left-color:#3D2B00;
  font-weight:700;
}
.nav-icon { display:none; }

/* Nav buttons (inactive) */
[data-testid="stSidebar"] .stButton > button {
  background:transparent !important;
  color:rgba(61,43,0,0.65) !important;
  border:none !important; border-radius:4px !important;
  border-left:3px solid transparent !important;
  text-align:left !important; justify-content:flex-start !important;
  padding:.75rem 1.25rem !important; margin:0 2px !important;
  font-size:.68rem !important; font-weight:600 !important;
  font-family:'Inter',sans-serif !important; letter-spacing:.12em !important;
  text-transform:uppercase !important;
  width:calc(100% - 4px) !important; transition:all .25s ease !important;
  box-shadow:none !important; min-height:0 !important;
  overflow:hidden !important; position:relative !important;
}
[data-testid="stSidebar"] .stButton > button::after {
  content:'' !important;
  position:absolute !important; top:0 !important; left:0 !important;
  width:45% !important; height:100% !important;
  background:linear-gradient(90deg,
    transparent 0%,
    rgba(255,248,200,0.55) 35%,
    rgba(240,208,128,0.85) 50%,
    rgba(255,248,200,0.55) 65%,
    transparent 100%) !important;
  transform:translateX(-120%) skewX(-18deg) !important;
  pointer-events:none !important;
}
[data-testid="stSidebar"] .stButton > button:hover::after {
  animation:gold-rush .65s ease forwards !important;
}
[data-testid="stSidebar"] .stButton > button:hover {
  background:rgba(255,255,255,0.28) !important;
  color:#3D2B00 !important;
  border-left-color:rgba(61,43,0,0.5) !important;
  transform:none !important;
  box-shadow:0 2px 12px rgba(61,43,0,0.12) !important;
}
[data-testid="stSidebar"] .stButton > button:active {
  transform:scale(0.97) !important;
  background:rgba(255,255,255,0.45) !important;
  box-shadow:0 0 18px rgba(240,208,128,0.5) !important;
}
[data-testid="stSidebar"] .stButton > button:focus { box-shadow:none !important; }

/* CTA / export wraps adapted to gold sidebar */
.nav-cta-wrap .stButton > button {
  background:rgba(61,43,0,0.18) !important;
  color:#3D2B00 !important;
  border:1.5px solid rgba(61,43,0,0.25) !important;
  border-radius:10px !important; font-weight:700 !important;
  box-shadow:none !important;
  letter-spacing:.06em !important;
}
.nav-cta-wrap .stButton > button:hover {
  background:rgba(61,43,0,0.28) !important;
  border-color:rgba(61,43,0,0.4) !important;
  transform:none !important;
  box-shadow:none !important;
}
.nav-export-wrap .stButton > button {
  background:rgba(255,255,255,0.22) !important;
  color:#3D2B00 !important;
  border:1.5px solid rgba(61,43,0,0.18) !important;
  border-radius:10px !important; font-weight:600 !important;
  box-shadow:none !important;
}
.nav-export-wrap .stButton > button:hover {
  background:rgba(255,255,255,0.35) !important;
  border-color:rgba(61,43,0,0.3) !important;
  transform:none !important;
}

/* Sidebar divider */
.sb-div {
  height:1px; margin:.75rem 1.25rem;
  background:linear-gradient(90deg,transparent,rgba(61,43,0,0.2),transparent);
}

/* Status badge */
.sb-status {
  display:inline-flex; align-items:center; gap:7px;
  padding:5px 12px 5px 10px;
  background:rgba(255,255,255,0.3);
  border:1px solid rgba(61,43,0,0.2);
  border-radius:20px;
  font-family:'Inter',sans-serif; font-size:.5625rem;
  font-weight:700; color:#3D2B00; letter-spacing:.07em; text-transform:uppercase;
}
.sb-dot {
  width:7px; height:7px; border-radius:50%; flex-shrink:0;
  background:#3D2B00;
  animation:pulse-dot 2.2s ease infinite;
}

/* Sidebar selectbox */
[data-testid="stSidebar"] [data-baseweb="select"] > div {
  background:rgba(249,244,232,0.9) !important;
  border:1px solid rgba(201,168,76,.2) !important;
  border-radius:10px !important;
  color:var(--text) !important; font-size:.8125rem !important;
}

/* ═══════════════════════════════════════
   MAIN CONTENT
═══════════════════════════════════════ */
.mwrap { padding:2.5rem 2.5rem 6rem; background:transparent; }

/* ── ANIMATIONS ── */
.anim-0 { animation:fadeInUp .5s ease .1s both; }
.anim-1 { animation:fadeInUp .5s ease .2s both; }
.anim-2 { animation:fadeInUp .5s ease .3s both; }
.anim-3 { animation:fadeInUp .5s ease .4s both; }
.anim-4 { animation:fadeInUp .5s ease .5s both; }

/* ── PAGE HEADER ── */
.ph-wrap { margin-bottom:2rem; animation:fadeInUp .55s ease both; }
.ph-eyebrow {
  font-family:'Inter',sans-serif; font-size:.65rem; font-weight:700;
  color:var(--gold); letter-spacing:.18em; text-transform:uppercase;
  margin-bottom:.6rem; display:flex; align-items:center; gap:8px;
}
.ph-dot {
  width:6px; height:6px; border-radius:50%; background:var(--gold);
  display:inline-block; animation:pulse-dot 2.4s ease infinite;
  box-shadow:0 0 6px 2px rgba(201,168,76,0.5);
  flex-shrink:0;
}
.ph-title {
  font-family:'Playfair Display',serif; font-size:2.25rem; font-weight:700;
  color:var(--text); line-height:1.1; letter-spacing:-.02em; margin:0 0 .6rem;
}
.ph-title .acc { color:var(--gold); }
.ph-sub {
  font-family:'Inter',sans-serif; font-size:.9375rem;
  color:var(--text-sub); margin:0; line-height:1.65; font-weight:400;
}

/* ── KPI CARDS ── */
.kpi-wrap {
  background: var(--card);
  border-radius:16px;
  padding:1.5rem;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  position:relative; overflow:hidden;
  transition:all .3s cubic-bezier(.34,1.56,.64,1);
}
.kpi-wrap::before {
  content:''; position:absolute; top:0; left:0; right:0; height:3px;
  background:var(--kpi-c,var(--gold)); border-radius:16px 16px 0 0;
}
.kpi-wrap::after {
  content:''; position:absolute;
  top:0; left:-100%; bottom:0; width:60%;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.4),transparent);
  transition:left .5s ease; pointer-events:none;
}
.kpi-wrap:hover {
  transform:translateY(-4px) scale(1.02);
  box-shadow:0 16px 40px rgba(201,168,76,.18);
  border-color:rgba(201,168,76,.3);
}
.kpi-wrap:hover::after { left:150%; }
.kpi-label {
  font-family:'Inter',sans-serif; font-size:.58rem; font-weight:700;
  color:var(--text-sub); letter-spacing:.15em; text-transform:uppercase; margin-bottom:.75rem;
}
.kpi-value {
  font-family:'Playfair Display',serif; font-size:2.4rem; font-weight:700;
  color:var(--text); line-height:1; letter-spacing:-.02em; margin-bottom:.3rem;
}
.kpi-sub {
  font-family:'Inter',sans-serif; font-size:.78rem;
  color:var(--text-sub); font-style:italic; margin-bottom:.9rem; line-height:1.4;
}
.kpi-badge {
  display:inline-flex; align-items:center; gap:4px;
  padding:.2rem .6rem; border-radius:20px;
  font-family:'Inter',sans-serif; font-size:.6rem; font-weight:700;
  letter-spacing:.05em; text-transform:uppercase;
}
.badge-up   { background:#DCFCE7; color:#16A34A; }
.badge-down { background:#FEE2E2; color:#DC2626; }
.badge-flat { background:#F3F4F6; color:#6B7280; }
.kpi-track { height:3px; background:rgba(0,0,0,.05); border-radius:2px; overflow:hidden; margin-top:.9rem; }
.kpi-fill  { height:100%; border-radius:2px;
             background:linear-gradient(90deg,var(--kpi-c,var(--gold)),var(--gold-light));
             animation:bar-grow 1.2s ease forwards; }

/* ── SECTION LABEL ── */
.sec {
  font-family:'Inter',sans-serif; font-size:.58rem; font-weight:700;
  color:var(--text-sub); letter-spacing:.16em; text-transform:uppercase;
  margin:2rem 0 1rem; display:flex; align-items:center; gap:12px;
}
.sec::before {
  content:''; width:3px; height:16px; background:var(--gold);
  border-radius:2px; flex-shrink:0;
}
.sec::after {
  content:''; flex:1; height:1px;
  background:linear-gradient(90deg,rgba(201,168,76,.3),transparent);
}

/* ── CARDS ── */
.crd {
  background:var(--card); border-radius:16px; overflow:hidden;
  box-shadow:var(--shadow-sm);
  border:1px solid var(--border);
}
.crd-hd {
  padding:12px 20px;
  background:linear-gradient(135deg,rgba(201,168,76,.06),rgba(249,244,232,.7));
  font-family:'Inter',sans-serif; font-size:.58rem; font-weight:700;
  color:var(--text-sub); letter-spacing:.12em; text-transform:uppercase;
  display:flex; justify-content:space-between;
  border-bottom:1px solid rgba(201,168,76,.1);
}

/* ── RANK ROW ── */
.rrow {
  display:grid; grid-template-columns:2rem 1fr auto auto;
  align-items:center; padding:10px 20px; gap:12px; transition:all .13s;
}
.rrow:hover {
  background:rgba(201,168,76,.04);
  box-shadow:inset 3px 0 0 rgba(201,168,76,.3);
}
.rn   { font-family:'Space Mono',monospace; font-size:.75rem; color:rgba(201,168,76,.5); text-align:right; font-weight:700; }
.rname{ font-size:.875rem; font-weight:600; color:var(--text); font-family:'Inter',sans-serif; }
.rcat { font-size:.6875rem; color:var(--text-sub); margin-top:2px; font-family:'Inter',sans-serif; }
.rbar-w { height:3px; border-radius:2px; background:rgba(0,0,0,.06); margin-top:5px; overflow:hidden; }
.rbar   { height:100%; border-radius:2px; }
.rscr { font-family:'Space Mono',monospace; font-size:.9375rem; font-weight:700; text-align:right; }
.rtrf { font-family:'Space Mono',monospace; font-size:.72rem; color:var(--gold-dark); text-align:right; white-space:nowrap; font-weight:700; }

/* ── INFO BOX ── */
.ibox {
  background:rgba(201,168,76,.06);
  color:var(--gold-dark); border-radius:12px; padding:16px 20px; font-size:.875rem;
  margin:1rem 0; border:1px solid rgba(201,168,76,.2);
  font-family:'Inter',sans-serif;
}

/* ── STATUS PILLS ── */
.pills { display:flex; gap:.5rem; flex-wrap:wrap; margin-bottom:1.5rem; }
.pill  {
  display:inline-flex; align-items:center; gap:.4rem;
  padding:.3rem .85rem; border-radius:20px;
  font-size:.625rem; font-weight:600; font-family:'Inter',sans-serif;
}
.pill-ok   { background:rgba(22,163,74,.09);  color:#16A34A; border:1px solid rgba(22,163,74,.22); }
.pill-warn { background:rgba(217,119,6,.09);  color:#b45309; border:1px solid rgba(217,119,6,.22); }
.pill-gray { background:rgba(107,114,128,.07);color:var(--text-sub); border:1px solid var(--border); }

/* ── DARK CARD ── */
.dark-crd {
  background:linear-gradient(135deg,#1A1A2E 0%,#2D2B45 60%,#1A1A2E 100%);
  border-radius:16px; padding:24px; color:#fff;
  box-shadow:0 8px 40px rgba(201,168,76,.2);
  border:1px solid rgba(201,168,76,.2);
}

/* ── CHART CARD ── */
.chart-card {
  background:var(--card); border-radius:14px;
  padding:1.5rem 1.5rem .5rem; box-shadow:var(--shadow-sm);
  border:1px solid rgba(0,0,0,.07);
  overflow:hidden; margin-bottom:1rem;
  transition:box-shadow .3s ease;
}
.chart-card:hover { box-shadow:0 8px 32px rgba(201,168,76,.12); }

/* ── GAUGE ── */
.gauge-lbl {
  font-family:'Playfair Display',serif; font-size:1.5rem; font-weight:700;
  color:var(--text); text-align:center; line-height:1; margin-bottom:2px;
}
.gauge-sub { font-family:'Inter',sans-serif; font-size:.6875rem; color:var(--text-sub); text-align:center; }

/* ── INPUTS ── */
[data-testid="stMultiSelect"] > div {
  background:var(--card) !important;
  border:1px solid rgba(201,168,76,.18) !important; border-radius:10px !important;
}
[data-testid="stMultiSelect"] span {
  background:rgba(201,168,76,.12) !important; color:var(--gold-dark) !important;
  border:none !important; border-radius:6px !important;
  font-size:.6875rem !important; font-weight:500 !important;
}
[data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
  background:var(--gold) !important;
}
[data-testid="stDataFrame"] { border-radius:14px !important; overflow:hidden !important; }
[data-testid="stDataFrame"] th {
  background:rgba(201,168,76,.06) !important; color:var(--text-sub) !important;
  font-size:.6875rem !important; letter-spacing:.08em !important;
  text-transform:uppercase !important; font-weight:600 !important;
  font-family:'Inter',sans-serif !important;
}
[data-testid="stDataFrame"] td {
  color:var(--text) !important; font-size:.875rem !important;
  background:var(--card) !important;
}

/* ── GLOBAL BUTTONS ── */
.stButton > button {
  background:linear-gradient(135deg,var(--gold),var(--gold-light)) !important;
  color:#fff !important;
  border:none !important; border-radius:10px !important;
  font-weight:600 !important; font-size:.875rem !important;
  padding:10px 20px !important; transition:all .18s !important;
  box-shadow:0 4px 14px rgba(201,168,76,.25) !important;
  font-family:'Inter',sans-serif !important;
}
.stButton > button:hover {
  transform:translateY(-1px) !important;
  box-shadow:0 6px 20px rgba(201,168,76,.35) !important;
}
[data-testid="stDownloadButton"] > button {
  background:linear-gradient(135deg,#C9A84C,#F0D080) !important;
  color:#3D2B00 !important; border:none !important;
  border-radius:10px !important; font-weight:700 !important;
  box-shadow:0 4px 16px rgba(201,168,76,0.35) !important;
  letter-spacing:.06em !important;
}
[data-testid="stDownloadButton"] > button:hover {
  background:linear-gradient(135deg,#8B6914,#C9A84C) !important;
  color:#fff !important;
  box-shadow:0 6px 22px rgba(201,168,76,0.45) !important;
  transform:translateY(-1px) !important;
}

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width:4px; height:4px; }
::-webkit-scrollbar-track { background:var(--bg); }
::-webkit-scrollbar-thumb { background:rgba(201,168,76,.3); border-radius:3px; }
::-webkit-scrollbar-thumb:hover { background:rgba(201,168,76,.5); }

/* ══════════════════════════════════════════════════════════
   PREMIUM DATA TABLE
══════════════════════════════════════════════════════════ */
.ptbl-outer {
  background: var(--card);
  border-radius: 16px; overflow: hidden;
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border);
  margin-bottom: 1.5rem; overflow-x: auto;
  animation: fadeInUp .5s ease both;
}
.ptbl-outer table { width:100%; border-collapse:collapse; font-family:'Inter',sans-serif; }
.ptbl-outer thead { position:sticky; top:0; z-index:2; }
.ptbl-outer thead tr {
  background:linear-gradient(135deg,rgba(201,168,76,.06),rgba(249,244,232,.7));
  border-bottom:1.5px solid rgba(201,168,76,.12);
}
.ptbl-outer th {
  padding:14px 18px; font-size:.5625rem; font-weight:700;
  letter-spacing:.14em; text-transform:uppercase; color:var(--text-sub);
  text-align:left; white-space:nowrap; font-family:'Inter',sans-serif;
}
.ptbl-outer td {
  padding:12px 18px; font-size:.8125rem; color:var(--text);
  border-bottom:1px solid rgba(0,0,0,.04);
  font-family:'Inter',sans-serif; white-space:nowrap;
}
.ptbl-outer tbody tr { transition:all .13s ease; }
.ptbl-outer tbody tr:hover td {
  background:rgba(201,168,76,.04);
  box-shadow:inset 3px 0 0 rgba(201,168,76,.3);
}
.ptbl-outer tbody tr:last-child td { border-bottom:none; }
.ptbl-outer .td-num {
  font-family:'Space Mono',monospace; font-weight:700;
  color:var(--text); font-variant-numeric:tabular-nums;
}
.ptbl-outer .td-score {
  font-family:'Space Mono',monospace; font-weight:700; font-size:.875rem;
}
.ptbl-outer .td-chip {
  display:inline-flex; align-items:center;
  padding:3px 10px; border-radius:20px;
  font-size:.5625rem; font-weight:700; letter-spacing:.06em; white-space:nowrap;
}
.ptbl-outer .chip-blue   { background:rgba(201,168,76,.12); color:var(--gold-dark); }
.ptbl-outer .chip-green  { background:rgba(22,163,74,.10);  color:#16A34A; }
.ptbl-outer .chip-purple { background:rgba(201,168,76,.10); color:var(--gold-dark); }
.ptbl-outer .chip-amber  { background:rgba(217,119,6,.10);  color:#b45309; }
.ptbl-outer .chip-red    { background:rgba(220,38,38,.10);  color:#DC2626; }
.ptbl-outer .chip-gray   { background:rgba(107,114,128,.07);color:var(--text-sub); }
.ptbl-outer .td-bar-wrap { display:flex; align-items:center; gap:8px; min-width:90px; }
.ptbl-outer .td-bar-bg   { flex:1; height:3px; background:rgba(0,0,0,.06); border-radius:3px; overflow:hidden; }
.ptbl-outer .td-bar-fill { height:100%; border-radius:3px; }

/* ══════════════════════════════════════════════════════════
   SENEGAL MAP CARD
══════════════════════════════════════════════════════════ */
.senegal-map-card {
  background:#F9F4E8; border:1px solid rgba(201,168,76,.2);
  border-radius:16px; padding:1.75rem;
  animation:fadeInUp .8s ease .2s both;
  transition:box-shadow .3s ease;
  margin-bottom:1.5rem;
}
.senegal-map-card:hover { box-shadow:0 12px 40px rgba(201,168,76,.15); }
.map-card-label {
  font-family:'Inter',sans-serif; font-size:.6rem; font-weight:700;
  letter-spacing:.18em; text-transform:uppercase; color:var(--gold);
  margin-bottom:.75rem;
}
.map-stat-label {
  font-size:.6rem; font-weight:600; letter-spacing:.15em;
  text-transform:uppercase; color:var(--text-sub); font-family:'Inter',sans-serif;
}
.map-stat-value {
  font-family:'Space Mono',monospace;
  font-size:1.2rem; font-weight:700; color:var(--text); margin-top:.2rem;
}
.connectivity-badge {
  display:inline-flex; align-items:center; gap:.4rem;
  background:rgba(22,163,74,.1); color:#16A34A;
  border:1px solid rgba(22,163,74,.25); border-radius:20px;
  padding:.3rem .9rem; font-size:.65rem; font-weight:600;
  letter-spacing:.1em; margin-top:1rem; font-family:'Inter',sans-serif;
}

/* ══════════════════════════════════════════════════════════
   FLOATING ACTION BUTTONS
══════════════════════════════════════════════════════════ */
.fab-wrap {
  position:fixed; bottom:2rem; right:2rem;
  display:flex; flex-direction:column; gap:.75rem; z-index:9999;
}
.fab {
  width:56px; height:56px; border-radius:14px;
  display:flex; align-items:center; justify-content:center;
  font-size:1.4rem; cursor:pointer;
  transition:all .3s cubic-bezier(.34,1.56,.64,1);
  box-shadow:0 4px 16px rgba(0,0,0,.15);
  position:relative;
}
.fab-ia {
  background:linear-gradient(135deg,var(--gold),var(--gold-light));
  color:white;
  animation:float-btn 3s ease-in-out infinite, pulse-glow 3s ease-in-out infinite;
}
.fab-data { background:#3D3215; color:var(--gold); animation:float-btn 3s ease-in-out 1.5s infinite; }
.fab:hover { transform:scale(1.15) translateY(-3px); box-shadow:0 8px 24px rgba(201,168,76,.4); }
.fab::before {
  content:attr(data-tooltip); position:absolute; right:70px;
  background:#1A1A2E; color:white;
  padding:.3rem .75rem; border-radius:6px;
  font-size:.75rem; font-family:'Inter',sans-serif;
  white-space:nowrap; opacity:0; pointer-events:none;
  transition:opacity .2s;
}
.fab:hover::before { opacity:1; }

/* ══════════════════════════════════════════════════════════
   SITE FOOTER — DARK GOLD MAJESTIC
══════════════════════════════════════════════════════════ */
.site-footer {
  background: linear-gradient(135deg,#1A1200 0%,#2D2000 40%,#3D3215 70%,#1A1200 100%);
  border-top: 2px solid #C9A84C;
  padding: 2.5rem 3rem;
  margin-top: 3rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  overflow: hidden;
  animation: fadeInUp .5s ease .6s both;
}
.site-footer::before {
  content:'';
  position:absolute; top:0; left:0; right:0; height:2px;
  background: linear-gradient(90deg,transparent 0%,#F0D080 30%,#C9A84C 50%,#F0D080 70%,transparent 100%);
}
.site-footer::after {
  content:'';
  position:absolute; bottom:0; right:0;
  width:280px; height:280px;
  background: radial-gradient(circle,rgba(201,168,76,0.08) 0%,transparent 70%);
  pointer-events:none;
}
.footer-brand {
  font-family:'Playfair Display',serif;
  font-size:1.15rem; font-weight:700;
  color:#F0D080;
  letter-spacing:.02em;
}
.footer-tagline {
  font-family:'Inter',sans-serif;
  font-size:.6rem; font-weight:500;
  color:rgba(240,208,128,0.45);
  letter-spacing:.2em; text-transform:uppercase;
  margin-top:.35rem;
}
.footer-copy {
  font-size:.7rem;
  color:rgba(240,208,128,0.4);
  margin-top:.25rem;
  font-family:'Inter',sans-serif;
}
.footer-divider {
  width:1px; height:40px;
  background:linear-gradient(180deg,transparent,rgba(201,168,76,0.3),transparent);
}
.footer-links {
  font-size:.75rem;
  color:rgba(240,208,128,0.55);
  display:flex; gap:1.25rem; align-items:center;
  font-family:'Inter',sans-serif;
}
.footer-links a {
  color:rgba(240,208,128,0.55);
  text-decoration:none;
  letter-spacing:.04em;
  transition:color .2s;
}
.footer-links a:hover { color:#F0D080; }
.footer-links .sep { color:rgba(201,168,76,0.25); }
.footer-badge {
  font-family:'Space Mono',monospace;
  font-size:.55rem; letter-spacing:.18em;
  color:rgba(201,168,76,0.4);
  text-transform:uppercase;
  border:1px solid rgba(201,168,76,0.15);
  border-radius:4px; padding:.25rem .6rem;
  margin-top:.5rem; display:inline-block;
}

/* ══════════════════════════════════════════════════════════
   SENEGAL MAP CARD
══════════════════════════════════════════════════════════ */
.map-card {
  background:var(--card); border-radius:18px;
  border:1px solid rgba(201,168,76,.18);
  padding:1.5rem 1.25rem 1.25rem;
  box-shadow:0 6px 32px rgba(201,168,76,.1);
  animation:fadeInLeft .6s ease both;
  transition:box-shadow .3s ease;
}
.map-card--hero {
  padding:1.75rem 1.5rem 1.5rem;
  box-shadow:0 8px 40px rgba(201,168,76,.14),0 2px 0 rgba(201,168,76,.25) inset;
  border:1.5px solid rgba(201,168,76,.22);
}
.map-card--hero:hover { box-shadow:0 14px 50px rgba(201,168,76,.22); }
.map-title {
  font-family:'Playfair Display',serif; font-size:.9rem; font-weight:700;
  color:var(--gold-dark); letter-spacing:.04em; margin-bottom:.75rem;
}
.sn-map { width:100%; display:block; }
.map-ping {
  animation:node-ping 2.4s ease-in-out infinite;
  transform-origin:center;
}
.map-legend {
  display:flex; align-items:center; gap:.5rem; justify-content:center;
  font-family:Inter,sans-serif; font-size:.65rem; color:var(--text-sub);
  margin-top:.75rem; letter-spacing:.04em;
}
.map-dot {
  width:7px; height:7px; border-radius:50%;
  background:var(--gold); display:inline-block;
  animation:pulse-glow 2s ease-in-out infinite;
}

/* ══════════════════════════════════════════════════════════
   RESPONSIVE
══════════════════════════════════════════════════════════ */
@media (max-width: 1200px) {
  .kpi-wrap { padding:.9rem 1rem; }
  .kpi-value { font-size:1.5rem; }
  .ph-title { font-size:1.6rem; }
}
@media (max-width: 900px) {
  .mwrap { padding:1.25rem 1rem; }
  .ph-title { font-size:1.3rem; }
  .site-footer { flex-direction:column; gap:1.5rem; text-align:center; }
  .footer-divider { display:none; }
}

/* ══════════════════════════════════════════════════════════
   METHODOLOGY CARD
══════════════════════════════════════════════════════════ */
@keyframes shimmer-bar {
  0%   { background-position:-200% 0; }
  100% { background-position: 200% 0; }
}
@keyframes mp-bar-in {
  from { width:0%; opacity:0; }
  to   { opacity:1; }
}
.methodo-card {
  border-radius:20px;
  background:linear-gradient(135deg,#1A1200 0%,#2D2000 45%,#3D3215 75%,#1A1200 100%);
  overflow:hidden; margin-bottom:2.25rem;
  box-shadow:0 12px 48px rgba(201,168,76,.22),0 2px 0 rgba(201,168,76,.15) inset;
  animation:fadeInUp .55s ease both; position:relative;
}
.methodo-card::after {
  content:''; position:absolute; inset:0;
  background:radial-gradient(ellipse 60% 80% at 80% 50%,rgba(201,168,76,.06) 0%,transparent 70%);
  pointer-events:none;
}
.methodo-shimmer {
  height:3px;
  background:linear-gradient(90deg,transparent 0%,#8B6914 15%,#C9A84C 35%,#F0D080 50%,#C9A84C 65%,#8B6914 85%,transparent 100%);
  background-size:200% 100%;
  animation:shimmer-bar 2.2s linear infinite;
}
.methodo-inner { padding:2rem 2.5rem 2.5rem; }
.methodo-eyebrow {
  font-family:'Inter',sans-serif; font-size:.5rem; font-weight:700;
  letter-spacing:.28em; text-transform:uppercase;
  color:rgba(201,168,76,.55); margin-bottom:.6rem;
}
.methodo-title {
  font-family:'Playfair Display',serif; font-size:1.35rem; font-weight:700;
  color:#F0D080; line-height:1.3; margin-bottom:1.75rem;
}
.methodo-formula {
  background:rgba(255,255,255,.04);
  border:1px solid rgba(201,168,76,.22); border-radius:12px;
  padding:1.1rem 1.5rem; font-family:'Space Mono',monospace;
  font-size:.9rem; font-weight:700; color:rgba(255,255,255,.9);
  letter-spacing:.04em; line-height:1.6;
  margin-bottom:2rem; position:relative; overflow:hidden;
}
.methodo-formula::before {
  content:''; position:absolute; top:0; left:0; right:0; height:1px;
  background:linear-gradient(90deg,transparent,rgba(201,168,76,.4),transparent);
}
.mf-gold { color:#F0D080; }
.mf-op   { color:rgba(255,255,255,.35); }
.methodo-pillars { display:grid; grid-template-columns:1fr 1fr 1fr; gap:1.5rem; margin-bottom:2rem; }
.mp {
  background:rgba(255,255,255,.04); border:1px solid rgba(201,168,76,.12);
  border-radius:14px; padding:1.25rem 1.25rem 1.5rem;
  position:relative; overflow:hidden; transition:border-color .25s,box-shadow .25s;
}
.mp:hover { border-color:rgba(201,168,76,.3); box-shadow:0 4px 24px rgba(201,168,76,.12); }
.mp::before {
  content:''; position:absolute; top:0; left:0; right:0; height:2px;
  background:linear-gradient(90deg,#C9A84C,#F0D080); border-radius:14px 14px 0 0;
}
.mp-pct { font-family:'Space Mono',monospace; font-size:1.8rem; font-weight:700; color:#F0D080; line-height:1; margin-bottom:.5rem; }
.mp-name { font-family:'Playfair Display',serif; font-size:.85rem; font-weight:700; color:#FFFFFF; margin-bottom:.75rem; }
.mp-bar-bg { height:4px; background:rgba(255,255,255,.08); border-radius:3px; overflow:hidden; margin-bottom:.85rem; }
.mp-bar-fill { height:100%; border-radius:3px; background:linear-gradient(90deg,#C9A84C,#F0D080); animation:mp-bar-in 1.2s ease forwards; }
.mp-sub { font-family:'Inter',sans-serif; font-size:.68rem; color:rgba(255,255,255,.55); line-height:1.6; }
.mp-sub strong { color:rgba(240,208,128,.8); font-weight:600; }
.methodo-sources { border-top:1px solid rgba(201,168,76,.12); padding-top:1.25rem; display:flex; flex-wrap:wrap; gap:.5rem; align-items:center; }
.ms-label { font-family:'Inter',sans-serif; font-size:.5rem; font-weight:700; letter-spacing:.2em; text-transform:uppercase; color:rgba(201,168,76,.4); margin-right:.5rem; }
.ms-chip { font-family:'Space Mono',monospace; font-size:.6rem; color:rgba(240,208,128,.6); background:rgba(255,255,255,.04); border:1px solid rgba(201,168,76,.15); border-radius:6px; padding:.2rem .6rem; letter-spacing:.05em; }
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

    bl = q("""SELECT site_id, total_backlinks, backlinks_change
              FROM site_backlinks sb
              WHERE collected_at=(SELECT MAX(collected_at) FROM site_backlinks WHERE site_id=sb.site_id)""")

    # Real authority data: Open PageRank (0-10 scale)
    authority = q("""SELECT site_id, page_rank, global_rank
                     FROM site_authority sa
                     WHERE collected_at=(SELECT MAX(collected_at) FROM site_authority WHERE site_id=sa.site_id)""")

    # Real search interest data: Google Trends (0-100 scale, geo=SN)
    trends = q("""SELECT site_id, trends_score
                  FROM site_trends st
                  WHERE collected_at=(SELECT MAX(collected_at) FROM site_trends WHERE site_id=st.site_id)""")

    df = sites.copy()
    for other in [meta, perf, bl, authority, trends]:
        if not other.empty:
            df = df.merge(other, left_on="id", right_on="site_id", how="left")
            if "site_id" in df.columns:
                df = df.drop(columns=["site_id"])

    # Boolean / counter columns: 0 is semantically correct for "absent"
    zero_fills = {
        "total_backlinks": 0, "backlinks_change": 0,
        "has_ssl": 0, "has_sitemap": 0, "has_robots_txt": 0,
        "word_count": 0, "internal_links_count": 0,
        "external_links_count": 0, "images_count": 0, "status_code": 200,
    }
    for col, val in zero_fills.items():
        if col not in df.columns:
            df[col] = val
        else:
            df[col] = df[col].fillna(val)

    # Ensure columns exist even if tables are empty
    for col in ["page_rank", "global_rank", "trends_score",
                "response_time_ms", "lcp_ms", "fcp_ms", "ttfb_ms", "cls_score",
                "seo_score", "performance_score", "accessibility_score", "best_practices_score"]:
        if col not in df.columns:
            df[col] = float("nan")

    # PageSpeed scores: fill missing values with median of real collected data
    # (never hardcode 50 — use the actual distribution of available measurements)
    for col in ["seo_score", "performance_score", "accessibility_score", "best_practices_score"]:
        real_median = df[col].median()
        df[col] = df[col].fillna(real_median if pd.notna(real_median) else 0.0)

    # response_time_ms: fill missing with median of real measurements
    rt_median = df["response_time_ms"].median()
    df["response_time_ms"] = df["response_time_ms"].fillna(rt_median if pd.notna(rt_median) else 3000.0)

    # score_autorite: Open PageRank (60%) + CommonCrawl indexed pages proxy (40%)
    # OPR is 0-10 → normalize to 0-100; CC pages already normalized
    df["page_rank"] = df["page_rank"].fillna(0.0)
    df["score_autorite"] = (_normalize(df["page_rank"]) * 0.60 +
                             _normalize(df["total_backlinks"]) * 0.40).round(1)

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

    # trends_score: Google Trends interest (0-100, geo=SN) used to modulate traffic estimate
    # Factor: 0.5 + trends/100 → range [0.5, 1.5] (no trends data → factor=1.0)
    trends_median = df["trends_score"].median()
    df["trends_score"] = df["trends_score"].fillna(trends_median if pd.notna(trends_median) else 50.0)
    trends_factor = 0.5 + df["trends_score"] / 100.0

    if _CTR_OK:
        try:
            df = compute_ctr_scores(df)
            df["trafic_estime"] = (df["trafic_ctr"] * trends_factor).astype(int)
        except Exception:
            base = df.apply(
                lambda r: int(CATEGORY_BASE.get(r["category"], 50000) * (r["score_global"] / 100) ** 1.5), axis=1)
            df["trafic_estime"] = (base * trends_factor).astype(int)
            df["trafic_ctr"] = df["trafic_estime"]
            df["position_estimee"] = 10
    else:
        base = df.apply(
            lambda r: int(CATEGORY_BASE.get(r["category"], 50000) * (r["score_global"] / 100) ** 1.5), axis=1)
        df["trafic_estime"] = (base * trends_factor).astype(int)
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

_HOVER = dict(bgcolor="rgba(255,255,255,0.97)", bordercolor="rgba(0,0,0,0.08)",
              font=dict(family="Inter", size=12, color="#1A1A2E"))
_GX = dict(showgrid=True, gridcolor="rgba(0,0,0,0.04)", gridwidth=1,
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
        plot_bgcolor="rgba(255,255,255,0.5)",
        height=height,
        font=dict(family="Inter, sans-serif", color="#1A1A2E", size=11),
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
            font=dict(family="Playfair Display, serif", size=14, color="#1A1A2E"),
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
      <div class="kpi-track"><div class="kpi-fill" style="--target-w:{bar_pct}%"></div></div>
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


def render_sector_pills():
    """Pills de filtre secteur — affichees en haut de chaque page."""
    cats_df  = q("SELECT DISTINCT category FROM sites ORDER BY category")
    cat_opts = ["Tous"] + (list(cats_df["category"].values) if not cats_df.empty else [])
    label_map = {**{"Tous": "Tous secteurs"}, **CATEGORY_LABELS}
    if "cat_filter" not in st.session_state:
        st.session_state.cat_filter = "Tous"
    cols = st.columns(len(cat_opts), gap="small")
    for i, (col, opt) in enumerate(zip(cols, cat_opts)):
        is_active = st.session_state.cat_filter == opt
        with col:
            if is_active:
                st.markdown(
                    f'<div style="background:linear-gradient(135deg,#C9A84C,#F0D080);'
                    f'color:#3D2B00;border-radius:20px;padding:.3rem .8rem;'
                    f'font-family:Inter,sans-serif;font-size:.6rem;font-weight:700;'
                    f'letter-spacing:.08em;text-transform:uppercase;text-align:center;'
                    f'cursor:default;">{label_map.get(opt, opt)}</div>',
                    unsafe_allow_html=True
                )
            else:
                if st.button(label_map.get(opt, opt), key=f"pill_{opt}_{i}"):
                    st.session_state.cat_filter = opt
                    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# CHARGEMENT GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=60)
def _load_counts():
    return (
        sv("SELECT COUNT(*) as n FROM sites"),
        sv("SELECT COUNT(DISTINCT site_id) as n FROM site_metadata"),
        sv("SELECT COUNT(DISTINCT site_id) as n FROM site_performance"),
        sv("SELECT COUNT(DISTINCT site_id) as n FROM site_backlinks"),
    )

with st.spinner(""):
    df_all = compute_scores()
n_sites, n_crawled, n_perf, n_bl = _load_counts()
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

# ── Garde-fou DB absente ───────────────────────────────────────────────────────
if get_conn() is None:
    st.markdown("""
    <div style="min-height:80vh;display:flex;align-items:center;justify-content:center;
                font-family:'Inter',sans-serif">
      <div style="text-align:center;max-width:480px;padding:3rem">
        <div style="font-family:'Playfair Display',serif;font-size:2.5rem;font-weight:700;
                    color:#C9A84C;margin-bottom:1rem">SenWebStats</div>
        <div style="font-size:1rem;font-weight:600;color:#1A1A2E;margin-bottom:.75rem">
          Base de données introuvable
        </div>
        <div style="font-size:.85rem;color:#6B7280;line-height:1.7;margin-bottom:2rem">
          Le fichier <code style="background:#F3F4F6;padding:.15rem .4rem;border-radius:4px">senwebstats.db</code>
          est absent. Place-le dans <code style="background:#F3F4F6;padding:.15rem .4rem;border-radius:4px">senwebstats/data/</code>
          puis relance l'application.
        </div>
        <div style="font-family:'Space Mono',monospace;font-size:.7rem;
                    background:#1A1A2E;color:#C9A84C;padding:1rem 1.25rem;
                    border-radius:10px;text-align:left;line-height:2">
          cd senwebstats<br>
          python scripts/crawl.py<br>
          streamlit run app/streamlit_app.py
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

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
NAV_ICONS = {
    "dashboard": "◈",
    "scoring":   "▸",
    "meta":      "◉",
    "perf":      "⚡",
    "backlinks": "⊕",
    "compare":   "⊞",
    "veille":    "◎",
    "export":    "↑",
}


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR — GOLD LIGHT THEME
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    # ── BRAND ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="brand-block">
      <div class="brand-icon">S</div>
      <div>
        <div class="brand-name">SenWebStats</div>
        <div class="brand-sub">Institutional Data</div>
      </div>
    </div>
    <div class="sb-status" style="margin:.25rem 1.25rem .5rem">
      <span class="sb-dot"></span>
      Live · {n_sites} sites
    </div>
    """, unsafe_allow_html=True)
    st.markdown('<div style="padding:.25rem 1rem .5rem">', unsafe_allow_html=True)
    if st.button("Actualiser les données", key="btn_refresh", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="sb-div"></div>
    <div class="sb-section">Navigation</div>
    """, unsafe_allow_html=True)

    # ── MAIN NAV ───────────────────────────────────────────────────────────────
    MAIN_NAV = [
        ("dashboard", "Dashboard"),
        ("scoring",   "Scoring & Trafic"),
        ("meta",      "Metadonnees"),
        ("perf",      "Performance"),
        ("backlinks", "Backlinks"),
        ("compare",   "Comparaison"),
        ("assistant", "Assistant IA"),
    ]
    for pid, label in MAIN_NAV:
        if st.session_state.page == pid:
            st.markdown(
                f'<div class="nav-item active">{label}</div>',
                unsafe_allow_html=True
            )
        else:
            if st.button(label, key=f"nav_{pid}", use_container_width=True):
                st.session_state.page = pid
                st.rerun()

    # ── CTA SECTION ────────────────────────────────────────────────────────────
    st.markdown('<div class="sb-div"></div><div class="sb-section">Analytics</div>', unsafe_allow_html=True)

    if st.session_state.page == "veille":
        st.markdown('<div class="nav-item active">Veille &amp; Tendances</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="nav-cta-wrap">', unsafe_allow_html=True)
        if st.button("Veille & Tendances", key="nav_veille", use_container_width=True):
            st.session_state.page = "veille"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    if st.session_state.page == "export":
        st.markdown('<div class="nav-item active">Rapports &amp; Export</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="nav-export-wrap">', unsafe_allow_html=True)
        if st.button("Rapports & Export", key="nav_export", use_container_width=True):
            st.session_state.page = "export"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # ── DATE ELEGANTE (remplace le filtre secteur) ─────────────────────────────
    cat_f = st.session_state.get("cat_filter", "Tous")
    if cat_f == "Tous":
        cat_f = "Tous secteurs"

    # ── SIDEBAR DATE FOOTER ─────────────────────────────────────────────────────
    _day   = datetime.now().strftime("%d")
    _month = datetime.now().strftime("%B").upper()
    _year  = datetime.now().strftime("%Y")
    _time  = datetime.now().strftime("%H:%M")
    st.markdown(f"""
    <div style="margin-top:2rem;padding:1.25rem 1.25rem 1.5rem;
                border-top:1px solid rgba(61,43,0,0.15);
                background:rgba(61,43,0,0.06);border-radius:0 0 4px 4px">
      <div style="font-family:'Inter',sans-serif;font-size:.45rem;font-weight:700;
                  letter-spacing:.25em;text-transform:uppercase;
                  color:rgba(61,43,0,0.35);margin-bottom:.5rem">Aujourd'hui</div>
      <div style="display:flex;align-items:baseline;gap:.4rem">
        <div style="font-family:'Playfair Display',serif;font-size:2rem;font-weight:700;
                    color:#3D2B00;line-height:1">{_day}</div>
        <div>
          <div style="font-family:'Inter',sans-serif;font-size:.65rem;font-weight:700;
                      color:#3D2B00;letter-spacing:.08em">{_month}</div>
          <div style="font-family:'Space Mono',monospace;font-size:.55rem;
                      color:rgba(61,43,0,0.45);letter-spacing:.06em">{_year}</div>
        </div>
      </div>
      <div style="font-family:'Space Mono',monospace;font-size:.55rem;
                  color:rgba(61,43,0,0.35);margin-top:.35rem;letter-spacing:.1em">{_time} · Dakar, SN</div>
    </div>
    """, unsafe_allow_html=True)

# ── FAB — query_params navigation ─────────────────────────────────────────────
_fab = st.query_params.get("fab", "")
if _fab in ("assistant", "export"):
    st.session_state.page = _fab
    st.query_params.clear()
    st.rerun()

# ── FAB FLOATING ACTION BUTTONS ───────────────────────────────────────────────
st.markdown("""
<div class="fab-wrap">
  <a href="?fab=assistant" class="fab fab-ia" data-tooltip="Assistant IA"
     style="text-decoration:none;display:flex;align-items:center;justify-content:center">
    <span style="font-family:'Space Mono',monospace;font-weight:700;font-size:.75rem;color:#fff;letter-spacing:.05em">IA</span>
  </a>
  <a href="?fab=export" class="fab fab-data" data-tooltip="Rapports &amp; Export"
     style="text-decoration:none;display:flex;align-items:center;justify-content:center">
    <span style="font-family:'Space Mono',monospace;font-weight:700;font-size:.65rem;color:#C9A84C;letter-spacing:.03em">AN</span>
  </a>
</div>
""", unsafe_allow_html=True)

page    = st.session_state.page
# ── Titre dynamique ────────────────────────────────────────────────────────────
_PAGE_TITLES = {
    "dashboard": "Dashboard",
    "scoring":   "Scoring & Trafic",
    "meta":      "Metadonnees",
    "perf":      "Performance",
    "backlinks": "Backlinks",
    "compare":   "Comparaison",
    "veille":    "Veille & Tendances",
    "export":    "Rapports & Export",
    "assistant": "Assistant IA",
}
_stc.html(
    f"<script>try{{parent.document.title='SenWebStats · {_PAGE_TITLES.get(page,'')}'}}catch(e){{}}</script>",
    height=0, scrolling=False
)
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

    # ── Senegal Map Hero ───────────────────────────────────────────────────────
    map_col, kpi_intro_col = st.columns([5, 3], gap="large")
    with map_col:
        st.markdown(f"""
<div class="map-card map-card--hero">
  <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:.75rem">
    <div class="map-title" style="margin:0">Sénégal · Web Coverage</div>
    <div style="font-family:'Space Mono',monospace;font-size:.55rem;color:rgba(61,43,0,0.4);
                letter-spacing:.15em;text-transform:uppercase">RÉSEAU · {n_sites} SITES</div>
  </div>
  <img src="{_SN_MAP_SRC}" class="sn-map" alt="Carte du Sénégal"
       style="width:100%;max-width:none;border-radius:10px;
              box-shadow:0 8px 32px rgba(201,168,76,0.18);" />
  <div class="map-legend" style="margin-top:1rem">
    <span class="map-dot"></span> Sites surveillés · 5 régions — Presse · E-commerce · Télécoms · Finance · Emploi
  </div>
</div>
""", unsafe_allow_html=True)
    with kpi_intro_col:
        st.markdown(f"""
<div style="padding:1rem 0 .5rem;height:100%;display:flex;flex-direction:column;justify-content:center">
  <div style="font-family:'Inter',sans-serif;font-size:.5rem;font-weight:700;
              letter-spacing:.25em;text-transform:uppercase;color:#C9A84C;margin-bottom:.75rem">
    Observatoire National
  </div>
  <div style="font-family:'Playfair Display',serif;font-size:1.75rem;font-weight:700;
              color:#1A1A2E;line-height:1.25;margin-bottom:1rem">
    Tableau de bord<br><span style="color:#C9A84C">en temps réel</span>
  </div>
  <div style="font-family:Inter,sans-serif;font-size:.8rem;color:#6B7280;line-height:1.75;
              border-left:2px solid rgba(201,168,76,0.3);padding-left:1rem;margin-bottom:1.5rem">
    Surveillance continue de l'écosystème web sénégalais — presse, e-commerce,
    télécoms, finance et emploi. Données actualisées quotidiennement.
  </div>
  <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:.75rem">
    <div style="background:linear-gradient(135deg,rgba(201,168,76,0.08),rgba(240,208,128,0.04));
                border:1px solid rgba(201,168,76,0.15);border-radius:10px;
                padding:.9rem .75rem;text-align:center">
      <div style="font-family:'Space Mono',monospace;font-size:1.5rem;font-weight:700;color:#C9A84C">{n_sites}</div>
      <div style="font-family:Inter,sans-serif;font-size:.5rem;color:#9CA3AF;
                  text-transform:uppercase;letter-spacing:.1em;margin-top:.2rem">Sites</div>
    </div>
    <div style="background:linear-gradient(135deg,rgba(201,168,76,0.08),rgba(240,208,128,0.04));
                border:1px solid rgba(201,168,76,0.15);border-radius:10px;
                padding:.9rem .75rem;text-align:center">
      <div style="font-family:'Space Mono',monospace;font-size:1.5rem;font-weight:700;color:#C9A84C">5</div>
      <div style="font-family:Inter,sans-serif;font-size:.5rem;color:#9CA3AF;
                  text-transform:uppercase;letter-spacing:.1em;margin-top:.2rem">Secteurs</div>
    </div>
    <div style="background:linear-gradient(135deg,rgba(201,168,76,0.08),rgba(240,208,128,0.04));
                border:1px solid rgba(201,168,76,0.15);border-radius:10px;
                padding:.9rem .75rem;text-align:center">
      <div style="font-family:'Space Mono',monospace;font-size:1.5rem;font-weight:700;color:#C9A84C">24/7</div>
      <div style="font-family:Inter,sans-serif;font-size:.5rem;color:#9CA3AF;
                  text-transform:uppercase;letter-spacing:.1em;margin-top:.2rem">Live</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

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
    st.markdown("""
<div class="methodo-card">
  <div class="methodo-shimmer"></div>
  <div class="methodo-inner">

    <div class="methodo-eyebrow">Transparence · Reproductibilité · Open Data</div>
    <div class="methodo-title">Méthodologie du Score Composite</div>

    <div class="methodo-formula">
      Score Global
      <span class="mf-op"> = </span>
      <span class="mf-gold">Autorité</span>
      <span class="mf-op"> × </span>0.45
      <span class="mf-op"> + </span>
      <span class="mf-gold">Qualité</span>
      <span class="mf-op"> × </span>0.35
      <span class="mf-op"> + </span>
      <span class="mf-gold">Technique</span>
      <span class="mf-op"> × </span>0.20
    </div>

    <div class="methodo-pillars">
      <div class="mp">
        <div class="mp-pct">45%</div>
        <div class="mp-name">Autorité</div>
        <div class="mp-bar-bg"><div class="mp-bar-fill" style="width:45%"></div></div>
        <div class="mp-sub">
          <strong>Open PageRank</strong> · 60%<br>
          <strong>CommonCrawl backlinks</strong> · 40%<br><br>
          Mesure la notoriété et l'influence du domaine sur le web international.
        </div>
      </div>
      <div class="mp">
        <div class="mp-pct">35%</div>
        <div class="mp-name">Qualité</div>
        <div class="mp-bar-bg"><div class="mp-bar-fill" style="width:35%"></div></div>
        <div class="mp-sub">
          <strong>SEO PageSpeed</strong> · 40%<br>
          <strong>Performance Lighthouse</strong> · 35%<br>
          <strong>Accessibilité</strong> · 25%<br><br>
          Mesure l'expérience utilisateur réelle.
        </div>
      </div>
      <div class="mp">
        <div class="mp-pct">20%</div>
        <div class="mp-name">Technique</div>
        <div class="mp-bar-bg"><div class="mp-bar-fill" style="width:20%"></div></div>
        <div class="mp-sub">
          <strong>SSL + Sitemap + Robots</strong><br>
          <strong>Temps de réponse + Contenu</strong><br><br>
          Mesure la santé technique et la conformité des bonnes pratiques.
        </div>
      </div>
    </div>

    <div class="methodo-sources">
      <span class="ms-label">Sources</span>
      <span class="ms-chip">CommonCrawl</span>
      <span class="ms-chip">Open PageRank</span>
      <span class="ms-chip">Google PageSpeed API</span>
      <span class="ms-chip">Google Trends · geo=SN</span>
      <span class="ms-chip">CTR Model AWR 2023</span>
    </div>

  </div>
</div>
""", unsafe_allow_html=True)
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
        df_bl["referring_domains"] = df_bl["referring_domains"].fillna(0)
        total_bl = int(df_bl["total_backlinks"].sum())
        best_bl  = df_bl.loc[df_bl["total_backlinks"].idxmax(), "name"] if not df_bl.empty else "—"
        avg_bl   = round(df_bl["total_backlinks"].mean(), 0)

        k1, k2, k3, k4 = st.columns(4, gap="medium")
        for col, (lbl, val, sub, badge, bcls, prog, color, delay) in zip([k1,k2,k3,k4], [
            ("Pages indexees CC", fmt(total_bl),    "total tous sites", "CommonCrawl", "badge-flat", 0.8,  "#0EA5E9", 0),
            ("Moyenne par site",  str(int(avg_bl)),  "pages indexees",  "Distribution","badge-flat", 0.5,  "#10B981", 1),
            ("Leader autorite",   best_bl[:14],      "top site",        "Max",         "badge-up",   1.0,  "#8B5CF6", 2),
            ("Dom. referents",    "N/A",             "via AWS Athena",  "Pro",         "badge-flat", 0.0,  "#F59E0B", 3),
        ]):
            col.markdown(kpi_master(lbl, val, sub, badge, bcls, prog, color, delay), unsafe_allow_html=True)

        st.markdown("<div style='height:2rem'></div>", unsafe_allow_html=True)

        # Hero : Treemap backlinks
        section_label("Treemap — poids de l'autorite par site")
        st.plotly_chart(
            make_treemap(df_bl, "total_backlinks", height=400),
            use_container_width=True, config={"displayModeBar": False}
        )

        # Open PageRank data for scatter
        df_opr = q("""SELECT s.name, s.category, sa.page_rank, sa.global_rank
                      FROM site_authority sa JOIN sites s ON s.id=sa.site_id
                      WHERE sa.collected_at=(SELECT MAX(collected_at) FROM site_authority WHERE site_id=sa.site_id)""")

        col1, col2 = st.columns(2, gap="large")
        with col1:
            section_label("Open PageRank vs Pages indexees (CommonCrawl)")
            if df_opr.empty:
                st.markdown('<div class="ibox">PageRank non collecte. Lance : <code>python main.py pagerank</code></div>', unsafe_allow_html=True)
            else:
                merged_sc = df_bl.merge(df_opr, on=["name","category"], how="inner")
                fig_sc = go.Figure()
                for cat in merged_sc["category"].unique():
                    dc = merged_sc[merged_sc["category"] == cat]
                    c  = CAT_COLORS.get(cat, "#0EA5E9")
                    fig_sc.add_trace(go.Scatter(
                        x=dc["page_rank"], y=dc["total_backlinks"],
                        mode="markers+text", name=CAT_LABEL.get(cat, cat),
                        text=dc["name"], textposition="top center",
                        textfont=dict(size=8, color="#6B7280", family="Inter"),
                        marker=dict(size=14, color=c, opacity=0.85,
                                    line=dict(width=2.5, color="#fff")),
                        hovertemplate="<b>%{text}</b><br>PageRank: %{x:.2f}<br>Pages CC: %{y:,}<extra></extra>",
                    ))
                lay_sc = base_layout(height=420)
                lay_sc["xaxis"]["title"] = dict(text="Open PageRank (0-10)", font=dict(size=11, color="#9CA3AF"))
                lay_sc["yaxis"]["title"] = dict(text="Pages indexees CC", font=dict(size=11, color="#9CA3AF"))
                fig_sc.update_layout(**lay_sc)
                st.plotly_chart(fig_sc, use_container_width=True, config={"displayModeBar": False})

        with col2:
            section_label("Sunburst — hierarchie secteur > site")
            st.plotly_chart(
                make_sunburst(df_bl, "total_backlinks", height=420),
                use_container_width=True, config={"displayModeBar": False}
            )

        section_label("Tableau complet — Pages indexees CommonCrawl")
        d = df_bl[["name","category","domain","total_backlinks","backlinks_change"]].copy()
        if not df_opr.empty:
            d = d.merge(df_opr[["name","page_rank","global_rank"]], on="name", how="left")
            d.columns = ["Site","Secteur","Domaine","Pages CC","Variation","PageRank","Rang mondial"]
            d["Rang mondial"] = d["Rang mondial"].apply(lambda x: fmt(int(x)) if pd.notna(x) else "—")
        else:
            d.columns = ["Site","Secteur","Domaine","Pages CC","Variation"]
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
        'Veille & <span class="acc">Tendances</span> <span style="font-family:Inter,sans-serif;font-size:.7rem;font-weight:700;background:rgba(201,168,76,0.15);color:#8B6914;border:1px solid rgba(201,168,76,0.3);border-radius:4px;padding:.15rem .5rem;letter-spacing:.08em;vertical-align:middle">BETA</span>',
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

        # Opportunites — dumbbell chart trafic actuel vs potentiel
        section_label("Pipeline d'opportunites de croissance")
        df_opp = df_all.copy()
        df_opp["score_qualite_proj"] = df_opp["score_qualite"].apply(lambda x: min(90, x + 30))
        df_opp["score_global_proj"]  = (df_opp["score_autorite"] * 0.45 + df_opp["score_qualite_proj"] * 0.35 + df_opp["score_technique"] * 0.20).round(1)
        df_opp["trafic_potentiel"]   = df_opp.apply(lambda r: int(CATEGORY_BASE.get(r["category"], 50000) * (r["score_global_proj"] / 100) ** 1.5), axis=1)
        df_opp["gap_trafic"]         = df_opp["trafic_potentiel"] - df_opp["trafic_estime"]
        df_opp["pct_gain"]           = (df_opp["gap_trafic"] / df_opp["trafic_estime"].replace(0, 1) * 100).round(0).astype(int)
        top_opp = df_opp.nlargest(15, "gap_trafic").sort_values("gap_trafic", ascending=True)

        fig_db = go.Figure()

        # Ligne connecteur (dumbbell)
        for _, row in top_opp.iterrows():
            cat_c = CAT_COLORS.get(row["category"], "#0EA5E9")
            fig_db.add_shape(
                type="line",
                x0=row["trafic_estime"], x1=row["trafic_potentiel"],
                y0=row["name"], y1=row["name"],
                line=dict(color=cat_c, width=2.5, dash="dot"),
                opacity=0.35,
            )

        # Barre actuelle
        fig_db.add_trace(go.Bar(
            x=top_opp["trafic_estime"],
            y=top_opp["name"],
            orientation="h",
            name="Trafic actuel",
            marker=dict(
                color=[hex_alpha(CAT_COLORS.get(c, "#0EA5E9"), 0.55) for c in top_opp["category"]],
                line=dict(width=0),
            ),
            width=0.35,
            hovertemplate="<b>%{y}</b><br>Trafic actuel : <b>%{x:,.0f}</b> vis/mois<extra></extra>",
        ))

        # Barre potentielle
        fig_db.add_trace(go.Bar(
            x=top_opp["trafic_potentiel"],
            y=top_opp["name"],
            orientation="h",
            name="Trafic potentiel",
            marker=dict(
                color=[CAT_COLORS.get(c, "#0EA5E9") for c in top_opp["category"]],
                line=dict(width=0),
                opacity=0.92,
            ),
            width=0.35,
            text=[f"+{fmt(g)}  (+{p}%)" for g, p in zip(top_opp["gap_trafic"], top_opp["pct_gain"])],
            textposition="outside",
            textfont=dict(family="Inter", size=10, color="#374151"),
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Potentiel : <b>%{x:,.0f}</b> vis/mois<br>"
                "Gain estimé : <b>+%{text}</b><extra></extra>"
            ),
        ))

        # Annotation "baseline" verticale
        max_x = int(top_opp["trafic_potentiel"].max() * 1.22)
        lay_db = base_layout(height=560, margin=dict(l=0, r=120, t=40, b=20))
        lay_db.update({
            "barmode": "overlay",
            "xaxis": {**_GX,
                "title": dict(text="Visites estimées / mois", font=dict(size=11, color="#9CA3AF")),
                "tickformat": ",.0f",
                "range": [0, max_x],
            },
            "yaxis": {**_GY,
                "tickfont": dict(size=10.5, color="#374151", family="Inter"),
                "categoryorder": "array",
                "categoryarray": list(top_opp["name"]),
            },
            "legend": dict(
                orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
                bgcolor="rgba(0,0,0,0)",
                font=dict(size=11, color="#4B5563", family="Inter"),
            ),
            "shapes": [dict(
                type="line", x0=0, x1=0, y0=-0.5, y1=len(top_opp) - 0.5,
                xref="x", yref="y",
                line=dict(color="#E5E7EB", width=1),
            )],
        })
        fig_db.update_layout(**lay_db)
        st.plotly_chart(fig_db, use_container_width=True, config={
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d", "toggleSpikelines"],
            "displaylogo": False,
        })

        # KPIs résumé opportunités
        total_gap  = int(top_opp["gap_trafic"].sum())
        best_opp   = top_opp.iloc[-1]
        avg_pct    = int(top_opp["pct_gain"].mean())
        k1, k2, k3 = st.columns(3, gap="large")
        for col, (lbl, val, sub, badge, color) in zip([k1, k2, k3], [
            ("Gain total top 15",   fmt(total_gap),             "vis/mois potentielles", "Potentiel", "#10B981"),
            ("Meilleure opportunite", best_opp["name"][:18],    f"+{fmt(best_opp['gap_trafic'])} vis", "Max gain", "#0EA5E9"),
            ("Gain moyen",          f"+{avg_pct}%",             "si qualite SEO → 90",   "Moyenne",   "#8B5CF6"),
        ]):
            col.markdown(kpi_master(lbl, val, sub, badge, "badge-up", 0.7, color, 0), unsafe_allow_html=True)

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
                          color:#C9A84C;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.5rem">
                CSV · Scores complets
              </div>
              <div style="font-size:.8125rem;color:#4B5563;line-height:1.65">
                Tous les scores pour les 28 sites. Compatible Excel, Google Sheets, Power BI.
              </div>
            </div>
            """, unsafe_allow_html=True)
            csv_cols = ["name","domain","category","score_global","score_autorite","score_qualite",
                        "score_technique","trafic_estime","total_backlinks","page_rank","trends_score",
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
                          color:#C9A84C;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.5rem">
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
                          color:#C9A84C;letter-spacing:.14em;text-transform:uppercase;margin-bottom:.5rem">
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


# ══════════════════════════════════════════════════════════════════════════════
# PAGE : ASSISTANT IA
# ══════════════════════════════════════════════════════════════════════════════
elif page == "assistant":
    try:
        from groq import Groq as _Groq
        _GROQ_OK = True
    except ImportError:
        _GROQ_OK = False

    st.markdown('<div class="mwrap">', unsafe_allow_html=True)
    page_header(
        "IA · Analyse · Insights",
        'Assistant <span class="acc">IA</span>',
        "Posez vos questions sur les données — l'IA analyse la base en temps réel",
    )

    # ── Styles chat ────────────────────────────────────────────────────────────
    st.markdown("""
    <style>
    /* Conteneur chat */
    .chat-wrap { max-width: 820px; margin: 0 auto; }

    /* Bulle utilisateur */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
      background: #3D3215 !important;
      border-radius: 16px 0 16px 16px !important;
      border: none !important;
      margin-bottom: .75rem !important;
      box-shadow: 0 2px 12px rgba(61,50,21,0.2) !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) div {
      color: #FFFFFF !important;
    }

    /* Bulle assistant */
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) {
      background: #FFFFFF !important;
      border-radius: 0 16px 16px 16px !important;
      border: 1px solid rgba(201,168,76,0.2) !important;
      box-shadow: 0 2px 8px rgba(0,0,0,0.06) !important;
      margin-bottom: .75rem !important;
    }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) p,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"]) div {
      color: #1A1A2E !important;
      font-family: Inter, sans-serif !important;
      font-size: 0.9rem !important;
    }

    /* Avatar assistant (icone IA) */
    [data-testid="stChatMessageAvatarAssistant"] {
      background: #C9A84C !important;
      border-radius: 8px !important;
      color: white !important;
      font-weight: 700 !important;
      font-size: 0.75rem !important;
      font-family: 'Space Mono', monospace !important;
    }

    /* Avatar utilisateur */
    [data-testid="stChatMessageAvatarUser"] {
      background: #C9A84C !important;
      border-radius: 50% !important;
      color: white !important;
      font-weight: 700 !important;
      font-size: 0.8rem !important;
    }

    /* Zone messages */
    [data-testid="stChatMessageContent"] {
      background: transparent !important;
    }

    /* Input du chat */
    [data-testid="stChatInput"] textarea,
    [data-testid="stChatInputTextArea"] {
      background: #FFFFFF !important;
      border: 1.5px solid rgba(201,168,76,0.4) !important;
      border-radius: 12px !important;
      color: #1A1A2E !important;
      font-family: Inter, sans-serif !important;
      font-size: 0.9rem !important;
      padding: 0.9rem 1.25rem !important;
      box-shadow: 0 2px 12px rgba(201,168,76,0.08) !important;
    }
    [data-testid="stChatInput"] textarea:focus,
    [data-testid="stChatInputTextArea"]:focus {
      border-color: #C9A84C !important;
      box-shadow: 0 0 0 3px rgba(201,168,76,0.15) !important;
      outline: none !important;
    }
    [data-testid="stChatInput"] textarea::placeholder {
      color: #9CA3AF !important;
      font-style: italic;
    }

    /* Bouton envoi */
    [data-testid="stChatInputSubmitButton"] button {
      background: #C9A84C !important;
      border-radius: 8px !important;
      color: white !important;
      transition: all 0.2s ease !important;
    }
    [data-testid="stChatInputSubmitButton"] button:hover {
      background: #8B6914 !important;
      transform: scale(1.05) !important;
    }

    /* Zone de messages avec scroll */
    .chat-area {
      background: #F9F5EE;
      border: 1px solid rgba(201,168,76,0.15);
      border-radius: 16px;
      padding: 1.5rem;
      min-height: 400px;
      max-height: 500px;
      overflow-y: auto;
    }
    </style>
    """, unsafe_allow_html=True)

    if not _GROQ_OK:
        st.markdown('<div class="ibox">Module manquant — lance : <code>pip install groq</code></div>', unsafe_allow_html=True)
        st.stop()

    _api_key = os.environ.get("GROQ_API_KEY", "")
    if not _api_key:
        st.markdown('<div class="ibox">Clé GROQ_API_KEY manquante dans .env</div>', unsafe_allow_html=True)
        st.stop()

    # ── Vérification clé API ────────────────────────────────────────────────────
    @st.cache_data(ttl=120)
    def _check_api(key: str) -> tuple[bool, str]:
        try:
            c = _Groq(api_key=key)
            c.chat.completions.create(
                model="llama-3.3-70b-versatile",
                max_tokens=5,
                messages=[{"role": "user", "content": "ok"}]
            )
            return True, ""
        except Exception as e:
            return False, str(e)

    _api_ok, _api_err = _check_api(_api_key)

    if not _api_ok:
        st.warning(
            f"**Erreur API Groq** : {_api_err}  \n"
            "Vérifie ta clé sur **[console.groq.com](https://console.groq.com)**  \n\n"
            "Le mode analyse hors-ligne reste disponible ci-dessous.",
            icon=None
        )

    # ── Mode hors-ligne : analyse directe des données ──────────────────────────
    def _analyse_hors_ligne(question: str) -> str:
        """Répond aux questions fréquentes en analysant directement le DataFrame."""
        df_a = compute_scores()
        if df_a.empty:
            return "Aucune donnée disponible dans la base."

        q_low = question.lower()
        lines = []

        # Classement général
        if any(w in q_low for w in ["classement", "meilleur", "top", "premier", "mieux", "classé"]):
            top = df_a.head(10)
            lines.append("**Classement général (top 10) :**\n")
            for i, (_, r) in enumerate(top.iterrows(), 1):
                lines.append(f"{i}. **{r['name']}** ({r['category']}) — score global **{r['score_global']:.1f}/100**")
            lines.append(f"\n*Score = combinaison autorité ({r['score_autorite']:.0f}), qualité ({r['score_qualite']:.0f}), technique ({r['score_technique']:.0f})*")

        # Trafic
        elif any(w in q_low for w in ["trafic", "visites", "audience", "visiteurs"]):
            top = df_a.nlargest(10, "trafic_estime")
            lines.append("**Estimation de trafic mensuel (top 10) :**\n")
            for _, r in top.iterrows():
                lines.append(f"- **{r['name']}** : ~{fmt(int(r['trafic_estime']))} visites/mois")
            lines.append("\n*Basé sur : PageRank OPR × pages indexées CC × score Google Trends*")

        # Performance / PageSpeed
        elif any(w in q_low for w in ["performance", "vitesse", "pagespeed", "rapide", "lent", "chargement"]):
            perf = df_a[df_a["performance_score"] > 0].nlargest(10, "performance_score")
            if perf.empty:
                return "Aucune donnée PageSpeed disponible pour l'instant."
            lines.append("**Performance PageSpeed (top 10) :**\n")
            for _, r in perf.iterrows():
                lines.append(f"- **{r['name']}** : perf={r['performance_score']:.0f}/100 | SEO={r['seo_score']:.0f}/100")
            worst = df_a[df_a["performance_score"] > 0].nsmallest(3, "performance_score")
            lines.append("\n**Sites les plus lents :**")
            for _, r in worst.iterrows():
                lines.append(f"- {r['name']} : {r['performance_score']:.0f}/100")

        # SEO
        elif any(w in q_low for w in ["seo", "référencement", "google", "visibilité"]):
            seo = df_a[df_a["seo_score"] > 0].nlargest(10, "seo_score")
            if seo.empty:
                return "Aucune donnée SEO disponible."
            lines.append("**Score SEO PageSpeed (top 10) :**\n")
            for _, r in seo.iterrows():
                lines.append(f"- **{r['name']}** : {r['seo_score']:.0f}/100")

        # Autorité / PageRank
        elif any(w in q_low for w in ["autorité", "autorite", "pagerank", "page rank", "domaine", "backlink", "lien"]):
            auth = df_a.nlargest(10, "score_autorite")
            lines.append("**Score d'autorité (OPR PageRank + CommonCrawl) :**\n")
            for _, r in auth.iterrows():
                pr = f" | PageRank={r['page_rank']:.2f}" if pd.notna(r.get("page_rank")) and r.get("page_rank",0)>0 else ""
                lines.append(f"- **{r['name']}** : autorité={r['score_autorite']:.1f}/100{pr}")

        # Tendances / Trends
        elif any(w in q_low for w in ["tendance", "trend", "intérêt", "recherche", "populaire"]):
            tr = df_a[df_a["trends_score"] > 0].nlargest(10, "trends_score")
            if tr.empty:
                return "Aucune donnée Google Trends disponible."
            lines.append("**Intérêt de recherche Google Trends au Sénégal (top 10) :**\n")
            for _, r in tr.iterrows():
                lines.append(f"- **{r['name']}** : {r['trends_score']:.0f}/100")
            lines.append("\n*Échelle 0-100 — 100 = pic maximal sur 12 mois*")

        # Secteur
        elif any(w in q_low for w in ["secteur", "presse", "ecommerce", "banque", "téléphonie", "telephonie", "emploi"]):
            lines.append("**Moyennes par secteur :**\n")
            for cat, grp in df_a.groupby("category"):
                lines.append(
                    f"**{cat.upper()}** ({len(grp)} sites) "
                    f"| score={grp['score_global'].mean():.1f} "
                    f"| perf={grp['performance_score'].mean():.1f} "
                    f"| SEO={grp['seo_score'].mean():.1f} "
                    f"| trafic≈{fmt(int(grp['trafic_estime'].mean()))}/mois"
                )

        # Risque / mauvais
        elif any(w in q_low for w in ["risque", "problème", "faible", "mauvais", "améliorer"]):
            worst = df_a.nsmallest(8, "score_global")
            lines.append("**Sites en zone de risque (score global le plus bas) :**\n")
            for _, r in worst.iterrows():
                pb = []
                if r["performance_score"] < 50 and r["performance_score"] > 0:
                    pb.append(f"perf={r['performance_score']:.0f}")
                if r["seo_score"] < 70 and r["seo_score"] > 0:
                    pb.append(f"SEO={r['seo_score']:.0f}")
                if r["score_autorite"] < 20:
                    pb.append("autorité faible")
                prob_str = " | ".join(pb) if pb else "données partielles"
                lines.append(f"- **{r['name']}** (score={r['score_global']:.1f}) — {prob_str}")

        # Comparaison deux sites
        else:
            # Cherche si un nom de site est mentionné
            matched = []
            for _, r in df_a.iterrows():
                if r["name"].lower() in q_low or r["domain"].lower().split(".")[0] in q_low:
                    matched.append(r)
            if matched:
                lines.append("**Données disponibles :**\n")
                for r in matched[:3]:
                    lines.append(
                        f"### {r['name']} ({r['category']})\n"
                        f"- Score global : **{r['score_global']:.1f}/100**\n"
                        f"- Autorité : {r['score_autorite']:.1f} | Qualité : {r['score_qualite']:.1f} | Technique : {r['score_technique']:.1f}\n"
                        + (f"- PageSpeed performance : {r['performance_score']:.0f}/100\n" if r['performance_score']>0 else "- PageSpeed : données non collectées\n")
                        + (f"- SEO : {r['seo_score']:.0f}/100\n" if r['seo_score']>0 else "")
                        + (f"- PageRank OPR : {r['page_rank']:.2f}/10\n" if pd.notna(r.get('page_rank')) and r.get('page_rank',0)>0 else "")
                        + (f"- Trends sénégal : {r['trends_score']:.0f}/100\n" if pd.notna(r.get('trends_score')) else "")
                        + f"- Trafic estimé : ~{fmt(int(r['trafic_estime']))}/mois"
                    )
            else:
                # Réponse générale
                lines.append(f"**Résumé de l'observatoire SenWebStats :**\n")
                lines.append(f"- {len(df_a)} sites analysés dans 5 secteurs")
                lines.append(f"- Score global moyen : {df_a['score_global'].mean():.1f}/100")
                lines.append(f"- Meilleur site : **{df_a.iloc[0]['name']}** ({df_a.iloc[0]['score_global']:.1f}/100)")
                lines.append(f"- Trafic total estimé : ~{fmt(int(df_a['trafic_estime'].sum()))}/mois\n")
                lines.append("*Questions possibles : classement, trafic, performance, SEO, autorité, tendances, secteurs, risques, ou le nom d'un site précis.*")

        return "\n".join(lines) if lines else "Je n'ai pas compris la question. Essaie : 'classement', 'trafic', 'performance', 'SEO', 'tendances', ou le nom d'un site."

    # ── Contexte données injecté dans le system prompt ─────────────────────────
    @st.cache_data(ttl=300)
    def _build_context() -> str:
        df = compute_scores()
        if df.empty:
            return "Aucune donnée disponible."
        lines = ["## Données SenWebStats — Observatoire Web Sénégal\n"]
        lines.append(f"Nombre de sites analysés : {len(df)}")
        lines.append(f"Secteurs : presse, ecommerce, telephonie, banque_finance, emploi\n")
        lines.append("### Classement global (top 15)")
        for _, r in df.head(15).iterrows():
            lines.append(
                f"- {r['name']} ({r['category']}) | score={r['score_global']} "
                f"| autorité={r['score_autorite']} | qualité={r['score_qualite']} "
                f"| technique={r['score_technique']} | trafic≈{fmt(int(r['trafic_estime']))}/mois"
                + (f" | PageRank={r['page_rank']:.2f}" if pd.notna(r.get('page_rank')) and r.get('page_rank',0)>0 else "")
                + (f" | Trends={r['trends_score']:.0f}/100" if pd.notna(r.get('trends_score')) else "")
            )
        lines.append("\n### Moyennes par secteur")
        for cat, grp in df.groupby("category"):
            lines.append(
                f"- {cat} : score moyen={grp['score_global'].mean():.1f} "
                f"| perf={grp['performance_score'].mean():.1f} "
                f"| SEO={grp['seo_score'].mean():.1f}"
            )
        lines.append("\n### Sites avec données PageSpeed disponibles")
        perf_df = df[df["performance_score"] > 0].sort_values("performance_score", ascending=False)
        for _, r in perf_df.head(10).iterrows():
            lines.append(
                f"- {r['name']} : perf={r['performance_score']:.0f} | SEO={r['seo_score']:.0f} "
                f"| access={r['accessibility_score']:.0f} | LCP={r.get('lcp_ms',0)/1000:.1f}s"
            )
        return "\n".join(lines)

    SYSTEM_PROMPT = """Tu es l'assistant IA de SenWebStats, un observatoire d'analyse du web sénégalais.
Tu analyses les données réelles collectées sur 28 sites web au Sénégal (presse, e-commerce, télécom, banque, emploi).

Tes capacités :
- Répondre aux questions sur les scores, classements, performances des sites
- Comparer des sites entre eux
- Expliquer les métriques (score_autorite, score_qualite, score_technique, PageRank, Google Trends, etc.)
- Identifier les points forts et faibles de chaque site
- Donner des recommandations SEO/performance concrètes
- Analyser les tendances par secteur

Règles :
- Réponds toujours en français
- Sois concis mais précis — utilise les vraies données fournies
- Quand tu cites un score, précise ce qu'il mesure
- N'invente jamais de données : si une info est manquante dis-le
- Utilise des emojis avec parcimonie pour structurer (✅ ⚠️ 📊)
- Format Markdown pour les listes et comparaisons

Données du contexte ci-dessous (mises à jour en temps réel depuis la base) :
"""

    # ── State messages ──────────────────────────────────────────────────────────
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []

    # ── Suggestions rapides ─────────────────────────────────────────────────────
    if not st.session_state.chat_messages:
        st.markdown("""
        <div style="max-width:820px;margin:0 auto 2rem">
          <div style="font-family:Inter,sans-serif;font-size:.75rem;font-weight:600;
                      color:var(--txt-3);letter-spacing:.1em;text-transform:uppercase;
                      margin-bottom:1rem">Suggestions</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:.75rem">
        """, unsafe_allow_html=True)

        suggestions = [
            ("📊 Classement", "Quel est le top 5 des sites les mieux classés et pourquoi ?"),
            ("⚡ Performance", "Quels sites ont les meilleures performances web (PageSpeed) ?"),
            ("🔍 SEO", "Donne-moi une analyse SEO comparative par secteur"),
            ("⚠️ Risques", "Quels sites sont en zone de risque technique et pourquoi ?"),
            ("📈 Tendances", "Quels sites ont le plus d'intérêt de recherche au Sénégal ?"),
            ("💡 Conseils", "Quelles sont les 3 recommandations prioritaires pour améliorer le web sénégalais ?"),
        ]
        cols = st.columns(2, gap="medium")
        for i, (title, prompt) in enumerate(suggestions):
            with cols[i % 2]:
                if st.button(f"{title}\n{prompt[:55]}…" if len(prompt)>55 else f"{title}\n{prompt}",
                             key=f"sug_{i}", use_container_width=True):
                    st.session_state.chat_messages.append({"role": "user", "content": prompt})
                    st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

    # ── Historique ──────────────────────────────────────────────────────────────
    st.markdown('<div class="chat-wrap">', unsafe_allow_html=True)
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"], avatar="S" if msg["role"]=="user" else "IA"):
            st.markdown(msg["content"])

    # ── Détection message en attente (via bouton suggestion) ────────────────────
    _pending = (
        st.session_state.chat_messages
        and st.session_state.chat_messages[-1]["role"] == "user"
        and (len(st.session_state.chat_messages) == 1 or st.session_state.chat_messages[-2]["role"] == "assistant")
        and not st.session_state.get("_last_answered") == st.session_state.chat_messages[-1]["content"]
    )

    def _generate_answer(question: str) -> str:
        if _api_ok:
            try:
                ctx = _build_context()
                client = _Groq(api_key=_api_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    max_tokens=1024,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT + "\n\n" + ctx},
                    ] + [
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.chat_messages
                    ],
                )
                return response.choices[0].message.content
            except Exception as e:
                return (f"⚠️ Erreur API Groq : {e}\n\n---\n\n**Mode analyse :**\n\n"
                        + _analyse_hors_ligne(question))
        return _analyse_hors_ligne(question)

    # ── Traitement message en attente (suggestion cliquée) ──────────────────────
    if _pending:
        pending_q = st.session_state.chat_messages[-1]["content"]
        with st.chat_message("assistant", avatar="IA"):
            with st.spinner("Analyse en cours…"):
                answer = _generate_answer(pending_q)
            st.markdown(answer)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.session_state["_last_answered"] = pending_q
        st.rerun()

    # ── Input ───────────────────────────────────────────────────────────────────
    user_input = st.chat_input("Posez votre question sur les données web sénégalaises…")

    if user_input:
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user", avatar="S"):
            st.markdown(user_input)

        with st.chat_message("assistant", avatar="IA"):
            with st.spinner("Analyse en cours…"):
                answer = _generate_answer(user_input)
            st.markdown(answer)
        st.session_state.chat_messages.append({"role": "assistant", "content": answer})
        st.session_state["_last_answered"] = user_input

    # ── Reset ────────────────────────────────────────────────────────────────────
    if st.session_state.chat_messages:
        if st.button("Nouvelle conversation", key="chat_reset"):
            st.session_state.chat_messages = []
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# SITE FOOTER
# ══════════════════════════════════════════════════════════════════════════════
st.markdown(f"""
<div class="site-footer">
  <div>
    <div class="footer-brand">SenWebStats</div>
    <div class="footer-tagline">Observatoire National du Web Sénégalais</div>
    <div class="footer-badge">v7 · {now[:10]}</div>
  </div>
  <div class="footer-divider"></div>
  <div class="footer-links">
    <a href="#">Documentation</a>
    <span class="sep">·</span>
    <a href="#">API</a>
    <span class="sep">·</span>
    <a href="#">GitHub</a>
    <span class="sep">·</span>
    <span style="color:rgba(201,168,76,0.3);font-size:.7rem;font-family:'Space Mono',monospace">SN · DAKAR</span>
  </div>
</div>
""", unsafe_allow_html=True)
