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

    # --- UI LOGIC ---
    if menu == "📊 Dashboard":
        st.markdown("<h2 style='color:white;'>📈 Dashboard Analytics</h2>", unsafe_allow_html=True)
        # ... (Kode metrik dashboard tetap sama seperti sebelumnya)
        if not df_raw.empty:
            p_data = df_raw['nama_barang'].apply(parse_detail)
            df_raw['SKU'], df_raw['Item'], df_raw['Unit'], df_raw['Pembuat'], df_raw['Editor'], df_raw['Ket'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2]), p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[4]), p_data.apply(lambda x: x[5])
            df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
            df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
            df_f = df_raw.loc[mask].copy()
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
        # ... (Logika tab edit/hapus tetap sama)

    elif menu == "👥 Manajemen User":
        st.markdown("<h2 style='color:white;'>👥 User Access & Password Control</h2>", unsafe_allow_html=True)
        
        # 1. Tabel User Aktif
        df_users = pd.DataFrame([
            {"Username": k, "Password": v[0], "Role": v[1], "Izin": ", ".join(v[2])} 
            for k, v in st.session_state["user_db"].items()
        ])
        st.dataframe(df_users, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # 2. Form Manajemen (Bisa Tambah atau Edit Password)
        tab_manage, tab_delete = st.tabs(["⚙️ Tambah / Edit User", "🗑️ Hapus Akses"])
        
        with tab_manage:
            st.markdown("### 🔑 Form Konfigurasi Akun")
            # Fitur Utama: Dropdown untuk memilih user yang sudah ada (termasuk admin) atau ketik baru
            all_users = list(st.session_state["user_db"].keys())
            selected_u = st.selectbox("Pilih User untuk Diedit (Atau biarkan untuk Tambah Baru)", ["-- Tambah User Baru --"] + all_users)
            
            with st.form("form_user_edit"):
                if selected_u == "-- Tambah User Baru --":
                    new_u = st.text_input("Username Baru")
                    curr_p, curr_r, curr_i = "", "Staff", ["Dashboard", "Input"]
                else:
                    new_u = st.text_input("Username (Tetap)", value=selected_u, disabled=True)
                    curr_p = st.session_state["user_db"][selected_u][0]
                    curr_r = st.session_state["user_db"][selected_u][1]
                    curr_i = st.session_state["user_db"][selected_u][2]
                
                new_p = st.text_input("Password", value=curr_p)
                new_r = st.selectbox("Role", ["Staff", "Admin"], index=0 if curr_r == "Staff" else 1)
                
                st.write("**Set Izin Fitur:**")
                c1, c2, c3, c4, c5 = st.columns(5)
                i_dash = c1.checkbox("Dashboard", "Dashboard" in curr_i)
                i_in = c2.checkbox("Input", "Input" in curr_i)
                i_edit = c3.checkbox("Edit", "Edit" in curr_i)
                i_del = c4.checkbox("Hapus", "Hapus" in curr_i)
                i_mgmt = c5.checkbox("User Management", "User Management" in curr_i)
                
                if st.form_submit_button("SIMPAN PERUBAHAN / USER BARU", use_container_width=True):
                    final_u = selected_u if selected_u != "-- Tambah User Baru --" else new_u
                    if final_u:
                        perms = []
                        if i_dash: perms.append("Dashboard")
                        if i_in: perms.append("Input")
                        if i_edit: perms.append("Edit")
                        if i_del: perms.append("Hapus")
                        if i_mgmt: perms.append("User Management")
                        
                        st.session_state["user_db"][final_u] = [new_p, new_r, perms]
                        st.success(f"Akun {final_u} Berhasil Diperbarui!")
                        st.rerun()
                    else:
                        st.error("Username tidak boleh kosong!")

        with tab_delete:
            st.markdown("### ❌ Hapus User")
            u_to_del = st.selectbox("Pilih User untuk Dihapus", ["-"] + [u for u in all_users if u != user_aktif])
            if st.button("KONFIRMASI HAPUS", use_container_width=True) and u_to_del != "-":
                del st.session_state["user_db"][u_to_del]
                st.warning(f"User {u_to_del} telah dihapus!")
                st.rerun()
