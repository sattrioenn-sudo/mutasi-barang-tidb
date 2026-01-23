import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
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
    .metric-label { font-size: 0.85rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; }
    .metric-value { font-size: 1.8rem; font-weight: 700; margin-top: 5px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Database & Parsing Detail
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def parse_inventory_name(val):
    # Struktur: SKU | Nama | Satuan | Admin Input | Admin Edit | Keterangan
    parts = str(val).split('|')
    parts = [p.strip() for p in parts]
    while len(parts) < 6:
        parts.append("-")
    return parts

# --- PROSES LOGIN ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:white;'>🚀 INV-PRIME LOGIN</h2>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.rerun()
                else: st.error("Akses Ditolak")
else:
    # --- LOAD DATA TERBARU ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    # --- SIDEBAR: KONTROL TOTAL ---
    with st.sidebar:
        st.markdown(f"### 🛡️ {st.session_state['current_user'].upper()}")
        st.markdown("---")
        start_date = st.date_input("📅 Mulai", datetime.now() - timedelta(days=365))
        end_date = st.date_input("📅 Akhir", datetime.now())
        
        # --- MENU TRANSAKSI (DETAIL PENUH) ---
        with st.expander("🛠️ Menu Transaksi Barang"):
            mode = st.radio("Aksi:", ["Input", "Edit", "Hapus"])
            
            if mode == "Input":
                with st.form("f_add", clear_on_submit=True):
                    sk, nm = st.text_input("SKU"), st.text_input("Nama Barang")
                    qt = st.number_input("Jumlah (Qty)", 1)
                    jn = st.selectbox("Jenis Mutasi", ["Masuk", "Keluar"])
                    stn = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit", "Liter"])
                    ket = st.text_input("Keterangan", value="-")
                    if st.form_submit_button("Simpan Data"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        # Format simpan yang sangat detail
                        full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ket}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                        conn.commit(); conn.close(); st.rerun()

            elif mode == "Edit" and not df_raw.empty:
                edit_id = st.selectbox("Pilih ID Data:", df_raw['id'])
                row = df_raw[df_raw['id'] == edit_id].iloc[0]
                p = parse_inventory_name(row['nama_barang'])
                with st.form("f_edit"):
                    e_nm = st.text_input("Nama", value=p[1])
                    e_qt = st.number_input("Qty", value=int(row['jumlah']))
                    e_ket = st.text_input("Keterangan", value=p[5])
                    if st.form_submit_button("Update"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        # Update Editor dengan user yang sedang login tanpa hapus inputer awal
                        full_upd = f"{p[0]} | {e_nm} | {p[2]} | {p[3]} | {st.session_state['current_user']} | {e_ket}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, e_qt, now, int(edit_id)))
                        conn.commit(); conn.close(); st.rerun()

            elif mode == "Hapus" and not df_raw.empty:
                del_id = st.selectbox("Hapus ID:", df_raw['id'])
                if st.button("🔴 KONFIRMASI HAPUS"):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(del_id),))
                    conn.commit(); conn.close(); st.rerun()

        # --- MENU SECURITY (LIHAT PASS) ---
        with st.expander("🔐 Security & Users"):
            st.write("**Data Login Aktif:**")
            df_u = pd.DataFrame(list(st.session_state["user_db"].items()), columns=['Username', 'Password'])
            st.table(df_u)
            nu, np = st.text_input("Username Baru"), st.text_input("Password Baru")
            if st.button("TAMBAH USER"):
                if nu and np: st.session_state["user_db"][nu] = np; st.rerun()
            st.markdown("---")
            list_rem = [u for u in st.session_state["user_db"].keys() if u != st.session_state["current_user"]]
            u_rem = st.selectbox("Hapus Akses:", ["-"] + list_rem)
            if st.button("HAPUS USER") and u_rem != "-":
                del st.session_state["user_db"][u_rem]; st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD UTAMA (DETAIL LAPORAN) ---
    st.markdown("<h2 style='color:white;'>📊 Command Center Inventory</h2>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # Menarik semua detail dari kolom nama_barang
        parsed = df_raw['nama_barang'].apply(parse_inventory_name)
        df_raw['SKU'] = parsed.str[0]
        df_raw['Item'] = parsed.str[1]
        df_raw['Unit'] = parsed.str[2]
        df_raw['Inputer'] = parsed.str[3]
        df_raw['Editor'] = parsed.str[4]
        df_raw['Keterangan'] = parsed.str[5]
        
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_p = df_raw.loc[mask].copy()
        
        # 1. METRIK VISUAL
        c1, c2, c3 = st.columns([1, 1, 2])
        m_in = df_p[df_p['jenis_mutasi'] == 'Masuk']['jumlah'].sum()
        m_out = df_p[df_p['jenis_mutasi'] == 'Keluar']['jumlah'].sum()
        c1.markdown(f"<div class='metric-card'><div class='metric-label'>TOTAL MASUK</div><div class='metric-value' style='color:#38bdf8;'>{int(m_in)}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-label'>TOTAL KELUAR</div><div class='metric-value' style='color:#f87171;'>{int(m_out)}</div></div>", unsafe_allow_html=True)
        with c3:
            if not df_p.empty:
                st.bar_chart(df_p.groupby('Item')['jumlah'].sum().head(5), height=160)

        # 2. LAPORAN STOCK OPNAME (TABEL 1)
        st.markdown("### 📋 Ringkasan Stok Barang")
        st
