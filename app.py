import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date
import pytz
import plotly.express as px
import plotly.graph_objects as go
import json
import os

# 1. Konfigurasi Halaman
st.set_page_config(page_title="APLICATION", page_icon="💎", layout="wide")

# --- INISIALISASI SESSION STATE & STORAGE ---
if "global_login_tracker" not in st.session_state:
    st.session_state["global_login_tracker"] = {}

if "security_logs" not in st.session_state:
    st.session_state["security_logs"] = []

# Fitur Baru: Simpan Waktu Solved (Non-DB)
if "solved_registry" not in st.session_state:
    st.session_state["solved_registry"] = {}

# Update Struktur User DB (Role & Permissions yang lebih detail)
if "user_db" not in st.session_state:
    # Format: [Password, Role, List_Izin]
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", [
            "Dashboard", "Masuk", "Keluar", "Edit", "User Management", "Security",
            "Input Ticket", "Update Ticket", "Export & Reporting", 
            "Input Barang Masuk", "Input Barang Keluar", "Approved", "Hapus Barang"
        ]]
    }

# --- CSS QUANTUM DASHBOARD DESIGN (TETAP SAMA) ---
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
    @keyframes shimmer { to { background-position: 200% center; } }
    .stat-label { color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { font-size: 1.8rem; font-weight: 800; color: #ffffff; margin-top: 5px; }
    .session-info {
        background: rgba(56, 189, 248, 0.05);
        border: 1px solid rgba(56, 189, 248, 0.2);
        padding: 12px; border-radius: 12px; margin-bottom: 15px;
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

def has_access(perm_name):
    return perm_name in st.session_state.get("user_perms", [])

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- LOGIC AUTH ---
if not st.session_state["logged_in"]:
    # (Halaman Login tetap sama seperti kode awal lu)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 class='shimmer-text'>SATRIO POS</h1></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("SYSTEM ENTRY"):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    tz = pytz.timezone('Asia/Jakarta')
                    now_str = datetime.now(tz).strftime('%d/%m/%Y %H:%M')
                    last_seen = st.session_state["global_login_tracker"].get(u, "First Session")
                    st.session_state["security_logs"].append({"Timestamp": now_str, "User": u, "Action": "Login Success", "Role": st.session_state["user_db"][u][1]})
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2], "last_login_display": last_seen, "current_login_time": now_str})
                    st.session_state["global_login_tracker"][u] = now_str
                    st.rerun()
                else: st.error("Invalid Credentials")
