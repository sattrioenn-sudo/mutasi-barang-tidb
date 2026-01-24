import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px  # Library baru untuk diagram

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="SATRIO POS PRO", page_icon="⚡", layout="wide")

# Inisialisasi User & Permissions
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Input", "Edit", "Hapus", "User Management"]]
    }

# --- CSS CUSTOM PREMIUM DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: radial-gradient(circle at 20% 10%, #1e293b 0%, #0f172a 100%); color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.8) !important; backdrop-filter: blur(15px); }
    .metric-container {
        background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    .chart-container {
        background: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px; padding: 1rem; margin-top: 1rem;
    }
    h1, h2, h3 { color: #f8fafc !important; font-weight: 800 !important; }
    .stButton>button { border-radius: 10px !important; background: linear-gradient(90deg, #0ea5e9, #2563eb) !important; color: white !important; font-weight: 600 !important; }
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
        st.markdown("<div style='text-align:center;'><h1>SATRIO <span style='color:#38bdf8;'>POS PRO</span></h1><p style='color:#94a3b8;'>Advanced Inventory Dashboard</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK KE SISTEM", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2]})
                    st.rerun()
                else: st.error("Kredensial Salah!")
else:
    user_aktif, role_aktif, izin_user = st.session_state["current_user"], st.session_state["user_role"], st.session_state["user_perms"]

    # Load & Process Data
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
        st.markdown(f"### ⚡ {user_aktif.upper()} ({role_aktif})")
        nav_options = [opt for opt, perm in zip(["📊 Dashboard", "➕ Input Barang", "🔧 Kontrol Transaksi", "👥 Manajemen User"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in izin_user]
        menu = st.selectbox("NAVIGATION", nav_options)
        st.markdown("---")
        start_date = st.date_input("Mulai", datetime.now() - timedelta(days=30))
        end_date = st.date_input("Akhir", datetime.now())
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- MENU: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h2><span style='color:#38bdf8;'>📊</span> Analytics Insight</h2>", unsafe_allow_html=True)
        if not df_raw.empty:
            df_f = df_raw[(df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)]
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stok')
            
            # Row 1: Key Metrics
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='metric-container'><small style='color:#38bdf8;'>TOTAL MASUK</small><br><h3>{int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum())}</h3></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='metric-container'><small style='color:#f43f5e;'>TOTAL KELUAR</small><br><h3>{int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum())}</h3></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='metric-container'><small style='color:#10b981;'>VARIASI SKU</small><br><h3>{len(stok_summary)}</h3></div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='metric-container'><small style='color:#fbbf24;'>TOTAL STOK</small><br><h3>{int(stok_summary['Stok'].sum())}</h3></div>", unsafe_allow_html=True)

            # Row 2: Charts
            col_chart1, col_chart2 = st.columns([2, 1])
            with col_chart1:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.markdown("#### Tren Aktivitas Harian")
                df_trend = df_f.groupby([df_f['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().reset_index()
                fig_line = px.line(df_trend, x='tanggal', y='jumlah', color='jenis_mutasi', markers=True,
                                  color_discrete_map={'Masuk': '#0ea5e9', 'Keluar': '#f43f5e'}, template='plotly_dark')
                fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig_line, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_chart2:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.markdown("#### Proporsi Stok")
                fig_pie = px.pie(stok_summary[stok_summary['Stok']>0], values='Stok', names='Item', hole=0.4, template='plotly_dark')
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300, showlegend=False, margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            # Row 3: Bar & Table
            c_bar, c_table = st.columns([1, 1])
            with c_bar:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.markdown("#### Top 5 Stok Terbanyak")
                top_stok = stok_summary.sort_values('Stok', ascending=False).head(5)
                fig_bar = px.bar(top_stok, x='Stok', y='Item', orientation='h', color='Stok', color_continuous_scale='Blues', template='plotly_dark')
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=250, margin=dict(l=0,r=0,t=20,b=0))
                st.plotly_chart(fig_bar, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
            with c_table:
                st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
                st.markdown("#### Log Transaksi Terkini")
                st.dataframe(df_f[['tanggal', 'Item', 'jenis_mutasi', 'jumlah']].head(8), use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("Database masih kosong, Bro!")

    # --- MENU: LAINNYA ---
    elif menu == "➕ Input Barang":
        st.markdown("<h2>➕ Transaksi Baru</h2>", unsafe_allow_html=True)
        with st.form("input_form"):
            col1, col2 = st.columns(2)
            with col1: sk, nm, qt = st.text_input("SKU"), st.text_input("Nama Barang"), st.number_input("Qty", 1)
            with col2: jn, stn, ke = st.selectbox("Jenis", ["Masuk", "Keluar"]), st.selectbox("Unit", ["Pcs", "Box", "Kg"]), st.text_input("Notes", "-")
            if st.form_submit_button("SUBMIT DATA", use_container_width=True):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                conn.commit(); conn.close(); st.success("Data Tersimpan!"); st.rerun()

    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h2>🔧 Control Center</h2>", unsafe_allow_html=True)
        if not df_raw.empty:
            tab_e, tab_h = st.tabs(["✏️ Edit Data", "🗑️ Hapus Data"])
            with tab_e:
                choice = st.selectbox("Pilih Data", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                with st.form("f_edit"):
                    enm = st.text_input("Nama Barang", value=parse_detail(row['nama_barang'])[1])
                    eqt = st.number_input("Qty", value=int(row['jumlah']))
                    if st.form_submit_button("UPDATE"):
                        p = parse_detail(row['nama_barang'])
                        upd_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {p[5]}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s WHERE id=%s", (upd_val, eqt, tid))
                        conn.commit(); conn.close(); st.success("Updated!"); st.rerun()
            with tab_h:
                did = st.selectbox("Hapus ID", df_raw['id'])
                if st.button("KONFIRMASI HAPUS", use_container_width=True):
                    conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id = %s", (int(did),))
                    conn.commit(); conn.close(); st.warning("Deleted!"); st.rerun()

    elif menu == "👥 Manajemen User":
        st.markdown("<h2>👥 User Management</h2>", unsafe_allow_html=True)
        all_u = list(st.session_state["user_db"].keys())
        st.table(pd.DataFrame([{"User": k, "Role": v[1], "Izin": ", ".join(v[2])} for k, v in st.session_state["user_db"].items()]))
        with st.form("add_user"):
            un, ps = st.text_input("New Username"), st.text_input("Password")
            if st.form_submit_button("ADD USER"):
                st.session_state["user_db"][un] = [ps, "Staff", ["Dashboard", "Input"]]
                st.success("User Added!"); st.rerun()
