import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
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
    .label-box {
        background: white; color: black; padding: 20px; border-radius: 5px; 
        border: 2px dashed #333; text-align: center; font-family: monospace;
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
    parts = str(val).split('|')
    parts = [p.strip() for p in parts]
    while len(parts) < 6:
        parts.append("-")
    return parts

# --- LOGIN ---
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
    # --- DATA ENGINE ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT id, nama_barang, jenis_mutasi, jumlah, tanggal FROM inventory", conn)
        conn.close()
    except Exception as e:
        st.error(f"Error Database: {e}")
        df_raw = pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"**User Active:** `{st.session_state['current_user'].upper()}`")
        
        # --- FITUR BARU: FILTER PERIODE ---
        st.markdown("---")
        st.markdown("### 🔍 Filter Periode")
        today = datetime.now()
        start_date = st.date_input("Tanggal Mulai", today - timedelta(days=30))
        end_date = st.date_input("Tanggal Akhir", today)
        
        st.markdown("---")
        
        # 1. TAMBAH DATA
        with st.expander("➕ Tambah Transaksi"):
            with st.form("input_form", clear_on_submit=True):
                sku_f = st.text_input("SKU")
                nama_f = st.text_input("Nama Barang")
                sat_f = st.selectbox("Satuan", ["Pcs", "Box", "Set", "Kg", "Ltr"])
                j_f = st.selectbox("Jenis", ["Masuk", "Keluar"])
                q_f = st.number_input("Qty", min_value=1)
                note_f = st.text_input("Ket")
                if st.form_submit_button("SIMPAN DATA", use_container_width=True):
                    if sku_f and nama_f:
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        u = st.session_state['current_user']
                        full = f"{sku_f} | {nama_f} | {sat_f} | {u} | {u} | {note_f if note_f else '-'}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, j_f, q_f, now))
                        conn.commit(); conn.close(); st.rerun()

        # 2. EDIT DATA
        with st.expander("📝 Edit Transaksi"):
            if not df_raw.empty:
                edit_id = st.selectbox("ID Edit", df_raw['id'].sort_values(ascending=False))
                row_edit = df_raw[df_raw['id'] == edit_id].iloc[0]
                p_old = parse_inventory_name(row_edit['nama_barang'])
                with st.form("edit_form"):
                    e_sku = st.text_input("SKU", value=p_old[0])
                    e_nama = st.text_input("Nama", value=p_old[1])
                    e_qty = st.number_input("Qty", value=int(row_edit['jumlah']))
                    e_note = st.text_input("Ket", value=p_old[5])
                    if st.form_submit_button("UPDATE"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        u = st.session_state['current_user']
                        full_upd = f"{e_sku} | {e_nama} | {p_old[2]} | {p_old[3]} | {u} | {e_note}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, e_qty, now, int(edit_id)))
                        conn.commit(); conn.close(); st.rerun()

        # 3. HAPUS DATA
        with st.expander("🗑️ Hapus Transaksi"):
            if not df_raw.empty:
                del_id = st.selectbox("ID Hapus", df_raw['id'].sort_values(ascending=False))
                if st.button("KONFIRMASI HAPUS"):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(del_id),))
                    conn.commit(); conn.close(); st.rerun()

        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- DASHBOARD UTAMA ---
    st.markdown("<h1 style='color: white;'>Inventory Overview</h1>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # Pre-processing Data
        parsed = df_raw['nama_barang'].apply(parse_inventory_name)
        df_raw['SKU'] = parsed.str[0]; df_raw['Item Name'] = parsed.str[1]
        df_raw['Unit'] = parsed.str[2]; df_raw['Keterangan'] = parsed.str[5]
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        
        # --- LOGIKA FILTER PERIODE ---
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_filtered = df_raw.loc[mask].copy()

        if not df_filtered.empty:
            df_filtered['adj'] = df_filtered.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            df_filtered['Status'] = df_filtered['jenis_mutasi'].apply(lambda x: "🟢 MASUK" if x == 'Masuk' else "🔴 KELUAR")

            # Section: Stok & Label
            st.markdown(f"### 📊 Stok Periode: {start_date.strftime('%d/%m/%y')} - {end_date.strftime('%d/%m/%y')}")
            stok_rekap = df_filtered.groupby(['SKU', 'Item Name', 'Unit'])['adj'].sum().reset_index()
            stok_rekap.columns = ['SKU', 'Produk', 'Satuan', 'Sisa Stok']
            
            c1, c2 = st.columns([2, 1])
            with c1:
                st.dataframe(stok_rekap, use_container_width=True, hide_index=True)
            with c2:
                t_sku = st.selectbox("Cetak Label SKU", ["-- Pilih --"] + list(stok_rekap['SKU']))
                if t_sku != "-- Pilih --":
                    r_l = stok_rekap[stok_rekap['SKU'] == t_sku].iloc[0]
                    st.markdown(f'<div class="label-box"><h2>{r_l["SKU"]}</h2><p><b>{r_l["Produk"]}</b></p><small>{r_l["Satuan"]} | STOK: {r_l["Sisa Stok"]}</small></div>', unsafe_allow_html=True)

            # Section: Log
            st.markdown("### 📜 Log Transaksi Periode Ini")
            df_display = df_filtered.sort_values(by='tanggal', ascending=False)
            st.dataframe(df_display[['id', 'Status', 'tanggal', 'SKU', 'Item Name', 'jumlah', 'Unit', 'Keterangan']], 
                         use_container_width=True, hide_index=True,
                         column_config={"tanggal": st.column_config.DatetimeColumn("Waktu", format="D MMM, HH:mm")})
        else:
            st.warning(f"Tidak ada data ditemukan pada periode {start_date} hingga {end_date}")
    else:
        st.info("Belum ada data di database.")
