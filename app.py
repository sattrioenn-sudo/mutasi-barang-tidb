import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date
import pytz
import plotly.express as px
import plotly.graph_objects as go

# 1. Konfigurasi Halaman
st.set_page_config(page_title="APLICATION", page_icon="💎", layout="wide")

# --- INISIALISASI SESSION STATE (NON-DATABASE) ---
if "global_login_tracker" not in st.session_state:
    st.session_state["global_login_tracker"] = {}

if "security_logs" not in st.session_state:
    st.session_state["security_logs"] = []

if "failed_attempts" not in st.session_state:
    st.session_state["failed_attempts"] = {}

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
                # Security Check: Brute Force
                if st.session_state["failed_attempts"].get(u, 0) >= 3:
                    st.error("AKUN TERKUNCI! Salah password 3x. Hubungi Admin.")
                    add_sec_log(u, "LOCKOUT", "Mencoba login pada akun terkunci")
                elif u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    tz = pytz.timezone('Asia/Jakarta')
                    now_str = datetime.now(tz).strftime('%d/%m/%Y %H:%M')
                    st.session_state["failed_attempts"][u] = 0 
                    add_sec_log(u, "LOGIN SUCCESS", "Masuk ke sistem")
                    st.session_state.update({
                        "logged_in": True, "current_user": u, 
                        "user_role": st.session_state["user_db"][u][1], 
                        "user_perms": st.session_state["user_db"][u][2],
                        "last_login_display": st.session_state["global_login_tracker"].get(u, "First Session"),
                        "current_login_time": now_str
                    })
                    st.session_state["global_login_tracker"][u] = now_str
                    st.rerun()
                else:
                    st.session_state["failed_attempts"][u] = st.session_state["failed_attempts"].get(u, 0) + 1
                    st.error(f"Kredensial Salah! Sisa percobaan: {3 - st.session_state['failed_attempts'][u]}")
                    add_sec_log(u, "FAILED LOGIN", f"Percobaan gagal ke-{st.session_state['failed_attempts'][u]}")
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
        
        all_menus = {"📊 Dashboard": "Dashboard", "➕ Barang Masuk": "Masuk", "📤 Barang Keluar": "Keluar", "🔧 Kontrol Transaksi": "Edit", "👥 Manajemen User": "User Management", "🛡️ Security Logs": "Security"}
        nav_options = [m for m, p in all_menus.items() if p in izin_user]
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        
        if st.button("🚪 LOGOUT", use_container_width=True):
            add_sec_log(user_aktif, "LOGOUT", "Keluar dari sistem")
            st.session_state["logged_in"] = False
            st.rerun()

    # --- MENU: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='shimmer-text'>Control Tower</h1>", unsafe_allow_html=True)
        # (Isi dashboard sesuai kode Anda...)

    # --- MENU: BARANG MASUK ---
    elif menu == "➕ Barang Masuk":
        st.markdown("<h1 class='shimmer-text'>Inbound Entry</h1>", unsafe_allow_html=True)
        with st.form("input_in"):
            c1, c2 = st.columns(2)
            sk, nm = c1.text_input("SKU Code"), c1.text_input("Item Name")
            stn = c1.selectbox("Unit", ["Pcs", "Box", "Kg", "Unit"])
            qt, ke = c2.number_input("Qty Masuk", min_value=1), c2.text_area("Catatan")
            if st.form_submit_button("SAVE INBOUND"):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (val, "Masuk", qt, now))
                conn.commit(); conn.close()
                add_sec_log(user_aktif, "ADD_ITEM", f"Input Masuk: {nm} ({qt} {stn})")
                st.balloons(); st.rerun()

    # --- MENU: KONTROL ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h1 class='shimmer-text'>System Control</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            choice = st.selectbox("Pilih Record", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
            tid = int(choice.split('|')[0].replace('ID:','').strip())
            row = df_raw[df_raw['id'] == tid].iloc[0]
            p = parse_detail(row['nama_barang'])
            with st.form("edit_f"):
                enm, eqt = st.text_input("Item Name", value=p[1]), st.number_input("Qty", value=int(row['jumlah']))
                if st.form_submit_button("UPDATE DATA"):
                    new_v = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | EDITED"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s WHERE id=%s", (new_v, eqt, tid))
                    conn.commit(); conn.close()
                    add_sec_log(user_aktif, "EDIT_DATA", f"Ubah ID:{tid} menjadi {enm} ({eqt})")
                    st.success("Updated!"); st.rerun()

    # --- MENU: USER MANAGEMENT (With Lock/Unlock) ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='shimmer-text'>User Control</h1>", unsafe_allow_html=True)
        col1, col2 = st.columns([1.5, 1])
        with col1:
            st.markdown("### 📋 User Directory")
            u_data = [{"User": k, "Role": v[1], "Status": "🔴 LOCKED" if st.session_state["failed_attempts"].get(k, 0) >= 3 else "🟢 ACTIVE"} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_data), use_container_width=True)
        with col2:
            st.markdown("### 🔓 Security Reset")
            locked_users = [u for u, att in st.session_state["failed_attempts"].items() if att >= 3]
            target = st.selectbox("Unlock User", locked_users if locked_users else ["No Locked User"])
            if st.button("OPEN ACCESS") and target != "No Locked User":
                st.session_state["failed_attempts"][target] = 0
                add_sec_log(user_aktif, "UNLOCK_USER", f"Membuka kunci akun {target}")
                st.rerun()

    # --- MENU: SECURITY ---
    elif menu == "🛡️ Security Logs":
        st.markdown("<h1 class='shimmer-text'>Security Audit</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        if st.session_state["security_logs"]:
            st.dataframe(pd.DataFrame(st.session_state["security_logs"]).iloc[::-1], use_container_width=True)
        else:
            st.info("Belum ada log.")
        if st.button("🗑️ Reset Log (Session Only)"):
            st.session_state["security_logs"] = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
