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
    .stApp { background: radial-gradient(circle at top left, #1e1b4b, #0f172a); background-attachment: fixed; }
    
    .glass-card {
        background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 25px; border-radius: 24px; backdrop-filter: blur(20px);
        transition: all 0.4s ease; box-shadow: 0 15px 35px rgba(0,0,0,0.2); margin-bottom: 20px;
    }
    .glass-card:hover { border: 1px solid rgba(56, 189, 248, 0.4); transform: translateY(-5px); }

    .hero-text {
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        font-weight: 800; letter-spacing: -1px;
    }

    .stat-box {
        padding: 20px; border-radius: 20px; background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05); text-align: center;
    }

    .stButton>button {
        background: linear-gradient(135deg, #0ea5e9 0%, #2563eb 100%) !important;
        border: none !important; border-radius: 15px !important; color: white !important;
        font-weight: 600 !important; transition: all 0.3s ease !important;
    }
    
    [data-testid="stSidebar"] { background: rgba(10, 15, 30, 0.8) !important; backdrop-filter: blur(10px) !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Core
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

def parse_detail(val):
    parts = [p.strip() for p in str(val).split('|')]
    # Memastikan ada 6 elemen agar tidak error (SKU, Nama, Satuan, Pembuat, Pengedit, Ket)
    while len(parts) < 6: parts.append("-")
    return parts

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- LOGIC AUTH ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 class='hero-text' style='font-size:3.5rem; margin-bottom:0;'>SATRIO</h1><h2 style='color:#f8fafc; font-weight:300; margin-top:0;'>POS PRO ELITE</h2></div>", unsafe_allow_html=True)
        with st.form("login_aesthetic"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("UNLOCK SYSTEM", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    st.session_state.update({"logged_in": True, "current_user": u, "user_role": st.session_state["user_db"][u][1], "user_perms": st.session_state["user_db"][u][2]})
                    st.rerun()
                else: st.error("Access Forbidden")
else:
    user_aktif, role_aktif, izin_user = st.session_state["current_user"], st.session_state["user_role"], st.session_state["user_perms"]

    # --- DATA ENGINE (Full Parsing) ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'] = p_data.apply(lambda x: x[0])
        df_raw['Item'] = p_data.apply(lambda x: x[1])
        df_raw['Unit'] = p_data.apply(lambda x: x[2])
        df_raw['CreatedBy'] = p_data.apply(lambda x: x[3])
        df_raw['Note'] = p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<h1 class='hero-text'>{user_aktif.upper()}</h1>", unsafe_allow_html=True)
        st.markdown(f"<p style='color:#94a3b8;'>{role_aktif}</p>", unsafe_allow_html=True)
        nav_options = [opt for opt, perm in zip(["📊 Dashboard", "➕ Input Barang", "🔧 Kontrol Transaksi", "👥 Manajemen User"], ["Dashboard", "Input", "Edit", "User Management"]) if perm in izin_user]
        menu = st.selectbox("COMMAND CENTER", nav_options)
        st.markdown("---")
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='hero-text'>Operations Insight</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            stok_summary = df_raw.groupby(['Item'])['adj'].sum().reset_index(name='Stock')
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='stat-box'><small style='color:#38bdf8;'>IN</small><h2>{int(df_raw[df_raw['jenis_mutasi']=='Masuk']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='stat-box'><small style='color:#f43f5e;'>OUT</small><h2>{int(df_raw[df_raw['jenis_mutasi']=='Keluar']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='stat-box'><small style='color:#10b981;'>SKU</small><h2>{len(stok_summary)}</h2></div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='stat-box'><small style='color:#fbbf24;'>TOTAL</small><h2>{int(stok_summary['Stock'].sum())}</h2></div>", unsafe_allow_html=True)

            st.markdown("<div class='glass-card' style='margin-top:20px;'>", unsafe_allow_html=True)
            st.markdown("##### 📦 Inventory Data Grid")
            st.dataframe(df_raw[['id', 'SKU', 'Item', 'Unit', 'jenis_mutasi', 'jumlah', 'CreatedBy', 'tanggal', 'Note']], use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("Database Empty")

    # --- INPUT (LENGKAP) ---
    elif menu == "➕ Input Barang":
        st.markdown("<h1 class='hero-text'>New Entry</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        with st.form("input_full"):
            c1, c2 = st.columns(2)
            with c1:
                sk = st.text_input("🆔 SKU / Barcode")
                nm = st.text_input("📦 Item Name")
                stn = st.selectbox("📏 Unit", ["Pcs", "Box", "Kg", "Unit", "Liter", "Meter"])
            with c2:
                jn = st.selectbox("🔄 Mutation", ["Masuk", "Keluar"])
                qt = st.number_input("🔢 Quantity", min_value=1)
                ke = st.text_area("📝 Note", height=70)
            if st.form_submit_button("🚀 SAVE TO DATABASE", use_container_width=True):
                if sk and nm:
                    tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                    # Format lengkap: SKU | Nama | Satuan | Pembuat | Pengedit | Ket
                    full_val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full_val, jn, qt, now))
                    conn.commit(); conn.close(); st.balloons(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- KONTROL ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h1 class='hero-text'>Control Hub</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["✏️ Edit Record", "🗑️ Delete Record"])
        with t1:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            if not df_raw.empty:
                choice = st.selectbox("Select Transaction", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("edit_full"):
                    enm = st.text_input("Edit Name", value=p[1])
                    eqt = st.number_input("Edit Qty", value=int(row['jumlah']))
                    eke = st.text_input("Edit Note", value=p[5])
                    if st.form_submit_button("APPLY UPDATE"):
                        upd_val = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {eke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s WHERE id=%s", (upd_val, eqt, tid))
                        conn.commit(); conn.close(); st.success("Updated!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
        with t2:
            st.markdown("<div class='glass-card' style='border:1px solid #f43f5e;'>", unsafe_allow_html=True)
            did = st.selectbox("Delete ID", df_raw['id'] if not df_raw.empty else [0])
            if st.button("🚨 PERMANENT DELETE", use_container_width=True):
                conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id=%s", (int(did),))
                conn.commit(); conn.close(); st.warning("Deleted!"); st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

    # --- USER MGMT (LENGKAP + HAPUS) ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='hero-text'>Identity Control</h1>", unsafe_allow_html=True)
        cl, cf = st.columns([1.5, 1])
        with cl:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            u_data = [{"User": k, "Jabatan": v[1], "Akses": " • ".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with cf:
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            m_u = st.radio("Action", ["Tambah Baru", "Edit / Hapus User"], horizontal=True)
            with st.form("u_manage"):
                if m_u == "Tambah Baru":
                    un_i, ps_i, rl_i = st.text_input("Username"), st.text_input("Password", type="password"), st.text_input("Jabatan")
                else:
                    un_i = st.selectbox("Select User", list(st.session_state["user_db"].keys()))
                    ps_i = st.text_input("New Password", value=st.session_state["user_db"][un_i][0])
                    rl_i = st.text_input("New Jabatan", value=st.session_state["user_db"][un_i][1])
                
                # Checkboxes Permissions
                st.write("Permissions:")
                c1, c2 = st.columns(2)
                p_dash = c1.checkbox("Dashboard", value=True)
                p_input = c1.checkbox("Input", value=True)
                p_edit = c2.checkbox("Edit", value=False)
                p_um = c2.checkbox("User Management", value=False)

                btn_save, btn_del = st.columns([2, 1])
                if btn_save.form_submit_button("💾 SAVE"):
                    perms = [p for p, v in zip(["Dashboard", "Input", "Edit", "User Management"], [p_dash, p_input, p_edit, p_um]) if v]
                    st.session_state["user_db"][un_i] = [ps_i, rl_i, perms]; st.rerun()
                if m_u == "Edit / Hapus User" and btn_del.form_submit_button("🗑️ DEL"):
                    if un_i != "admin":
                        del st.session_state["user_db"][un_i]; st.rerun()
                    else: st.error("Admin Protected!")
            st.markdown("</div>", unsafe_allow_html=True)
