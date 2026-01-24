import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import pytz
import plotly.express as px

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="💎", layout="wide")

# FIX: Inisialisasi User agar tidak hilang saat navigasi
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Administrator", ["Dashboard", "Input", "Edit", "User Management"]]
    }

# --- UPGRADED CREATIVE CSS (NEON QUANTUM DESIGN) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    
    .stApp {
        background: #050505;
        background-image: 
            radial-gradient(circle at 20% 35%, rgba(56, 189, 248, 0.05) 0%, transparent 40%),
            radial-gradient(circle at 80% 10%, rgba(192, 132, 252, 0.05) 0%, transparent 40%);
    }

    /* Glassmorphism Card with Neon Border */
    .glass-card {
        background: rgba(255, 255, 255, 0.02);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
        backdrop-filter: blur(10px);
        transition: all 0.3s ease;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    
    .glass-card:hover {
        border: 1px solid rgba(56, 189, 248, 0.4);
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.1);
    }

    /* Shimmer Text with Animation */
    .shimmer-text {
        background: linear-gradient(to right, #38bdf8 20%, #818cf8 40%, #c084fc 60%, #38bdf8 80%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shine 4s linear infinite;
        font-weight: 800;
        letter-spacing: -1px;
    }
    
    @keyframes shine {
        to { background-position: 200% center; }
    }

    /* User Avatar Circle */
    .user-avatar {
        width: 50px;
        height: 50px;
        background: linear-gradient(45deg, #38bdf8, #c084fc);
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
        color: white;
        margin-bottom: 10px;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0a0a0a !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Clean Buttons */
    .stButton>button {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.05);
        color: white;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background: #38bdf8;
        color: black;
        border: none;
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
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='glass-card' style='text-align:center;'>", unsafe_allow_html=True)
        st.markdown("<h1 class='shimmer-text' style='font-size:3rem;'>SATRIO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#64748b;'>Enter System Credentials</p>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("UNLOCKED ACCESS", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2]})
                    st.rerun()
                else:
                    st.error("Access Denied: Invalid Signature")
        st.markdown("</div>", unsafe_allow_html=True)
else:
    # --- DATA ENGINE ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except:
        df_raw = pd.DataFrame()

    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1])
        df_raw['Unit'], df_raw['PIC'] = p_data.apply(lambda x: x[2]), p_data.apply(lambda x: x[3])
        df_raw['Note'], df_raw['tanggal'] = p_data.apply(lambda x: x[5]), pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<div class='user-avatar'>{st.session_state['current_user'][0].upper()}</div>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='margin:0;'>{st.session_state['current_user']}</h3>", unsafe_allow_html=True)
        st.caption(st.session_state["user_role"])
        st.markdown("<br>", unsafe_allow_html=True)
        
        nav_options = [opt for opt, perm in zip(["📊 Dashboard", "➕ Inbound", "🔧 System Control", "👥 Access Control"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in st.session_state["user_perms"]]
        menu = st.radio("SENSORY MENU", nav_options)
        
        if st.button("🚪 LOGOUT"):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- ROUTING ---
    if "Dashboard" in menu:
        st.markdown("<h1 class='shimmer-text'>Quantum Intelligence</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stock')
            m1, m2, m3 = st.columns(3)
            m1.markdown(f"<div class='glass-card'><small>TOTAL BALANCE</small><h2>{int(stok_summary['Stock'].sum())}</h2></div>", unsafe_allow_html=True)
            m2.markdown(f"<div class='glass-card'><small>INFLOW</small><h2 style='color:#10b981;'>{int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            m3.markdown(f"<div class='glass-card'><small>OUTFLOW</small><h2 style='color:#f43f5e;'>{int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            fig = px.area(df_raw.sort_values('tanggal'), x='tanggal', y='jumlah', color='jenis_mutasi', template="plotly_dark", color_discrete_sequence=["#38bdf8", "#f43f5e"])
            fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    elif "Access Control" in menu:
        st.markdown("<h1 class='shimmer-text'>Identity Governance</h1>", unsafe_allow_html=True)
        
        col_list, col_form = st.columns([1.5, 1])
        
        with col_list:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.subheader("Active Operatives")
            # Menampilkan data dari session_state
            u_data = [{"User": k, "Role": v[1], "Permissions": ", ".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.table(pd.DataFrame(u_data))
            st.markdown("</div>", unsafe_allow_html=True)
            
        with col_form:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            mode = st.radio("Operation", ["Create New", "Update/Delete"], horizontal=True)
            
            with st.form("user_manage_form"):
                if mode == "Create New":
                    new_u = st.text_input("Username ID")
                    new_p = st.text_input("Security Hash", type="password")
                    new_r = st.text_input("Operational Role")
                else:
                    target_u = st.selectbox("Select User", [u for u in st.session_state["user_db"].keys() if u != 'admin'])
                    new_p = st.text_input("New Hash", value=st.session_state["user_db"][target_u][0] if target_u else "")
                    new_r = st.text_input("New Role", value=st.session_state["user_db"][target_u][1] if target_u else "")
                    new_u = target_u
                
                st.write("Permissions Scope:")
                p_d = st.checkbox("Dashboard", value=True)
                p_i = st.checkbox("Input", value=True)
                p_e = st.checkbox("Edit", value=False)
                p_u = st.checkbox("User Management", value=False)
                
                save_btn, del_btn = st.columns(2)
                if save_btn.form_submit_button("SYNC USER"):
                    perms = [p for p, v in zip(["Dashboard", "Input", "Edit", "User Management"], [p_d, p_i, p_e, p_u]) if v]
                    st.session_state["user_db"][new_u] = [new_p, new_r, perms]
                    st.success(f"User {new_u} Authorized!")
                    st.rerun()
                
                if mode == "Update/Delete" and del_btn.form_submit_button("WIPE USER"):
                    del st.session_state["user_db"][new_u]
                    st.warning("User De-authorized")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # ... (Bagian Input dan Edit tetap sama secara fungsional, hanya styling mengikuti glass-card)
