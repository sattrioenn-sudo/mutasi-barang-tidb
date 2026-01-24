import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="⚡", layout="wide")

# Inisialisasi User dengan Role (Tanpa merusak database)
# Struktur: "username": ["password", "role"]
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["admin123", "Admin"],
        "staff1": ["staff123", "Staff"]
    }

# --- CSS CUSTOM: THE "ULTRA MODERN" LOOK ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at top right, #1e293b, #0f172a); }
    .metric-card {
        background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px);
        padding: 25px; border-radius: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
        transition: all 0.3s ease;
    }
    .metric-label { color: #94a3b8; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #ffffff; font-size: 2.5rem; font-weight: 800; margin: 5px 0; }
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.95) !important; }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #0f172a !important; font-weight: 700; }
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
        st.markdown("<div style='text-align: center;'><h1 style='color: white; font-size: 3rem; margin-bottom:0;'>SATRIO <span style='color: #38bdf8;'>POS</span></h1></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("ENTER DASHBOARD", use_container_width=True):
                # Cek kredensial dan role
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = u
                    st.session_state["user_role"] = st.session_state["user_db"][u][1]
                    st.rerun()
                else: st.error("Invalid Credentials")
else:
    # Definisi Role Aktif
    user_aktif = st.session_state["current_user"]
    role_aktif = st.session_state["user_role"]

    # --- LOAD DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    # --- SIDEBAR (DINAMIS BERDASARKAN ROLE) ---
    with st.sidebar:
        st.markdown(f"### 🛡️ {user_aktif.upper()}")
        st.markdown(f"Role: **{role_aktif}**")
        st.markdown("---")
        
        # Menu Filter: Staff tidak bisa melihat menu Management
        options = ["📊 Overview Dashboard", "✨ Input Transaksi"]
        if role_aktif == "Admin":
            options.append("🔧 Management Records")
            options.append("👥 User Access")
            
        menu = st.selectbox("NAVIGATION", options)
        
        st.markdown("---")
        start_date = st.date_input("Start", datetime.now() - timedelta(days=30))
        end_date = st.date_input("End", datetime.now())
        if st.button("🚪 Sign Out", use_container_width=True):
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
    if menu == "📊 Overview Dashboard":
        st.markdown("<h2 style='color:white;'>📈 Dashboard</h2>", unsafe_allow_html=True)
        m1, m2, m3 = st.columns(3)
        total_in = int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum()) if not df_raw.empty else 0
        total_out = int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum()) if not df_raw.empty else 0
        stok_skr = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Stok') if not df_raw.empty else pd.DataFrame()
        
        m1.markdown(f"<div class='metric-card'><div class='metric-label'>Masuk</div><div class='metric-value'>{total_in}</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><div class='metric-label'>Keluar</div><div class='metric-value' style='color:#f87171;'>{total_out}</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><div class='metric-label'>Total SKU</div><div class='metric-value' style='color:#fbbf24;'>{len(stok_skr)}</div></div>", unsafe_allow_html=True)
        
        st.markdown("### 🕒 Recent Activity")
        st.dataframe(df_f[['id', 'tanggal', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Pembuat']].head(10), use_container_width=True, hide_index=True)

    elif menu == "✨ Input Transaksi":
        st.markdown("<h2 style='color:white;'>✍️ Input Mutasi Barang</h2>", unsafe_allow_html=True)
        # Semua Role Berhak Akses Input
        with st.form("f_add_pro", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                sk, nm, qt = st.text_input("SKU"), st.text_input("Product Name"), st.number_input("Quantity", min_value=1)
            with col2:
                jn = st.selectbox("Type", ["Masuk", "Keluar"])
                stn = st.selectbox("Unit", ["Pcs", "Box", "Kg", "Ltr"])
                ke = st.text_input("Notes", "-")
            if st.form_submit_button("SAVE RECORD", use_container_width=True):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                conn.commit(); conn.close(); st.success("Data Saved!"); st.rerun()

    elif menu == "🔧 Management Records" and role_aktif == "Admin":
        st.markdown("<h2 style='color:white;'>🔧 Admin Control (Edit/Delete)</h2>", unsafe_allow_html=True)
        # Khusus Admin
        t_ed, t_del = st.tabs(["🔧 Edit Record", "⚠️ Delete Record"])
        with t_ed:
            if not df_raw.empty:
                df_raw['label'] = df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1)
                target = st.selectbox("Pilih Data", df_raw['label'])
                tid = int(target.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("f_edit_pro"):
                    enm = st.text_input("Update Name", value=p[1]); eqt = st.number_input("Update Qty", value=int(row['jumlah']))
                    if st.form_submit_button("COMMIT UPDATE"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full_upd = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {p[5]}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, eqt, now, tid))
                        conn.commit(); conn.close(); st.success("Updated!"); st.rerun()
        with t_del:
            did = st.selectbox("Pilih ID Hapus", df_raw['id'])
            if st.button("🔴 CONFIRM DELETE", use_container_width=True):
                conn = init_connection(); cur = conn.cursor()
                cur.execute("DELETE FROM inventory WHERE id = %s", (int(did),))
                conn.commit(); conn.close(); st.warning("Deleted!"); st.rerun()

    elif menu == "👥 User Access" and role_aktif == "Admin":
        st.markdown("<h2 style='color:white;'>👥 User Role Management</h2>", unsafe_allow_html=True)
        # Khusus Admin
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### Add New User")
            nu = st.text_input("New Username")
            np = st.text_input("New Password", type="password")
            nr = st.selectbox("Assign Role", ["Staff", "Admin"])
            if st.button("Create User"): 
                st.session_state["user_db"][nu] = [np, nr]; st.success(f"User {nu} created as {nr}!")
        with c2:
            st.markdown("### Existing Users")
            st.table(pd.DataFrame([(k, v[1]) for k, v in st.session_state["user_db"].items()], columns=['User', 'Role']))
