import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date
import pytz
import plotly.express as px
import plotly.graph_objects as go

# 1. Konfigurasi Halaman
st.set_page_config(page_title="SATRIO POS PRO", page_icon="💎", layout="wide")

# Inisialisasi Security Logs & Tracker di Memori Aplikasi
if "global_login_tracker" not in st.session_state:
    st.session_state["global_login_tracker"] = {}
if "security_logs" not in st.session_state:
    st.session_state["security_logs"] = []

# Inisialisasi User & Permissions
if "user_db" not in st.session_state:
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
    @keyframes shimmer { to { background-position: 200% center; } }
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
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    tz = pytz.timezone('Asia/Jakarta')
                    now_str = datetime.now(tz).strftime('%d/%m/%Y %H:%M:%S')
                    
                    last_seen = st.session_state["global_login_tracker"].get(u, "First Session")
                    
                    # Simpan Log Keamanan
                    st.session_state["security_logs"].append({
                        "Timestamp": now_str,
                        "User": u,
                        "Action": "LOGIN SUCCESS",
                        "Role": st.session_state["user_db"][u][1]
                    })
                    
                    st.session_state.update({
                        "logged_in": True, 
                        "current_user": u, 
                        "user_role": st.session_state["user_db"][u][1], 
                        "user_perms": st.session_state["user_db"][u][2],
                        "last_login_display": last_seen,
                        "current_login_time": now_str
                    })
                    
                    st.session_state["global_login_tracker"][u] = now_str
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
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
        
        st.markdown(f"""
            <div class="session-info">
                <div style="font-size:0.65rem; color:#94a3b8; font-weight:bold;">LAST LOGIN</div>
                <div style="font-size:0.8rem; color:#f8fafc;">📅 {st.session_state.get('last_login_display')}</div>
                <div style="margin-top:8px; font-size:0.65rem; color:#94a3b8; font-weight:bold;">CURRENT LOGIN</div>
                <div style="font-size:0.8rem; color:#38bdf8;">🕒 {st.session_state.get('current_login_time')}</div>
            </div>
        """, unsafe_allow_html=True)
        
        all_menus = {
            "📊 Dashboard": "Dashboard", 
            "➕ Barang Masuk": "Masuk", 
            "📤 Barang Keluar": "Keluar", 
            "🔧 Kontrol Transaksi": "Edit", 
            "👥 Manajemen User": "User Management",
            "🛡️ Security Logs": "Security"
        }
        nav_options = [m for m, p in all_menus.items() if p in izin_user]
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        
        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- MENU: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='shimmer-text'>Control Tower</h1>", unsafe_allow_html=True)
        # ... (Kode Dashboard tetap sama seperti sebelumnya) ...
        st.info("Gunakan filter tanggal untuk melihat analisis arus barang.")

    # --- MENU: BARANG MASUK & KELUAR & EDIT (TETAP SAMA) ---
    elif menu == "➕ Barang Masuk":
        st.markdown("<h1 class='shimmer-text'>Inbound Entry</h1>", unsafe_allow_html=True)
        # (Isi form masuk)
    elif menu == "📤 Barang Keluar":
        st.markdown("<h1 class='shimmer-text'>Outbound System</h1>", unsafe_allow_html=True)
        # (Isi form keluar)

    # --- MENU: USER MANAGEMENT ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='shimmer-text'>User Control</h1>", unsafe_allow_html=True)
        # (Isi manajemen user)

    # --- MENU: SECURITY LOGS (NEW) ---
    elif menu == "🛡️ Security Logs":
        st.markdown("<h1 class='shimmer-text'>Security Audit</h1>", unsafe_allow_html=True)
        
        col_log, col_stat = st.columns([2, 1])
        
        with col_log:
            st.markdown("### 📜 System Access Log")
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if st.session_state["security_logs"]:
                log_df = pd.DataFrame(st.session_state["security_logs"])
                # Balik urutan agar yang terbaru di atas
                st.dataframe(log_df.iloc[::-1], use_container_width=True, hide_index=True)
            else:
                st.write("No logs recorded yet.")
            st.markdown("</div>", unsafe_allow_html=True)
            
            if st.button("Clear Logs (Session Only)"):
                st.session_state["security_logs"] = []
                st.rerun()

        with col_stat:
            st.markdown("### 📊 Login Activity")
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if st.session_state["security_logs"]:
                log_df = pd.DataFrame(st.session_state["security_logs"])
                user_counts = log_df['User'].value_counts().reset_index()
                user_counts.columns = ['User', 'Login Count']
                
                fig_security = px.bar(user_counts, x='User', y='Login Count', 
                                     color='User', template="plotly_dark",
                                     color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig_security, use_container_width=True)
            else:
                st.write("No data to visualize.")
            st.markdown("</div>", unsafe_allow_html=True)
