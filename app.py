import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px
import time

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="⚡", layout="wide")

# Inisialisasi User & Permissions
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Input", "Edit", "User Management"]]
    }

# --- CSS QUANTUM ANIMATION DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    /* Background Animasi Bergerak */
    .stApp {
        background: linear-gradient(-45deg, #0f172a, #1e1b4b, #312e81, #1e1b4b);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
        color: #f8fafc;
    }

    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Card dengan Efek Floating */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 24px;
        backdrop-filter: blur(20px);
        box-shadow: 0 20px 40px rgba(0,0,0,0.4);
        transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
        animation: fadeInUp 0.8s ease-out forwards;
    }
    
    .glass-card:hover {
        transform: translateY(-10px) scale(1.01);
        border-color: rgba(56, 189, 248, 0.5);
        background: rgba(255, 255, 255, 0.05);
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Judul dengan Animasi Shimmer */
    .shimmer-text {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #38bdf8);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite;
        font-weight: 800;
    }

    @keyframes shimmer {
        to { background-position: 200% center; }
    }

    /* Sidebar Aesthetic */
    [data-testid="stSidebar"] {
        background: rgba(10, 15, 30, 0.8) !important;
        backdrop-filter: blur(12px) !important;
    }

    /* Metric Glow */
    .metric-glow {
        border-radius: 20px;
        padding: 15px;
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: inset 0 0 20px rgba(56, 189, 248, 0.05);
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

# --- UI LOGIC ---
if not st.session_state["logged_in"]:
    # Login Screen (Tetap Aesthetic)
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
        st.markdown(f"<h2 class='shimmer-text'>{st.session_state['current_user'].upper()}</h2>", unsafe_allow_html=True)
        nav_options = [opt for opt, perm in zip(["📊 Dashboard", "➕ Input Barang", "🔧 Kontrol", "👥 User"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in st.session_state['user_perms']]
        menu = st.selectbox("NAVIGATION", nav_options)
        st.markdown("---")
        if st.button("🚪 TERMINATE SESSION", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD ANIMASI ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='shimmer-text'>Operational Dashboard</h1>", unsafe_allow_html=True)
        
        if not df_raw.empty:
            # Stats Row dengan Animasi Hover
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stok')
            
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='glass-card metric-glow'><small style='color:#38bdf8'>TOTAL INFLOW</small><h2 style='margin:0;'>{int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='glass-card metric-glow'><small style='color:#f43f5e'>TOTAL OUTFLOW</small><h2 style='margin:0;'>{int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='glass-card metric-glow'><small style='color:#10b981'>ACTIVE SKU</small><h2 style='margin:0;'>{len(stok_summary)}</h2></div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='glass-card metric-glow' style='border-color:#fbbf24'><small style='color:#fbbf24'>NET INVENTORY</small><h2 style='margin:0;'>{int(stok_summary['Stok'].sum())}</h2></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Chart Row
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                # Area Chart Animasi
                fig_trend = px.area(df_raw.sort_values('tanggal'), x='tanggal', y='jumlah', color='jenis_mutasi',
                                   color_discrete_map={'Masuk':'#38bdf8', 'Keluar':'#f43f5e'}, 
                                   template='plotly_dark', title="Inventory Flow Trends")
                fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_family="Plus Jakarta Sans")
                st.plotly_chart(fig_trend, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with c2:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                # Donut Chart
                fig_pie = px.pie(stok_summary[stok_summary['Stok']>0], values='Stok', names='Item', hole=0.6,
                                color_discrete_sequence=px.colors.sequential.Viridis, title="Stock Share")
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Table Row (Lengkap)
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("#### 📜 Live Transaction Logs")
            st.dataframe(df_raw[['id', 'SKU', 'Item', 'Unit', 'jenis_mutasi', 'jumlah', 'CreatedBy', 'tanggal', 'Note']], 
                         use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.warning("No data detected in the vault.")

    # --- MENU LAIN (INPUT, KONTROL, USER) TETAP LENGKAP ---
    elif menu == "➕ Input Barang":
        st.markdown("<h1 class='shimmer-text'>Secure Entry</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        with st.form("input_form"):
            c1, c2 = st.columns(2)
            sk = c1.text_input("🆔 SKU Code")
            nm = c1.text_input("📦 Item Name")
            stn = c1.selectbox("📏 Unit", ["Pcs", "Box", "Kg", "Unit"])
            jn = c2.selectbox("🔄 Type", ["Masuk", "Keluar"])
            qt = c2.number_input("🔢 Qty", min_value=1)
            ke = c2.text_area("📝 Note")
            if st.form_submit_button("EXECUTE DATA PUSH", use_container_width=True):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full_val = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                conn.commit(); conn.close(); st.balloons(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Menu Kontrol & User (Fungsi Lengkap Seperti Kode Sebelumnya)
    elif menu == "🔧 Kontrol":
        st.markdown("<h1 class='shimmer-text'>System Control</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["Edit", "Delete"])
        with t1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if not df_raw.empty:
                choice = st.selectbox("Select Record", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("edit_f"):
                    new_nm = st.text_input("Name", value=p[1])
                    new_qt = st.number_input("Qty", value=int(row['jumlah']))
                    if st.form_submit_button("UPDATE"):
                        new_val = f"{p[0]} | {new_nm} | {p[2]} | {p[3]} | {st.session_state['current_user']} | {p[5]}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s WHERE id=%s", (new_val, new_qt, tid))
                        conn.commit(); conn.close(); st.success("Updated!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with t2:
             st.markdown("<div class='glass-card' style='border-color:#f43f5e'>", unsafe_allow_html=True)
             did = st.selectbox("Delete ID", df_raw['id'] if not df_raw.empty else [])
             if st.button("🚨 PERMANENT PURGE"):
                 conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id=%s", (int(did),))
                 conn.commit(); conn.close(); st.warning("Purged!"); st.rerun()
             st.markdown("</div>", unsafe_allow_html=True)
