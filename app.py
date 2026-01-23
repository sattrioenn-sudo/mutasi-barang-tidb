import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & Tema Premium
st.set_page_config(page_title="INV-PRIME PRO", page_icon="🚀", layout="wide")

# Inisialisasi User di Session
if "user_db" not in st.session_state:
    st.session_state["user_db"] = dict(st.secrets["auth_users"])

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #0f172a; }
    .metric-card {
        background: #1e293b; padding: 15px; border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;
    }
    .metric-label { font-size: 0.85rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 1.8rem; font-weight: 700; margin-top: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Database
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# Fungsi Parse Lengkap: SKU | Nama | Satuan | Creator | Editor | Keterangan
def parse_inventory_name(val):
    parts = [p.strip() for p in str(val).split('|')]
    while len(parts) < 6: parts.append("-")
    return parts

# --- AUTH LOGIC ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:white;'>🚀 INV-PRIME LOGIN</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK", use_container_width=True):
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

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 🛡️ {st.session_state['current_user'].upper()}")
        st.markdown("---")
        start_date = st.date_input("📅 Mulai", datetime.now() - timedelta(days=365))
        end_date = st.date_input("📅 Akhir", datetime.now())
        
        with st.expander("🛠️ Menu Transaksi"):
            mode = st.radio("Aksi:", ["Input", "Edit", "Hapus"])
            
            if mode == "Input":
                with st.form("f_add", clear_on_submit=True):
                    sk, nm = st.text_input("SKU"), st.text_input("Nama Barang")
                    qt = st.number_input("Qty", 1)
                    jn = st.selectbox("Jenis", ["Masuk", "Keluar"])
                    stn = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit", "Liter"])
                    ket = st.text_input("Keterangan", value="-")
                    if st.form_submit_button("Simpan Barang"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        # Simpan detail ke string nama_barang
                        full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ket}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                        conn.commit(); conn.close(); st.rerun()
            
            elif mode == "Edit" and not df_raw.empty:
                edit_id = st.selectbox("ID Edit", df_raw['id'])
                row = df_raw[df_raw['id'] == edit_id].iloc[0]
                p = parse_inventory_name(row['nama_barang'])
                with st.form("f_edit"):
                    e_nm = st.text_input("Nama Barang", value=p[1])
                    e_qt = st.number_input("Jumlah", value=int(row['jumlah']))
                    e_stn = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit", "Liter"], index=["Pcs", "Box", "Kg", "Unit", "Liter"].index(p[2]) if p[2] in ["Pcs", "Box", "Kg", "Unit", "Liter"] else 0)
                    e_ket = st.text_input("Keterangan", value=p[5])
                    if st.form_submit_button("Update"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        # Tetap simpan Creator awal (p[3]), lalu masukkan Editor baru (current_user)
                        full_upd = f"{p[0]} | {e_nm} | {e_stn} | {p[3]} | {st.session_state['current_user']} | {e_ket}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, e_qt, now, int(edit_id)))
                        conn.commit(); conn.close(); st.rerun()

            elif mode == "Hapus" and not df_raw.empty:
                del_id = st.selectbox("ID Hapus", df_raw['id'])
                if st.button("🔴 Hapus Permanen"):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(del_id),))
                    conn.commit(); conn.close(); st.rerun()

        with st.expander("🔐 Security & Users"):
            st.write("**Daftar Kredensial**")
            df_u = pd.DataFrame(list(st.session_state["user_db"].items()), columns=['User', 'Pass'])
            st.dataframe(df_u, use_container_width=True, hide_index=True)
            st.markdown("---")
            nu, np = st.text_input("Username Baru"), st.text_input("Password Baru", type="password")
            if st.button("CREATE USER"):
                if nu and np: st.session_state["user_db"][nu] = np; st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD CONTENT ---
    st.markdown("<h2 style='color:white;'>📊 Command Center</h2>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # Pecah Data Detail
        p_data = df_raw['nama_barang'].apply(parse_inventory_name)
        df_raw['SKU'] = p_data.apply(lambda x: x[0])
        df_raw['Item'] = p_data.apply(lambda x: x[1])
        df_raw['Unit'] = p_data.apply(lambda x: x[2])
        df_raw['Creator'] = p_data.apply(lambda x: x[3])
        df_raw['Editor'] = p_data.apply(lambda x: x[4])
        df_raw['Keterangan'] = p_data.apply(lambda x: x[5])
        
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_p = df_raw.loc[mask].copy()
        
        # Metrics & Charts (Sesuai Dashboard Awal)
        c1, c2, c3 = st.columns([1, 1, 2])
        total_m = df_p[df_p['jenis_mutasi'] == 'Masuk']['jumlah'].sum()
        total_k = df_p[df_p['jenis_mutasi'] == 'Keluar']['jumlah'].sum()
        c1.markdown(f"<div class='metric-card'><div class='metric-label'>MASUK</div><div class='metric-value' style='color:#38bdf8;'>{int(total_m)}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-label'>KELUAR</div><div class='metric-value' style='color:#f87171;'>{int(total_k)}</div></div>", unsafe_allow_html=True)
        with c3:
            if not df_p.empty: st.bar_chart(df_p.groupby('Item')['jumlah'].sum().head(5), height=160)

        # TABEL 1: STOCK OPNAME (Ringkasan)
        st.markdown("### 📋 Laporan Stock Opname")
        stok_awal = df_raw[df_raw['tanggal'].dt.date < start_date].groupby('SKU')['adj'].sum().reset_index(name='Awal')
        mut = df_p.groupby(['SKU', 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0).reset_index()
        for c in ['Masuk', 'Keluar']: 
            if c not in mut: mut[c] = 0
            
        res = pd.merge(df_raw[['SKU', 'Item', 'Unit']].drop_duplicates('SKU'), stok_awal, on='SKU', how='left').fillna(0)
        res = pd.merge(res, mut, on='SKU', how='left').fillna(0)
        res['Saldo'] = res['Awal'] + res['Masuk'] - res['Keluar']
        st.dataframe(res[['SKU', 'Item', 'Unit', 'Awal', 'Masuk', 'Keluar', 'Saldo']], use_container_width=True, hide_index=True)
        
        # TABEL 2: LOG DETAIL (Creator, Editor, Keterangan)
        st.markdown("### 📜 Log Pergerakan Detail")
        df_p['St'] = df_p['jenis_mutasi'].apply(lambda x: "🟢 MASUK" if x == 'Masuk' else "🔴 KELUAR")
        st.dataframe(df_p[['St', 'tanggal', 'SKU', 'Item', 'jumlah', 'Unit', 'Creator', 'Editor', 'Keterangan']], 
                     use_container_width=True, hide_index=True)
    else:
        st.info("Database kosong.")
