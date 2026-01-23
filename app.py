import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman
st.set_page_config(page_title="INV-PRIME PRO", page_icon="🚀", layout="wide")

if "user_db" not in st.session_state:
    st.session_state["user_db"] = dict(st.secrets["auth_users"])

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #0f172a; }
    .metric-card {
        background: #1e293b; padding: 15px; border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1); text-align: center;
    }
    .metric-label { font-size: 0.85rem; color: #94a3b8; font-weight: 600; }
    .metric-value { font-size: 1.8rem; font-weight: 700; margin-top: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Database
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# FUNGSI PARSING ANTI-ERROR (PENTING!)
def parse_detail(val):
    try:
        parts = [p.strip() for p in str(val).split('|')]
        # Pastikan ada 6 komponen: SKU, Nama, Satuan, Inputer, Editor, Keterangan
        while len(parts) < 6:
            parts.append("-")
        return parts
    except:
        return ["-", str(val), "-", "-", "-", "-"]

# --- AUTH ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:white;'>🚀 LOGIN INV-PRIME</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.rerun()
                else: st.error("Akses Ditolak")
else:
    # --- LOAD DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except Exception as e:
        st.error(f"Koneksi DB Gagal: {e}")
        df_raw = pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"### 🛡️ {st.session_state['current_user'].upper()}")
        st.markdown("---")
        start_date = st.date_input("📅 Mulai", datetime.now() - timedelta(days=365))
        end_date = st.date_input("📅 Akhir", datetime.now())
        
        with st.expander("🛠️ Menu Transaksi"):
            mode = st.radio("Aksi:", ["Input", "Edit", "Hapus"])
            if mode == "Input":
                with st.form("f_add", clear_on_submit=True):
                    sk, nm = st.text_input("SKU"), st.text_input("Nama")
                    qt = st.number_input("Qty", 1)
                    jn = st.selectbox("Jenis", ["Masuk", "Keluar"])
                    stn = st.selectbox("Sat", ["Pcs", "Box", "Kg", "Unit"])
                    ket = st.text_input("Ket", value="-")
                    if st.form_submit_button("Simpan"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ket}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                        conn.commit(); conn.close(); st.rerun()
            
            elif mode == "Edit" and not df_raw.empty:
                edit_id = st.selectbox("ID Edit", df_raw['id'])
                old_val = df_raw[df_raw['id'] == edit_id].iloc[0]
                p = parse_detail(old_val['nama_barang'])
                with st.form("f_edit"):
                    enm = st.text_input("Nama", value=p[1])
                    eqt = st.number_input("Qty", value=int(old_val['jumlah']))
                    if st.form_submit_button("Update"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full_upd = f"{p[0]} | {enm} | {p[2]} | {p[3]} | {st.session_state['current_user']} | {p[5]}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, eqt, now, int(edit_id)))
                        conn.commit(); conn.close(); st.rerun()

            elif mode == "Hapus" and not df_raw.empty:
                del_id = st.selectbox("ID Hapus", df_raw['id'])
                if st.button("🔴 Konfirmasi Hapus"):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id=%s", (int(del_id),))
                    conn.commit(); conn.close(); st.rerun()

        with st.expander("🔐 Security & Users"):
            st.dataframe(pd.DataFrame(list(st.session_state["user_db"].items()), columns=['User', 'Pass']), use_container_width=True)
            nu, np = st.text_input("User Baru"), st.text_input("Pass Baru")
            if st.button("ADD USER"):
                if nu and np: st.session_state["user_db"][nu] = np; st.rerun()
            u_rem = st.selectbox("Hapus User:", ["-"] + [u for u in st.session_state["user_db"].keys() if u != st.session_state["current_user"]])
            if st.button("DEL USER") and u_rem != "-":
                del st.session_state["user_db"][u_rem]; st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD ---
    st.markdown("<h2 style='color:white;'>📊 Command Center</h2>", unsafe_allow_html=True)
    if not df_raw.empty:
        # Parsing data dengan pengaman
        details = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'] = details.apply(lambda x: x[0])
        df_raw['Item'] = details.apply(lambda x: x[1])
        df_raw['Keterangan'] = details.apply(lambda x: x[5])
        
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_p = df_raw.loc[mask].copy()

        # Metrics
        c1, c2 = st.columns(2)
        c1.markdown(f"<div class='metric-card'><div class='metric-label'>MASUK</div><div class='metric-value'>{int(df_p[df_p['jenis_mutasi']=='Masuk']['jumlah'].sum())}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-label'>KELUAR</div><div class='metric-value'>{int(df_p[df_p['jenis_mutasi']=='Keluar']['jumlah'].sum())}</div></div>", unsafe_allow_html=True)

        st.markdown("### 📜 Log Aktivitas")
        st.dataframe(df_p[['tanggal', 'SKU', 'Item', 'jenis_mutasi', 'jumlah', 'Keterangan']], use_container_width=True, hide_index=True)
    else:
        st.warning("Belum ada data.")
