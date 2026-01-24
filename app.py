import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz
import plotly.express as px

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
    
    .glass-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 2rem;
        border-radius: 20px;
        backdrop-filter: blur(10px);
        margin-bottom: 20px;
    }
    
    .metric-container {
        background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,0,0,0.2);
    }
    
    [data-testid="stSidebar"] { background-color: rgba(15, 23, 42, 0.9) !important; }
    h1, h2, h3 { color: #f8fafc !important; font-weight: 800 !important; letter-spacing: -0.5px; }
    
    .stButton>button { 
        border-radius: 12px !important; 
        background: linear-gradient(90deg, #0ea5e9, #2563eb) !important; 
        border: none !important; color: white !important; font-weight: 600 !important;
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 5px 15px rgba(14, 165, 233, 0.4); }
    
    .danger-zone {
        background: rgba(244, 63, 94, 0.1);
        border: 1px solid rgba(244, 63, 94, 0.2);
        padding: 1.5rem;
        border-radius: 15px;
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
            
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='metric-container'><small style='color:#38bdf8;'>TOTAL MASUK</small><br><h3>{int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum())}</h3></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='metric-container'><small style='color:#f43f5e;'>TOTAL KELUAR</small><br><h3>{int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum())}</h3></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='metric-container'><small style='color:#10b981;'>VARIASI SKU</small><br><h3>{len(stok_summary)}</h3></div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='metric-container'><small style='color:#fbbf24;'>TOTAL STOK</small><br><h3>{int(stok_summary['Stok'].sum())}</h3></div>", unsafe_allow_html=True)

            col_chart1, col_chart2 = st.columns([2, 1])
            with col_chart1:
                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                df_trend = df_f.groupby([df_f['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().reset_index()
                fig_line = px.line(df_trend, x='tanggal', y='jumlah', color='jenis_mutasi', markers=True,
                                  color_discrete_map={'Masuk': '#0ea5e9', 'Keluar': '#f43f5e'}, title="Tren Mutasi Harian", template='plotly_dark')
                fig_line.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
                st.plotly_chart(fig_line, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_chart2:
                st.markdown("<div class='metric-container'>", unsafe_allow_html=True)
                fig_pie = px.pie(stok_summary[stok_summary['Stok']>0], values='Stok', names='Item', hole=0.4, title="Komposisi Stok", template='plotly_dark')
                fig_pie.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', showlegend=False)
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("Database masih kosong!")

    # --- MENU: INPUT ---
    elif menu == "➕ Input Barang":
        st.markdown("<h2><span style='color:#38bdf8;'>➕</span> Pencatatan Transaksi Baru</h2>", unsafe_allow_html=True)
        with st.container():
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            with st.form("input_form_revised", clear_on_submit=True):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### 📦 Data Master Barang")
                    sk = st.text_input("SKU / Barcode", placeholder="Contoh: SN-001")
                    nm = st.text_input("Nama Lengkap Barang", placeholder="Masukan nama produk...")
                    stn = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit", "Liter", "Meter"])
                with c2:
                    st.markdown("##### 🔄 Logistik & Mutasi")
                    jn = st.selectbox("Jenis Transaksi", ["Masuk", "Keluar"])
                    qt = st.number_input("Jumlah Barang", min_value=1, step=1)
                    ke = st.text_area("Keterangan Tambahan", placeholder="Catatan opsional...", height=68)
                if st.form_submit_button("💾 SIMPAN KE CLOUD DATABASE", use_container_width=True):
                    if sk and nm:
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                        conn.commit(); conn.close()
                        st.balloons(); st.success(f"Data {nm} Berhasil Dicatat!"); st.rerun()
                    else: st.warning("Harap isi SKU dan Nama Barang!")
            st.markdown("</div>", unsafe_allow_html=True)

    # --- MENU: KONTROL ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h2><span style='color:#38bdf8;'>🔧</span> Control Management</h2>", unsafe_allow_html=True)
        if df_raw.empty: st.warning("Data tidak ditemukan.")
        else:
            t_edit, t_delete = st.tabs(["✏️ Mode Edit Cepat", "🗑️ Penghapusan Data"])
            with t_edit:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                choice = st.selectbox("Pilih item yang ingin dikoreksi:", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']} ({x['jenis_mutasi']})", axis=1))
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("form_edit_revised"):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        enm = st.text_input("Revisi Nama Barang", value=p[1])
                        eqt = st.number_input("Revisi Jumlah", value=int(row['jumlah']))
                    with ec2:
                        ejn = st.selectbox("Revisi Jenis", ["Masuk", "Keluar"], index=0 if row['jenis_mutasi'] == "Masuk" else 1)
                        eke = st.text_input("Revisi Catatan", value=p[5])
                    if st.form_submit_button("✅ KONFIRMASI PERUBAHAN", use_container_width=True):
                        upd_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {eke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, jenis_mutasi=%s WHERE id=%s", (upd_val, eqt, ejn, tid))
                        conn.commit(); conn.close(); st.success("Database telah diperbarui!"); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with t_delete:
                st.markdown("<div class='danger-zone'>", unsafe_allow_html=True)
                did = st.selectbox("Pilih ID Transaksi:", df_raw['id'])
                if st.button("🔥 HAPUS DATA PERMANEN", use_container_width=True):
                    conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id = %s", (int(did),))
                    conn.commit(); conn.close(); st.warning(f"Data ID {did} Berhasil Dihapus!"); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

    # --- MENU: USER MANAGEMENT (DYNAMIC ROLE) ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h2><span style='color:#38bdf8;'>👥</span> User Access Control</h2>", unsafe_allow_html=True)
        c_list, c_form = st.columns([3, 2])
        
        with c_list:
            st.markdown("<div class='glass-card' style='height: 100%;'>", unsafe_allow_html=True)
            st.markdown("##### 👥 Daftar Pengguna")
            u_data = [{"User": k, "Jabatan": v[1], "Akses": " • ".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
            
        with c_form:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.markdown("##### 🔑 Kelola Akun")
            m_user = st.radio("Aksi:", ["Tambah Baru", "Edit User"], horizontal=True)
            
            with st.form("form_user_dynamic"):
                if m_user == "Tambah Baru":
                    un_input = st.text_input("Username")
                    ps_input = st.text_input("Password", type="password")
                    # Diubah menjadi text_input agar bisa diisi bebas (IT Department, dsb)
                    rl_input = st.text_input("Level Jabatan", placeholder="Contoh: IT Department")
                else:
                    un_input = st.selectbox("Pilih User:", list(st.session_state["user_db"].keys()))
                    ps_input = st.text_input("Ganti Password", value=st.session_state["user_db"][un_input][0])
                    # Diubah menjadi text_input agar bisa diedit bebas
                    rl_input = st.text_input("Level Jabatan", value=st.session_state["user_db"][un_input][1])
                
                st.write("Izin Akses:")
                i_dash = st.checkbox("Dashboard", value=True)
                i_input = st.checkbox("Input Data", value=True)
                i_edit = st.checkbox("Kontrol/Edit", value=False)
                i_um = st.checkbox("User Management", value=False)
                
                if st.form_submit_button("💾 SIMPAN PENGATURAN USER", use_container_width=True):
                    if un_input and rl_input:
                        perms = []
                        if i_dash: perms.append("Dashboard")
                        if i_input: perms.append("Input")
                        if i_edit: perms.append("Edit")
                        if i_um: perms.append("User Management")
                        st.session_state["user_db"][un_input] = [ps_input, rl_input, perms]
                        st.success(f"User {un_input} ({rl_input}) Disimpan!"); st.rerun()
                    else: st.error("Username dan Jabatan wajib diisi!")
            st.markdown("</div>", unsafe_allow_html=True)
