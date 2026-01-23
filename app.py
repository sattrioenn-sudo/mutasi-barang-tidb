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
    # --- FUNGSI PARSING DATA (SEKARANG 6 BAGIAN) ---
    def parse_inventory_name(val):
        parts = val.split('|')
        parts = [p.strip() for p in parts]
        # Urutan: 0:SKU, 1:Nama, 2:Satuan, 3:Creator, 4:Editor, 5:Catatan
        while len(parts) < 6:
            parts.append("-")
        return parts

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"**User Active:** `{st.session_state['current_user'].upper()}`")
        st.markdown("---")
        
        # 1. TAMBAH DATA
        with st.expander("➕ Tambah Transaksi"):
            with st.form("input_form", clear_on_submit=True):
                sku_in = st.text_input("SKU")
                nama_in = st.text_input("Nama Barang")
                sat_in = st.selectbox("Satuan", ["Pcs", "Box", "Set", "Kg", "Liter", "Meter"])
                j_in = st.selectbox("Aksi", ["Masuk", "Keluar"])
                q_in = st.number_input("Qty", min_value=1)
                note_in = st.text_input("Keterangan (Contoh: Retur, Rusak, dll)")
                
                if st.form_submit_button("SIMPAN DATA", use_container_width=True):
                    if nama_in:
                        tz = pytz.timezone('Asia/Jakarta')
                        now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        sku_f = sku_in if sku_in else "-"
                        user_now = st.session_state['current_user']
                        note_f = note_in if note_in else "-"
                        
                        # Gabungkan 6 bagian
                        full_entry = f"{sku_f} | {nama_in} | {sat_in} | {user_now} | {user_now} | {note_f}"
                        
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_entry, j_in, q_in, now))
                        conn.commit(); conn.close()
                        st.rerun()

        # 2. EDIT DATA
        with st.expander("📝 Edit Transaksi"):
            try:
                conn = init_connection()
                raw_data = pd.read_sql("SELECT id, nama_barang, jenis_mutasi, jumlah FROM inventory ORDER BY tanggal DESC", conn)
                conn.close()
                if not raw_data.empty:
                    selected_id = st.selectbox("Pilih ID Data:", raw_data['id'])
                    row_to_edit = raw_data[raw_data['id'] == selected_id].iloc[0]
                    p_old = parse_inventory_name(row_to_edit['nama_barang'])
                    
                    with st.form("edit_form"):
                        e_sku = st.text_input("SKU", value=p_old[0])
                        e_nama = st.text_input("Nama Barang", value=p_old[1])
                        e_sat = st.selectbox("Satuan", ["Pcs", "Box", "Set", "Kg", "Liter", "Meter"], 
                                           index=["Pcs", "Box", "Set", "Kg", "Liter", "Meter"].index(p_old[2]) if p_old[2] in ["Pcs", "Box", "Set", "Kg", "Liter", "Meter"] else 0)
                        e_aksi = st.selectbox("Aksi", ["Masuk", "Keluar"], index=0 if row_to_edit['jenis_mutasi'] == "Masuk" else 1)
                        e_qty = st.number_input("Qty", min_value=1, value=int(row_to_edit['jumlah']))
                        e_note = st.text_input("Keterangan", value=p_old[5])
                        
                        if st.form_submit_button("UPDATE DATA", use_container_width=True):
                            tz = pytz.timezone('Asia/Jakarta')
                            edit_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                            user_now = st.session_state['current_user']
                            
                            # Update: SKU | Nama | Satuan | Creator Asli | Editor Sekarang | Note Baru
                            new_entry = f"{e_sku} | {e_nama} | {e_sat} | {p_old[3]} | {user_now} | {e_note}"
                            
                            conn = init_connection(); cur = conn.cursor()
                            query = "UPDATE inventory SET nama_barang=%s, jenis_mutasi=%s, jumlah=%s, tanggal=%s WHERE id=%s"
                            cur.execute(query, (new_entry, e_aksi, e_qty, edit_time, int(selected_id)))
                            conn.commit(); conn.close()
                            st.rerun()
            except Exception as e: st.write(f"Error: {e}")

        if st.button("LOGOUT"):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- MAIN DASHBOARD ---
    st.markdown("<h1 style='color: white;'>Inventory Overview</h1>", unsafe_allow_html=True)
    
    try:
        conn = init_connection()
        df = pd.read_sql("SELECT id, nama_barang, jenis_mutasi, jumlah, tanggal FROM inventory ORDER BY tanggal DESC", conn); conn.close()

        if not df.empty:
            split_results = df['nama_barang'].apply(parse_inventory_name)
            df['SKU'] = split_results.str[0]
            df['Item Name'] = split_results.str[1]
            df['Unit'] = split_results.str[2]
            df['Input By'] = split_results.str[3]
            df['Edited By'] = split_results.str[4]
            df['Keterangan'] = split_results.str[5]
            
            df['tanggal'] = pd.to_datetime(df['tanggal'])
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            
            # --- TABEL RINGKASAN STOK (ALERT) ---
            st.markdown("### 📊 Ringkasan Stok (Alert < 5)")
            stok_df = df.groupby(['SKU', 'Item Name', 'Unit'])['adj'].sum().reset_index()
            stok_df.columns = ['SKU', 'Produk', 'Satuan', 'Sisa Stok']

            def color_low_stock(row):
                if row['Sisa Stok'] < 5:
                    return ['background-color: #991b1b; color: white; font-weight: bold'] * len(row)
                return [''] * len(row)

            st.dataframe(stok_df.style.apply(color_low_stock, axis=1), use_container_width=True, hide_index=True)

            st.write("---")

            # --- TABEL LOG DENGAN KOLOM KETERANGAN ---
            st.markdown("### 📜 Log Transaksi & Audit")
            st.dataframe(df[['id', 'tanggal', 'SKU', 'Item Name', 'Unit', 'Keterangan', 'Input By', 'Edited By', 'jenis_mutasi', 'jumlah']], 
                         use_container_width=True, hide_index=True,
                         column_config={
                             "id": "ID",
                             "tanggal": st.column_config.DatetimeColumn("Update", format="D MMM, HH:mm"),
                             "Keterangan": st.column_config.TextColumn("Keterangan", width="medium")
                         })
            
        else:
            st.info("Data kosong.")
    except Exception as e: st.error(f"Error: {e}")
