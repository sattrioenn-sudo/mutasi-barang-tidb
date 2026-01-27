import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, date
import pytz
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="SATRIO POS PRO", page_icon="💎", layout="wide")

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
        padding: 1.5rem; border-radius: 24px;
        backdrop-filter: blur(15px); box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-bottom: 20px;
    }
    .shimmer-text {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #38bdf8);
        background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite; font-weight: 800; font-size: 2.5rem;
    }
    @keyframes shimmer { to { background-position: 200% center; } }
    .metric-box { text-align: center; padding: 1rem; border-radius: 18px; background: rgba(255, 255, 255, 0.02); border: 1px solid rgba(255, 255, 255, 0.05); }
    
    /* Receipt Styling */
    .receipt-container {
        background: #ffffff; color: #1e293b; padding: 30px; border-radius: 20px; 
        box-shadow: 0 20px 50px rgba(0,0,0,0.3); font-family: 'Courier New', Courier, monospace; 
        position: relative; overflow: hidden; border-top: 8px solid #f43f5e;
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
        df_raw['Pembuat'], df_raw['Editor'], df_raw['Note'] = p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[4]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

    # --- SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.markdown(f"<h2 class='shimmer-text' style='font-size:1.5rem;'>{user_aktif.upper()}</h2>", unsafe_allow_html=True)
        all_menus = {"📊 Dashboard": "Dashboard", "➕ Barang Masuk": "Masuk", "📤 Barang Keluar": "Keluar", "🔧 Kontrol Transaksi": "Edit", "👥 Manajemen User": "User Management"}
        nav_options = [m for m, p in all_menus.items() if p in izin_user]
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        if st.button("🚪 LOGOUT"):
            st.session_state["logged_in"] = False; st.rerun()

    # --- MENU: DASHBOARD ---
    if menu == "📊 Dashboard":
        st.markdown("<h1 class='shimmer-text'>Operational Intelligence</h1>", unsafe_allow_html=True)
        with st.sidebar:
            st.markdown("---")
            st.markdown("📅 **Filter Periode**")
            d_range = st.date_input("Pilih Rentang Tanggal", [date.today().replace(day=1), date.today()])
        
        if not df_raw.empty and len(d_range) == 2:
            mask = (df_raw['tanggal'].dt.date >= d_range[0]) & (df_raw['tanggal'].dt.date <= d_range[1])
            df_filt = df_raw.loc[mask]
            stok_summary = df_raw.groupby(['SKU', 'Item'])['adj'].sum().reset_index(name='Stock')
            
            m1, m2, m3, m4 = st.columns(4)
            with m1: st.markdown(f"<div class='glass-card metric-box'><small style='color:#38bdf8'>INFLOW</small><h2>{int(df_filt[df_filt['jenis_mutasi']=='Masuk']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='glass-card metric-box'><small style='color:#f43f5e'>OUTFLOW</small><h2>{int(df_filt[df_filt['jenis_mutasi']=='Keluar']['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='glass-card metric-box'><small style='color:#10b981'>ACTIVE SKU</small><h2>{len(stok_summary[stok_summary['Stock']>0])}</h2></div>", unsafe_allow_html=True)
            with m4: st.markdown(f"<div class='glass-card metric-box' style='border-color:#fbbf24'><small style='color:#fbbf24'>BALANCE</small><h2>{int(stok_summary['Stock'].sum())}</h2></div>", unsafe_allow_html=True)
            
            st.markdown("### 🔍 Log Transaksi Per Periode")
            t_in, t_out, t_stok = st.tabs(["📥 Log Masuk", "📤 Log Keluar", "📦 Sisa Stok"])
            with t_in: st.dataframe(df_filt[df_filt['jenis_mutasi']=='Masuk'][['tanggal', 'SKU', 'Item', 'jumlah', 'Unit', 'Pembuat', 'Note']], use_container_width=True, hide_index=True)
            with t_out: st.dataframe(df_filt[df_filt['jenis_mutasi']=='Keluar'][['tanggal', 'SKU', 'Item', 'jumlah', 'Unit', 'Pembuat', 'Note']], use_container_width=True, hide_index=True)
            with t_stok: st.dataframe(stok_summary[stok_summary['Stock'] > 0], use_container_width=True, hide_index=True)
        else: st.info("Pilih rentang tanggal yang valid.")

    # --- MENU: BARANG KELUAR ---
    elif menu == "📤 Barang Keluar":
        st.markdown("<h1 class='shimmer-text' style='background: linear-gradient(90deg, #f43f5e, #fb7185); -webkit-background-clip: text;'>Outbound System</h1>", unsafe_allow_html=True)
        if not df_raw.empty:
            stok_skrng = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index()
            stok_ready = stok_skrng[stok_skrng['adj'] > 0]
            
            col_f, col_r = st.columns([1, 1.2])
            with col_f:
                st.markdown("<div class='glass-card' style='border-color: rgba(244,63,94,0.3)'>", unsafe_allow_html=True)
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
                    st.markdown(f"""
                        <div class="receipt-container">
                            <div style="text-align: center; margin-bottom: 20px;">
                                <h2 style="margin: 0; color: #0f172a; letter-spacing: 2px;">SATRIO POS PRO</h2>
                                <p style="margin: 0; font-size: 0.8rem; color: #64748b;">DIGITAL DELIVERY RECEIPT</p>
                                <div style="border-bottom: 2px solid #e2e8f0; margin: 15px 0;"></div>
                            </div>
                            <div style="font-size: 0.9rem; line-height: 1.6;">
                                <div style="display: flex; justify-content: space-between;"><span><b>REF:</b></span><span>SJ-{r.get('id','-')}</span></div>
                                <div style="display: flex; justify-content: space-between;"><span><b>DATE:</b></span><span>{r.get('time','-')}</span></div>
                                <div style="background: #f8fafc; padding: 15px; border-radius: 12px; border: 1px dashed #cbd5e1; margin: 15px 0;">
                                    <div style="font-weight: bold; font-size: 1.1rem;">[{r.get('sku','N/A')}] {r.get('item','-')}</div>
                                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px;">
                                        <span style="font-size: 1.3rem; font-weight: 800; color: #f43f5e;">{r.get('qty',0)} {r.get('unit','')}</span>
                                        <span style="background: #fee2e2; color: #f43f5e; padding: 2px 10px; border-radius: 20px; font-size: 0.65rem; font-weight: bold;">KELUAR</span>
                                    </div>
                                </div>
                                <p style="margin: 0;"><b>PENERIMA:</b> {r.get('to','-')}</p>
                            </div>
                            <div style="text-align: center; border-top: 1px solid #e2e8f0; padding-top: 15px; margin-top: 20px; font-size: 0.7rem; color: #94a3b8;">
                                {datetime.now().year} © Satrio POS System
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    if st.button("🗑️ Hapus Struk"): del st.session_state['receipt']; st.rerun()
        else: st.warning("Stok sedang kosong.")

    # --- MENU LAIN ---
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

    elif menu == "🔧 Kontrol Transaksi":
        st.markdown("<h1 class='shimmer-text'>System Control</h1>", unsafe_allow_html=True)
        t1, t2 = st.tabs(["✏️ Edit Data", "🗑️ Hapus"])
        with t1:
            if not df_raw.empty:
                choice = st.selectbox("Pilih Record", df_raw.apply(lambda x: f"ID:{x['id']} | {x['Item']}", axis=1))
                tid = int(choice.split('|')[0].replace('ID:','').strip())
                row = df_raw[df_raw['id'] == tid].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("edit_f"):
                    enm, eqt = st.text_input("Item Name", value=p[1]), st.number_input("Qty", value=int(row['jumlah']))
                    ejn = st.selectbox("Mutation", ["Masuk", "Keluar"], index=0 if row['jenis_mutasi']=="Masuk" else 1)
                    eke = st.text_area("Note", value=p[5])
                    if st.form_submit_button("UPDATE DATA"):
                        new_v = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {user_aktif} | {eke}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, jenis_mutasi=%s WHERE id=%s", (new_v, eqt, ejn, tid))
                        conn.commit(); conn.close(); st.success("Updated!"); st.rerun()
        with t2:
            did = st.selectbox("ID to Delete", df_raw['id'] if not df_raw.empty else [])
            if st.button("🚨 DELETE PERMANENT"):
                conn = init_connection(); cur = conn.cursor(); cur.execute("DELETE FROM inventory WHERE id=%s", (int(did),))
                conn.commit(); conn.close(); st.warning("Deleted!"); st.rerun()

    elif menu == "👥 Manajemen User":
        st.markdown("<h1 class='shimmer-text'>User Control</h1>", unsafe_allow_html=True)
        cl, cf = st.columns([1.5, 1])
        with cl:
            u_data = [{"User": k, "Role": v[1], "Akses": "•".join(v[2])} for k, v in st.session_state["user_db"].items()]
            st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)
        with cf:
            mode = st.radio("Aksi", ["Tambah", "Edit/Hapus"], horizontal=True)
            with st.form("user_m"):
                un = st.text_input("Username") if mode == "Tambah" else st.selectbox("Pilih User", [u for u in st.session_state["user_db"].keys() if u != 'admin'])
                ps, rl = st.text_input("Password", type="password"), st.text_input("Role")
                p_dash, p_in, p_out, p_ed, p_um = st.checkbox("Dashboard", value=True), st.checkbox("Masuk", value=True), st.checkbox("Keluar", value=True), st.checkbox("Edit", value=False), st.checkbox("User Management", value=False)
                if st.form_submit_button("SIMPAN"):
                    perms = [p for p, v in zip(["Dashboard", "Masuk", "Keluar", "Edit", "User Management"], [p_dash, p_in, p_out, p_ed, p_um]) if v]
                    st.session_state["user_db"][un] = [ps, rl, perms]; st.rerun()
