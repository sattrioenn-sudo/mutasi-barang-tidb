import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px

# 1. Konfigurasi Halaman & UI Premium Penuh Warna
st.set_page_config(page_title="SATRIO POS PRO", page_icon="⚡", layout="wide")

# Inisialisasi User & Permissions
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Input", "Edit", "User Management"]]
    }

# --- CSS CUSTOM VIBRANT & ELEGANT DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    /* Background Utama dengan Gradient Mewah */
    .stApp { 
        background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #581c87 100%); 
        color: #f8fafc; 
    }
    
    /* Glassmorphism Card dengan Border Glow */
    .glass-card {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
        border-radius: 24px;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        margin-bottom: 20px;
    }
    
    /* Warna-warni Metric Container */
    .metric-blue { background: rgba(14, 165, 233, 0.15); border-left: 5px solid #0ea5e9; padding: 1.5rem; border-radius: 16px; }
    .metric-rose { background: rgba(244, 63, 94, 0.15); border-left: 5px solid #f43f5e; padding: 1.5rem; border-radius: 16px; }
    .metric-emerald { background: rgba(16, 185, 129, 0.15); border-left: 5px solid #10b981; padding: 1.5rem; border-radius: 16px; }
    .metric-amber { background: rgba(245, 158, 11, 0.15); border-left: 5px solid #f59e0b; padding: 1.5rem; border-radius: 16px; }
    
    /* Sidebar Styling */
    [data-testid="stSidebar"] { 
        background: rgba(15, 23, 42, 0.95) !important; 
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Judul dengan Gradient Text */
    .gradient-text {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
    
    /* Custom Buttons */
    .stButton>button { 
        border-radius: 14px !important; 
        background: linear-gradient(90deg, #6366f1, #a855f7) !important; 
        border: none !important; color: white !important; font-weight: 700 !important;
        height: 3rem; transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    .stButton>button:hover { 
        transform: scale(1.02); 
        box-shadow: 0 10px 20px rgba(168, 85, 247, 0.4); 
    }
    
    /* Tab Styling */
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px 10px 0 0;
        padding: 10px 20px;
        color: white;
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
        st.markdown("<div style='text-align:center;'><h1 class='gradient-text' style='font-size:3rem;'>SATRIO POS PRO</h1><p style='color:#94a3b8;'>Elite Inventory Management System</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("👤 Username")
            p = st.text_input("🔑 Password", type="password")
            if st.form_submit_button("AUTHENTICATE SYSTEM", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2]})
                    st.rerun()
                else: st.error("Access Denied: Invalid Credentials")
else:
    user_aktif, role_aktif, izin_user = st.session_state["current_user"], st.session_state["user_role"], st.session_state["user_perms"]

    # Load Data
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
        st.markdown(f"<h2 class='gradient-text'>{user_aktif.upper()}</h2><p style='color:#818cf8;'>{role_aktif}</p>", unsafe_allow_html=True)
        nav_options = [opt for opt, perm in zip(["📊 Dashboard", "➕ Input Barang", "🔧 Kontrol Transaksi", "👥 Manajemen User"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in izin_user]
        menu = st.selectbox("COMMAND CENTER", nav_options)
        st.markdown("---")
        start_date = st.date_input("Filter Date From", datetime.now() - timedelta(days=30))
        end_date = st.date_input("To", datetime.now())
        if st.button("🚪 TERMINATE SESSION", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- MENU: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h2 class='gradient-text'>📊 Analytics Command Center</h2>", unsafe_allow_html=True)
        if not df_raw.empty:
            df_f = df_raw[(df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)]
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stok')
            
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='metric-blue'><small>TOTAL MASUK</small><h3>{int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum())}</h3></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='metric-rose'><small>TOTAL KELUAR</small><h3>{int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum())}</h3></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='metric-emerald'><small>SKU COUNT</small><h3>{len(stok_summary)}</h3></div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='metric-amber'><small>TOTAL STOCK</small><h3>{int(stok_summary['Stok'].sum())}</h3></div>", unsafe_allow_html=True)

            c1, c2 = st.columns([2, 1])
            with c1:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                df_trend = df_f.groupby([df_f['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().reset_index()
                fig_line = px.line(df_trend, x='tanggal', y='jumlah', color='jenis_mutasi', markers=True,
                                  color_discrete_map={'Masuk': '#0ea5e9', 'Keluar': '#f43f5e'}, title="Stock Flow Analysis", template='plotly_dark')
                fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_line, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                fig_pie = px.pie(stok_summary[stok_summary['Stok']>0], values='Stok', names='Item', hole=0.5, title="Inventory Distribution", template='plotly_dark')
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("No data found in current period.")

    # --- MENU: INPUT ---
    elif menu == "➕ Input Barang":
        st.markdown("<h2 class='gradient-text'>➕ New Transaction</h2>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        with st.form("input_form"):
            c1, c2 = st.columns(2)
            with c1:
                sk = st.text_input("🆔 SKU / Barcode")
                nm = st.text_input("📦 Item Name")
                stn = st.selectbox("📏 Unit", ["Pcs", "Box", "Kg", "Unit", "Liter"])
            with c2:
                jn = st.selectbox("🔄 Mutation Type", ["Masuk", "Keluar"])
                qt = st.number_input("🔢 Quantity", min_value=1)
                ke = st.text_area("📝 Note", height=70)
            if st.form_submit_button("🚀 PUSH TO CLOUD DATABASE", use_container_width=True):
                if sk and nm:
                    tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                    conn.commit(); conn.close(); st.balloons(); st.success("Transaction Secured!"); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- MENU: KONTROL ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h2 class='gradient-text'>🔧 System Management</h2>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["📝 Edit Transaction", "🗑️ Delete Records"])
        with t1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            choice = st.selectbox("Select ID to update:", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
            tid = int(choice.split('|')[0].replace('ID:','').strip())
            row = df_raw[df_raw['id'] == tid].iloc[0]
            p = parse_detail(row['nama_barang'])
            with st.form("edit_f"):
                ec1, ec2 = st.columns(2)
                with ec1:
                    enm = st.text_input("New Name", value=p[1])
                    eqt = st.number_input("New Qty", value=int(row['jumlah']))
                with ec2:
                    ejn = st.selectbox("New Type", ["Masuk", "Keluar"], index=0 if row['jenis_mutasi'] == "Masuk" else 1)
                    eke = st.text_input("New Note", value=p[5])
                if st.form_submit_button("🔥 UPDATE SYSTEM", use_container_width=True):
                    upd_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {eke}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, jenis_mutasi=%s WHERE id=%s", (upd_val, eqt, ejn, tid))
                    conn.commit(); conn.close(); st.success("Database Synchronized!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with t2:
            st.markdown("<div class='danger-zone' style='background:rgba(244,63,94,0.1); padding:2rem; border-radius:20px; border:1px solid #f43f5e;'>", unsafe_allow_html=True)
            did = st.selectbox("Delete ID:", df_raw['id'])
            if st.button("🚨 PERMANENT DELETE", use_container_width=True):
                conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id = %s", (int(did),))
                conn.commit(); conn.close(); st.warning(f"Record {did} Purged!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- MENU: USER MANAGEMENT ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h2 class='gradient-text'>👥 User Access Control</h2>", unsafe_allow_html=True)
        cl, cf = st.columns([1.5, 1])
        with cl:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            u_data = [{"User": k, "Jabatan": v[1], "Akses": " • ".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with cf:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            m_u = st.radio("Mode:", ["Tambah Baru", "Edit / Hapus User"], horizontal=True)
            with st.form("u_form"):
                if m_u == "Tambah Baru":
                    un_i = st.text_input("Username")
                    ps_i = st.text_input("Password", type="password")
                    rl_i = st.text_input("Level Jabatan", placeholder="IT, Manager, dll")
                else:
                    un_i = st.selectbox("Select User", list(st.session_state["user_db"].keys()))
                    ps_i = st.text_input("New Password", value=st.session_state["user_db"][un_i][0])
                    rl_i = st.text_input("Level Jabatan", value=st.session_state["user_db"][un_i][1])
                
                i_dash = st.checkbox("Dashboard", value=True)
                i_input = st.checkbox("Input", value=True)
                i_edit = st.checkbox("Control", value=False)
                i_um = st.checkbox("User Management", value=False)
                
                cb1, cb2 = st.columns([2, 1])
                with cb1:
                    if st.form_submit_button("💾 SAVE CONFIG"):
                        if un_i and rl_i:
                            perms = [p for p, v in zip(["Dashboard", "Input", "Edit", "User Management"], [i_dash, i_input, i_edit, i_um]) if v]
                            st.session_state["user_db"][un_i] = [ps_i, rl_i, perms]; st.success("Updated!"); st.rerun()
                with cb2:
                    if m_u == "Edit / Hapus User" and st.form_submit_button("🗑️ DEL"):
                        if un_i != "admin":
                            del st.session_state["user_db"][un_i]; st.warning("Deleted!"); st.rerun()
                        else: st.error("Protected!")
            st.markdown("</div>", unsafe_allow_html=True)
