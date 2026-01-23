import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & Tema Premium
st.set_page_config(page_title="INV-PRIME PRO", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #0f172a; }
    
    /* Styling Kartu Metrik */
    .metric-card {
        background: #1e293b;
        padding: 12px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; }
    .metric-value { font-size: 1.5rem; font-weight: 700; margin-top: 5px; }

    /* Custom Label Style */
    .label-box {
        background: white; color: black; padding: 15px; border-radius: 8px; 
        border: 2px dashed #333; text-align: center; font-family: 'Courier New', monospace;
    }
    
    [data-testid="stSidebar"] { background-color: #1e293b; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Database
def init_connection():
    return mysql.connector.connect(
        host=st.secrets["tidb"]["host"],
        port=int(st.secrets["tidb"]["port"]),
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        ssl_verify_cert=False,
        use_pure=True
    )

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def parse_inventory_name(val):
    parts = str(val).split('|')
    parts = [p.strip() for p in parts]
    while len(parts) < 6: parts.append("-")
    return parts

# --- LOGIN ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:white;'>🚀 INV-PRIME PRO</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK", use_container_width=True):
                users = st.secrets["auth_users"]
                if u in users and str(p) == str(users[u]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.rerun()
                else: st.error("Akses Ditolak")
else:
    # --- LOAD DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT id, nama_barang, jenis_mutasi, jumlah, tanggal FROM inventory", conn)
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")
        df_raw = pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 🛡️ {st.session_state['current_user'].upper()}")
        st.markdown("---")
        start_date = st.date_input("📅 Mulai", datetime.now() - timedelta(days=7))
        end_date = st.date_input("📅 Akhir", datetime.now())
        st.markdown("---")
        
        # TAB MENU AKSI
        with st.expander("🛠️ Menu Transaksi"):
            mode = st.radio("Pilih Aksi:", ["Input", "Edit", "Hapus"])
            
            if mode == "Input":
                with st.form("f_add", clear_on_submit=True):
                    sk, nm, qt = st.text_input("SKU"), st.text_input("Nama"), st.number_input("Qty", 1)
                    jn, stn = st.selectbox("Jenis", ["Masuk", "Keluar"]), st.selectbox("Sat", ["Pcs", "Box", "Kg"])
                    if st.form_submit_button("Simpan", use_container_width=True):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | -"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                        conn.commit(); conn.close(); st.rerun()
            
            elif mode == "Edit" and not df_raw.empty:
                edit_id = st.selectbox("ID Edit", df_raw['id'].sort_values(ascending=False))
                row_edit = df_raw[df_raw['id'] == edit_id].iloc[0]
                p_old = parse_inventory_name(row_edit['nama_barang'])
                with st.form("f_edit"):
                    e_nm = st.text_input("Nama Barang", value=p_old[1])
                    e_qt = st.number_input("Qty", value=int(row_edit['jumlah']))
                    if st.form_submit_button("Update", use_container_width=True):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full_upd = f"{p_old[0]} | {e_nm} | {p_old[2]} | {p_old[3]} | {st.session_state['current_user']} | -"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, e_qt, now, int(edit_id)))
                        conn.commit(); conn.close(); st.rerun()

            elif mode == "Hapus" and not df_raw.empty:
                del_id = st.selectbox("ID Hapus", df_raw['id'].sort_values(ascending=False))
                if st.button("🔴 KONFIRMASI HAPUS", use_container_width=True):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(del_id),))
                    conn.commit(); conn.close(); st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- DASHBOARD CONTENT ---
    if not df_raw.empty:
        # Pre-processing
        p = df_raw['nama_barang'].apply(parse_inventory_name)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'] = p.str[0], p.str[1], p.str[2]
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

        # Hitung Laporan Opname
        awal = df_raw[df_raw['tanggal'].dt.date < start_date].groupby('SKU')['adj'].sum().reset_index(name='Awal')
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_p = df_raw.loc[mask].copy()
        
        mut = df_p.groupby(['SKU', 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0).reset_index()
        for c in ['Masuk', 'Keluar']:
            if c not in mut: mut[c] = 0

        res = pd.merge(df_raw[['SKU', 'Item', 'Unit']].drop_duplicates('SKU'), awal, on='SKU', how='left').fillna(0)
        res = pd.merge(res, mut[['SKU', 'Masuk', 'Keluar']], on='SKU', how='left').fillna(0)
        res['Saldo'] = res['Awal'] + res['Masuk'] - res['Keluar']

        # Header Section
        st.markdown("<h3 style='color:white;'>📊 Command Center Laporan</h3>", unsafe_allow_html=True)
        col_m1, col_m2, col_chart = st.columns([0.8, 0.8, 2.4])
        
        with col_m1:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>TOTAL MASUK</div><div class='metric-value' style='color:#38bdf8;'>{int(res['Masuk'].sum())}</div></div>", unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"<div class='metric-card'><div class='metric-label'>TOTAL KELUAR</div><div class='metric-value' style='color:#f87171;'>{int(res['Keluar'].sum())}</div></div>", unsafe_allow_html=True)
        with col_chart:
            top_5 = res.sort_values('Keluar', ascending=False).head(5)
            top_5 = top_5[top_5['Keluar'] > 0]
            if not top_5.empty:
                st.bar_chart(top_5.set_index('Item')['Keluar'], height=150)
            else: st.info("Tidak ada mutasi keluar periode ini.")

        # Laporan Opname Table
        st.markdown("### 📋 Ringkasan Stock Opname")
        st.dataframe(res[['SKU', 'Item', 'Unit', 'Awal', 'Masuk', 'Keluar', 'Saldo']], use_container_width=True, hide_index=True)

        # Footer Section
        b1, b2 = st.columns([1, 2])
        with b1:
            st.markdown("### 🏷️ Cetak Label")
            s_sku = st.selectbox("Pilih SKU:", ["-"] + list(res['SKU']))
            if s_sku != "-":
                r_data = res[res['SKU'] == s_sku].iloc[0]
                st.markdown(f"<div class='label-box'><b>{r_data['SKU']}</b><br>{r_data['Item']}<br><small>Stok: {int(r_data['Saldo'])}</small></div>", unsafe_allow_html=True)
        with b2:
            st.markdown("### 📜 Log Pergerakan")
            df_p['St'] = df_p['jenis_mutasi'].apply(lambda x: "🟢" if x == 'Masuk' else "🔴")
            st.dataframe(df_p[['St', 'tanggal', 'SKU', 'Item', 'jumlah']], use_container_width=True, hide_index=True)
    else:
        st.info("Database masih kosong.")
