import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="⚡", layout="wide")

# Inisialisasi User & Permissions (Data Session)
# Format: "username": ["password", "role", ["list_izin"]]
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["admin123", "Admin", ["Dashboard", "Input", "Edit", "Hapus", "User Management"]],
        "staff1": ["staff123", "Staff", ["Dashboard", "Input"]]
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
    .metric-label { color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #ffffff; font-size: 2.2rem; font-weight: 800; }
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

    # --- LOAD DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

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

    # --- DATA PROCESSING ---
    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'], df_raw['Pembuat'], df_raw['Editor'], df_raw['Ket'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2]), p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[4]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_f = df_raw.loc[mask].copy()

    # --- UI LOGIC ---
    if menu == "📊 Dashboard":
        st.markdown("<h2 style='color:white;'>📈 Dashboard Analytics</h2>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        total_in = int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum()) if not df_raw.empty else 0
        total_out = int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum()) if not df_raw.empty else 0
        stok_skr = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Stok') if not df_raw.empty else pd.DataFrame()
        
        m1.markdown(f"<div class='metric-card'><div class='metric-label'>Masuk</div><div class='metric-value'>{total_in}</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><div class='metric-label'>Keluar</div><div class='metric-value' style='color:#f87171;'>{total_out}</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><div class='metric-label'>SKU</div><div class='metric-value' style='color:#fbbf24;'>{len(stok_skr)}</div></div>", unsafe_allow_html=True)
        m4.markdown(f"<div class='metric-card'><div class='metric-label'>On Hand</div><div class='metric-value' style='color:#38bdf8;'>{int(stok_skr['Stok'].sum()) if not stok_skr.empty else 0}</div></div>", unsafe_allow_html=True)
        
        st.dataframe(df_f[['id', 'tanggal', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Pembuat', 'Editor', 'Ket']], use_container_width=True, hide_index=True)

    elif menu == "➕ Input Barang":
        st.markdown("<h2 style='color:white;'>➕ Record New Transaction</h2>", unsafe_allow_html=True)
        with st.form("input_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                sk, nm, qt = st.text_input("SKU"), st.text_input("Nama Barang"), st.number_input("Qty", 1)
            with c2:
                jn, stn, ke = st.selectbox("Jenis", ["Masuk", "Keluar"]), st.selectbox("Unit", ["Pcs", "Box", "Kg"]), st.text_input("Notes", "-")
            if st.form_submit_button("SUBMIT", use_container_width=True):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                conn.commit(); conn.close(); st.success("Data Tersimpan!"); st.rerun()

    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h2 style='color:white;'>🔧 Transaction Control</h2>", unsafe_allow_html=True)
        tabs_visible = []
        if "Edit" in izin_user: tabs_visible.append("✏️ Edit")
        if "Hapus" in izin_user: tabs_visible.append("🗑️ Hapus")
        
        if not tabs_visible:
            st.warning("Anda tidak memiliki izin khusus untuk Edit atau Hapus.")
        else:
            t_items = st.tabs(tabs_visible)
            for i, tab_name in enumerate(tabs_visible):
                with t_items[i]:
                    if "Edit" in tab_name:
                        df_raw['sel'] = df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1)
                        choice = st.selectbox("Pilih Data", df_raw['sel'])
                        tid = int(choice.split('|')[0].replace('ID:','').strip())
                        row = df_raw[df_raw['id'] == tid].iloc[0]; p = parse_detail(row['nama_barang'])
                        with st.form("edit_form"):
                            enm = st.text_input("Nama Baru", value=p[1]); eqt = st.number_input("Qty Baru", value=int(row['jumlah']))
                            if st.form_submit_button("UPDATE"):
                                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                                upd_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {p[5]}"
                                conn = init_connection(); cur = conn.cursor()
                                cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (upd_val, eqt, now, tid))
                                conn.commit(); conn.close(); st.success("Updated!"); st.rerun()
                    else:
                        did = st.selectbox("ID Hapus", df_raw['id'])
                        if st.button("HAPUS PERMANEN", use_container_width=True):
                            conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id = %s", (int(did),))
                            conn.commit(); conn.close(); st.warning("Deleted!"); st.rerun()

    elif menu == "👥 Manajemen User":
        st.markdown("<h2 style='color:white;'>👥 User & Permission Management</h2>", unsafe_allow_html=True)
        
        # TABEL USER
        df_users = pd.DataFrame([
            {"Username": k, "Password": v[0], "Role": v[1], "Izin": ", ".join(v[2])} 
            for k, v in st.session_state["user_db"].items()
        ])
        st.dataframe(df_users, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        col_conf, col_del = st.columns(2)
        with col_conf:
            st.markdown("### ⚙️ Configure User Access")
            with st.form("manage_user"):
                u_name = st.text_input("Username (Baru/Lama)")
                u_pass = st.text_input("Password")
                u_role = st.selectbox("Role", ["Staff", "Admin"])
                st.write("**Izin Fitur:**")
                c1, c2, c3 = st.columns(3)
                f_dash = c1.checkbox("Dashboard", True)
                f_in = c2.checkbox("Input", True)
                f_edit = c3.checkbox("Edit")
                f_del = c1.checkbox("Hapus")
                f_mgmt = c2.checkbox("User Management")
                
                if st.form_submit_button("SIMPAN HAK AKSES", use_container_width=True):
                    perms = []
                    if f_dash: perms.append("Dashboard")
                    if f_in: perms.append("Input")
                    if f_edit: perms.append("Edit")
                    if f_del: perms.append("Hapus")
                    if f_mgmt: perms.append("User Management")
                    st.session_state["user_db"][u_name] = [u_pass, u_role, perms]
                    st.success(f"Akses {u_name} diperbarui!"); st.rerun()
        
        with col_del:
            st.markdown("### ❌ Hapus Akses")
            target = st.selectbox("Pilih User", ["-"] + [u for u in st.session_state["user_db"].keys() if u != user_aktif])
            if st.button("HAPUS USER", use_container_width=True) and target != "-":
                del st.session_state["user_db"][target]; st.rerun()
