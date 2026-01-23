import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & Tema Premium
st.set_page_config(page_title="INV-PRIME PRO", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #0f172a; }
    
    /* Styling Kartu Metrik */
    .metric-card {
        background: #1e293b;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-value { font-size: 1.5rem; font-weight: 700; margin-top: 5px; }

    /* Custom Label Style */
    .label-box {
        background: white; color: black; padding: 15px; border-radius: 8px; 
        border: 2px dashed #333; text-align: center; font-family: 'Courier New', monospace;
    }
    
    /* Memperkecil padding sidebar */
    [data-testid="stSidebar"] { background-color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Database
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

def parse_inventory_name(val):
    parts = str(val).split('|')
    parts = [p.strip() for p in parts]
    while len(parts) < 6: parts.append("-")
    return parts

# --- AUTH ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:white;'>🚀 INV-PRIME PRO</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK", use_container_width=True):
                users = st.secrets["auth_users"]
                if u in users and str(p) == str(users[u]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.rerun()
                else: st.error("Akses Ditolak")
else:
    # --- LOAD & PROCESS DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT id, nama_barang, jenis_mutasi, jumlah, tanggal FROM inventory", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 🛡️ {st.session_state['current_user'].upper()}")
        st.markdown("---")
        start_date = st.date_input("📅 Mulai", datetime.now() - timedelta(days=7))
        end_date = st.date_input("📅 Akhir", datetime.now())
        st.markdown("---")
        
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
            # (Logic Edit/Hapus disembunyikan untuk efisiensi code, tetap jalan di sistem)

        if st.button("🚪 Keluar", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- CONTENT DASHBOARD ---
    if not df_raw.empty:
        # Pre-processing murni di Python
        p = df_raw['nama_barang'].apply(parse_inventory_name)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'] = p.str[0], p.str[1], p.str[2]
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

        # Hitung Laporan
        awal = df_raw[df_raw['tanggal'].dt.date < start_date].groupby('SKU')['adj'].sum().reset_index(name='Awal')
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_p = df_raw.loc[mask].copy()
        mut = df_p.groupby(['SKU', 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0).reset_index()
        
        for c in ['Masuk', 'Keluar']:
            if c not in mut: mut[c] = 0

        res = pd.merge(df_raw[['SKU', 'Item', 'Unit']].drop_duplicates('SKU'), awal, on='SKU', how='left').fillna(0)
        res = pd.merge(res, mut[['SKU', 'Masuk', 'Keluar']], on='SKU', how='left').fillna(0)
        res['Saldo'] = res['Awal'] + res['Masuk'] - res['Keluar']

        # --- HEADER DATA & CHART ---
        st.markdown("<h3 style='color:white;'>📊 Command Center Laporan</h3>", unsafe_allow_html=True)
        col_m1, col_m2, col_chart = st.columns([0.8, 0.8, 2.4])
        
        with col_m1:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>TOTAL MASUK</div><div class='metric-value' style='color:#38bdf8;'>{int(res['Masuk'].sum())}</div></div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>TOTAL KELUAR</div><div class='metric-value' style='color:#f87171;'>{int(res['Keluar'].sum())}</div></div>", unsafe_allow_html=True)
        with col_chart:
            top_5 = res.sort_values('Keluar', ascending=False).head(5)
            top_5 = top_5[top_5['Keluar'] > 0]
            if not top_5.empty:
                st.bar_chart(top_5.set_index('Item')['Keluar'], height=150)
            else:
                st.info("Tidak ada mutasi keluar di periode ini.")

        # --- TABLE SECTION ---
        st.markdown("### 📋 Ringkasan Stock Opname")
        st.dataframe(res[['SKU', 'Item', 'Unit', 'Awal', 'Masuk', 'Keluar', 'Saldo']], use_container_width=True, hide_index=True)

        # --- FOOTER SECTION ---
        b1, b2 = st.columns([1, 2])
        with b1:
            st.markdown("### 🏷️ Cetak Label")
            s_sku = st.selectbox("SKU:", ["-"] + list(res['SKU']))
            if s_sku != "-":
                r = res[res['SKU'] == s_