else:
    user_aktif, izin_user = st.session_state["current_user"], st.session_state["user_perms"]

    # --- FETCH DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2])
        df_raw['Pembuat'], df_raw['Editor'], df_raw['Note'] = p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[4]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<h2 class='shimmer-text' style='font-size:1.5rem;'>{user_aktif.upper()}</h2>", unsafe_allow_html=True)
        st.markdown(f"""<div class="session-info"><div style="font-size:0.65rem; color:#94a3b8; font-weight:bold;">LAST LOGIN</div><div style="font-size:0.8rem; color:#f8fafc;">📅 {st.session_state.get('last_login_display')}</div><div style="margin-top:8px; font-size:0.65rem; color:#94a3b8; font-weight:bold;">CURRENT LOGIN</div><div style="font-size:0.8rem; color:#38bdf8;">🕒 {st.session_state.get('current_login_time')}</div></div>""", unsafe_allow_html=True)
        
        all_menus = {"📊 Dashboard": "Dashboard", "➕ Barang Masuk": "Masuk", "📤 Barang Keluar": "Keluar", "🔧 Kontrol Transaksi": "Edit", "👥 Manajemen User": "User Management", "🛡️ Security Logs": "Security"}
        nav_options = [m for m, p in all_menus.items() if p in izin_user]
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        
        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- MENU: DASHBOARD (WITH AUTO TIME INPUT/SOLVED) ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='shimmer-text'>Control Tower</h1>", unsafe_allow_html=True)
        
        if not df_raw.empty:
            # INTEGRASI WAKTU INPUT & SOLVED OTOMATIS
            df_raw['Waktu Input'] = df_raw['tanggal'].dt.strftime('%d/%m/%Y %H:%M')
            # Cek di registry apakah ada ID yang statusnya "Keluar" atau "Solved"
            df_raw['Waktu Solved'] = df_raw['id'].apply(lambda x: st.session_state["solved_registry"].get(str(x), "-"))
            
            stok_summary = df_raw.groupby(['SKU', 'Item'])['adj'].sum().reset_index(name='Stock')
            m1, m2, m3, m4 = st.columns(4)
            metrics = [
                ("Inbound Flow", int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum()), "#38bdf8", m1),
                ("Outbound Flow", int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum()), "#f43f5e", m2),
                ("Stock Value (Qty)", int(stok_summary['Stock'].sum()), "#fbbf24", m3),
                ("Active SKU", len(stok_summary[stok_summary['Stock']>0]), "#10b981", m4)
            ]
            for label, val, color, col in metrics:
                with col:
                    st.markdown(f"<div class='glass-card' style='border-left: 5px solid {color}'><div class='stat-label'>{label}</div><div class='stat-value'>{val:,}</div></div>", unsafe_allow_html=True)

            # Dashboard Table yang diperbarui kolomnya
            st.markdown("### 📋 Transaction Monitor")
            st.dataframe(df_raw[['id', 'SKU', 'Item', 'jenis_mutasi', 'jumlah', 'Waktu Input', 'Waktu Solved', 'Note']], use_container_width=True, hide_index=True)

    # --- MENU: MANAJEMEN USER (UPDATED TO USER MANAGEMENT WITH DETAIL PERMS) ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='shimmer-text'>User Access Control</h1>", unsafe_allow_html=True)
        c_list, c_add = st.columns([1, 1.2])
        
        with c_list:
            st.markdown("### 📋 User Directory")
            u_data = [{"User": k, "Role": v[1], "Perms": len(v[2])} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)

        with c_add:
            st.markdown("### 🛠️ Configure Permissions")
            with st.form("u_form_new"):
                un, ps = st.text_input("Username"), st.text_input("Password", type="password")
                rl = st.selectbox("Role", ["Staff", "Supervisor", "Manager", "Admin"])
                
                st.write("**Specific Access Rights:**")
                col_p1, col_p2 = st.columns(2)
                with col_p1:
                    p_tix_in = st.checkbox("Input Ticket")
                    p_tix_up = st.checkbox("Update Ticket")
                    p_exp = st.checkbox("Export & Reporting")
                    p_in_m = st.checkbox("Input Barang Masuk")
                with col_p2:
                    p_in_k = st.checkbox("Input Barang Keluar")
                    p_app = st.checkbox("Approved")
                    p_del = st.checkbox("Hapus Barang")
                    p_adm = st.checkbox("User Management")

                if st.form_submit_button("SAVE USER CONFIG"):
                    # Mapping izin ke list
                    new_perms = ["Dashboard"] # Default
                    if p_tix_in: new_perms.append("Input Ticket")
                    if p_tix_up: new_perms.append("Update Ticket")
                    if p_exp: new_perms.append("Export & Reporting")
                    if p_in_m: new_perms.append("Masuk"); new_perms.append("Input Barang Masuk")
                    if p_in_k: new_perms.append("Keluar"); new_perms.append("Input Barang Keluar")
                    if p_app: new_perms.append("Approved")
                    if p_del: new_perms.append("Hapus Barang"); new_perms.append("Edit")
                    if p_adm: new_perms.append("User Management"); new_perms.append("Security")
                    
                    st.session_state["user_db"][un] = [ps, rl, new_perms]
                    st.success(f"Permissions for {un} updated!"); st.rerun()

    # --- LOGIC UNTUK INPUT BARANG MASUK / KELUAR (WITH AUTO SOLVED TRACKER) ---
    elif menu == "➕ Barang Masuk":
        if has_access("Input Barang Masuk"):
            # (Gunakan form lu yang sudah ada, tambahkan logic simpan)
            st.markdown("<h1 class='shimmer-text'>Inbound Entry</h1>")
            with st.form("in_form"):
                sk, nm = st.text_input("SKU"), st.text_input("Name")
                qt = st.number_input("Qty", min_value=1)
                if st.form_submit_button("SAVE"):
                    # Simpan ke DB lu (tetap sama)
                    st.success("Barang Masuk Tercatat")
        else: st.warning("Akses Ditolak")

    elif menu == "📤 Barang Keluar":
        if has_access("Input Barang Keluar"):
            # (Sama seperti kode lu, tapi saat simpan tambahkan ini:)
            # st.session_state["solved_registry"][str(new_id)] = datetime.now(tz).strftime('%d/%m/%Y %H:%M')
            st.markdown("<h1 class='shimmer-text'>Outbound System</h1>")
            # ... (Form keluar lu)
        else: st.warning("Akses Ditolak")

    # (Menu lainnya seperti Security Logs tetap sama)
