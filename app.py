import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date
import pytz
import plotly.express as px
import plotly.graph_objects as go

# 1. Konfigurasi Halaman
st.set_page_config(page_title="APLICATION", page_icon="💎", layout="wide")

# --- INISIALISASI SESSION STATE (Wajib Ada Agar Menu Tidak Hilang) ---
if "global_login_tracker" not in st.session_state:
    st.session_state["global_login_tracker"] = {}

if "security_logs" not in st.session_state:
    st.session_state["security_logs"] = []

if "failed_attempts" not in st.session_state:
    st.session_state["failed_attempts"] = {}

if "user_db" not in st.session_state:
    # Data user awal (admin)
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Masuk", "Keluar", "Edit", "User Management", "Security"]]
    }

# --- CSS QUANTUM DASHBOARD DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at top right, #1e1b4b, #0f172a, #020617); color: #f8fafc; }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem; border-radius: 20px;
        backdrop-filter: blur(15px); margin-bottom: 20px;
    }
    .shimmer-text {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #38bdf8);
        background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite; font-weight: 800; font-size: 2.2rem;
    }
    .stat-label { color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { font-size: 1.8rem; font-weight: 800; color: #ffffff; margin-top: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Core
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

def parse_detail(val):
    parts = [p.strip() for p in str(val).split('|')]
    while len(parts) < 6: parts.append("-")
    return parts

def add_sec_log(user, action, detail):
    tz = pytz.timezone('Asia/Jakarta')
    now = datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')
    st.session_state["security_logs"].append({
        "Timestamp": now, "User": user, "Action": action, "Detail": detail
    })

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- LOGIC AUTH ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 class='shimmer-text'>SATRIO POS</h1></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("SYSTEM ENTRY"):
                if st.session_state["failed_attempts"].get(u, 0) >= 3:
                    st.error("AKUN TERKUNCI! Hubungi Admin.")
                elif u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    tz = pytz.timezone('Asia/Jakarta')
                    now_str = datetime.now(tz).strftime('%d/%m/%Y %H:%M')
                    st.session_state["failed_attempts"][u] = 0 
                    st.session_state.update({
                        "logged_in": True, "current_user": u, 
                        "user_role": st.session_state["user_db"][u][1], 
                        "user_perms": st.session_state["user_db"][u][2],
                        "last_login_display": st.session_state["global_login_tracker"].get(u, "First Session"),
                        "current_login_time": now_str
                    })
                    st.session_state["global_login_tracker"][u] = now_str
                    add_sec_log(u, "LOGIN", "Berhasil masuk ke sistem")
                    st.rerun()
                else:
                    st.session_state["failed_attempts"][u] = st.session_state["failed_attempts"].get(u, 0) + 1
                    st.error("Username/Password Salah")
else:
    user_aktif, izin_user = st.session_state["current_user"], st.session_state["user_perms"]

    # --- AMBIL DATA DARI DATABASE ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.markdown(f"<h2 class='shimmer-text' style='font-size:1.5rem;'>{user_aktif.upper()}</h2>", unsafe_allow_html=True)
        all_menus = {
            "📊 Dashboard": "Dashboard", 
            "➕ Barang Masuk": "Masuk", 
            "📤 Barang Keluar": "Keluar", 
            "🔧 Kontrol": "Edit", 
            "👥 User Management": "User Management", 
            "🛡️ Security": "Security"
        }
        nav_options = [m for m, p in all_menus.items() if p in izin_user]
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- 📊 MENU: DASHBOARD (DIPERBAIKI) ---
    if "Dashboard" in menu:
        st.markdown("<h1 class='shimmer-text'>Control Tower</h1>", unsafe_allow_html=True)
        d_range = st.date_input("Periode Analisis", [date.today().replace(day=1), date.today()])

        if not df_raw.empty and len(d_range) == 2:
            mask = (df_raw['tanggal'].dt.date >= d_range[0]) & (df_raw['tanggal'].dt.date <= d_range[1])
            df_filt = df_raw.loc[mask]
            stok_summary = df_raw.groupby(['SKU', 'Item'])['adj'].sum().reset_index(name='Stock')
            
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='glass-card'><div class='stat-label'>Inbound</div><div class='stat-value'>{int(df_filt[df_filt['jenis_mutasi']=='Masuk']['jumlah'].sum()):,}</div></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='glass-card'><div class='stat-label'>Outbound</div><div class='stat-value'>{int(df_filt[df_filt['jenis_mutasi']=='Keluar']['jumlah'].sum()):,}</div></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='glass-card'><div class='stat-label'>Total Stock</div><div class='stat-value'>{int(stok_summary['Stock'].sum()):,}</div></div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='glass-card'><div class='stat-label'>Active SKU</div><div class='stat-value'>{len(stok_summary[stok_summary['Stock']>0])}</div></div>", unsafe_allow_html=True)

            c1, c2 = st.columns([2, 1])
            with c1:
                trend = df_filt.groupby([df_filt['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().reset_index()
                st.plotly_chart(px.area(trend, x='tanggal', y='jumlah', color='jenis_mutasi', title="Activity Trend", template="plotly_dark"), use_container_width=True)
            with c2:
                pie_data = df_filt['jenis_mutasi'].value_counts()
                st.plotly_chart(px.pie(values=pie_data.values, names=pie_data.index, hole=0.6, title="Mutation Mix"), use_container_width=True)

    # --- ➕ BARANG MASUK & KELUAR (SAMA SEPERTI ASLI) ---
    elif "Masuk" in menu:
        st.markdown("<h1 class='shimmer-text'>Inbound Entry</h1>")
        with st.form("in_form"):
            sk, nm, stn = st.text_input("SKU"), st.text_input("Nama"), st.selectbox("Unit", ["Pcs", "Box"])
            qt = st.number_input("Qty", min_value=1)
            if st.form_submit_button("SIMPAN"):
                now = datetime.now(pytz.timezone('Asia/Jakarta')).strftime('%Y-%m-%d %H:%M:%S')
                val = f"{sk} | {nm} | {stn} | {user_aktif} | - | Manual Input"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (val, "Masuk", qt, now))
                conn.commit(); conn.close(); st.rerun()

    # --- 👥 MENU: USER MANAGEMENT (DIPERBAIKI TOTAL) ---
    elif "User Management" in menu:
        st.markdown("<h1 class='shimmer-text'>User Control</h1>", unsafe_allow_html=True)
        col_list, col_action = st.columns([1.5, 1])
        
        with col_list:
            st.markdown("### 📋 User Directory")
            u_data = [{"Username": k, "Role": v[1], "Akses": len(v[2])} for k, v in st.session_state["user_db"].items()]
            st.table(pd.DataFrame(u_data))

        with col_action:
            st.markdown("### 🛠️ Add / Update User")
            with st.form("add_user"):
                new_u = st.text_input("Username Baru")
                new_p = st.text_input("Password Baru", type="password")
                new_r = st.selectbox("Role", ["Staff", "Supervisor", "Manager"])
                st.write("Izin Akses:")
                p1 = st.checkbox("Dashboard", True)
                p2 = st.checkbox("Masuk", True)
                p3 = st.checkbox("Keluar", True)
                p4 = st.checkbox("Edit", False)
                p5 = st.checkbox("User Management", False)
                if st.form_submit_button("SAVE USER"):
                    perms = [m for m, val in zip(["Dashboard", "Masuk", "Keluar", "Edit", "User Management", "Security"], [p1,p2,p3,p4,p5, True]) if val]
                    st.session_state["user_db"][new_u] = [new_p, new_r, perms]
                    st.success(f"User {new_u} Berhasil Disimpan!")
                    st.rerun()
            
            st.markdown("---")
            st.markdown("### 🚨 Delete User")
            target_del = st.selectbox("Pilih User", [u for u in st.session_state["user_db"].keys() if u != 'admin'])
            if st.button("HAPUS USER"):
                del st.session_state["user_db"][target_del]
                st.warning(f"User {target_del} telah dihapus.")
                st.rerun()

    # --- 🛡️ MENU: SECURITY ---
    elif "Security" in menu:
        st.markdown("<h1 class='shimmer-text'>Security Audit</h1>", unsafe_allow_html=True)
        if st.session_state["security_logs"]:
            st.dataframe(pd.DataFrame(st.session_state["security_logs"]).iloc[::-1], use_container_width=True)
        if st.button("Clear Logs"):
            st.session_state["security_logs"] = []
            st.rerun()
