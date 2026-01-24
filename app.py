import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="⚡", layout="wide")

# Inisialisasi User & Permissions (Data Session)
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Input", "Edit", "Hapus", "User Management"]]
    }

# --- CSS CUSTOM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a); }
    .metric-card {
        background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.95) !important; }
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
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='text-align:center; color:white;'><h1>SATRIO <span style='color:#38bdf8;'>POS PRO</span></h1></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = u
                    st.session_state["user_role"] = st.session_state["user_db"][u][1]
                    st.session_state["user_perms"] = st.session_state["user_db"][u][2]
                    st.rerun()
                else: st.error("Akses Ditolak!")
else:
    user_aktif = st.session_state["current_user"]
    role_aktif = st.session_state["user_role"]
    izin_user = st.session_state["user_perms"]

    # --- GLOBAL DATA LOADING (PENTING AGAR DATA TIDAK HILANG) ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    # --- GLOBAL DATA PROCESSING ---
    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'] = p_data.apply(lambda x: x[0])
        df_raw['Item'] = p_data.apply(lambda x: x[1])
        df_raw['Unit'] = p_data.apply(lambda x: x[2])
        df_raw['Pembuat'] = p_data.apply(lambda x: x[3])
        df_raw['Editor'] = p_data.apply(lambda x: x[4])
        df_raw['Ket'] = p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR DYNAMIC ---
    with st.sidebar:
        st.markdown(f"### ⚡ {user_aktif.upper()} ({role_aktif})")
        st.markdown("---")
        nav_options = []
        if "Dashboard" in izin_user: nav_options.append("📊 Dashboard")
        if "Input" in izin_user: nav_options.append("➕ Input Barang")
        if "Edit" in izin_user or "Hapus" in izin_user: nav_options.append("🔧 Kontrol Transaksi")
        if "User Management" in izin_user: nav_options.append("👥 Manajemen User")
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        
        st.markdown("---")
        start_date = st.date_input("Mulai", datetime.now() - timedelta(days=30))
        end_date = st.date_input("Akhir", datetime.now())
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DATA FILTERING BY DATE ---
    if not df_raw.empty:
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_f = df_raw.loc[mask].copy()
    else:
        df_f = pd.DataFrame()

    # --- UI LOGIC ---
    if menu == "📊 Dashboard":
        st.markdown("<h2 style='color:white;'>📈 Dashboard Analytics</h2>", unsafe_allow_html=True)
        if not df_f.empty:
            m1, m2, m3, m4 = st.columns(4)
            stok_skr = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Stok')
            m1.metric("Masuk", int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum()))
            m2.metric("Keluar", int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum()))
            m3.metric("Total SKU", len(stok_skr))
            m4.metric("Stok On Hand", int(stok_skr['Stok'].sum()))
            st.dataframe(df_f[['id', 'tanggal', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Pembuat', 'Editor', 'Ket']], use_container_width=True, hide_index=True)

    elif menu == "➕ Input Barang":
        st.markdown("<h2 style='color:white;'>➕ Record New Transaction</h2>", unsafe_allow_html=True)
        with st.form("input_form", clear_on_submit=True):
            sk = st.text_input("SKU"); nm = st.text_input("Nama Barang"); qt = st.number_input("Qty", 1)
            jn = st.selectbox("Jenis", ["Masuk", "Keluar"]); stn = st.selectbox("Unit", ["Pcs", "Box", "Kg"]); ke = st.text_input("Notes", "-")
            if st.form_submit_button("SUBMIT", use_container_width=True):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                conn.commit(); conn.close(); st.success("Data Tersimpan!"); st.rerun()

    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h2 style='color:white;'>🔧 Transaction Control</h2>", unsafe_allow_html=True)
        if df_raw.empty:
            st.warning("Database Kosong!")
        else:
            tabs_visible = []
            if "Edit" in izin_user: tabs_visible.append("✏️ Edit")
            if "Hapus" in izin_user: tabs_visible.append("🗑️ Hapus")
            
            t_items = st.tabs(tabs_visible)
            for i, tab_name in enumerate(tabs_visible):
                with t_items[i]:
                    if "Edit" in tab_name:
                        df_raw['sel'] = df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']} ({x['jenis_mutasi']})", axis=1)
                        choice = st.selectbox("Pilih Data", df_raw['sel'], key="sb_edit")
                        tid = int(choice.split('|')[0].replace('ID:','').strip())
                        row = df_raw[df_raw['id'] == tid].iloc[0]
                        p = parse_detail(row['nama_barang'])
                        with st.form("form_edit"):
                            enm = st.text_input("Nama Barang", value=p[1]); eqt = st.number_input("Qty", value=int(row['jumlah']))
                            if st.form_submit_button("UPDATE"):
                                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                                upd_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {p[5]}"
                                conn = init_connection(); cur = conn.cursor()
                                cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (upd_val, eqt, now, tid))
                                conn.commit(); conn.close(); st.success("Updated!"); st.rerun()
                    else:
                        did = st.selectbox("ID Hapus", df_raw['id'], key="sb_del")
                        if st.button("KONFIRMASI HAPUS PERMANEN"):
                            conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id = %s", (int(did),))
                            conn.commit(); conn.close(); st.warning("Deleted!"); st.rerun()

    elif menu == "👥 Manajemen User":
        st.markdown("<h2 style='color:white;'>👥 User & Password Control</h2>", unsafe_allow_html=True)
        all_u = list(st.session_state["user_db"].keys())
        st.table(pd.DataFrame([{"User": k, "Pass": v[0], "Role": v[1], "Izin": ", ".join(v[2])} for k, v in st.session_state["user_db"].items()]))
        
        tab_e, tab_d = st.tabs(["⚙️ Tambah / Edit User", "🗑️ Hapus User"])
        with tab_e:
            sel_u = st.selectbox("Pilih Akun", ["-- Tambah Baru --"] + all_u)
            with st.form("f_user"):
                if sel_u == "-- Tambah Baru --":
                    un, ps, rl, iz = st.text_input("Username"), "", "Staff", ["Dashboard", "Input"]
                else:
                    un = st.text_input("Username", value=sel_u, disabled=True)
                    ps, rl, iz = st.session_state["user_db"][sel_u][0], st.session_state["user_db"][sel_u][1], st.session_state["user_db"][sel_u][2]
                
                new_ps = st.text_input("Password", value=ps)
                new_rl = st.selectbox("Role", ["Staff", "Admin"], index=0 if rl=="Staff" else 1)
                st.write("Izin:")
                c1, c2, c3, c4, c5 = st.columns(5)
                i1 = c1.checkbox("Dashboard", "Dashboard" in iz)
                i2 = c2.checkbox("Input", "Input" in iz)
                i3 = c3.checkbox("Edit", "Edit" in iz)
                i4 = c4.checkbox("Hapus", "Hapus" in iz)
                i5 = c5.checkbox("User Management", "User Management" in iz)
                
                if st.form_submit_button("SIMPAN"):
                    target_u = sel_u if sel_u != "-- Tambah Baru --" else un
                    new_perms = []
                    if i1: new_perms.append("Dashboard")
                    if i2: new_perms.append("Input")
                    if i3: new_perms.append("Edit")
                    if i4: new_perms.append("Hapus")
                    if i5: new_perms.append("User Management")
                    st.session_state["user_db"][target_u] = [new_ps, new_rl, new_perms]
                    st.success("User Berhasil Disimpan!"); st.rerun()
        with tab_d:
            u_del = st.selectbox("Pilih User Hapus", [u for u in all_u if u != user_aktif])
            if st.button("HAPUS USER"):
                del st.session_state["user_db"][u_del]; st.rerun()
