import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import pytz
import plotly.express as px

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="💎", layout="wide")

# --- PERBAIKAN: PERSISTENCE LOGIC ---
# Inisialisasi user_db agar tidak terhapus saat rerun
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Administrator", ["Dashboard", "Input", "Edit", "User Management"]]
    }

# --- UPGRADED CREATIVE CSS (CARBON NEON DESIGN) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'JetBrains Mono', monospace; }
    
    .stApp {
        background: #0a0a0c;
        background-image: 
            linear-gradient(rgba(56, 189, 248, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(56, 189, 248, 0.03) 1px, transparent 1px);
        background-size: 30px 30px;
    }

    /* Neon Glass Card */
    .glass-card {
        background: rgba(17, 25, 40, 0.75);
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px;
        backdrop-filter: blur(12px);
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.5);
        margin-bottom: 20px;
    }

    /* Cyberpunk Heading */
    .cyber-title {
        background: linear-gradient(90deg, #00f2fe, #4facfe);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 3px;
    }

    /* Custom Metric */
    .metric-vibe {
        border-left: 4px solid #38bdf8;
        padding-left: 15px;
        background: rgba(56, 189, 248, 0.05);
        border-radius: 0 10px 10px 0;
    }

    /* Sidebar Fix */
    section[data-testid="stSidebar"] {
        background-color: #050505 !important;
        border-right: 1px solid #1e293b;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Core Functions
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

def parse_detail(val):
    parts = [p.strip() for p in str(val).split('|')]
    while len(parts) < 6: parts.append("-")
    return parts

# --- AUTH LOGIC ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<br><br><div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.markdown("<h1 class='cyber-title'>Core System</h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Operator ID")
            p = st.text_input("Access Token", type="password")
            if st.form_submit_button("INITIALIZE SESSION", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({
                        "logged_in": True, 
                        "current_user": u, 
                        "user_role": st.session_state["user_db"][u][1], 
                        "user_perms": st.session_state["user_db"][u][2]
                    })
                    st.rerun()
                else:
                    st.error("Credential Mismatch")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- FETCH DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except:
        df_raw = pd.DataFrame()

    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1])
        df_raw['PIC'], df_raw['Note'] = p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- MENU NAVIGATION ---
    with st.sidebar:
        st.markdown(f"<h2 class='cyber-title'>{st.session_state['current_user']}</h2>", unsafe_allow_html=True)
        st.caption(f"Role: {st.session_state['user_role']}")
        st.markdown("---")
        nav_options = [opt for opt, perm in zip(["📊 Intelligence", "➕ Data Push", "🔧 Ledger Control", "👥 Access Hub"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in st.session_state["user_perms"]]
        menu = st.radio("SENSORY INPUT", nav_options)
        
        if st.button("TERMINATE SESSION", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- DASHBOARD ---
    if "Intelligence" in menu:
        st.markdown("<h1 class='cyber-title'>Operational Intelligence</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            stok_sum = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stock')
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='glass-card metric-vibe'><small>CURRENT BALANCE</small><h2>{int(stok_sum['Stock'].sum())}</h2></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='glass-card metric-vibe' style='border-color:#10b981'><small>INFLOW</small><h2>{int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='glass-card metric-vibe' style='border-color:#f43f5e'><small>OUTFLOW</small><h2>{int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)

            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            fig = px.bar(stok_sum, x='Item', y='Stock', color='Stock', color_continuous_scale='Blues', template="plotly_dark")
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- ACCESS HUB (MODUL PERBAIKAN) ---
    elif "Access Hub" in menu:
        st.markdown("<h1 class='cyber-title'>Identity Control Hub</h1>", unsafe_allow_html=True)
        
        l_col, r_col = st.columns([1.5, 1])
        
        with l_col:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("Authorized Personnel")
            # Tampilkan user_db dari session_state
            u_list = [{"User ID": k, "Rank": v[1], "Scope": " • ".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_list), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with r_col:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            mode = st.radio("Protocol", ["Add Operative", "Modify/Remove"], horizontal=True)
            
            with st.form("user_form"):
                if mode == "Add Operative":
                    u_id = st.text_input("New User ID")
                    u_pw = st.text_input("Secret Key", type="password")
                    u_rk = st.text_input("Rank/Role")
                else:
                    u_id = st.selectbox("Select Operative", [x for x in st.session_state["user_db"].keys() if x != 'admin'])
                    u_pw = st.text_input("New Key", value=st.session_state["user_db"][u_id][0] if u_id else "")
                    u_rk = st.text_input("New Rank", value=st.session_state["user_db"][u_id][1] if u_id else "")
                
                st.write("Access Permissions:")
                c1, c2 = st.columns(2)
                p_dash = c1.checkbox("Dashboard", value=True)
                p_in = c1.checkbox("Input", value=True)
                p_ed = c2.checkbox("Edit", value=False)
                p_um = c2.checkbox("User Management", value=False)
                
                btn_save, btn_del = st.columns(2)
                if btn_save.form_submit_button("SYNC TO SYSTEM", use_container_width=True):
                    perms = [p for p, v in zip(["Dashboard", "Input", "Edit", "User Management"], [p_dash, p_in, p_ed, p_um]) if v]
                    st.session_state["user_db"][u_id] = [u_pw, u_rk, perms]
                    st.success("Identity Synced")
                    st.rerun()
                
                if mode == "Modify/Remove" and btn_del.form_submit_button("PURGE ID", use_container_width=True):
                    if u_id != 'admin':
                        del st.session_state["user_db"][u_id]
                        st.warning("Identity Purged")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
