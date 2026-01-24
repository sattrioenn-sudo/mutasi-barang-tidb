import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="⚡", layout="wide")

# Inisialisasi User
if "user_db" not in st.session_state:
    st.session_state["user_db"] = dict(st.secrets["auth_users"])

# --- CSS CUSTOM: THE "ULTRA MODERN" LOOK ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    
    /* Global Styles */
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp {
        background: radial-gradient(circle at top right, #1e293b, #0f172a);
    }

    /* Glassmorphism Cards */
    .metric-card {
        background: rgba(30, 41, 59, 0.7);
        backdrop-filter: blur(10px);
        padding: 25px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #38bdf8;
        box-shadow: 0 0 20px rgba(56, 189, 248, 0.2);
    }
    .metric-label { color: #94a3b8; font-size: 0.9rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .metric-value { color: #ffffff; font-size: 2.5rem; font-weight: 800; margin: 5px 0; }
    
    /* Custom Sidebar */
    [data-testid="stSidebar"] {
        background-color: rgba(15, 23, 42, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        background-color: rgba(30, 41, 59, 0.5);
        padding: 5px;
        border-radius: 12px;
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 8px 16px;
        color: #94a3b8;
        transition: all 0.2s;
    }
    .stTabs [aria-selected="true"] {
        background-color: #38bdf8 !important;
        color: #0f172a !important;
        font-weight: 700;
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

# --- AUTH LOGIC ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div style='text-align: center;'><h1 style='color: white; font-size: 3rem; margin-bottom:0;'>SATRIO <span style='color: #38bdf8;'>POS</span></h1><p style='color: #64748b; margin-bottom:30px;'>Inventory Management System v2.5</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("ENTER DASHBOARD", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.rerun()
                else: st.error("Invalid Credentials")
else:
    # --- LOAD DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 🛡️ {st.session_state['current_user'].upper()}")
        st.markdown("---")
        menu = st.selectbox("NAVIGATION", ["📊 Overview Dashboard", "📦 Inventory Manager", "👥 User Access"])
        st.markdown("---")
        st.markdown("🔍 **Filter Periode**")
        start_date = st.date_input("Start", datetime.now() - timedelta(days=30))
        end_date = st.date_input("End", datetime.now())
        if st.button("🚪 Sign Out", use_container_width=True):
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
    if menu == "📊 Overview Dashboard":
        st.markdown("<h2 style='color:white; margin-bottom: 25px;'>📈 Business Overview</h2>", unsafe_allow_html=True)
        
        # Row 1: Key Metrics
        m1, m2, m3, m4 = st.columns(4)
        total_in = int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum()) if not df_raw.empty else 0
        total_out = int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum()) if not df_raw.empty else 0
        stok_skr = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Stok') if not df_raw.empty else pd.DataFrame()
        
        m1.markdown(f"<div class='metric-card'><div class='metric-label'>Inbound</div><div class='metric-value'>{total_in}</div><div style='color:#10b981; font-size:0.8rem;'>📦 Items Received</div></div>", unsafe_allow_html=True)
        m2.markdown(f"<div class='metric-card'><div class='metric-label'>Outbound</div><div class='metric-value' style='color:#f87171;'>{total_out}</div><div style='color:#f87171; font-size:0.8rem;'>📤 Items Shipped</div></div>", unsafe_allow_html=True)
        m3.markdown(f"<div class='metric-card'><div class='metric-label'>Total SKU</div><div class='metric-value' style='color:#fbbf24;'>{len(stok_skr)}</div><div style='color:#fbbf24; font-size:0.8rem;'>🏷️ Active Products</div></div>", unsafe_allow_html=True)
        m4.markdown(f"<div class='metric-card'><div class='metric-label'>Stock Level</div><div class='metric-value' style='color:#38bdf8;'>{int(stok_skr['Stok'].sum()) if not stok_skr.empty else 0}</div><div style='color:#38bdf8; font-size:0.8rem;'>🏢 On Hand</div></div>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 2: Charts & Analysis
        c1, c2 = st.columns([2, 1])
        with c1:
            st.markdown("### 📈 Trend Mutasi Barang")
            if not df_f.empty:
                chart_data = df_f.groupby([df_f['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0)
                st.area_chart(chart_data, color=["#f87171", "#10b981"])
            else: st.info("Pilih periode data untuk melihat tren.")
        
        with c2:
            st.markdown("### 🏆 Top 5 Stock")
            if not stok_skr.empty:
                top_5 = stok_skr.sort_values('Stok', ascending=False).head(5)
                st.bar_chart(data=top_5, x="Item", y="Stok", color="#38bdf8")

        # Row 3: Live Data
        st.markdown("### 🕒 Recent Transactions")
        st.dataframe(df_f[['id', 'tanggal', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Pembuat']].head(10), use_container_width=True, hide_index=True)

    elif menu == "📦 Inventory Manager":
        st.markdown("<h2 style='color:white;'>📦 Inventory Operations</h2>", unsafe_allow_html=True)
        t_in, t_ed, t_del = st.tabs(["✨ Transaction Input", "🔧 Edit Records", "⚠️ Delete Records"])
        
        with t_in:
            with st.form("f_add_pro", clear_on_submit=True):
                col1, col2 = st.columns(2)
                with col1:
                    sk = st.text_input("Product SKU")
                    nm = st.text_input("Product Name")
                    qt = st.number_input("Quantity", min_value=1)
                with col2:
                    jn = st.selectbox("Type", ["Masuk", "Keluar"])
                    stn = st.selectbox("Unit", ["Pcs", "Box", "Kg", "Ltr"])
                    ke = st.text_input("Notes", "-")
                if st.form_submit_button("PROCESS TRANSACTION", use_container_width=True):
                    tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ke}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                    conn.commit(); conn.close(); st.success("Transaction Securely Recorded!"); st.rerun()

        with t_ed:
            if not df_raw.empty:
                df_raw['label'] = df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']} | {x['tanggal'].strftime('%H:%M')}", axis=1)
                target = st.selectbox("Select Transaction to Edit", df_raw['label'])
                tid = int(target.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("f_edit_pro"):
                    enm = st.text_input("Update Name", value=p[1])
                    eqt = st.number_input("Update Qty", value=int(row['jumlah']))
                    est = st.selectbox("Update Unit", ["Pcs", "Box", "Kg"], index=0)
                    eke = st.text_input("Update Notes", value=p[5])
                    if st.form_submit_button("COMMIT CHANGES"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full_upd = f"{p[0]} | {enm} | {est} | {p[3]} | {st.session_state['current_user']} | {eke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, eqt, now, tid))
                        conn.commit(); conn.close(); st.success("Updated!"); st.rerun()

        with t_del:
            if not df_raw.empty:
                did = st.selectbox("Select ID to Remove", df_raw['id'])
                st.error("WARNING: This action is permanent and will be logged.")
                conf = st.checkbox("I understand the consequences")
                if st.button("CONFIRM DELETE", disabled=not conf, use_container_width=True):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(did),))
                    conn.commit(); conn.close(); st.warning(f"Record {did} Deleted."); st.rerun()

    elif menu == "👥 User Access":
        st.markdown("<h2 style='color:white;'>👥 User Management</h2>", unsafe_allow_html=True)
        col_l, col_r = st.columns([1, 1])
        with col_l:
            st.markdown("### Active Personnel")
            st.table(pd.DataFrame(list(st.session_state["user_db"].items()), columns=['Username', 'Secret Key']))
        with col_r:
            st.markdown("### Access Control")
            with st.expander("Add New User"):
                nu = st.text_input("New Username")
                np = st.text_input("New Password", type="password")
                if st.button("Authorize"): st.session_state["user_db"][nu] = np; st.rerun()
            with st.expander("Revoke Access"):
                u_rem = st.selectbox("Choose User", ["-"] + [u for u in st.session_state["user_db"].keys() if u != st.session_state['current_user']])
                if st.button("Revoke Now") and u_rem != "-": del st.session_state["user_db"][u_rem]; st.rerun()
