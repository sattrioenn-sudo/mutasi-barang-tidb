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
        if st.button("LOGOUT"):
            st.session_state["logged_in"] = False
            st.rerun()
        
        st.markdown("---")
        with st.expander("➕ Tambah Transaksi", expanded=True):
            with st.form("input_form", clear_on_submit=True):
                sku_f = st.text_input("SKU")
                nama_f = st.text_input("Nama Barang")
                sat_f = st.selectbox("Satuan", ["Pcs", "Box", "Set", "Kg", "Ltr"])
                j_f = st.selectbox("Jenis", ["Masuk", "Keluar"])
                q_f = st.number_input("Qty", min_value=1)
                note_f = st.text_input("Ket")
                
                if st.form_submit_button("SIMPAN"):
                    tz = pytz.timezone('Asia/Jakarta')
                    now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    u = st.session_state['current_user']
                    full = f"{sku_f} | {nama_f} | {sat_f} | {u} | {u} | {note_f if note_f else '-'}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, j_f, q_f, now))
                    conn.commit(); conn.close()
                    st.rerun()

    # --- MAIN DASHBOARD ---
    st.markdown("<h1 style='color: white;'>Inventory Overview</h1>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # Data Processing
        parsed = df_raw['nama_barang'].apply(parse_inventory_name)
        df_raw['SKU'] = parsed.str[0]
        df_raw['Item Name'] = parsed.str[1]
        df_raw['Unit'] = parsed.str[2]
        df_raw['Keterangan'] = parsed.str[5]
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
        df_raw['Status'] = df_raw['jenis_mutasi'].apply(lambda x: "🟢 MASUK" if x == 'Masuk' else "🔴 KELUAR")

        # --- SECTION 1: RINGKASAN & PRINT LABEL ---
        st.markdown("### 📊 Ringkasan Stok & Cetak Label")
        stok_rekap = df_raw.groupby(['SKU', 'Item Name', 'Unit'])['adj'].sum().reset_index()
        stok_rekap.columns = ['SKU', 'Produk', 'Satuan', 'Sisa Stok']
        
        c1, c2 = st.columns([2, 1])
        with c1:
            st.dataframe(stok_rekap, use_container_width=True, hide_index=True)
        
        with c2:
            target_sku = st.selectbox("Pilih SKU untuk Label", ["-- Pilih --"] + list(stok_rekap['SKU']))
            if target_sku != "-- Pilih --":
                row = stok_rekap[stok_rekap['SKU'] == target_sku].iloc[0]
                st.markdown(f"""
                <div class="label-box">
                    <h2 style="margin:0; border-bottom:2px solid black;">{row['SKU']}</h2>
                    <p style="margin:10px 0; font-weight:bold; font-size:18px;">{row['Produk']}</p>
                    <small>SATUAN: {row['Satuan']} | STOCK: {row['Sisa Stok']}</small><br>
                    <div style="margin-top:10px; font-size:9px; color:gray;">INV-PRIME SYSTEM</div>
                </div>
                """, unsafe_allow_html=True)
                st.caption("Gunakan Snipping Tool (Win+Shift+S) untuk ambil gambar label.")

        st.markdown("---")

        # --- SECTION 2: LOG TRANSAKSI ---
        st.markdown("### 📜 Log Transaksi")
        df_display = df_raw.sort_values(by='tanggal', ascending=False)
        cols_show = ['id', 'Status', 'tanggal', 'SKU', 'Item Name', 'jumlah', 'Unit', 'Keterangan']
        
        st.dataframe(
            df_display[cols_show],
            use_container_width=True,
            hide_index=True,
            column_config={"tanggal": st.column_config.DatetimeColumn("Waktu", format="D MMM, HH:mm")}
        )
    else:
        st.info("Data
