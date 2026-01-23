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

def parse_inventory_name(val):
    parts = str(val).split('|'); parts = [p.strip() for p in parts]
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
        # Default Filter: 1 Tahun ke belakang agar data lama muncul
        start_date = st.date_input("📅 Mulai", datetime.now() - timedelta(days=365))
        end_date = st.date_input("📅 Akhir", datetime.now())
        
        # 1. MENU TRANSAKSI (LENGKAP: INPUT, EDIT, HAPUS)
        with st.expander("🛠️ Menu Transaksi"):
            mode = st.radio("Aksi:", ["Input", "Edit", "Hapus"])
            if mode == "Input":
                with st.form("f_add", clear_on_submit=True):
                    sk, nm, qt = st.text_input("SKU"), st.text_input("Nama"), st.number_input("Qty", 1)
                    jn, stn = st.selectbox("Jenis", ["Masuk", "Keluar"]), st.selectbox("Sat", ["Pcs", "Box", "Kg"])
                    if st.form_submit_button("Simpan Barang"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | -"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                        conn.commit(); conn.close(); st.rerun()
            
            elif mode == "Edit" and not df_raw.empty:
                edit_id = st.selectbox("ID Edit", df_raw['id'])
                row = df_raw[df_raw['id'] == edit_id].iloc[0]
                p_old = parse_inventory_name(row['nama_barang'])
                with st.form("f_edit"):
                    e_nm = st.text_input("Nama Barang", value=p_old[1])
                    e_qt = st.number_input("Jumlah", value=int(row['jumlah']))
                    if st.form_submit_button("Update"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full_upd = f"{p_old[0]} | {e_nm} | {p_old[2]} | {p_old[3]} | {st.session_state['current_user']} | -"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, e_qt, now, int(edit_id)))
                        conn.commit(); conn.close(); st.rerun()

            elif mode == "Hapus" and not df_raw.empty:
                del_id = st.selectbox("ID Hapus", df_raw['id'])
                if st.button("🔴 Hapus Permanen"):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(del_id),))
                    conn.commit(); conn.close(); st.rerun()

        # 2. MENU SECURITY (LENGKAP: LIHAT, TAMBAH, HAPUS)
        with st.expander("🔐 Security & Users"):
            st.write("**Daftar Kredensial**")
            df_u = pd.DataFrame(list(st.session_state["user_db"].items()), columns=['User', 'Pass'])
            st.dataframe(df_u, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            nu, np = st.text_input("Username Baru"), st.text_input("Password Baru", type="password")
            if st.button("CREATE USER"):
                if nu and np: st.session_state["user_db"][nu] = np; st.rerun()
            
            st.markdown("---")
            list_rem = [u for u in st.session_state["user_db"].keys() if u != st.session_state["current_user"]]
            u_rem = st.selectbox("Hapus User:", ["-"] + list_rem)
            if st.button("DELETE USER") and u_rem != "-":
                del st.session_state["user_db"][u_rem]; st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD CONTENT ---
    st.markdown("<h2 style='color:white;'>📊 Command Center</h2>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # Processing Data
        p = df_raw['nama_barang'].apply(parse_inventory_name)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'] = p.str[0], p.str[1], p.str[2]
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

        # Logic Stock Opname
        stok_awal = df_raw[df_raw['tanggal'].dt.date < start_date].groupby('SKU')['adj'].sum().reset_index(name='Awal')
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_p = df_raw.loc[mask].copy()
        
        mut = df_p.groupby(['SKU', 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0).reset_index()
        for c in ['Masuk', 'Keluar']:
            if c not in mut: mut[c] = 0

        res = pd.merge(df_raw[['SKU', 'Item', 'Unit']].drop_duplicates('SKU'), stok_awal, on='SKU', how='left').fillna(0)
        res = pd.merge(res, mut[['SKU', 'Masuk', 'Keluar']], on='SKU', how='left').fillna(0)
        res['Saldo'] = res['Awal'] + res['Masuk'] - res['Keluar']

        # Visual Row 1: Metrics & Chart
        col_m1, col_m2, col_chart = st.columns([1, 1, 2])
        col_m1.markdown(f"<div class='metric-card'><div class='metric-label'>MASUK</div><div class='metric-value' style='color:#38bdf8;'>{int(res['Masuk'].sum())}</div></div>", unsafe_allow_html=True)
        col_m2.markdown(f"<div class='metric-card'><div class='metric-label'>KELUAR</div><div class='metric-value' style='color:#f87171;'>{int(res['Keluar'].sum())}</div></div>", unsafe_allow_html=True)
        
        with col_chart:
            top_5 = res.sort_values('Keluar', ascending=False).head(5)
            if top_5['Keluar'].sum() > 0:
                st.bar_chart(top_5.set_index('Item')['Keluar'], height=160)
            else: st.info("Belum ada data keluar di periode ini.")

        # Visual Row 2: Tables
        st.markdown("### 📋 Laporan Stock Opname")
        st.dataframe(res[['SKU', 'Item', 'Unit', 'Awal', 'Masuk', 'Keluar', 'Saldo']], use_container_width=True, hide_index=True)
        
        st.markdown("### 📜 Log Pergerakan")
        df_p['St'] = df_p['jenis_mutasi'].apply(lambda x: "🟢" if x == 'Masuk' else "🔴")
        st.dataframe(df_p[['St', 'tanggal', 'SKU', 'Item', 'jumlah']], use_container_width=True, hide_index=True)
    else:
        st.info("Database kosong atau koneksi bermasalah.")
