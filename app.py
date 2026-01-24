import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="INV-PRIME PRO RETAIL", page_icon="🛍️", layout="wide")

# Inisialisasi User di Session agar bisa ditambah/hapus tanpa ubah database/secrets
if "user_db" not in st.session_state:
    st.session_state["user_db"] = dict(st.secrets["auth_users"])

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #0f172a; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px; border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-value { font-size: 2rem; font-weight: 800; margin-top: 10px; color: #f8fafc; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Utama
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

def parse_detail(val):
    parts = [p.strip() for p in str(val).split('|')]
    while len(parts) < 6: parts.append("-")
    return parts

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- AUTH SYSTEM ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 style='color:white;'>PRIME-POS</h1></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK KE SISTEM", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.rerun()
                else: st.error("Akses Ditolak")
else:
    # --- LOAD DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    # --- SIDEBAR CONTROL PANEL ---
    with st.sidebar:
        st.markdown(f"### 📦 TOKO: {st.session_state['current_user'].upper()}")
        st.markdown("---")
        
        search_query = st.text_input("🔍 Cari Barang/SKU", "")
        start_date = st.date_input("📅 Mulai", datetime.now() - timedelta(days=30))
        end_date = st.date_input("📅 Akhir", datetime.now())
        
        with st.expander("📝 Transaksi Baru"):
            with st.form("f_add", clear_on_submit=True):
                sk, nm = st.text_input("SKU"), st.text_input("Nama Produk")
                qt = st.number_input("Jumlah", 1)
                jn = st.selectbox("Aksi", ["Masuk", "Keluar"])
                stn = st.selectbox("Satuan", ["Pcs", "Box", "Pack", "Kg"])
                ket = st.text_input("Catatan", value="-")
                if st.form_submit_button("Proses"):
                    tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ket}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                    conn.commit(); conn.close(); st.rerun()

        # --- MENU PENGATURAN & USER (DIPERLENGKAP Tanpa Ubah Database) ---
        with st.expander("⚙️ Pengaturan & User"):
            st.markdown("#### Daftar Akses")
            # Tampilkan tabel User & Password agar admin tahu kredensialnya
            df_users = pd.DataFrame(list(st.session_state["user_db"].items()), columns=['Username', 'Password'])
            st.dataframe(df_users, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.markdown("#### Tambah User")
            new_u = st.text_input("User Baru", key="new_u")
            new_p = st.text_input("Pass Baru", key="new_p")
            if st.button("Simpan User Baru", use_container_width=True):
                if new_u and new_p:
                    st.session_state["user_db"][new_u] = new_p
                    st.success(f"User {new_u} berhasil ditambah!")
                    st.rerun()
            
            st.markdown("---")
            st.markdown("#### Hapus User")
            # Ambil list user kecuali admin yang sedang login (biar nggak hapus diri sendiri)
            list_user = [u for u in st.session_state["user_db"].keys() if u != st.session_state["current_user"]]
            user_to_del = st.selectbox("Pilih User", ["-"] + list_user)
            if st.button("Hapus User Terpilih", use_container_width=True):
                if user_to_del != "-":
                    del st.session_state["user_db"][user_to_del]
                    st.warning(f"User {user_to_del} telah dihapus!")
                    st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD CONTENT ---
    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'], df_raw['Ket'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        if search_query:
            mask = mask & (df_raw['Item'].str.contains(search_query, case=False) | df_raw['SKU'].str.contains(search_query, case=False))
        
        df_f = df_raw.loc[mask].copy()

        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><div class='metric-label'>TOTAL MASUK</div><div class='metric-value'>{int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum())}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-label'>TOTAL KELUAR</div><div class='metric-value'>{int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum())}</div></div>", unsafe_allow_html=True)
        stok_f = df_raw.groupby(['SKU', 'Item'])['adj'].sum().reset_index(name='Saldo')
        c3.markdown(f"<div class='metric-card'><div class='metric-label'>PRODUK AKTIF</div><div class='metric-value'>{len(stok_f)}</div></div>", unsafe_allow_html=True)

        st.markdown("### 📋 Tabel Stok & Log")
        t1, t2 = st.tabs(["Stok Saat Ini", "Histori Transaksi"])
        with t1:
            st.dataframe(stok_f, use_container_width=True, hide_index=True)
        with t2:
            st.dataframe(df_f[['tanggal', 'SKU', 'Item', 'jenis_mutasi', 'jumlah', 'Ket']], use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data transaksi.")
