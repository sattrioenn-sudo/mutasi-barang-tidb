import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import pytz

# 1. Konfigurasi Halaman
st.set_page_config(page_title="INV-PRIME PRO", page_icon="🚀", layout="wide")

# 2. CSS UI Design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 0% 0%, #0f172a 0%, #020617 100%); }
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid rgba(255, 255, 255, 0.05); }
    .stButton>button {
        background: linear-gradient(90deg, #38bdf8 0%, #2563eb 100%);
        color: white; border-radius: 8px; border: none; font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Fungsi Database
def init_connection():
    return mysql.connector.connect(
        host=st.secrets["tidb"]["host"],
        port=int(st.secrets["tidb"]["port"]),
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        ssl_verify_cert=False,
        use_pure=True
    )

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- UI LOGIN ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:white;'>🔐 INV-PRIME LOGIN</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                users = st.secrets["auth_users"]
                if u_input in users and str(p_input) == str(users[u_input]):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = u_input
                    st.rerun()
                else: st.error("Akses Ditolak")

else:
    def parse_inventory_name(val):
        parts = val.split('|')
        parts = [p.strip() for p in parts]
        while len(parts) < 6:
            parts.append("-")
        return parts

    # --- PRE-LOAD DATA MASTER UNTUK AUTO-FILL ---
    conn = init_connection()
    all_raw = pd.read_sql("SELECT nama_barang FROM inventory", conn); conn.close()
    
    sku_map = {}
    if not all_raw.empty:
        for entry in all_raw['nama_barang']:
            p = parse_inventory_name(entry)
            if p[0] != "-" and p[0] not in sku_map:
                sku_map[p[0]] = {"nama": p[1], "satuan": p[2]}
    
    sku_options = ["-- Ketik Baru --"] + sorted(list(sku_map.keys()))

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"**User Active:** `{st.session_state['current_user'].upper()}`")
        st.markdown("---")
        
        # 1. TAMBAH DATA (WITH AUTO-FILL)
        with st.expander("➕ Tambah Transaksi"):
            selected_sku = st.selectbox("Pilih SKU Eksis", sku_options)
            
            with st.form("input_form", clear_on_submit=True):
                if selected_sku == "-- Ketik Baru --":
                    sku_final = st.text_input("Input SKU Baru")
                    nama_final = st
