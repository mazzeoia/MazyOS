"""Shared interface primitives for the Creative Media OS."""
from __future__ import annotations

import base64
from html import escape
from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
LOGO_PATH = ROOT / "identidade" / "logo.png"


def logo_data_uri() -> str:
    if not LOGO_PATH.exists():
        return ""
    payload = base64.b64encode(LOGO_PATH.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{payload}"


def inject_product_theme() -> None:
    st.markdown(
        """
        <style>
          :root {
            --canvas: #f6f7f9;
            --surface: #ffffff;
            --surface-subtle: #fafafa;
            --border: #e4e7ec;
            --text: #17191f;
            --muted: #68707d;
            --accent: #e34716;
            --accent-dark: #b82715;
            --warning: #b86a00;
            --success: #16825d;
          }
          .stApp { background: var(--canvas) !important; color: var(--text); }
          [data-testid="stHeader"] { background: rgba(246,247,249,.9); }
          [data-testid="stSidebar"] {
            background: #ffffff !important;
            border-right: 1px solid var(--border) !important;
          }
          [data-testid="stSidebarContent"] { background: #ffffff !important; }
          [data-testid="stSidebarNav"] { padding-top: 0; }
          .block-container { max-width: 1440px; padding: 1.4rem 2rem 4rem; }
          h1, h2, h3, h4 { color: var(--text) !important; letter-spacing: 0 !important; }
          p { color: var(--muted); }
          div[data-testid="stMetric"] {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            padding: 16px 18px !important;
            box-shadow: none !important;
            min-height: 112px;
          }
          div[data-testid="stMetricLabel"] { color: var(--muted); font-weight: 600; }
          div[data-testid="stMetricValue"] { color: var(--text); font-size: 1.65rem; }
          div[data-testid="stMetricDelta"] { font-weight: 700; }
          div[data-testid="stForm"], div[data-testid="stExpander"] {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 8px;
          }
          div[data-baseweb="select"] > div,
          div[data-testid="stTextInput"] input,
          div[data-testid="stNumberInput"] input,
          div[data-testid="stTextArea"] textarea {
            border-radius: 6px !important;
          }
          .stButton > button, .stDownloadButton > button {
            border-radius: 6px !important;
            min-height: 40px;
            font-weight: 700;
            box-shadow: none !important;
          }
          .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
            background: var(--accent) !important;
            border-color: var(--accent) !important;
          }
          [data-testid="stTabs"] button { letter-spacing: 0 !important; }
          [data-testid="stDataFrame"] { border: 1px solid var(--border); border-radius: 8px; overflow: hidden; }

          .hero {
            background: transparent !important;
            border: 0 !important;
            border-radius: 0 !important;
            padding: 4px 0 18px !important;
            box-shadow: none !important;
            margin-bottom: 0 !important;
          }
          .hero h1 { font-size: 28px !important; line-height: 1.2 !important; margin-bottom: 6px !important; }
          .hero p { font-size: 14px !important; max-width: 780px !important; }
          .brand-line { display: none !important; }
          .soft-card, .step-card, .connector-card {
            background: var(--surface) !important;
            border: 1px solid var(--border) !important;
            border-radius: 8px !important;
            box-shadow: none !important;
          }
          .step-card { min-height: 128px !important; padding: 18px !important; }
          .step-index { border-radius: 6px !important; background: #24262c !important; }
          .status-chip { border-radius: 999px !important; background: #f6f7f9 !important; }
          .summary-strip { border-radius: 8px !important; }
          .alert-red, .alert-yellow { border-radius: 6px !important; }

          .sidebar-shell { padding: 8px 7px 20px !important; }
          .sidebar-brand { padding: 8px 9px 18px !important; gap: 10px !important; }
          .sidebar-logo-image {
            width: 38px; height: 38px; object-fit: cover; border-radius: 7px;
            border: 1px solid #1f2229;
          }
          .sidebar-brand strong { font-size: 15px !important; }
          .sidebar-brand span { font-size: 11px !important; }
          .sidebar-spotlight {
            background: #17191f !important;
            border-radius: 8px !important;
            box-shadow: none !important;
            margin: 0 5px 18px !important;
            padding: 13px !important;
          }
          .sidebar-spotlight strong { color: #ffffff !important; }
          .sidebar-spotlight p { color: #b8bdc7 !important; font-size: 12px !important; }
          .sidebar-label { color: #878e9a !important; letter-spacing: .06em !important; }
          .sidebar-link {
            border-radius: 6px !important;
            margin: 2px 5px !important;
            padding: 10px 11px !important;
            color: #535a67 !important;
            font-size: 13px !important;
          }
          .sidebar-link:hover { background: #f3f4f6 !important; transform: none !important; }
          .sidebar-link.active {
            background: #fff1eb !important;
            color: #b82715 !important;
            box-shadow: inset 3px 0 0 #e34716 !important;
          }
          .sidebar-link .icon {
            width: 22px !important; height: 22px !important; flex-basis: 22px !important;
            border-radius: 5px !important; background: transparent !important;
            font-size: 15px !important; color: inherit !important;
          }
          .sidebar-divider { background: var(--border) !important; }
          .sidebar-footer {
            border-radius: 7px !important;
            background: #fafafa !important;
            box-shadow: none !important;
          }

          .page-topline {
            display: flex; align-items: flex-start; justify-content: space-between;
            gap: 18px; margin: 2px 0 20px;
          }
          .page-eyebrow {
            color: var(--accent-dark); font-size: 11px; font-weight: 800;
            text-transform: uppercase; letter-spacing: .08em;
          }
          .page-title { margin: 4px 0 4px; font-size: 28px; line-height: 1.2; font-weight: 780; }
          .page-subtitle { margin: 0; max-width: 760px; font-size: 14px; line-height: 1.5; }
          .sync-state {
            white-space: nowrap; border: 1px solid var(--border); background: var(--surface);
            border-radius: 999px; padding: 8px 11px; color: #525966; font-size: 12px; font-weight: 700;
          }
          .sync-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: var(--success); margin-right: 7px; }
          .section-heading { display:flex; align-items:end; justify-content:space-between; gap:16px; margin: 24px 0 10px; }
          .section-heading h2 { margin:0; font-size:17px; }
          .section-heading p { margin:3px 0 0; font-size:12px; }
          .command-card {
            background: var(--surface); border: 1px solid var(--border); border-radius: 8px;
            padding: 17px; min-height: 136px;
          }
          .command-card.critical { border-left: 4px solid #c72d2d; }
          .command-card.warning { border-left: 4px solid #d78300; }
          .command-card.good { border-left: 4px solid #16825d; }
          .command-label { color:#7b818d; font-size:11px; font-weight:800; text-transform:uppercase; letter-spacing:.06em; }
          .command-card h3 { margin:8px 0 5px; font-size:15px; line-height:1.35; }
          .command-card p { margin:0; font-size:12px; line-height:1.45; }
          .command-meta { margin-top:12px; font-size:11px; color:#8a909b; }
          .account-row {
            display:grid; grid-template-columns:minmax(170px,1.6fr) 1fr 1fr 1fr 90px;
            align-items:center; gap:14px; padding:13px 15px; background:#fff;
            border:1px solid var(--border); border-bottom:0;
          }
          .account-row:first-child { border-radius:8px 8px 0 0; }
          .account-row:last-child { border-bottom:1px solid var(--border); border-radius:0 0 8px 8px; }
          .account-name { font-weight:750; color:var(--text); font-size:13px; }
          .account-sub { color:#858b96; font-size:11px; margin-top:2px; }
          .account-value { color:#3c424c; font-size:12px; }
          .health { display:inline-flex; align-items:center; gap:6px; font-size:11px; font-weight:800; }
          .health-dot { width:7px; height:7px; border-radius:50%; display:inline-block; }
          .health.good { color:#16825d; } .health.good .health-dot { background:#16825d; }
          .health.warning { color:#a45d00; } .health.warning .health-dot { background:#d78300; }
          .health.critical { color:#b42318; } .health.critical .health-dot { background:#c72d2d; }
          .progress-track { width:100%; height:6px; background:#eceef1; border-radius:99px; overflow:hidden; margin-top:5px; }
          .progress-fill { height:100%; background:#30343b; border-radius:99px; }
          .empty-product {
            border:1px dashed #cfd3da; border-radius:8px; padding:34px 22px; text-align:center; background:#fff;
          }
          .empty-product strong { display:block; color:var(--text); margin-bottom:6px; }
          .empty-product p { margin:0 auto; max-width:520px; font-size:13px; }
          @media (max-width: 900px) {
            .block-container { padding: 1rem 1rem 3rem; }
            .page-topline { display:block; }
            .sync-state { display:inline-block; margin-top:12px; }
            .account-row { grid-template-columns:1fr 1fr; }
            .account-row > div:nth-child(4) { display:none; }
          }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str, subtitle: str, eyebrow: str = "Creative Media OS", sync_text: str = "Sistema online") -> None:
    st.markdown(
        f"""
        <div class="page-topline">
          <div>
            <div class="page-eyebrow">{escape(eyebrow)}</div>
            <h1 class="page-title">{escape(title)}</h1>
            <p class="page-subtitle">{escape(subtitle)}</p>
          </div>
          <div class="sync-state"><span class="sync-dot"></span>{escape(sync_text)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_heading(title: str, subtitle: str = "") -> None:
    st.markdown(
        f'<div class="section-heading"><div><h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div></div>',
        unsafe_allow_html=True,
    )


def command_card(label: str, title: str, body: str, meta: str, tone: str = "warning") -> None:
    st.markdown(
        f"""
        <div class="command-card {escape(tone)}">
          <div class="command-label">{escape(label)}</div>
          <h3>{escape(title)}</h3>
          <p>{escape(body)}</p>
          <div class="command-meta">{escape(meta)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_product(title: str, body: str) -> None:
    st.markdown(
        f'<div class="empty-product"><strong>{escape(title)}</strong><p>{escape(body)}</p></div>',
        unsafe_allow_html=True,
    )
