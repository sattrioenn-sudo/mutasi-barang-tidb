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
    .metric-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 16px; text-align: center; margin-bottom: 10px;
    }
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
    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"**User Active:** `{st.session_state['current_user'].upper()}`")
        st.markdown("---")
        
        with st.expander("➕ Tambah Transaksi", expanded=True):
            with st.form("input_form", clear_on_submit=True):
                sku_in = st.text_input("SKU (Kode Barang)")
                nama_in = st.text_input("Nama Barang (Item Name)")
                sat_in = st.selectbox("Satuan (Unit)", ["Pcs", "Box", "Set", "Kg", "Liter", "Meter"])
                j_in = st.selectbox("Aksi", ["Masuk", "Keluar"])
                q_in = st.number_input("Qty", min_value=1)
                
                if st.form_submit_button("SIMPAN DATA", use_container_width=True):
                    if nama_in:
                        tz = pytz.timezone('Asia/Jakarta')
                        now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        user = st.session_state['current_user']
                        
                        # FORMAT PENYIMPANAN: SKU | NAMA | SATUAN | USER
                        sku_final = sku_in if sku_in else "-"
                        full_entry = f"{sku_final} | {nama_in} | {sat_in} | {user}"
                        
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_entry, j_in, q_in, now))
                        conn.commit(); conn.close()
                        st.rerun()

        with st.expander("🗑️ Hapus Data"):
            try:
                conn = init_connection()
                items = pd.read_sql("SELECT DISTINCT nama_barang FROM inventory", conn); conn.close()
                target = st.selectbox("Pilih Data Untuk Dihapus:", items['nama_barang'])
                if st.button("HAPUS PERMANEN", use_container_width=True):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE nama_barang = %s", (target,))
                    conn.commit(); conn.close()
                    st.rerun()
            except: pass

        if st.button("LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- MAIN DASHBOARD ---
    st.markdown("<h1 style='color: white;'>Inventory Overview</h1>", unsafe_allow_html=True)
    
    try:
