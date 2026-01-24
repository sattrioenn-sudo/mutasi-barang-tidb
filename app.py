import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="PRIME-POS RETAIL PRO", page_icon="📈", layout="wide")

# Inisialisasi User di Memori (Session State)
if "user_db" not in st.session_state:
    st.session_state["user_db"] = dict(st.secrets["auth_users"])

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: #0f172a; }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        padding: 20px; border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center; box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .metric-label { font-size: 0.8rem; color: #94a3b8; font-weight: 600; letter-spacing: 1px; }
    .metric-value { font-size: 2rem; font-weight: 800; margin-top: 10px; color: #f8fafc; }
    </style>
    """, unsafe_allow_html=True)

# 2. Fungsi Database & Parsing
def init_connection():
    return mysql.connector.connect(**st.secrets["tidb"], ssl_verify_cert=False, use_pure=True)

def parse_detail(val):
    # Struktur: SKU | Nama | Satuan | Creator | Editor | Keterangan
    parts = [p.strip() for p in str(val).split('|')]
    while len(parts) < 6: parts.append("-")
    return parts

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- AUTH LOGIC ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:white;'>🚀 LOGIN PRIME-POS</h2>", unsafe_allow_html=True)
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

    # --- SIDEBAR CONTROL ---
    with st.sidebar:
        st.markdown(f"### 🛡️ ADMIN: {st.session_state['current_user'].upper()}")
        st.markdown("---")
        
        start_date = st.date_input("📅 Mulai", datetime.now() - timedelta(days=30))
        end_date = st.date_input("📅 Akhir", datetime.now())
        
        with st.expander("🛠️ Kelola Transaksi"):
            mode = st.radio("Pilih Aksi:", ["Input Baru", "Edit Data", "Hapus Data"])
            
            if mode == "Input Baru":
                with st.form("f_add", clear_on_submit=True):
                    sk, nm = st.text_input("SKU"), st.text_input("Nama Produk")
                    qt = st.number_input("Jumlah", 1)
                    jn = st.selectbox("Jenis", ["Masuk", "Keluar"])
                    stn = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit"])
                    ket = st.text_input("Keterangan", value="-")
                    if st.form_submit_button("Simpan Transaksi"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        # Simpan user login sebagai pembuat
                        full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ket}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                        conn.commit(); conn.close(); st.rerun()

            elif mode == "Edit Data" and not df_raw.empty:
                edit_id = st.selectbox("Pilih ID Transaksi:", df_raw['id'])
                row = df_raw[df_raw['id'] == edit_id].iloc[0]
                p = parse_detail(row['nama_barang'])
                with st.form("f_edit"):
                    enm = st.text_input("Nama Produk", value=p[1])
                    eqt = st.number_input("Jumlah", value=int(row['jumlah']))
                    estn = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit"], index=0)
                    eket = st.text_input("Keterangan", value=p[5])
                    if st.form_submit_button("Update Data"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        # Simpan p[3] (pembuat asal) dan user login sekarang sebagai pengedit
                        full_upd = f"{p[0]} | {enm} | {estn} | {p[3]} | {st.session_state['current_user']} | {eket}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, eqt, now, int(edit_id)))
                        conn.commit(); conn.close(); st.rerun()

            elif mode == "Hapus Data" and not df_raw.empty:
                del_id = st.selectbox("Hapus ID Transaksi:", df_raw['id'])
                if st.button("🔴 KONFIRMASI HAPUS"):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(del_id),))
                    conn.commit(); conn.close(); st.rerun()

        with st.expander("⚙️ Pengaturan & User"):
            st.dataframe(pd.DataFrame(list(st.session_state["user_db"].items()), columns=['User', 'Pass']), hide_index=True)
            nu, np = st.text_input("Username Baru"), st.text_input("Password Baru")
            if st.button("Tambah User"):
                if nu and np: st.session_state["user_db"][nu] = np; st.rerun()

        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DASHBOARD CONTENT ---
    st.markdown("<h2 style='color:white;'>📊 Business Dashboard</h2>", unsafe_allow_html=True)
    
    if not df_raw.empty:
        # Pecah Data Nama Barang menjadi kolom-kolom detail
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'] = p_data.apply(lambda x: x[0])
        df_raw['Item'] = p_data.apply(lambda x: x[1])
        df_raw['Unit'] = p_data.apply(lambda x: x[2])
        df_raw['Pembuat'] = p_data.apply(lambda x: x[3])
        df_raw['Editor'] = p_data.apply(lambda x: x[4])
        df_raw['Ket'] = p_data.apply(lambda x: x[5])
        
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_f = df_raw.loc[mask].copy()

        # Metrics
        c1, c2, c3 = st.columns(3)
        c1.markdown(f"<div class='metric-card'><div class='metric-label'>MASUK</div><div class='metric-value' style='color:#38bdf8;'>{int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum())}</div></div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='metric-card'><div class='metric-label'>KELUAR</div><div class='metric-value' style='color:#f87171;'>{int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum())}</div></div>", unsafe_allow_html=True)
        stok_skr = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Stok')
        c3.markdown(f"<div class='metric-card'><div class='metric-label'>JENIS PRODUK</div><div class='metric-value'>{len(stok_skr)}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tab_stok, tab_histori, tab_grafik = st.tabs(["📋 Stok & Satuan", "📜 Log Transaksi Detail", "📈 Analisis Grafik"])
        
        with tab_stok:
            st.dataframe(stok_skr, use_container_width=True, hide_index=True)

        with tab_histori:
            # MENAMPILKAN PEMBUAT DAN EDITOR DI SINI
            st.dataframe(df_f[['id', 'tanggal', 'SKU', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Pembuat', 'Editor', 'Ket']], 
                         use_container_width=True, hide_index=True)

        with tab_grafik:
            if not df_f.empty:
                st.markdown("#### Tren Pergerakan Barang")
                chart_data = df_f.groupby([df_f['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0)
                st.line_chart(chart_data)
                
                st.markdown("#### Top 5 Produk Terlaris")
                top_out = df_f[df_f['jenis_mutasi'] == 'Keluar'].groupby('Item')['jumlah'].sum().sort_values(ascending=False).head(5)
                if not top_out.empty: st.bar_chart(top_out)
            else:
                st.info("Pilih range tanggal untuk melihat grafik.")
    else:
        st.info("Database kosong.")
