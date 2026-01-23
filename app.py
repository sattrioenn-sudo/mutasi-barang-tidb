import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman
st.set_page_config(page_title="INV-PRIME PRO", page_icon="🚀", layout="wide")

# Tambahan: Inisialisasi daftar user di session state jika belum ada
if "user_db" not in st.session_state:
    # Mengambil user awal dari secrets sebagai database awal
    st.session_state["user_db"] = dict(st.secrets["auth_users"])

# --- CSS UI (Sama seperti sebelumnya) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #0f172a; }
    .metric-card {
        background: #1e293b; padding: 12px; border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-value { font-size: 1.5rem; font-weight: 700; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Database
def init_connection():
    return mysql.connector.connect(
        **st.secrets["tidb"],
        ssl_verify_cert=False, use_pure=True
    )

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def parse_inventory_name(val):
    parts = str(val).split('|'); parts = [p.strip() for p in parts]
    while len(parts) < 6: parts.append("-")
    return parts

# --- AUTH LOGIC ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:white;'>🚀 INV-PRIME PRO</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK", use_container_width=True):
                # Cek ke session_state user_db
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.rerun()
                else: st.error("Akses Ditolak")
else:
    # --- LOAD DATA ---
    try:
        conn = init_connection(); df_raw = pd.read_sql("SELECT * FROM inventory", conn); conn.close()
    except: df_raw = pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 🛡️ {st.session_state['current_user'].upper()}")
        st.markdown("---")
        start_date = st.date_input("📅 Mulai", datetime.now() - timedelta(days=7))
        end_date = st.date_input("📅 Akhir", datetime.now())
        st.markdown("---")
        
        # 1. MENU TRANSAKSI
        with st.expander("🛠️ Menu Transaksi"):
            mode = st.radio("Aksi:", ["Input", "Edit", "Hapus"])
            if mode == "Input":
                with st.form("f_add", clear_on_submit=True):
                    sk, nm, qt = st.text_input("SKU"), st.text_input("Nama"), st.number_input("Qty", 1)
                    jn, stn = st.selectbox("Jenis", ["Masuk", "Keluar"]), st.selectbox("Sat", ["Pcs", "Box", "Kg"])
                    if st.form_submit_button("Simpan"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | -"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                        conn.commit(); conn.close(); st.rerun()
            # (Logic Edit & Hapus tetap sama seperti kode sebelumnya)

        # 2. MENU SECURITY & USER (FITUR BARU)
        with st.expander("🔐 Security & Users"):
            st.write("Daftar User Aktif:")
            for usr in st.session_state["user_db"].keys():
                st.code(f"User: {usr}")
            
            st.markdown("---")
            st.write("➕ Tambah User Baru")
            new_u = st.text_input("New Username")
            new_p = st.text_input("New Password", type="password")
            if st.button("CREATE USER"):
                if new_u and new_p:
                    st.session_state["user_db"][new_u] = new_p
                    st.success(f"User {new_u} berhasil dibuat!")
                    st.info("Catatan: User ini aktif selama sesi aplikasi berjalan.")
                else:
                    st.warning("Isi username & password!")

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- MAIN CONTENT (Sama seperti kode sebelumnya untuk Dashboard & Chart) ---
    st.markdown("<h3 style='color:white;'>📊 Dashboard Overview</h3>", unsafe_allow_html=True)
    if not df_raw.empty:
        # (Semua logika pengolahan data & grafik tetap sama)
        st.write("Silakan lanjutkan pengelolaan inventaris Anda.")
        # ... [Sisa kode dashboard seperti sebelumnya] ...
    else:
        st.info("Database kosong.")
