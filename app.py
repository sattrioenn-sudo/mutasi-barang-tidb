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

# --- CSS CUSTOM PREMIUM DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    /* Background Utama */
    .stApp {
        background: radial-gradient(circle at 20% 10%, #1e293b 0%, #0f172a 100%);
        color: #f8fafc;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.8) !important;
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Card Metrics */
    .metric-container {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.2);
        transition: transform 0.3s ease;
    }
    .metric-container:hover {
        transform: translateY(-5px);
        border: 1px solid #38bdf8;
    }

    /* Header & Title */
    h1, h2, h3 { color: #f8fafc !important; font-weight: 800 !important; letter-spacing: -0.5px; }
    
    /* Dataframe Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255,255,255,0.05);
    }

    /* Buttons */
    .stButton>button {
        border-radius: 10px !important;
        background: linear-gradient(90deg, #0ea5e9, #2563eb) !important;
        border: none !important;
        color: white !important;
        font-weight: 600 !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px rgba(14, 165, 233, 0.4) !important;
        transform: scale(1.02);
    }

    /* Form Inputs */
    .stTextInput>div>div>input, .stNumberInput>div>div>input, .stSelectbox>div>div>div {
        background-color: rgba(15, 23, 42, 0.6) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.1) !important;
        border-radius: 10px !important;
    }
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

# --- AUTH LOGIC (LOGIN VIEW) ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("""
            <div style='text-align:center; padding: 2rem; background: rgba(30,41,59,0.5); border-radius: 24px; border: 1px solid rgba(255,255,255,0.1);'>
                <h1 style='margin-bottom:0;'>SATRIO <span style='color:#38bdf8;'>POS PRO</span></h1>
                <p style='color:#94a3b8;'>Inventory Management System v2.0</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK KE SISTEM", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = u
                    st.session_state["user_role"] = st.session_state["user_db"][u][1]
                    st.session_state["user_perms"] = st.session_state["user_db"][u][2]
                    st.rerun()
                else: st.error("Kredensial salah, Bro!")
else:
    # --- APP CONTENT ---
    user_aktif = st.session_state["current_user"]
    role_aktif = st.session_state["user_role"]
    izin_user = st.session_state["user_perms"]

    # Load Data Global
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2])
        df_raw['Pembuat'], df_raw['Editor'], df_raw['Ket'] = p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[4]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<div style='background:rgba(56, 189, 248, 0.1); padding:1rem; border-radius:12px; border:1px solid rgba(56, 189, 248, 0.3); text-align:center;'> <span style='color:#38bdf8; font-weight:800;'>{user_aktif.upper()}</span><br><small style='color:#94a3b8;'>Role: {role_aktif}</small></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        nav_options = []
        if "Dashboard" in izin_user: nav_options.append("📊 Dashboard")
        if "Input" in izin_user: nav_options.append("➕ Input Barang")
        if "Edit" in izin_user or "Hapus" in izin_user: nav_options.append("🔧 Kontrol Transaksi")
        if "User Management" in izin_user: nav_options.append("👥 Manajemen User")
        menu = st.selectbox("MAIN MENU", nav_options)
        
        st.markdown("---")
        start_date = st.date_input("Dari Tanggal", datetime.now() - timedelta(days=30))
        end_date = st.date_input("Sampai Tanggal", datetime.now())
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- FILTERING ---
    if not df_raw.empty:
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_f = df_raw.loc[mask].copy()
    else: df_f = pd.DataFrame()

    # --- MENU: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h2><span style='color:#38bdf8;'>📊</span> Dashboard Overview</h2>", unsafe_allow_html=True)
        if df_f.empty:
            st.info("Belum ada transaksi di rentang tanggal ini.")
        else:
            c1, c2, c3, c4 = st.columns(4)
            stok_skr = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Stok')
            
            with c1: st.markdown(f"<div class='metric-container'><small style='color:#38bdf8;'>MASUK</small><br><span style='font-size:2rem; font-weight:800;'>{int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum())}</span></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-container'><small style='color:#f43f5e;'>KELUAR</small><br><span style='font-size:2rem; font-weight:800;'>{int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum())}</span></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-container'><small style='color:#10b981;'>TOTAL SKU</small><br><span style='font-size:2rem; font-weight:800;'>{len(stok_skr)}</span></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='metric-container'><small style='color:#fbbf24;'>ON HAND</small><br><span style='font-size:2rem; font-weight:800;'>{int(stok_skr['Stok'].sum())}</span></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.dataframe(df_f[['id', 'tanggal', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Pembuat', 'Ket']], use_container_width=True, hide_index=True)

    # --- MENU: INPUT ---
    elif menu == "➕ Input Barang":
        st.markdown("<h2><span style='color:#38bdf8;'>➕</span> New Transaction</h2>", unsafe_allow_html=True)
        with st.form("input_form"):
            cc1, cc2 = st.columns(2)
            with cc1:
                sk = st.text_input("SKU Barang")
                nm = st.text_input("Nama Barang")
                qt = st.number_input("Jumlah (Qty)", min_value=1)
            with cc2:
                jn = st.selectbox("Jenis Gerakan", ["Masuk", "Keluar"])
                stn = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit"])
                ke = st.text_input("Keterangan/Notes", "-")
            if st.form_submit_button("SUBMIT DATA SEKARANG", use_container_width=True):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                conn.commit(); conn.close(); st.success("Data berhasil tercatat!"); st.rerun()

    # --- MENU: KONTROL ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h2><span style='color:#38bdf8;'>🔧</span> Control Center</h2>", unsafe_allow_html=True)
        if df_raw.empty: st.warning("Belum ada data.")
        else:
            tab_e, tab_h = st.tabs(["✏️ Edit Data", "🗑️ Hapus Data"])
            with tab_e:
                df_raw['sel'] = df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']} ({x['jenis_mutasi']})", axis=1)
                choice = st.selectbox("Pilih Transaksi untuk Diedit", df_raw['sel'])
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("edit_form"):
                    enm = st.text_input("Revisi Nama Barang", value=p[1])
                    eqt = st.number_input("Revisi Qty", value=int(row['jumlah']))
                    if st.form_submit_button("SIMPAN PERUBAHAN"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        upd_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {p[5]}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (upd_val, eqt, now, tid))
                        conn.commit(); conn.close(); st.success("Data diupdate!"); st.rerun()
            with tab_h:
                did = st.selectbox("Pilih ID untuk Hapus", df_raw['id'])
                if st.button("HAPUS PERMANEN", use_container_width=True):
                    conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id = %s", (int(did),))
                    conn.commit(); conn.close(); st.warning("Data berhasil dihapus!"); st.rerun()

    # --- MENU: USER MANAGEMENT ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h2><span style='color:#38bdf8;'>👥</span> User Access</h2>", unsafe_allow_html=True)
        all_users = list(st.session_state["user_db"].keys())
        
        # Table User dengan Desain Bersih
        st.dataframe(pd.DataFrame([{"User": k, "Role": v[1], "Akses": ", ".join(v[2])} for k, v in st.session_state["user_db"].items()]), use_container_width=True)
        
        st.markdown("---")
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("### 🔑 Konfigurasi Akun")
            sel_u = st.selectbox("Pilih User (atau Tambah Baru)", ["-- Baru --"] + all_users)
            with st.form("user_premium_form"):
                if sel_u == "-- Baru --":
                    un, ps, rl, iz = st.text_input("Username"), "", "Staff", ["Dashboard", "Input"]
                else:
                    un = st.text_input("Username", value=sel_u, disabled=True)
                    ps, rl, iz = st.session_state["user_db"][sel_u][0], st.session_state["user_db"][sel_u][1], st.session_state["user_db"][sel_u][2]
                
                new_ps = st.text_input("Password Baru", value=ps)
                new_rl = st.selectbox("Level Jabatan", ["Staff", "Admin"], index=0 if rl=="Staff" else 1)
                st.write("Izin Fitur:")
                i_cols = st.columns(5)
                i1 = i_cols[0].checkbox("Dashboard", "Dashboard" in iz)
                i2 = i_cols[1].checkbox("Input", "Input" in iz)
                i3 = i_cols[2].checkbox("Edit", "Edit" in iz)
                i4 = i_cols[3].checkbox("Hapus", "Hapus" in iz)
                i5 = i_cols[4].checkbox("User Management", "User Management" in iz)
                
                if st.form_submit_button("SIMPAN AKUN"):
                    target = sel_u if sel_u != "-- Baru --" else un
                    p_list = []
                    if i1: p_list.append("Dashboard"); 
                    if i2: p_list.append("Input"); 
                    if i3: p_list.append("Edit"); 
                    if i4: p_list.append("Hapus"); 
                    if i5: p_list.append("User Management")
                    st.session_state["user_db"][target] = [new_ps, new_rl, p_list]
                    st.success("User updated!"); st.rerun()
        with c2:
            st.markdown("### 🗑️ Hapus Akses")
            u_del = st.selectbox("User yang akan dihapus", [u for u in all_users if u != user_aktif])
            if st.button("HAPUS USER INI"):
                del st.session_state["user_db"][u_del]; st.rerun()
