import streamlit as st
import json
import os
from streamlit_autorefresh import st_autorefresh

# Page config with SEO
st.set_page_config(
    page_title="SikkaTrade - AI-Powered Trading Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Load environment
from dotenv import load_dotenv

load_dotenv()

APP_MODE = os.getenv("APP_MODE", "dev").upper()
APP_NAME = os.getenv("APP_NAME", "SikkaTrade")
AUTHOR_NAME = os.getenv("AUTHOR_NAME", "Hassan Ali")
AUTHOR_URL = os.getenv("AUTHOR_URL", "https://linktr.ee/softdevhassan")

# Inject modern CSS + Remix Icons
st.markdown(
    """
<link href="https://cdn.jsdelivr.net/npm/remixicon@4.0.0/fonts/remixicon.css" rel="stylesheet">

<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Dark theme base */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #e2e8f0;
    }
    
    .block-container {
        padding: 1rem 2rem !important;
        max-width: 1280px !important;
    }
    
    /* Custom card style */
    .metric-card {
        background: rgba(30, 41, 59, 0.6);
        border: 1px solid #334155;
        border-radius: 0.5rem;
        padding: 0.75rem;
        backdrop-filter: blur(10px);
        margin-bottom: 0.5rem; /* Gap between cards */
    }
    
    .metric-label {
        color: #94a3b8;
        font-size: 0.75rem;
        margin-bottom: 0.25rem;
    }
    
    .metric-value {
        color: white;
        font-size: 1.25rem;
        font-weight: bold;
    }
    
    .profit-positive { color: #10b981; }
    .profit-negative { color: #ef4444; }
    
    /* Table styles */
    .dataframe {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid #334155;
        border-radius: 0.5rem;
    }
    
    /* Custom scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: #1e293b;
    }
    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 4px;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Load state
try:
    with open("state.json", "r") as f:
        state = json.load(f)
except:
    state = {}

phase = state.get("phase", "UNKNOWN")

# Shutdown screen
if phase == "SHUTDOWN":
    st.markdown(
        """
    <div style='text-align: center; padding: 4rem;'>
        <i class='ri-shut-down-line' style='font-size: 4rem; color: #ef4444;'></i>
        <h1 style='margin-top: 1rem;'>System Closed</h1>
        <p style='color: #94a3b8;'>Runtime ended. All trades closed successfully.</p>
        <p style='margin-top: 1rem; font-size: 0.875rem; color: #64748b;'>
            <i class='ri-file-text-line'></i> Check logs for final report
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    st.stop()

# Auto refresh
st_autorefresh(interval=500, key="refresh")

# Extract data
wallet = state.get("wallet", {})
runtime_elapsed = state.get("runtime_elapsed", 0)
runtime_total = state.get("runtime_total", 30)
trades_history = state.get("trades_history", [])

total = wallet.get("total", 0)
free = wallet.get("free", 0)
used = wallet.get("used", 0)
profit = wallet.get("profit", 0)

# Main two-column layout - left sidebar, right table
col_sidebar, col_table = st.columns([1, 2.5])  # 28% sidebar, 72% table

with col_sidebar:
    # Title with animated mode badge
    mode_color = "#10b981" if APP_MODE == "DEV" else "#f59e0b"
    mode_text = "DEV MODE" if APP_MODE == "DEV" else "⚠ PROD MODE"

    st.markdown(
        f"""
    <div style='display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.5rem;'>
        <h1 style='margin: 0; font-size: 1.75rem; color: white;'>
            <i class='ri-currency-line' style='color: #3b82f6;'></i>
            {APP_NAME}
        </h1>
        <span class='mode-badge' style='
            background: {mode_color};
            color: white;
            padding: 0.25rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            font-weight: 600;
            animation: fadeIn 0.5s ease-in;
        '>
            {mode_text}
        </span>
    </div>
    <a href='{AUTHOR_URL}' target='_blank' style='
        color: #94a3b8;
        font-size: 0.875rem;
        text-decoration: none;
        display: flex;
        align-items: center;
        gap: 0.25rem;
        margin-bottom: 1rem;
    '>
        <i class='ri-user-line'></i>
        {AUTHOR_NAME}
        <i class='ri-external-link-line' style='font-size: 0.75rem;'></i>
    </a>
    <style>
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: scale(0.9); }}
            to {{ opacity: 1; transform: scale(1); }}
        }}
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Phase and progress
    phase_name = phase.replace("PHASE_", "").replace("_", " ").title()
    progress_pct = min(1.0, runtime_elapsed / runtime_total) if runtime_total > 0 else 0

    st.markdown(
        f"""
    <div style='margin-bottom: 0.75rem;'>
        <div style='display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem;'>
            <i class='ri-pulse-line' style='color: #60a5fa;'></i>
            <span style='font-weight: 600; color: white;'>Phase: {phase_name}</span>
        </div>
        <div style='color: #94a3b8; font-size: 0.875rem; margin-bottom: 0.5rem;'>
            <i class='ri-time-line'></i> {runtime_elapsed}s / {runtime_total}s
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.progress(progress_pct)
    st.markdown(
        "<hr style='margin:1rem 0; border-color:#334155;'>", unsafe_allow_html=True
    )

    # Wallet section
    st.markdown(
        """
    <h2 style='margin:0 0 1rem 0; display:flex; align-items:center; gap:0.5rem; font-size:1.25rem;'>
        <i class='ri-wallet-line' style='color:#3b82f6;'></i>
        Wallet
    </h2>
    """,
        unsafe_allow_html=True,
    )

    # Wallet metrics - 2x2 grid
    row1_col1, row1_col2 = st.columns(2)
    row2_col1, row2_col2 = st.columns(2)

    with row1_col1:
        st.markdown(
            f"""
        <div class='metric-card' style='background:#1e293b; padding:1rem; border-radius:0.5rem; border:1px solid #334155; margin-bottom:0.5rem;'>
            <div style='color:#94a3b8; font-size:0.875rem; margin-bottom:0.25rem;'>Total</div>
            <div style='font-size:1.5rem; font-weight:700; color:white;'>${total:.2f}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with row1_col2:
        st.markdown(
            f"""
        <div class='metric-card' style='background:#1e293b; padding:1rem; border-radius:0.5rem; border:1px solid #334155; margin-bottom:0.5rem;'>
            <div style='color:#94a3b8; font-size:0.875rem; margin-bottom:0.25rem;'>Free</div>
            <div style='font-size:1.5rem; font-weight:700; color:white;'>${free:.2f}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with row2_col1:
        st.markdown(
            f"""
        <div class='metric-card' style='background:#1e293b; padding:1rem; border-radius:0.5rem; border:1px solid #334155; margin-bottom:0.5rem;'>
            <div style='color:#94a3b8; font-size:0.875rem; margin-bottom:0.25rem;'>Used</div>
            <div style='font-size:1.5rem; font-weight:700; color:white;'>${used:.2f}</div>
        </div>
        """,
            unsafe_allow_html=True,
        )

    with row2_col2:
        profit_color = "#10b981" if profit >= 0 else "#ef4444"
        profit_icon = "arrow-up" if profit >= 0 else "arrow-down"
        st.markdown(
            f"""
        <div class='metric-card' style='background:#1e293b; padding:1rem; border-radius:0.5rem; border:1px solid #334155; margin-bottom:0.5rem;'>
            <div style='color:#94a3b8; font-size:0.875rem; margin-bottom:0.25rem;'>Profit</div>
            <div style='font-size:1.5rem; font-weight:700; color:{profit_color}; display:flex; align-items:center; gap:0.25rem;'>
                <i class='ri-{profit_icon}-line'></i> ${profit:.4f}
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

with col_table:
    # Live trades table (full height on right side)
    st.markdown(
        """
    <h2 style='margin:0 0 1rem 0; display:flex; align-items:center; gap:0.5rem; font-size:1.25rem;'>
        <i class='ri-line-chart-line' style='color:#60a5fa;'></i>
        Live Trades
    </h2>
    """,
        unsafe_allow_html=True,
    )

    if not trades_history:
        st.info("⏳ Waiting for Phase 3 to start trading...")
    else:
        import pandas as pd

        # Reverse order - newest trades first
        df = pd.DataFrame(trades_history[::-1])

        # Style function
        def style_row(row):
            pnl_color = "#10b981" if row["pnl"] >= 0 else "#ef4444"
            status_bg = "#1e3a8a" if row["status"] == "OPEN" else "#374151"
            return [
                "color: #9ca3af",  # no
                "color: #d1d5db",  # time
                "color: white; font-weight: bold",  # coin
                "color: #d1d5db",  # entry_price
                "color: #d1d5db",  # amount
                f"background-color: {status_bg}; color: white; font-weight: bold",  # status
                f"color: {pnl_color}; font-weight: bold",  # pnl
            ]

        styled_df = df.style.apply(style_row, axis=1).format(
            {
                "entry_price": "${:.2f}",
                "amount": "${:.2f}",
                "pnl": lambda x: f"+${x:.4f}" if x >= 0 else f"-${abs(x):.4f}",
            }
        )

        st.dataframe(
            styled_df,
            width="stretch",
            height=400,  # Fixed height for scrollbar
            column_config={
                "no": st.column_config.NumberColumn("#", width="small"),
                "time": st.column_config.TextColumn("Time", width="small"),
                "coin": st.column_config.TextColumn("Coin", width="small"),
                "entry_price": st.column_config.NumberColumn("Entry"),
                "amount": st.column_config.NumberColumn("Amount"),
                "status": st.column_config.TextColumn("Status", width="small"),
                "pnl": st.column_config.NumberColumn("PnL"),
            },
            hide_index=True,
        )

        # Stats
        open_count = sum(1 for t in trades_history if t["status"] == "OPEN")
        closed_count = len(trades_history) - open_count
        st.caption(
            f"📊 Total: {len(trades_history)} | 🟢 Open: {open_count} | ⚫ Closed: {closed_count}"
        )
