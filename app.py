import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="RETAIL-SATRIO PRO", page_icon="🛍️", layout="wide")

# Inisialisasi User
if "user_db" not in st.session_state:
    st.session_state["user_db"] = dict(st.secrets["auth_users"])

# CSS Custom untuk Tampilan Mewah
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0f172a; }
    .metric-card {
        background: #1e293b; padding: 24px; border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .metric-label { color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #f8fafc; font-size: 2.2rem; font-weight: 700; margin: 8px 0; }
    section[data-testid="stSidebar"] { background-color: #1e293b !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] { 
        background-color: #1e293b; border-radius: 8px 8px 0 0; padding: 10px 20px; color: #94a3b8;
    }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: white !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Core
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

def parse_detail(val):
    parts = [p.strip() for p in str(val).split('|')]
    while len(parts) < 6: parts.append("-")
    return parts

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- AUTH LOGIC ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h1 style='color: white; text-align: center;'>SATRIO <span style='color: #38bdf8;'>POS</span></h1>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
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

    # --- SIDEBAR NAV ---
    with st.sidebar:
        st.markdown(f"### 👤 {st.session_state['current_user'].upper()}")
        st.markdown("---")
        menu = st.selectbox("MENU UTAMA", ["🏠 Dashboard", "📦 Manajemen Barang", "👥 Kelola User"])
        st.markdown("---")
        start_date = st.date_input("Mulai", datetime.now() - timedelta(days=30))
        end_date = st.date_input("Akhir", datetime.now())
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DATA PROCESSING ---
    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'], df_raw['Pembuat'], df_raw['Editor'], df_raw['Ket'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2]), p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[4]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_f = df_raw.loc[mask].copy()

    # --- UI LOGIC ---
    if menu == "🏠 Dashboard":
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f"<div class='metric-card'><div class='metric-label'>Masuk</div><div class='metric-value'>{int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum()) if not df_raw.empty else 0}</div></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div class='metric-card'><div class='metric-label'>Keluar</div><div class='metric-value' style='color:#f87171;'>{int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum()) if not df_raw.empty else 0}</div></div>", unsafe_allow_html=True)
        stok_skr = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Stok') if not df_raw.empty else pd.DataFrame()
        with c3: st.markdown(f"<div class='metric-card'><div class='metric-label'>Produk</div><div class='metric-value' style='color:#fbbf24;'>{len(stok_skr)}</div></div>", unsafe_allow_html=True)
        
        t1, t2, t3 = st.tabs(["📊 Stok", "📜 Log", "📈 Tren"])
        with t1: st.dataframe(stok_skr, use_container_width=True, hide_index=True)
        with t2: st.dataframe(df_f[['id', 'tanggal', 'SKU', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Pembuat', 'Ket']], use_container_width=True, hide_index=True)
        with t3: 
            if not df_f.empty: st.area_chart(df_f.groupby([df_f['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0))

    elif menu == "📦 Manajemen Barang":
        st.markdown("<h2 style='color:white;'>📦 Manajemen Persediaan</h2>", unsafe_allow_html=True)
        tab_in, tab_ed, tab_del = st.tabs(["➕ Input Baru", "✏️ Edit Transaksi", "🗑️ Hapus Data"])
        
        with tab_in:
            with st.form("f_add", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1: sk, nm, qt = st.text_input("SKU"), st.text_input("Nama"), st.number_input("Qty", 1)
                with c2: jn, stn, ke = st.selectbox("Jenis", ["Masuk", "Keluar"]), st.selectbox("Satuan", ["Pcs", "Box", "Kg"]), st.text_input("Ket", "-")
                if st.form_submit_button("SIMPAN TRANSAKSI", use_container_width=True):
                    tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ke}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                    conn.commit(); conn.close(); st.success("Berhasil!"); st.rerun()

        with tab_ed:
            if not df_raw.empty:
                df_raw['search'] = df_raw.apply(lambda x: f"ID {x['id']} - {x['Item']} ({x['tanggal'].strftime('%d/%m')})", axis=1)
                pilih = st.selectbox("Cari Transaksi untuk Diubah:", df_raw['search'])
                id_edit = int(pilih.split(' ')[1])
                row = df_raw[df_raw['id'] == id_edit].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("f_edit"):
                    e_nm = st.text_input("Nama Produk", value=p[1])
                    e_qt = st.number_input("Jumlah", value=int(row['jumlah']))
                    e_st = st.selectbox("Satuan", ["Pcs", "Box", "Kg"], index=0)
                    e_ke = st.text_input("Keterangan", value=p[5])
                    if st.form_submit_button("UPDATE DATA", use_container_width=True):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full_upd = f"{p[0]} | {e_nm} | {e_st} | {p[3]} | {st.session_state['current_user']} | {e_ke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, e_qt, now, id_edit))
                        conn.commit(); conn.close(); st.success("Terupdate!"); st.rerun()
            else: st.info("Kosong")

        with tab_del:
            if not df_raw.empty:
                id_del = st.selectbox("Pilih ID untuk Dihapus:", df_raw['id'])
                confirm = st.checkbox("Konfirmasi: Saya sadar data ini akan hilang permanen.")
                if st.button("🔴 HAPUS DATA", use_container_width=True, disabled=not confirm):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(id_del),))
                    conn.commit(); conn.close(); st.warning("Terhapus!"); st.rerun()

    elif menu == "👥 Kelola User":
        st.markdown("<h2 style='color:white;'>👥 Manajemen Akses</h2>", unsafe_allow_html=True)
        t_list, t_add = st.tabs(["📋 Daftar User", "➕ Tambah/Hapus"])
        with t_list: st.table(pd.DataFrame(list(st.session_state["user_db"].items()), columns=['Username', 'Password']))
        with t_add:
            c1, c2 = st.columns(2)
            with c1:
                nu, np = st.text_input("User Baru"), st.text_input("Pass Baru", type="password")
                if st.button("Simpan User"): 
                    st.session_state["user_db"][nu] = np; st.success("User ditambahkan"); st.rerun()
            with c2:
                u_rem = st.selectbox("Hapus User:", ["-"] + [u for u in st.session_state["user_db"].keys() if u != st.session_state["current_user"]])
                if st.button("Hapus") and u_rem != "-": 
                    del st.session_state["user_db"][u_rem]; st.warning("User dihapus"); st.rerun()
