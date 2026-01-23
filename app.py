import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman
st.set_page_config(page_title="INV-PRIME PRO ELITE", page_icon="🚀", layout="wide")

# 2. CSS UI Design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 0% 0%, #0f172a 0%, #020617 100%); }
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid rgba(255, 255, 255, 0.05); }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 1.5rem; border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }
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

# --- UTILS ---
def parse_inventory_name(val):
    parts = [p.strip() for p in str(val).split('|')]
    while len(parts) < 6: parts.append("-")
    return parts

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
    # --- PRE-LOAD DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory", conn)
        conn.close()
    except Exception as e:
        st.error(f"Database Error: {e}")
        st.stop()

    # --- DATA PROCESSING ---
    if not df_raw.empty:
        parsed = df_raw['nama_barang'].apply(parse_inventory_name)
        df_raw['SKU'] = parsed.str[0]
        df_raw['Item Name'] = parsed.str[1]
        df_raw['Unit'] = parsed.str[2]
        df_raw['Input By'] = parsed.str[3]
        df_raw['Edited By'] = parsed.str[4]
        df_raw['Keterangan'] = parsed.str[5]
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
        
        sku_map = {}
        for _, r in df_raw.iterrows():
            if r['SKU'] != "-" and r['SKU'] not in sku_map:
                sku_map[r['SKU']] = {"nama": r['Item Name'], "satuan": r['Unit']}
    else:
        sku_map = {}

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"👋 Halo, **{st.session_state['current_user'].upper()}**")
        st.markdown("---")
        
        # Form Input
        sku_options = ["-- Baru --"] + sorted(list(sku_map.keys()))
        with st.expander("📝 Transaksi Baru", expanded=False):
            selected_sku = st.selectbox("Cari SKU", sku_options)
            with st.form("input_form", clear_on_submit=True):
                if selected_sku == "-- Baru --":
                    sku_f = st.text_input("SKU Baru")
                    nama_f = st.text_input("Nama Barang")
                    sat_f = st.selectbox("Satuan", ["Pcs", "Box", "Set", "Kg", "Ltr", "Mtr"])
                else:
                    sku_f = selected_sku
                    nama_f = st.text_input("Nama Barang", value=sku_map[selected_sku]["nama"])
                    sat_f = st.selectbox("Satuan", ["Pcs", "Box", "Set", "Kg", "Ltr", "Mtr"], 
                                         index=["Pcs", "Box", "Set", "Kg", "Ltr", "Mtr"].index(sku_map[selected_sku]["satuan"]) if sku_map[selected_sku]["satuan"] in ["Pcs", "Box", "Set", "Kg", "Ltr", "Mtr"] else 0)
                
                j_in = st.selectbox("Tipe", ["Masuk", "Keluar"])
                q_in = st.number_input("Qty", min_value=1)
                note_in = st.text_input("Catatan")
                
                if st.form_submit_button("SIMPAN"):
                    tz = pytz.timezone('Asia/Jakarta')
                    now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    user = st.session_state['current_user']
                    full_entry = f"{sku_f} | {nama_f} | {sat_f} | {user} | {user} | {note_in if note_in else '-'}"
                    
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_entry, j_in, q_in, now))
                    conn.commit(); conn.close()
                    st.rerun()

        # Filter
        st.markdown("### 🔍 Filter")
        date_range = st.date_input("Rentang Tanggal", [datetime.now() - timedelta(days=30), datetime.now()])
        search_query = st.text_input("Cari Nama/SKU")
        
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- MAIN CONTENT ---
    if not df_raw.empty:
        # Filter Logic
        mask = (df_raw['tanggal'].dt.date >= date_range[0]) & (df_raw['tanggal'].dt.date <= date_range[1])
        if search_query:
            mask &= df_raw['Item Name'].str.contains(search_query, case=False) | df_raw['SKU'].str.contains(search_query, case=False)
        df_filtered = df_raw[mask]

        # 1. ANALYTICS ROW
        st.markdown("### 📈 Ringkasan Performa")
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(f"<div class='metric-card'><small>Total Stok Masuk</small><h2>{df_filtered[df_filtered['jenis_mutasi']=='Masuk']['jumlah'].sum():,.0f}</h2></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-card'><small>Total Stok Keluar</small><h2>{df_filtered[df_filtered['jenis_mutasi']=='Keluar']['jumlah'].sum():,.0f}</h2></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-card'><small>Item Unik Aktif</small><h2>{df_filtered['SKU'].nunique()}</h2></div>", unsafe_allow_html=True)
        with m4:
            net = df_filtered['adj'].sum()
            color = "#4ade80" if net >= 0 else "#f87171"
            st.markdown(f"<div class='metric-card'><small>Net Flow</small><h2 style='color:{color}'>{net:,.0f}</h2></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 2. STOCK TABLE
        st.markdown("### 📊 Status Inventaris Saat Ini")
        stok_rekap = df_raw.groupby(['SKU', 'Item Name', 'Unit'])['adj'].sum().reset_index()
        stok_rekap.columns = ['SKU', 'Produk', 'Satuan', 'Sisa Stok']
        
        def style_stock(v):
            if v < 0: return 'color: #f87171; font-weight: bold'
            if v < 10: return 'color: #fbbf24; font-weight: bold'
            return 'color: #4ade80'

        st.dataframe(
            stok_rekap.style.map(style_stock, subset=['Sisa Stok']),
            use_container_width=True, hide_index=True
        )

        # 3. TRANSACTION LOG
        st.markdown("### 📜 Riwayat Mutasi Detail")
        
        # Tambahkan kolom penanda visual
        df_display = df_filtered.copy().sort_values('tanggal', ascending=False)
        df_display['Status'] = df_display['jenis_mutasi'].apply(lambda x: "📥 MASUK" if x == "Masuk" else "📤 KELUAR")
        
        st.dataframe(
            df_display[['id', 'tanggal', 'Status', 'SKU', 'Item Name', 'jumlah', 'Unit', 'Keterangan', 'Input By', 'Edited By']],
            use_container_width=True,
            hide_index=True,
            column_config={
                "id": "ID",
                "tanggal": st.column_config.DatetimeColumn("Waktu", format="DD/MM/YY HH:mm"),
                "jumlah": st.column_config.NumberColumn("Qty", format="%d"),
            }
        )

        # 4. EXPORT
        st.markdown("---")
        col_down, _ = st.columns([1, 4])
        csv = df_filtered.to_csv(index=False).encode('utf-8')
        col_down.download_button("📥 Download Laporan (CSV)", data=csv, file_name=f"report_{datetime.now().strftime('%Y%m%d')}.csv", mime='text/csv')

    else:
        st.info("Belum ada data transaksi tersimpan.")
