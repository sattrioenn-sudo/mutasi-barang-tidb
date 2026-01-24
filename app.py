import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="⚡", layout="wide")

# Inisialisasi User & Role (Simulasi di Session State agar tidak merusak DB)
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
    
    /* Card Styling */
    .metric-card {
        background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    }
    .metric-label { color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; }
    .metric-value { color: #ffffff; font-size: 2.2rem; font-weight: 800; }
    
    /* Sidebar & Tab Styling */
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.95) !important; }
    .stTabs [aria-selected="true"] { background-color: #38bdf8 !important; color: #0f172a !important; font-weight: 700; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Core
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

def parse_detail(val):
    # Format database: SKU | Nama | Satuan | Pembuat | Pengedit | Keterangan
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
        st.markdown("<div style='text-align:center; color:white;'><h1>SATRIO <span style='color:#38bdf8;'>POS PRO</span></h1><p>Inventory Control System</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.session_state["user_role"] = st.session_state["user_db"][u][1]
                    st.rerun()
                else: st.error("Akses Ditolak!")
else:
    user_aktif = st.session_state["current_user"]
    role_aktif = st.session_state["user_role"]

    # --- DATA LOADING ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### ⚡ {user_aktif.upper()} ({role_aktif})")
        st.markdown("---")
        nav_options = ["📊 Dashboard", "➕ Input Barang"]
        if role_aktif == "Admin":
            nav_options += ["🔧 Edit/Hapus Data", "👥 Manajemen User"]
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        
        st.markdown("---")
        start_date = st.date_input("Filter Mulai", datetime.now() - timedelta(days=30))
        end_date = st.date_input("Filter Akhir", datetime.now())
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
        st.markdown("<h2 style='color:white;'>📈 Inventory Analytics</h2>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        total_in = int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum()) if not df_raw.empty else 0
        total_out = int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum()) if not df_raw.empty else 0
        stok_skr = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Stok') if not df_raw.empty else pd.DataFrame()
        
        m1.markdown(f"<div class='metric-card'><div class='metric-label'>Masuk</div><div class='metric-value'>{total_in}</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><div class='metric-label'>Keluar</div><div class='metric-value' style='color:#f87171;'>{total_out}</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><div class='metric-label'>SKU</div><div class='metric-value' style='color:#fbbf24;'>{len(stok_skr)}</div></div>", unsafe_allow_html=True)
        m4.markdown(f"<div class='metric-card'><div class='metric-label'>On Hand</div><div class='metric-value' style='color:#38bdf8;'>{int(stok_skr['Stok'].sum()) if not stok_skr.empty else 0}</div></div>", unsafe_allow_html=True)
        
        st.markdown("### 🕒 Recent Logs (Audit Trail)")
        # Menampilkan Pembuat & Pengedit secara transparan
        st.dataframe(df_f[['id', 'tanggal', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Pembuat', 'Editor', 'Ket']], use_container_width=True, hide_index=True)

    elif menu == "➕ Input Barang":
        st.markdown("<h2 style='color:white;'>➕ Record New Transaction</h2>", unsafe_allow_html=True)
        with st.form("input_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                sk = st.text_input("SKU Code")
                nm = st.text_input("Item Name")
                qt = st.number_input("Quantity", min_value=1)
            with c2:
                jn = st.selectbox("Transaction Type", ["Masuk", "Keluar"])
                stn = st.selectbox("Measurement Unit", ["Pcs", "Box", "Kg", "Ltr"])
                ke = st.text_input("Additional Notes", "-")
            if st.form_submit_button("SUBMIT TRANSACTION", use_container_width=True):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                # Format: SKU | Nama | Unit | Pembuat | Pengedit (Default -) | Keterangan
                full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                conn.commit(); conn.close(); st.success("Transaction Logged Successfully!"); st.rerun()

    elif menu == "🔧 Edit/Hapus Data" and role_aktif == "Admin":
        st.markdown("<h2 style='color:white;'>🔧 Admin Tools</h2>", unsafe_allow_html=True)
        tab_e, tab_d = st.tabs(["Edit Data", "Hapus Data"])
        
        with tab_e:
            if not df_raw.empty:
                df_raw['sel'] = df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']} ({x['tanggal']})", axis=1)
                choice = st.selectbox("Select Record to Modify", df_raw['sel'])
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                
                with st.form("edit_form"):
                    enm = st.text_input("Update Item Name", value=p[1])
                    eqt = st.number_input("Update Quantity", value=int(row['jumlah']))
                    eke = st.text_input("Update Notes", value=p[5])
                    if st.form_submit_button("COMMIT CHANGES"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        # Update LOGIKA EDITOR: Menggunakan user_aktif yang sedang mengedit
                        # Format: SKU | Nama | Unit | Pembuat (Tetap p[3]) | Pengedit (user_aktif) | Keterangan
                        upd_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {eke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (upd_val, eqt, now, tid))
                        conn.commit(); conn.close(); st.success(f"Record ID {tid} Updated by {user_aktif}!"); st.rerun()

        with tab_d:
            did = st.selectbox("Select ID to Delete", df_raw['id'])
            if st.button("DELETE PERMANENTLY", use_container_width=True):
                conn = init_connection(); cur = conn.cursor()
                cur.execute("DELETE FROM inventory WHERE id = %s", (int(did),))
                conn.commit(); conn.close(); st.warning("Record Erased!"); st.rerun()

    elif menu == "👥 Manajemen User" and role_aktif == "Admin":
        st.markdown("<h2 style='color:white;'>👥 User Access Control</h2>", unsafe_allow_html=True)
        c_list, c_add = st.columns([1.5, 1])
        with c_list:
            st.markdown("### Active Users")
            st.table(pd.DataFrame([{"Username": k, "Role": v[1]} for k, v in st.session_state["user_db"].items()]))
        with c_add:
            st.markdown("### Add/Update User")
            nu = st.text_input("Username")
            np = st.text_input("Password", type="password")
            nr = st.selectbox("Role", ["Staff", "Admin"])
            if st.button("Save User"):
                st.session_state["user_db"][nu] = [np, nr]; st.success("User Updated!"); st.rerun()
            if st.button("Delete User") and nu != user_aktif:
                if nu in st.session_state["user_db"]:
                    del st.session_state["user_db"][nu]; st.warning("User Deleted!"); st.rerun()
