import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import io

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="INV-PRIME PRO RETAIL", page_icon="🛍️", layout="wide")

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
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        text-align: center;
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; letter-spacing: 1px; }
    .metric-value { font-size: 2rem; font-weight: 800; margin-top: 10px; color: #f8fafc; }
    .low-stock { background-color: #7f1d1d; color: white; padding: 2px 8px; border-radius: 4px; font-weight: bold; }
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
        st.markdown("<div style='text-align:center;'><h1 style='color:white; margin-bottom:0;'>PRIME-POS</h1><p style='color:#64748b;'>Retail Inventory Management System</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK KE SISTEM", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.rerun()
                else: st.error("Akses Ditolak: Kredensial Salah")
else:
    # --- LOAD & PREPARE DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    # --- SIDEBAR CONTROL PANEL ---
    with st.sidebar:
        st.markdown(f"### 📦 TOKO: {st.session_state['current_user'].upper()}")
        st.markdown("---")
        
        # Penambahan Filter Pencarian Global
        search_query = st.text_input("🔍 Cari Barang/SKU", "")
        
        start_date = st.date_input("📅 Laporan Mulai", datetime.now() - timedelta(days=30))
        end_date = st.date_input("📅 Laporan Akhir", datetime.now())
        
        with st.expander("📝 Transaksi Baru"):
            with st.form("f_add", clear_on_submit=True):
                sk, nm = st.text_input("SKU / Kode"), st.text_input("Nama Produk")
                qt = st.number_input("Jumlah", 1)
                jn = st.selectbox("Aksi", ["Masuk", "Keluar"])
                stn = st.selectbox("Satuan", ["Pcs", "Box", "Pack", "Kg", "Ltr"])
                ket = st.text_input("Catatan/Supplier", value="-")
                if st.form_submit_button("Proses Transaksi"):
                    tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ket}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                    conn.commit(); conn.close(); st.rerun()

        with st.expander("⚙️ Pengaturan & User"):
            # Fitur Lihat User tetap ada
            st.write("User Aktif:")
            st.json(st.session_state["user_db"])
            if st.button("Logout", use_container_width=True):
                st.session_state["logged_in"] = False; st.rerun()

    # --- MAIN DASHBOARD ---
    if not df_raw.empty:
        # Parsing data detail
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'] = p_data.apply(lambda x: x[0])
        df_raw['Item'] = p_data.apply(lambda x: x[1])
        df_raw['Unit'] = p_data.apply(lambda x: x[2])
        df_raw['Ket'] = p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

        # Filter Berdasarkan Tanggal & Search
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        if search_query:
            mask = mask & (df_raw['Item'].str.contains(search_query, case=False) | df_raw['SKU'].str.contains(search_query, case=False))
        
        df_filtered = df_raw.loc[mask].copy()

        # Dashboard Metrics
        c1, c2, c3, c4 = st.columns(4)
        total_items = df_raw['SKU'].nunique()
        total_in = df_filtered[df_filtered['jenis_mutasi'] == 'Masuk']['jumlah'].sum()
        total_out = df_filtered[df_filtered['jenis_mutasi'] == 'Keluar']['jumlah'].sum()
        
        c1.markdown(f"<div class='metric-card'><div class='metric-label'>JENIS BARANG</div><div class='metric-value'>{total_items}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-label'>BARANG MASUK</div><div class='metric-value' style='color:#38bdf8;'>{int(total_in)}</div></div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='metric-card'><div class='metric-label'>BARANG KELUAR</div><div class='metric-value' style='color:#f87171;'>{int(total_out)}</div></div>", unsafe_allow_html=True)
        
        # Kalkulasi Stok Saat Ini
        stok_final = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Saldo')
        stok_tipis = stok_final[stok_final['Saldo'] < 5].shape[0] # Contoh alert stok < 5
        c4.markdown(f"<div class='metric-card'><div class='metric-label'>STOK TIPIS</div><div class='metric-value' style='color:#fbbf24;'>{stok_tipis}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Main Tabs
        tab1, tab2, tab3 = st.tabs(["📋 Inventori & Stok", "📜 Histori Transaksi", "📈 Analisis"])

        with tab1:
            st.markdown("### Daftar Inventori Aktif")
            # Menampilkan saldo dengan kondisi warna jika stok tipis
            def color_stock(val):
                color = '#f87171' if val < 5 else '#34d399'
                return f'color: {color}; font-weight: bold'
            
            st.dataframe(stok_final.style.applymap(color_stock, subset=['Saldo']), use_container_width=True, hide_index=True)
            
            # Export Button
            csv = stok_final.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Laporan Stok (CSV)", csv, "Laporan_Stok.csv", "text/csv")

        with tab2:
            st.markdown("### Log Transaksi Toko")
            st.dataframe(df_filtered[['tanggal', 'SKU', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Ket']], use_container_width=True, hide_index=True)

        with tab3:
            st.markdown("### Grafik Pergerakan Barang")
            if not df_filtered.empty:
                chart_data = df_filtered.groupby(['tanggal', 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0)
                st.line_chart(chart_data)
            else:
                st.info("Data tidak cukup untuk grafik.")

    else:
        st.info("Toko baru? Silakan masukkan barang pertama di sidebar!")
