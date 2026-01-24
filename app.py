import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px
import plotly.graph_objects as go

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="💎", layout="wide")

# Inisialisasi User & Permissions
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Input", "Edit", "User Management"]]
    }

# --- CSS QUANTUM DASHBOARD DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    
    .stApp {
        background: radial-gradient(circle at top right, #1e1b4b, #0f172a, #020617);
        color: #f8fafc;
    }

    /* Card Aesthetic */
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem;
        border-radius: 24px;
        backdrop-filter: blur(15px);
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        margin-bottom: 20px;
    }

    /* Shimmer Effect for Title */
    .shimmer-text {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #38bdf8);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite;
        font-weight: 800;
        font-size: 2.5rem;
    }
    @keyframes shimmer { to { background-position: 200% center; } }

    /* Metric Box */
    .metric-box {
        text-align: center;
        padding: 1rem;
        border-radius: 18px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Core (Koneksi & Parsing)
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
    # (Form login tetap sama seperti sebelumnya agar aman)
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 class='shimmer-text'>SATRIO POS</h1></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("SYSTEM ENTRY"):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2]})
                    st.rerun()
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
        df_raw['Pembuat'], df_raw['Note'] = p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<h2 class='shimmer-text' style='font-size:1.5rem;'>{user_aktif.upper()}</h2>", unsafe_allow_html=True)
        nav_options = [opt for opt, perm in zip(["📊 Dashboard", "➕ Input Barang", "🔧 Kontrol Transaksi", "👥 Manajemen User"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in izin_user]
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        if st.button("🚪 LOGOUT"):
            st.session_state["logged_in"] = False; st.rerun()

    # --- MENU: DASHBOARD (DETAIL & KEREN) ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='shimmer-text'>Operational Intelligence</h1>", unsafe_allow_html=True)
        
        if not df_raw.empty:
            # Row 1: Key Metrics
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stock')
            tot_in = int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum())
            tot_out = int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum())
            
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='glass-card metric-box'><small style='color:#38bdf8'>INFLOW</small><h2>{tot_in}</h2></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='glass-card metric-box'><small style='color:#f43f5e'>OUTFLOW</small><h2>{tot_out}</h2></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='glass-card metric-box'><small style='color:#10b981'>TOTAL SKU</small><h2>{len(stok_summary)}</h2></div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='glass-card metric-box' style='border-color:#fbbf24'><small style='color:#fbbf24'>BALANCE</small><h2>{int(stok_summary['Stock'].sum())}</h2></div>", unsafe_allow_html=True)

            # Row 2: Charts (Diagram)
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                # Area Chart Trend
                fig_line = px.area(df_raw.sort_values('tanggal'), x='tanggal', y='jumlah', color='jenis_mutasi',
                                  color_discrete_map={'Masuk':'#0ea5e9', 'Keluar':'#f43f5e'},
                                  title="Stock Flow Over Time", template="plotly_dark")
                fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_line, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with c2:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                # Donut Chart Stock Composition
                fig_pie = px.pie(stok_summary[stok_summary['Stock']>0], values='Stock', names='Item', hole=0.5,
                                title="Inventory Distribution", template="plotly_dark")
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Row 3: Bar Comparison & Table
            c3, c4 = st.columns([1, 1.5])
            with c3:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                # Bar Chart Comparison
                df_bar = df_raw.groupby('jenis_mutasi')['jumlah'].sum().reset_index()
                fig_bar = px.bar(df_bar, x='jenis_mutasi', y='jumlah', color='jenis_mutasi',
                                color_discrete_map={'Masuk':'#10b981', 'Keluar':'#f43f5e'},
                                title="Volume Comparison", template="plotly_dark")
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            
            with c4:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.markdown("#### 📜 Recent Transactions")
                st.dataframe(df_raw[['SKU', 'Item', 'jenis_mutasi', 'jumlah', 'tanggal', 'Note']].head(10), use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No data available to visualize.")

    # --- MENU: INPUT (Tetap Lengkap) ---
    elif menu == "➕ Input Barang":
        st.markdown("<h1 class='shimmer-text'>Push Data</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        with st.form("input_f"):
            c1, c2 = st.columns(2)
            sk = c1.text_input("SKU Code")
            nm = c1.text_input("Item Name")
            stn = c1.selectbox("Unit", ["Pcs", "Box", "Kg", "Unit"])
            jn = c2.selectbox("Mutation", ["Masuk", "Keluar"])
            qt = c2.number_input("Qty", min_value=1)
            ke = c2.text_area("Note")
            if st.form_submit_button("SAVE TO DATABASE"):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (val, jn, qt, now))
                conn.commit(); conn.close(); st.balloons(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- MENU: KONTROL (LENGKAP: EDIT NAMA, QTY, KET, DLL) ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h1 class='shimmer-text'>System Control</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["✏️ Edit Data", "🗑️ Hapus"])
        with t1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if not df_raw.empty:
                choice = st.selectbox("Pilih Record", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("edit_f"):
                    c1, c2 = st.columns(2)
                    enm = c1.text_input("Item Name", value=p[1])
                    eqt = c1.number_input("Quantity", value=int(row['jumlah']))
                    ejn = c2.selectbox("Mutation", ["Masuk", "Keluar"], index=0 if row['jenis_mutasi']=="Masuk" else 1)
                    eke = c2.text_area("Keterangan", value=p[5])
                    if st.form_submit_button("🔥 UPDATE"):
                        new_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {eke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, jenis_mutasi=%s WHERE id=%s", (new_val, eqt, ejn, tid))
                        conn.commit(); conn.close(); st.success("Updated!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with t2:
            st.markdown("<div class='glass-card' style='border-color:#f43f5e'>", unsafe_allow_html=True)
            did = st.selectbox("ID to Delete", df_raw['id'] if not df_raw.empty else [])
            if st.button("🚨 DELETE PERMANENT"):
                conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id=%s", (int(did),))
                conn.commit(); conn.close(); st.warning("Deleted!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- MENU: USER MANAGEMENT (LENGKAP) ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='shimmer-text'>User Control</h1>", unsafe_allow_html=True)
        cl, cf = st.columns([1.5, 1])
        with cl:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            u_data = [{"User": k, "Role": v[1], "Akses": "•".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with cf:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            mode = st.radio("Aksi", ["Tambah", "Edit/Hapus"], horizontal=True)
            with st.form("user_m"):
                if mode == "Tambah":
                    un, ps, rl = st.text_input("Username"), st.text_input("Password", type="password"), st.text_input("Role")
                else:
                    un = st.selectbox("Pilih User", [u for u in st.session_state["user_db"].keys() if u != 'admin'])
                    ps = st.text_input("Password", value=st.session_state["user_db"][un][0] if un else "")
                    rl = st.text_input("Role", value=st.session_state["user_db"][un][1] if un else "")
                
                p_dash = st.checkbox("Dashboard", value=True)
                p_in = st.checkbox("Input", value=True)
                p_ed = st.checkbox("Edit", value=False)
                p_um = st.checkbox("User Management", value=False)

                b_save, b_del = st.columns([2, 1])
                if b_save.form_submit_button("SIMPAN"):
                    perms = [p for p, v in zip(["Dashboard", "Input", "Edit", "User Management"], [p_dash, p_in, p_ed, p_um]) if v]
                    st.session_state["user_db"][un] = [ps, rl, perms]; st.rerun()
                if mode == "Edit/Hapus" and b_del.form_submit_button("🗑️"):
                    del st.session_state["user_db"][un]; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
