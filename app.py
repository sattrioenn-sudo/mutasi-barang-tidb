import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date
import pytz
import plotly.express as px
import plotly.graph_objects as go

# 1. Konfigurasi Halaman
st.set_page_config(page_title="SATRIO POS PRO", page_icon="💎", layout="wide")

# Inisialisasi History Login di Memori Aplikasi
if "global_login_tracker" not in st.session_state:
    st.session_state["global_login_tracker"] = {}

# Inisialisasi User & Permissions
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard", "Masuk", "Keluar", "Edit", "User Management"]]
    }

# --- CSS QUANTUM DASHBOARD DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at top right, #1e1b4b, #0f172a, #020617); color: #f8fafc; }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem; border-radius: 20px;
        backdrop-filter: blur(15px); margin-bottom: 20px;
    }
    .shimmer-text {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #38bdf8);
        background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite; font-weight: 800; font-size: 2.2rem;
    }
    @keyframes shimmer { to { background-position: 200% center; } }
    .stat-label { color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { font-size: 1.8rem; font-weight: 800; color: #ffffff; margin-top: 5px; }
    
    .session-info {
        background: rgba(56, 189, 248, 0.05);
        border: 1px solid rgba(56, 189, 248, 0.2);
        padding: 12px; border-radius: 12px; margin-bottom: 15px;
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

# --- LOGIC AUTH ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 class='shimmer-text'>SATRIO POS</h1></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("SYSTEM ENTRY"):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    tz = pytz.timezone('Asia/Jakarta')
                    now_str = datetime.now(tz).strftime('%d/%m/%Y %H:%M')
                    
                    last_seen = st.session_state["global_login_tracker"].get(u, "First Session")
                    
                    st.session_state.update({
                        "logged_in": True, 
                        "current_user": u, 
                        "user_role": st.session_state["user_db"][u][1], 
                        "user_perms": st.session_state["user_db"][u][2],
                        "last_login_display": last_seen,
                        "current_login_time": now_str
                    })
                    
                    st.session_state["global_login_tracker"][u] = now_str
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
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
        df_raw['Pembuat'], df_raw['Editor'], df_raw['Note'] = p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[4]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<h2 class='shimmer-text' style='font-size:1.5rem;'>{user_aktif.upper()}</h2>", unsafe_allow_html=True)
        
        st.markdown(f"""
            <div class="session-info">
                <div style="font-size:0.65rem; color:#94a3b8; font-weight:bold;">LAST LOGIN</div>
                <div style="font-size:0.8rem; color:#f8fafc;">📅 {st.session_state.get('last_login_display')}</div>
                <div style="margin-top:8px; font-size:0.65rem; color:#94a3b8; font-weight:bold;">CURRENT LOGIN</div>
                <div style="font-size:0.8rem; color:#38bdf8;">🕒 {st.session_state.get('current_login_time')}</div>
            </div>
        """, unsafe_allow_html=True)
        
        all_menus = {"📊 Dashboard": "Dashboard", "➕ Barang Masuk": "Masuk", "📤 Barang Keluar": "Keluar", "🔧 Kontrol Transaksi": "Edit", "👥 Manajemen User": "User Management"}
        nav_options = [m for m, p in all_menus.items() if p in izin_user]
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        
        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- MENU: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='shimmer-text'>Control Tower</h1>", unsafe_allow_html=True)
        with st.container():
            _, c_filter2 = st.columns([2, 1])
            with c_filter2:
                d_range = st.date_input("Periode Analisis", [date.today().replace(day=1), date.today()])

        if not df_raw.empty and len(d_range) == 2:
            mask = (df_raw['tanggal'].dt.date >= d_range[0]) & (df_raw['tanggal'].dt.date <= d_range[1])
            df_filt = df_raw.loc[mask]
            stok_summary = df_raw.groupby(['SKU', 'Item'])['adj'].sum().reset_index(name='Stock')
            
            m1, m2, m3, m4 = st.columns(4)
            metrics = [
                ("Inbound Flow", int(df_filt[df_filt['jenis_mutasi']=='Masuk']['jumlah'].sum()), "#38bdf8", m1),
                ("Outbound Flow", int(df_filt[df_filt['jenis_mutasi']=='Keluar']['jumlah'].sum()), "#f43f5e", m2),
                ("Stock Value (Qty)", int(stok_summary['Stock'].sum()), "#fbbf24", m3),
                ("Active SKU", len(stok_summary[stok_summary['Stock']>0]), "#10b981", m4)
            ]
            for label, val, color, col in metrics:
                with col:
                    st.markdown(f"""<div class='glass-card' style='border-left: 5px solid {color}'>
                        <div class='stat-label'>{label}</div>
                        <div class='stat-value'>{val:,}</div>
                    </div>""", unsafe_allow_html=True)

            col_chart1, col_chart2 = st.columns([2, 1])
            with col_chart1:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                trend_df = df_filt.groupby([df_filt['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().reset_index()
                fig_trend = px.area(trend_df, x='tanggal', y='jumlah', color='jenis_mutasi',
                                    color_discrete_map={'Masuk':'#38bdf8', 'Keluar':'#f43f5e'},
                                    title="Activity Trend", template="plotly_dark")
                st.plotly_chart(fig_trend, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

            with col_chart2:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                mutasi_counts = df_filt['jenis_mutasi'].value_counts()
                fig_pie = px.pie(values=mutasi_counts.values, names=mutasi_counts.index, hole=0.7, 
                                 color_discrete_sequence=['#38bdf8', '#f43f5e'], title="Activity Mix")
                st.plotly_chart(fig_pie, use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)
        else: st.info("Pilih rentang tanggal.")

    # --- MENU: BARANG MASUK ---
    elif menu == "➕ Barang Masuk":
        st.markdown("<h1 class='shimmer-text'>Inbound Entry</h1>", unsafe_allow_html=True)
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        with st.form("input_in"):
            c1, c2 = st.columns(2)
            sk, nm = c1.text_input("SKU Code"), c1.text_input("Item Name")
            stn = c1.selectbox("Unit", ["Pcs", "Box", "Kg", "Unit"])
            qt, ke = c2.number_input("Qty Masuk", min_value=1), c2.text_area("Catatan")
            if st.form_submit_button("SAVE INBOUND"):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                val = f"{sk} | {nm} | {stn} | {user_aktif} | - | {ke}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (val, "Masuk", qt, now))
                conn.commit(); conn.close(); st.balloons(); st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # --- MENU: BARANG KELUAR ---
    elif menu == "📤 Barang Keluar":
        st.markdown("<h1 class='shimmer-text' style='background: linear-gradient(90deg, #f43f5e, #fb7185); -webkit-background-clip: text;'>Outbound System</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            stok_skrng = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index()
            stok_ready = stok_skrng[stok_skrng['adj'] > 0]
            col_f, col_r = st.columns([1, 1.2])
            with col_f:
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                with st.form("out_f"):
                    choice = st.selectbox("Pilih Barang", stok_ready.apply(lambda x: f"{x['SKU']} | {x['Item']} (Sisa: {int(x['adj'])} {x['Unit']})", axis=1))
                    sku_o = choice.split('|')[0].strip()
                    nama_o = choice.split('|')[1].split('(')[0].strip()
                    unit_o = stok_ready[stok_ready['SKU']==sku_o]['Unit'].iloc[0]
                    stok_m = int(stok_ready[stok_ready['SKU']==sku_o]['adj'].iloc[0])
                    qty_o = st.number_input("Qty Keluar", min_value=1, max_value=stok_m)
                    tujuan = st.text_input("Tujuan")
                    note_o = st.text_area("Catatan")
                    if st.form_submit_button("🔥 KONFIRMASI KELUAR"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz)
                        val = f"{sku_o} | {nama_o} | {unit_o} | {user_aktif} | - | TO: {tujuan} - {note_o}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (val, "Keluar", qty_o, now.strftime('%Y-%m-%d %H:%M:%S')))
                        conn.commit(); conn.close()
                        st.session_state['receipt'] = {"id": now.strftime('%y%m%d%H%M'), "item": nama_o, "qty": qty_o, "unit": unit_o, "to": tujuan, "time": now.strftime('%d/%m/%Y %H:%M'), "sku": sku_o}
                        st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with col_r:
                if 'receipt' in st.session_state:
                    r = st.session_state['receipt']
                    st.markdown(f"""<div style="background: white; color: #1e293b; padding: 25px; border-radius: 15px; border-top: 10px solid #f43f5e; font-family: 'Courier New';">
                        <center><h3>SURAT JALAN DIGITAL</h3><hr></center>
                        <b>ID:</b> SJ-{r.get('id')}<br><b>SKU:</b> {r.get('sku')}<br><b>ITEM:</b> {r.get('item')}<br>
                        <b>QTY:</b> {r.get('qty')} {r.get('unit')}<br><b>TUJUAN:</b> {r.get('to')}<br><b>WAKTU:</b> {r.get('time')}<hr>
                        <center><small>Admin: {user_aktif}</small></center>
                    </div>""", unsafe_allow_html=True)
                    if st.button("🗑️ Clear Struk"): del st.session_state['receipt']; st.rerun()

    # --- MENU: KONTROL ---
    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h1 class='shimmer-text'>System Control</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            choice = st.selectbox("Pilih Record", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
            tid = int(choice.split('|')[0].replace('ID:','').strip())
            row = df_raw[df_raw['id'] == tid].iloc[0]
            p = parse_detail(row['nama_barang'])
            with st.form("edit_f"):
                enm, eqt = st.text_input("Item Name", value=p[1]), st.number_input("Qty", value=int(row['jumlah']))
                ejn = st.selectbox("Mutation", ["Masuk", "Keluar"], index=0 if row['jenis_mutasi']=="Masuk" else 1)
                if st.form_submit_button("UPDATE DATA"):
                    new_v = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | EDITED"
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, jenis_mutasi=%s WHERE id=%s", (new_v, eqt, ejn, tid))
                    conn.commit(); conn.close(); st.success("Updated!"); st.rerun()

    # --- MENU: USER MANAGEMENT (REVISED) ---
    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='shimmer-text'>User Control</h1>", unsafe_allow_html=True)
        c_list, c_add = st.columns([1.5, 1])
        with c_list:
            st.markdown("### 📋 User Directory")
            u_data = [{"User": k, "Role": v[1], "Permissions": len(v[2]), "Last Login": st.session_state["global_login_tracker"].get(k, "Never")} for k, v in st.session_state["user_db"].items()]
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        with c_add:
            st.markdown("### 🛠️ Configuration")
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            t1, t2 = st.tabs(["Add/Update", "Remove"])
            with t1:
                with st.form("u_form"):
                    un, ps = st.text_input("Username"), st.text_input("Password", type="password")
                    rl = st.selectbox("Role", ["Staff", "Supervisor", "Manager"])
                    st.write("Access:")
                    p1, p2, p3, p4 = st.checkbox("Dashboard", True), st.checkbox("Masuk", True), st.checkbox("Keluar", True), st.checkbox("Edit", False)
                    p5 = st.checkbox("User Management", False)
                    if st.form_submit_button("SAVE"):
                        perms = [m for m, val in zip(["Dashboard", "Masuk", "Keluar", "Edit", "User Management"], [p1,p2,p3,p4,p5]) if val]
                        st.session_state["user_db"][un] = [ps, rl, perms]
                        st.success("User Updated"); st.rerun()
            with t2:
                target = st.selectbox("Select User", [u for u in st.session_state["user_db"].keys() if u != 'admin'])
                if st.button("🚨 DELETE"):
                    del st.session_state["user_db"][target]; st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
