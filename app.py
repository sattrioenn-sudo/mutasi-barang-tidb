import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="⚡", layout="wide")

# Inisialisasi User & Permissions (Session State)
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Input", "Edit", "User Management"]]
    }

# --- CSS QUANTUM ANIMATION & GLASSMORPHISM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #1e1b4b, #312e81, #1e1b4b);
        background-size: 400% 400%; animation: gradient 15s ease infinite; color: #f8fafc;
    }
    @keyframes gradient { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }

    .glass-card {
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem; border-radius: 24px; backdrop-filter: blur(20px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4); margin-bottom: 20px;
    }
    .shimmer-text {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #38bdf8);
        background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite; font-weight: 800;
    }
    @keyframes shimmer { to { background-position: 200% center; } }

    .stButton>button { 
        border-radius: 14px !important; background: linear-gradient(90deg, #6366f1, #a855f7) !important; 
        border: none !important; color: white !important; font-weight: 700 !important; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 10px 20px rgba(168, 85, 247, 0.4); }
    [data-testid="stSidebar"] { background: rgba(10, 15, 30, 0.8) !important; backdrop-filter: blur(12px); }
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

# --- UI LOGIC ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 class='shimmer-text' style='font-size:3.5rem;'>SATRIO POS</h1><p style='color:#94a3b8;'>Enterprise Intelligence System</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("👤 Username")
            p = st.text_input("🔑 Password", type="password")
            if st.form_submit_button("SYSTEM ENTRY", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2]})
                    st.rerun()
                else: st.error("Access Denied")
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
        df_raw['CreatedBy'], df_raw['Note'] = p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<h2 class='shimmer-text'>{user_aktif.upper()}</h2>", unsafe_allow_html=True)
        nav_options = []
        mapping = {"📊 Dashboard": "Dashboard", "➕ Input Barang": "Input", "🔧 Kontrol Transaksi": "Edit", "👥 Manajemen User": "User Management"}
        for k, v in mapping.items():
            if v in izin_user: nav_options.append(k)
        
        menu = st.selectbox("NAVIGATION", nav_options)
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- 1. DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='shimmer-text'>Operational Dashboard</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stok')
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Items In", int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum()))
            m2.metric("Items Out", int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum()))
            m3.metric("SKU Active", len(stok_summary))
            m4.metric("Net Stock", int(stok_summary['Stok'].sum()))
            
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.dataframe(df_raw[['id', 'SKU', 'Item', 'Unit', 'jenis_mutasi', 'jumlah', 'CreatedBy', 'tanggal', 'Note']], use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 2. INPUT BARANG ---
    elif menu == "➕ Input Barang":
        st.markdown("<h1 class='shimmer-text'>Transaction Entry</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        with st.form("input_f"):
            c1, c2 = st.columns(2)
            sk = c1.text_input("🆔 SKU Code")
            nm = c1.text_input("📦 Item Name")
            stn = c1.selectbox("📏 Unit", ["Pcs", "Box", "Kg", "Unit"])
            jn = c2.selectbox("🔄 Mutation", ["Masuk", "Keluar"])
            qt = c2.number_input("🔢 Qty", min_value=1)
            ke = c2.text_area("📝 Note")
            if st.form_submit_button("🚀 SAVE TO CLOUD"):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                conn.commit(); conn.close(); st.balloons(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- 3. KONTROL TRANSAKSI (LENGKAP) ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h1 class='shimmer-text'>Control Center</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["✏️ Edit Data", "🗑️ Hapus Data"])
        with t1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if not df_raw.empty:
                choice = st.selectbox("Pilih Transaksi", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']} ({x['SKU']})", axis=1))
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("edit_full"):
                    c1, c2 = st.columns(2)
                    enm = c1.text_input("Nama Barang", value=p[1])
                    eqt = c1.number_input("Jumlah", value=int(row['jumlah']))
                    ejn = c2.selectbox("Jenis Mutasi", ["Masuk", "Keluar"], index=0 if row['jenis_mutasi']=="Masuk" else 1)
                    est = c2.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit"], index=["Pcs", "Box", "Kg", "Unit"].index(p[2]) if p[2] in ["Pcs", "Box", "Kg", "Unit"] else 0)
                    eke = st.text_area("Keterangan / Note", value=p[5])
                    if st.form_submit_button("🔥 UPDATE DATA"):
                        new_val = f"{p[0]} | {enm} | {est} | {p[3]} | {user_aktif} | {eke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, jenis_mutasi=%s WHERE id=%s", (new_val, eqt, ejn, tid))
                        conn.commit(); conn.close(); st.success("Database Updated!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with t2:
            st.markdown("<div class='glass-card' style='border-color:#f43f5e'>", unsafe_allow_html=True)
            did = st.selectbox("Pilih ID untuk Dihapus", df_raw['id'] if not df_raw.empty else [])
            if st.button("🚨 HAPUS PERMANEN", use_container_width=True):
                conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id=%s", (int(did),))
                conn.commit(); conn.close(); st.warning(f"ID {did} Terhapus!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 4. MANAJEMEN USER (MUNCUL LAGI) ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='shimmer-text'>User Access Control</h1>", unsafe_allow_html=True)
        cl, cf = st.columns([1.5, 1])
        with cl:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            u_data = [{"User": k, "Role": v[1], "Izin": "•".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with cf:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            mode = st.radio("Aksi", ["Tambah User", "Edit/Hapus User"], horizontal=True)
            with st.form("user_manage"):
                if mode == "Tambah User":
                    un, ps, rl = st.text_input("Username"), st.text_input("Password", type="password"), st.text_input("Jabatan")
                else:
                    un = st.selectbox("Pilih User", [u for u in st.session_state["user_db"].keys() if u != 'admin'])
                    ps = st.text_input("Password Baru", value=st.session_state["user_db"][un][0] if un else "")
                    rl = st.text_input("Jabatan Baru", value=st.session_state["user_db"][un][1] if un else "")
                
                st.write("Izin Akses:")
                i1, i2 = st.columns(2)
                p_ds = i1.checkbox("Dashboard", value=True)
                p_in = i1.checkbox("Input", value=True)
                p_ed = i2.checkbox("Edit", value=False)
                p_um = i2.checkbox("User Management", value=False)
                
                b_save, b_del = st.columns([2, 1])
                if b_save.form_submit_button("💾 SIMPAN"):
                    perms = [p for p, v in zip(["Dashboard", "Input", "Edit", "User Management"], [p_ds, p_in, p_ed, p_um]) if v]
                    st.session_state["user_db"][un] = [ps, rl, perms]; st.rerun()
                if mode == "Edit/Hapus User" and b_del.form_submit_button("🗑️"):
                    del st.session_state["user_db"][un]; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
