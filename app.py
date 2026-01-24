import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px  # Library Diagram Tambahan

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
    .stPlotlyChart { background: rgba(30, 41, 59, 0.3); border-radius: 16px; padding: 10px; }
    h1, h2, h3 { color: #f8fafc !important; font-weight: 800 !important; }
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
        st.markdown("<div style='text-align:center;'><h1>SATRIO <span style='color:#38bdf8;'>POS PRO</span></h1><p style='color:#94a3b8;'>v2.5 Dashboard Edition</p></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = u
                    st.session_state["user_role"] = st.session_state["user_db"][u][1]
                    st.session_state["user_perms"] = st.session_state["user_db"][u][2]
                    st.rerun()
                else: st.error("Akses Ditolak!")
else:
    # --- APP CONTENT ---
    user_aktif = st.session_state["current_user"]
    role_aktif = st.session_state["user_role"]
    izin_user = st.session_state["user_perms"]

    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2])
        df_raw['Pembuat'], df_raw['Editor'], df_raw['Ket'] = p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[4]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    with st.sidebar:
        st.markdown(f"### ⚡ {user_aktif.upper()}")
        nav_options = []
        if "Dashboard" in izin_user: nav_options.append("📊 Dashboard")
        if "Input" in izin_user: nav_options.append("➕ Input Barang")
        if "Edit" in izin_user or "Hapus" in izin_user: nav_options.append("🔧 Kontrol Transaksi")
        if "User Management" in izin_user: nav_options.append("👥 Manajemen User")
        menu = st.selectbox("MAIN MENU", nav_options)
        st.markdown("---")
        start_date = st.date_input("Mulai", datetime.now() - timedelta(days=30))
        end_date = st.date_input("Akhir", datetime.now())
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    if not df_raw.empty:
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_f = df_raw.loc[mask].copy()
    else: df_f = pd.DataFrame()

    # --- MENU: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h2><span style='color:#38bdf8;'>📊</span> Analytics Dashboard</h2>", unsafe_allow_html=True)
        
        if df_f.empty:
            st.info("Data kosong untuk rentang tanggal yang dipilih.")
        else:
            # Row 1: Metrik Utama
            c1, c2, c3, c4 = st.columns(4)
            stok_total = df_raw.groupby(['Item'])['adj'].sum().reset_index()
            
            with c1: st.markdown(f"<div class='metric-container'><small>MASUK</small><br><b>{int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum())}</b></div>", unsafe_allow_html=True)
            with c2: st.markdown(f"<div class='metric-container'><small>KELUAR</small><br><b>{int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum())}</b></div>", unsafe_allow_html=True)
            with c3: st.markdown(f"<div class='metric-container'><small>TOTAL ITEM</small><br><b>{len(stok_total)}</b></div>", unsafe_allow_html=True)
            with c4: st.markdown(f"<div class='metric-container'><small>STOK GUDANG</small><br><b>{int(stok_total['adj'].sum())}</b></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Row 2: Diagram Visual
            col_chart1, col_chart2 = st.columns([2, 1])
            
            with col_chart1:
                st.markdown("### 📈 Tren Aktivitas Barang")
                # Group data by date and mutation type
                df_trend = df_f.groupby([df_f['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().reset_index()
                fig_trend = px.line(df_trend, x='tanggal', y='jumlah', color='jenis_mutasi',
                                  color_discrete_map={'Masuk': '#38bdf8', 'Keluar': '#f43f5e'},
                                  template="plotly_dark", markers=True)
                fig_trend.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350)
                st.plotly_chart(fig_trend, use_container_width=True)

            with col_chart2:
                st.markdown("### 🥧 Komposisi Stok")
                # Filter item yang stoknya > 0
                df_pie = stok_total[stok_total['adj'] > 0]
                fig_pie = px.pie(df_pie, values='adj', names='Item', hole=0.4,
                               template="plotly_dark", color_discrete_sequence=px.colors.sequential.Skycloud)
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=350, showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)

            # Row 3: Bar Chart & Dataframe
            col_bar, col_tbl = st.columns([1, 1])
            with col_bar:
                st.markdown("### 📊 Top 5 Barang Terbanyak")
                top_5 = stok_total.sort_values(by='adj', ascending=False).head(5)
                fig_bar = px.bar(top_5, x='adj', y='Item', orientation='h',
                               template="plotly_dark", color='adj', color_continuous_scale='Blues')
                fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', height=300)
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col_tbl:
                st.markdown("### 📝 Log Transaksi Terakhir")
                st.dataframe(df_f[['tanggal', 'Item', 'jenis_mutasi', 'jumlah']].head(10), use_container_width=True, hide_index=True)

    # --- MENU LAINNYA (Input, Kontrol, User Tetap Sama) ---
    elif menu == "➕ Input Barang":
        st.markdown("<h2>➕ Transaksi Baru</h2>", unsafe_allow_html=True)
        with st.form("input_form"):
            sk, nm, qt = st.text_input("SKU"), st.text_input("Nama Barang"), st.number_input("Qty", 1)
            jn, stn, ke = st.selectbox("Jenis", ["Masuk", "Keluar"]), st.selectbox("Unit", ["Pcs", "Box", "Kg"]), st.text_input("Notes", "-")
            if st.form_submit_button("SIMPAN DATA"):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                conn.commit(); conn.close(); st.success("Tersimpan!"); st.rerun()

    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h2>🔧 Kontrol Data</h2>", unsafe_allow_html=True)
        # Logika Edit/Hapus kamu yang sudah berhasil
        df_raw['sel'] = df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1)
        choice = st.selectbox("Pilih Data", df_raw['sel'])
        tid = int(choice.split('|')[0].replace('ID:','').strip())
        if st.button("HAPUS DATA"):
            conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id = %s", (tid,))
            conn.commit(); conn.close(); st.warning("Terhapus!"); st.rerun()

    elif menu == "👥 Manajemen User":
        st.markdown("<h2>👥 Pengaturan User</h2>", unsafe_allow_html=True)
        all_u = list(st.session_state["user_db"].keys())
        sel_u = st.selectbox("Pilih User", ["-- Baru --"] + all_u)
        with st.form("u_form"):
            un = st.text_input("Username", value="" if sel_u=="-- Baru --" else sel_u)
            ps = st.text_input("Password", value="" if sel_u=="-- Baru --" else st.session_state["user_db"][sel_u][0])
            if st.form_submit_button("Simpan User"):
                st.session_state["user_db"][un] = [ps, "Staff", ["Dashboard", "Input"]]
                st.success("User Tersimpan!"); st.rerun()
