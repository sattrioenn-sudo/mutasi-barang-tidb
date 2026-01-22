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
    # --- FUNGSI PARSING DATA ---
    def parse_inventory_name(val):
        parts = val.split('|')
        parts = [p.strip() for p in parts]
        while len(parts) < 4:
            parts.append("-")
        return parts

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"**User Active:** `{st.session_state['current_user'].upper()}`")
        st.markdown("---")
        
        # 1. TAMBAH TRANSAKSI
        with st.expander("➕ Tambah Transaksi"):
            with st.form("input_form", clear_on_submit=True):
                sku_in = st.text_input("SKU")
                nama_in = st.text_input("Nama Barang")
                sat_in = st.selectbox("Satuan", ["Pcs", "Box", "Set", "Kg", "Liter", "Meter"])
                j_in = st.selectbox("Aksi", ["Masuk", "Keluar"])
                q_in = st.number_input("Qty", min_value=1)
                
                if st.form_submit_button("SIMPAN DATA", use_container_width=True):
                    if nama_in:
                        tz = pytz.timezone('Asia/Jakarta')
                        now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        sku_final = sku_in if sku_in else "-"
                        full_entry = f"{sku_final} | {nama_in} | {sat_in} | {st.session_state['current_user']}"
                        
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_entry, j_in, q_in, now))
                        conn.commit(); conn.close()
                        st.rerun()

        # 2. EDIT TRANSAKSI (FITUR BARU)
        with st.expander("📝 Edit Transaksi"):
            try:
                conn = init_connection()
                # Kita ambil data ID dan Nama Barang mentah untuk pilihan
                raw_data = pd.read_sql("SELECT id, nama_barang, jenis_mutasi, jumlah FROM inventory ORDER BY tanggal DESC", conn)
                conn.close()
                
                if not raw_data.empty:
                    selected_id = st.selectbox("Pilih Data (Berdasarkan ID):", raw_data['id'])
                    # Ambil data spesifik yang mau diedit
                    row_to_edit = raw_data[raw_data['id'] == selected_id].iloc[0]
                    p_old = parse_inventory_name(row_to_edit['nama_barang'])
                    
                    with st.form("edit_form"):
                        e_sku = st.text_input("Edit SKU", value=p_old[0])
                        e_nama = st.text_input("Edit Nama", value=p_old[1])
                        e_sat = st.selectbox("Edit Satuan", ["Pcs", "Box", "Set", "Kg", "Liter", "Meter"], index=["Pcs", "Box", "Set", "Kg", "Liter", "Meter"].index(p_old[2]) if p_old[2] in ["Pcs", "Box", "Set", "Kg", "Liter", "Meter"] else 0)
                        e_aksi = st.selectbox("Edit Aksi", ["Masuk", "Keluar"], index=0 if row_to_edit['jenis_mutasi'] == "Masuk" else 1)
                        e_qty = st.number_input("Edit Qty", min_value=1, value=int(row_to_edit['jumlah']))
                        
                        if st.form_submit_button("UPDATE DATA", use_container_width=True):
                            new_entry = f"{e_sku} | {e_nama} | {e_sat} | {p_old[3]}" # Tetap pakai User lama (p_old[3]) atau mau ganti user aktif juga bisa
                            
                            conn = init_connection(); cur = conn.cursor()
                            query = "UPDATE inventory SET nama_barang=%s, jenis_mutasi=%s, jumlah=%s WHERE id=%s"
                            cur.execute(query, (new_entry, e_aksi, e_qty, int(selected_id)))
                            conn.commit(); conn.close()
                            st.success(f"ID {selected_id} Updated!")
                            st.rerun()
                else: st.write("Belum ada data")
            except Exception as e: st.write(f"Error load edit: {e}")

        # 3. HAPUS DATA
        with st.expander("🗑️ Hapus Data"):
            try:
                conn = init_connection()
                items = pd.read_sql("SELECT id, nama_barang FROM inventory ORDER BY tanggal DESC", conn); conn.close()
                target_id = st.selectbox("Pilih ID Untuk Dihapus:", items['id'])
                if st.button("HAPUS PERMANEN", use_container_width=True):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(target_id),))
                    conn.commit(); conn.close()
                    st.rerun()
            except: pass

        if st.button("LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- MAIN DASHBOARD ---
    st.markdown("<h1 style='color: white;'>Inventory Overview</h1>", unsafe_allow_html=True)
    
    try:
        conn = init_connection()
        # Kita ambil ID juga agar user tahu mana yang mau diedit
        df = pd.read_sql("SELECT id, nama_barang, jenis_mutasi, jumlah, tanggal FROM inventory ORDER BY tanggal DESC", conn); conn.close()

        if not df.empty:
            split_results = df['nama_barang'].apply(parse_inventory_name)
            df['SKU'] = split_results.str[0]
            df['Item Name'] = split_results.str[1]
            df['Unit'] = split_results.str[2]
            df['PIC'] = split_results.str[3]
            
            df['tanggal'] = pd.to_datetime(df['tanggal'])
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            
            stok_df = df.groupby(['SKU', 'Item Name', 'Unit'])['adj'].sum().reset_index()
            stok_df.columns = ['SKU', 'Produk', 'Satuan', 'Sisa Stok']

            # Metrics
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f"<div class='metric-card'><small>Total Record</small><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-card'><small>Total Unit</small><h2>{int(df['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-card'><small>Jenis Barang</small><h2>{len(stok_df)}</h2></div>", unsafe_allow_html=True)

            st.write("---")

            # Tampilan Tabel
            col_a, col_b = st.columns([2.5, 1.2])
            with col_a:
                st.markdown("### 📜 Log Transaksi Terakhir")
                # Kita tampilkan ID agar user mudah memilih saat mengedit
                st.dataframe(df[['id', 'tanggal', 'SKU', 'Item Name', 'Unit', 'PIC', 'jenis_mutasi', 'jumlah']], 
                             use_container_width=True, hide_index=True,
                             column_config={
                                 "id": st.column_config.NumberColumn("ID", width="small"),
                                 "tanggal": st.column_config.DatetimeColumn("Waktu", format="D MMM, HH:mm"),
                                 "Item Name": st.column_config.TextColumn("Nama Barang", width="medium"),
                                 "Unit": "Satuan",
                                 "PIC": "User",
                                 "jenis_mutasi": "Aksi",
                                 "jumlah": "Qty"
                             })
            
            with col_b:
                st.markdown("### 📊 Ringkasan Stok")
                st.dataframe(stok_df, use_container_width=True, hide_index=True,
                             column_config={"Sisa Stok": st.column_config.NumberColumn(format="%d 📦")})
        else:
            st.info("Belum ada data.")
    except Exception as e: st.error(f"Error: {e}")
