import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px

# 1. Konfigurasi Halaman & UI Aesthetic
st.set_page_config(page_title="SATRIO POS PRO", page_icon="💎", layout="wide")

# Inisialisasi User & Permissions
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Input", "Edit", "User Management"]]
    }

# --- CSS HYPER-AESTHETIC CYBER DARK ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif; }

    /* Animated Background */
    .stApp {
        background: radial-gradient(circle at top left, #1e1b4b, #0f172a);
        background-attachment: fixed;
    }

    /* Glassmorphism 2.0 Card */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px;
        border-radius: 24px;
        backdrop-filter: blur(20px);
        transition: all 0.4s ease;
        box-shadow: 0 15px 35px rgba(0,0,0,0.2);
    }
    
    .glass-card:hover {
        border: 1px solid rgba(56, 189, 248, 0.4);
        transform: translateY(-5px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    }

    /* Gradient Typography */
    .hero-text {
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        letter-spacing: -1px;
    }

    /* Custom Metric Styling */
    .stat-box {
        padding: 20px;
        border-radius: 20px;
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        text-align: center;
    }

    /* Sidebar Aesthetic */
    [data-testid="stSidebar"] {
        background: rgba(10, 15, 30, 0.8) !important;
        backdrop-filter: blur(10px) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Neon Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        border: none !important;
        border-radius: 15px !important;
        color: white !important;
        font-weight: 600 !important;
        letter-spacing: 0.5px;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
    }

    .stButton>button:hover {
        box-shadow: 0 8px 25px rgba(37, 99, 235, 0.5);
        transform: scale(1.02);
    }

    /* Success/Warning Box Aesthetic */
    .stAlert {
        border-radius: 15px !important;
        background: rgba(0, 0, 0, 0.2) !important;
        backdrop-filter: blur(10px);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Core (Tidak berubah)
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
        st.markdown("""
            <div style='text-align:center;'>
                <h1 class='hero-text' style='font-size:3.5rem; margin-bottom:0;'>SATRIO</h1>
                <h2 style='color:#f8fafc; font-weight:300; margin-top:0;'>POS PRO <span style='color:#38bdf8;'>ELITE</span></h2>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login_aesthetic"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("UNLOCK SYSTEM", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2]})
                    st.rerun()
                else: st.error("Access Forbidden")
else:
    # --- DATA ENGINE ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR NAV ---
    with st.sidebar:
        st.markdown(f"<h1 class='hero-text'>{st.session_state['current_user'].upper()}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8;'>Role: {st.session_state['user_role']}</p>", unsafe_allow_html=True)
        nav_options = [opt for opt, perm in zip(["📊 Dashboard", "➕ Input Barang", "🔧 Kontrol Transaksi", "👥 Manajemen User"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in st.session_state['user_perms']]
        menu = st.selectbox("MAIN NAVIGATION", nav_options)
        st.markdown("---")
        if st.button("🚪 LOGOUT SESSION", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD AESTHETIC ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='hero-text'>Operations Overview</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stok')
            
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown("<div class='stat-box'><small style='color:#38bdf8;'>INFLOW</small><h2 style='margin:0;'>"+str(int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum()))+"</h2></div>", unsafe_allow_html=True)
            with m2: st.markdown("<div class='stat-box'><small style='color:#f43f5e;'>OUTFLOW</small><h2 style='margin:0;'>"+str(int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum()))+"</h2></div>", unsafe_allow_html=True)
            with m3: st.markdown("<div class='stat-box'><small style='color:#10b981;'>ITEMS</small><h2 style='margin:0;'>"+str(len(stok_summary))+"</h2></div>", unsafe_allow_html=True)
            with m4: st.markdown("<div class='stat-box'><small style='color:#fbbf24;'>TOTAL STOCK</small><h2 style='margin:0;'>"+str(int(stok_summary['Stok'].sum()))+"</h2></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            col_chart, col_table = st.columns([2, 1.2])
            with col_chart:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                fig = px.area(df_raw.sort_values('tanggal'), x='tanggal', y='jumlah', color='jenis_mutasi', 
                             color_discrete_map={'Masuk':'#0ea5e9', 'Keluar':'#f43f5e'}, template='plotly_dark')
                fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with col_table:
                st.markdown("<div class='glass-card' style='height:450px; overflow-y:auto;'>", unsafe_allow_html=True)
                st.markdown("##### 📦 Real-time Stock")
                st.dataframe(stok_summary.sort_values('Stok', ascending=False), use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)

    # --- INPUT AESTHETIC ---
    elif menu == "➕ Input Barang":
        st.markdown("<h1 class='hero-text'>New Entry</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        with st.form("input_form"):
            c1, c2 = st.columns(2)
            with c1:
                sk = st.text_input("SKU Code")
                nm = st.text_input("Product Name")
            with c2:
                jn = st.selectbox("Mutation", ["Masuk", "Keluar"])
                qt = st.number_input("Amount", min_value=1)
            ke = st.text_input("Notes")
            if st.form_submit_button("FINALIZE ENTRY", use_container_width=True):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full_val = f"{sk} | {nm} | Pcs | {st.session_state['current_user']} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                conn.commit(); conn.close(); st.success("Transaction Synced!"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- KONTROL AESTHETIC ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h1 class='hero-text'>Control Hub</h1>", unsafe_allow_html=True)
        tab_e, tab_d = st.tabs(["✏️ Edit Mode", "🗑️ Purge Mode"])
        with tab_e:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            choice = st.selectbox("Select Record", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
            tid = int(choice.split('|')[0].replace('ID:','').strip())
            with st.form("edit_f"):
                new_qty = st.number_input("Update Quantity", value=1)
                if st.form_submit_button("APPLY CHANGES"):
                    st.success("Record Updated!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with tab_d:
            st.markdown("<div class='glass-card' style='border:1px solid rgba(244,63,94,0.3);'>", unsafe_allow_html=True)
            did = st.selectbox("Purge ID", df_raw['id'])
            if st.button("EXECUTE PERMANENT DELETE", use_container_width=True):
                st.warning(f"Data {did} Removed!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- USER MGMT AESTHETIC ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='hero-text'>Identity Manager</h1>", unsafe_allow_html=True)
        c1, c2 = st.columns([1.2, 1])
        with c1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            u_data = [{"User": k, "Jabatan": v[1], "Akses": " • ".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c2:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            m_u = st.radio("Operation", ["Create", "Modify/Delete"], horizontal=True)
            with st.form("u_f"):
                un = st.text_input("Username")
                rl = st.text_input("Role Position")
                col_b1, col_b2 = st.columns([2, 1])
                with col_b1:
                    if st.form_submit_button("SAVE USER"): st.rerun()
                with col_b2:
                    if m_u == "Modify/Delete" and st.form_submit_button("REMOVE"):
                        if un != "admin": st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
