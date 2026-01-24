import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="SATRIO POS PRO", page_icon="💎", layout="wide")

# Inisialisasi User & Permissions (Session State)
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Input", "Edit", "User Management"]]
    }

# --- CSS HYPER-AESTHETIC (REFINED) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    .stApp { background: radial-gradient(circle at top left, #1e1b4b, #0f172a); background-attachment: fixed; }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px; border-radius: 24px; backdrop-filter: blur(20px);
        box-shadow: 0 15px 35px rgba(0,0,0,0.2); margin-bottom: 20px;
    }
    .hero-text {
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    .stButton>button {
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important;
        border: none !important; border-radius: 12px !important; color: white !important;
        font-weight: 600 !important; height: 3rem; width: 100%; transition: 0.3s;
    }
    .stButton>button:hover { transform: scale(1.02); box-shadow: 0 8px 20px rgba(168, 85, 247, 0.4); }
    [data-testid="stSidebar"] { background: rgba(10, 15, 30, 0.8) !important; backdrop-filter: blur(10px); }
    </style>
    """, unsafe_allow_html=True)

# 2. Core Functions
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

def parse_detail(val):
    parts = [p.strip() for p in str(val).split('|')]
    while len(parts) < 6: parts.append("-")
    return parts

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- AUTH SYSTEM ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 class='hero-text' style='font-size:3.5rem; margin-bottom:0;'>SATRIO</h1><h2 style='color:white; font-weight:200; margin-top:0;'>POS PRO ELITE</h2></div>", unsafe_allow_html=True)
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("AUTHENTICATE"):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2]})
                    st.rerun()
                else: st.error("Access Denied")
else:
    user_aktif, izin_user = st.session_state["current_user"], st.session_state["user_perms"]

    # --- DATA ENGINE ---
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
        st.markdown(f"<h1 class='hero-text'>{user_aktif.upper()}</h1>", unsafe_allow_html=True)
        nav_options = [opt for opt, perm in zip(["📊 Dashboard", "➕ Input Barang", "🔧 Kontrol Transaksi", "👥 Manajemen User"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in izin_user]
        menu = st.selectbox("COMMAND CENTER", nav_options)
        if st.button("🚪 LOGOUT"):
            st.session_state["logged_in"] = False; st.rerun()

    # --- 1. DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='hero-text'>Operations Overview</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stock')
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Items In", int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum()))
            m2.metric("Items Out", int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum()))
            m3.metric("Total SKU", len(stok_summary))
            m4.metric("Net Stock", int(stok_summary['Stock'].sum()))

            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.dataframe(df_raw[['id', 'SKU', 'Item', 'Unit', 'jenis_mutasi', 'jumlah', 'CreatedBy', 'tanggal', 'Note']], use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 2. INPUT BARANG ---
    elif menu == "➕ Input Barang":
        st.markdown("<h1 class='hero-text'>Entry Form</h1>", unsafe_allow_html=True)
        with st.form("input_f"):
            c1, c2 = st.columns(2)
            sk = c1.text_input("SKU Code")
            nm = c1.text_input("Item Name")
            stn = c1.selectbox("Unit", ["Pcs", "Box", "Kg", "Unit"])
            jn = c2.selectbox("Mutation", ["Masuk", "Keluar"])
            qt = c2.number_input("Qty", min_value=1)
            ke = c2.text_area("Note")
            if st.form_submit_button("SAVE TRANSACTION"):
                if sk and nm:
                    tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (val, jn, qt, now))
                    conn.commit(); conn.close(); st.success("Synced!"); st.rerun()

    # --- 3. KONTROL TRANSAKSI (FUNGSI LENGKAP) ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h1 class='hero-text'>Management Hub</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["✏️ Edit Record", "🗑️ Delete Record"])
        
        with t1:
            if not df_raw.empty:
                choice = st.selectbox("Select Record to Update", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']} ({x['SKU']})", axis=1))
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                
                with st.form("edit_f"):
                    c1, c2 = st.columns(2)
                    enm = c1.text_input("Item Name", value=p[1])
                    eqt = c1.number_input("Quantity", value=int(row['jumlah']))
                    ejn = c2.selectbox("Mutation", ["Masuk", "Keluar"], index=0 if row['jenis_mutasi'] == "Masuk" else 1)
                    eke = c2.text_input("Note", value=p[5])
                    if st.form_submit_button("UPDATE DATABASE"):
                        new_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {eke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, jenis_mutasi=%s WHERE id=%s", (new_val, eqt, ejn, tid))
                        conn.commit(); conn.close(); st.success("Updated!"); st.rerun()

        with t2:
            st.markdown("<div style='background:rgba(244,63,94,0.1); padding:20px; border-radius:15px; border:1px solid #f43f5e;'>", unsafe_allow_html=True)
            did = st.selectbox("Select ID to Purge", df_raw['id'] if not df_raw.empty else [])
            if st.button("🚨 PERMANENT DELETE"):
                conn = init_connection(); cur = conn.cursor()
                cur.execute("DELETE FROM inventory WHERE id=%s", (int(did),))
                conn.commit(); conn.close(); st.warning("Deleted!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 4. MANAJEMEN USER (FUNGSI LENGKAP) ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='hero-text'>Identity Control</h1>", unsafe_allow_html=True)
        col_list, col_form = st.columns([1.5, 1])
        
        with col_list:
            st.markdown("##### Current Users")
            u_data = [{"User": k, "Role": v[1], "Access": "•".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.table(pd.DataFrame(u_data))
            
        with col_form:
            mode = st.radio("Action", ["Add New", "Edit/Delete"], horizontal=True)
            with st.form("user_f"):
                if mode == "Add New":
                    un, ps, rl = st.text_input("Username"), st.text_input("Password", type="password"), st.text_input("Role")
                else:
                    un = st.selectbox("Target User", [u for u in st.session_state["user_db"].keys() if u != 'admin'])
                    ps = st.text_input("New Password", value=st.session_state["user_db"][un][0] if un else "")
                    rl = st.text_input("New Role", value=st.session_state["user_db"][un][1] if un else "")
                
                st.write("Permissions:")
                p_dash = st.checkbox("Dashboard", value=True)
                p_in = st.checkbox("Input", value=True)
                p_ed = st.checkbox("Edit/Control", value=False)
                p_um = st.checkbox("User Management", value=False)
                
                b1, b2 = st.columns([2, 1])
                if b1.form_submit_button("SAVE CONFIG"):
                    perms = [p for p, v in zip(["Dashboard", "Input", "Edit", "User Management"], [p_dash, p_in, p_ed, p_um]) if v]
                    st.session_state["user_db"][un] = [ps, rl, perms]; st.success("Saved!"); st.rerun()
                if mode == "Edit/Delete" and b2.form_submit_button("🗑️"):
                    del st.session_state["user_db"][un]; st.warning("Removed!"); st.rerun()
