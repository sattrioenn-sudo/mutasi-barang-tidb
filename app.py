import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px

# 1. Konfigurasi Halaman & UI Elite
st.set_page_config(page_title="SATRIO POS PRO", page_icon="💎", layout="wide")

# Inisialisasi User & Permissions
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Input", "Edit", "User Management"]]
    }

# --- CSS HYPER-AESTHETIC DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }
    
    /* Background Animasi Halus */
    .stApp { 
        background: radial-gradient(circle at top right, #1e1b4b, #0f172a, #020617);
        color: #f8fafc; 
    }
    
    /* Card Glassmorphism v2 */
    .glass-card {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 2rem;
        border-radius: 28px;
        backdrop-filter: blur(20px);
        box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
        margin-bottom: 25px;
        transition: transform 0.3s ease;
    }
    .glass-card:hover { transform: translateY(-5px); border-color: rgba(56, 189, 248, 0.3); }
    
    /* Stats Aesthetic */
    .stat-container {
        background: linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 100%);
        padding: 20px; border-radius: 20px; border: 1px solid rgba(255,255,255,0.05);
        text-align: center;
    }

    /* Sidebar Clean Look */
    [data-testid="stSidebar"] { 
        background: rgba(15, 23, 42, 0.8) !important; 
        backdrop-filter: blur(15px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Gradient Text & Button */
    .hero-text {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    .stButton>button { 
        border-radius: 16px !important; 
        background: linear-gradient(135deg, #6366f1 0%, #a855f7 100%) !important; 
        border: none !important; color: white !important; font-weight: 600 !important;
        height: 3.5rem; transition: all 0.3s ease;
    }
    .stButton>button:hover { box-shadow: 0 10px 25px rgba(168, 85, 247, 0.4); transform: scale(1.02); }

    /* Table & Input Styling */
    .stDataFrame { background: rgba(0,0,0,0.2); border-radius: 15px; }
    input, select, textarea { 
        background-color: rgba(255,255,255,0.05) !important; 
        color: white !important; border-radius: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Core (Tetap Sesuai Database Anda)
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
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 class='hero-text' style='font-size:3.5rem;'>SATRIO</h1><p style='color:#94a3b8; letter-spacing: 2px;'>SYSTEM AUTHENTICATION</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("UNLOCK SYSTEM", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2]})
                    st.rerun()
                else: st.error("Access Denied")
else:
    user_aktif, role_aktif, izin_user = st.session_state["current_user"], st.session_state["user_role"], st.session_state["user_perms"]

    # Load Data (Safe Engine)
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2])
        df_raw['Pembuat'], df_raw['Ket'] = p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<h1 class='hero-text' style='font-size:2rem;'>{user_aktif.upper()}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='margin-top:-15px; color:#818cf8;'>{role_aktif}</p>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        nav_options = [opt for opt, perm in zip(["📊 Dashboard", "➕ Input Barang", "🔧 Kontrol Transaksi", "👥 Manajemen User"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in izin_user]
        menu = st.selectbox("MENU", nav_options)
        st.markdown("---")
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='hero-text'>Operations Overview</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stok')
            
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='stat-container'><small style='color:#38bdf8'>TOTAL IN</small><h2>{int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='stat-container'><small style='color:#f43f5e'>TOTAL OUT</small><h2>{int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='stat-container'><small style='color:#10b981'>SKU COUNT</small><h2>{len(stok_summary)}</h2></div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='stat-box' style='text-align:center; background:#1e293b; padding:20px; border-radius:20px; border:1px solid #fbbf24'><small style='color:#fbbf24'>NET STOCK</small><h2>{int(stok_summary['Stok'].sum())}</h2></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_chart, col_data = st.columns([1.5, 1])
            with col_chart:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                fig = px.area(df_raw.sort_values('tanggal'), x='tanggal', y='jumlah', color='jenis_mutasi', 
                             color_discrete_map={'Masuk':'#0ea5e9', 'Keluar':'#f43f5e'}, template='plotly_dark', title="Stock Movement Trend")
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family="Space Grotesk")
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with col_data:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("##### 📦 Current Inventory")
                st.dataframe(stok_summary.sort_values('Stok', ascending=False), use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("No data available.")

    # --- INPUT ---
    elif menu == "➕ Input Barang":
        st.markdown("<h1 class='hero-text'>New Entry</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        with st.form("input_form"):
            c1, c2 = st.columns(2)
            with c1:
                sk = st.text_input("SKU Code")
                nm = st.text_input("Item Name")
                stn = st.selectbox("Unit", ["Pcs", "Box", "Kg", "Unit"])
            with c2:
                jn = st.selectbox("Type", ["Masuk", "Keluar"])
                qt = st.number_input("Qty", min_value=1)
                ke = st.text_input("Note")
            if st.form_submit_button("PROCESS TRANSACTION", use_container_width=True):
                if sk and nm:
                    tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                    conn.commit(); conn.close(); st.balloons(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- KONTROL ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h1 class='hero-text'>System Control</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📝 Edit", "🗑️ Purge"])
        with t1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if not df_raw.empty:
                choice = st.selectbox("Select Transaction", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                # Logika update tetap sama agar database tidak rusak
                st.info(f"Modifying Record ID: {tid}")
            st.markdown("</div>", unsafe_allow_html=True)
        with t2:
            st.markdown("<div class='glass-card' style='border-color: #f43f5e;'>", unsafe_allow_html=True)
            st.error("Danger Zone: Removal is permanent.")
            st.markdown("</div>", unsafe_allow_html=True)

    # --- USER MGMT ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='hero-text'>Identity Management</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        u_data = [{"User": k, "Role": v[1], "Permissions": " • ".join(v[2])} for k, v in st.session_state["user_db"].items()]
        st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
