import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman & UI Premium
st.set_page_config(page_title="RETAIL-SATRIO PRO", page_icon="🛍️", layout="wide")

# Inisialisasi User
if "user_db" not in st.session_state:
    st.session_state["user_db"] = dict(st.secrets["auth_users"])

# CSS Custom untuk Tampilan Mewah
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0f172a; }
    
    /* Card Style */
    .metric-card {
        background: #1e293b;
        padding: 24px;
        border-radius: 16px;
        border: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
    }
    .metric-card:hover { transform: translateY(-5px); border-color: #38bdf8; }
    .metric-label { color: #94a3b8; font-size: 0.85rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { color: #f8fafc; font-size: 2.2rem; font-weight: 700; margin: 8px 0; }
    
    /* Sidebar styling */
    section[data-testid="stSidebar"] { background-color: #1e293b !important; width: 300px !important; }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; background-color: transparent; }
    .stTabs [data-baseweb="tab"] {
        height: 50px; background-color: transparent; border: none; 
        color: #94a3b8; font-weight: 600; font-size: 1rem;
    }
    .stTabs [aria-selected="true"] { color: #38bdf8 !important; border-bottom: 2px solid #38bdf8 !important; }
    
    /* Status Badge */
    .badge-in { background-color: #064e3b; color: #34d399; padding: 4px 12px; border-radius: 99px; font-size: 0.8rem; font-weight: 600; }
    .badge-out { background-color: #450a0a; color: #f87171; padding: 4px 12px; border-radius: 99px; font-size: 0.8rem; font-weight: 600; }
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
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("""
            <div style='text-align: center; margin-bottom: 20px;'>
                <h1 style='color: white; font-size: 2.5rem;'>SATRIO <span style='color: #38bdf8;'>POS</span></h1>
                <p style='color: #94a3b8;'>Inventory Management System v2.0</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("MASUK KE DASHBOARD", use_container_width=True):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u]):
                    st.session_state["logged_in"], st.session_state["current_user"] = True, u
                    st.rerun()
                else: st.error("Kredensial salah, silakan coba lagi.")
else:
    # --- LOAD DATA ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
        conn.close()
    except: df_raw = pd.DataFrame()

    # --- SIDEBAR NAV ---
    with st.sidebar:
        st.markdown(f"""
            <div style='padding: 10px; border-radius: 10px; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.2); margin-bottom: 20px;'>
                <p style='margin:0; color: #38bdf8; font-size: 0.8rem;'>LOGGED IN AS</p>
                <h3 style='margin:0; color: white;'>{st.session_state['current_user'].upper()}</h3>
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📅 Periode Laporan")
        start_date = st.date_input("Mulai", datetime.now() - timedelta(days=30))
        end_date = st.date_input("Akhir", datetime.now())
        
        st.markdown("---")
        st.markdown("### 🛠️ Manajemen")
        menu = st.selectbox("Pilih Menu:", ["Dashboard & Stok", "Input Transaksi", "Edit/Hapus Data", "Kelola User"])
        
        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("🚪 KELUAR SISTEM", use_container_width=True):
            st.session_state["logged_in"] = False; st.rerun()

    # --- DATA PROCESSING ---
    if not df_raw.empty:
        p_data = df_raw['nama_barang'].apply(parse_detail)
        df_raw['SKU'], df_raw['Item'], df_raw['Unit'], df_raw['Pembuat'], df_raw['Editor'], df_raw['Ket'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1]), p_data.apply(lambda x: x[2]), p_data.apply(lambda x: x[3]), p_data.apply(lambda x: x[4]), p_data.apply(lambda x: x[5])
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_f = df_raw.loc[mask].copy()

    # --- UI LOGIC BERDASARKAN MENU ---
    
    if menu == "Input Transaksi":
        st.markdown("<h2 style='color:white;'>📝 Input Transaksi Baru</h2>", unsafe_allow_html=True)
        with st.form("f_add", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                sk = st.text_input("SKU / Kode Barang")
                nm = st.text_input("Nama Produk")
                qt = st.number_input("Jumlah (Qty)", 1)
            with c2:
                jn = st.selectbox("Jenis Mutasi", ["Masuk", "Keluar"])
                stn = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit", "Lusin"])
                ket = st.text_input("Keterangan Tambahan", value="-")
            
            if st.form_submit_button("SIMPAN DATA KE DATABASE", use_container_width=True):
                tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                full = f"{sk} | {nm} | {stn} | {st.session_state['current_user']} | - | {ket}"
                conn = init_connection(); cur = conn.cursor()
                cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, jn, qt, now))
                conn.commit(); conn.close()
                st.success("Transaksi berhasil dicatat!"); st.rerun()

    elif menu == "Edit/Hapus Data":
        st.markdown("<h2 style='color:white;'>🔧 Koreksi Data</h2>", unsafe_allow_html=True)
        if not df_raw.empty:
            edit_id = st.selectbox("Pilih ID Transaksi yang akan diubah:", df_raw['id'])
            row = df_raw[df_raw['id'] == edit_id].iloc[0]
            p = parse_detail(row['nama_barang'])
            
            col_a, col_b = st.columns(2)
            with col_a:
                with st.form("f_edit"):
                    st.markdown("#### Form Update")
                    enm = st.text_input("Nama Produk", value=p[1])
                    eqt = st.number_input("Jumlah", value=int(row['jumlah']))
                    estn = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Unit"], index=0)
                    eket = st.text_input("Keterangan", value=p[5])
                    if st.form_submit_button("UPDATE DATA"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        full_upd = f"{p[0]} | {enm} | {estn} | {p[3]} | {st.session_state['current_user']} | {eket}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, eqt, now, int(edit_id)))
                        conn.commit(); conn.close(); st.rerun()
            with col_b:
                st.markdown("#### Hapus Permanen")
                st.warning("Data yang dihapus tidak bisa dikembalikan.")
                if st.button("🗑️ HAPUS TRANSAKSI INI", use_container_width=True):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(edit_id),))
                    conn.commit(); conn.close(); st.rerun()

    elif menu == "Kelola User":
        st.markdown("<h2 style='color:white;'>👥 Manajemen Akses Karyawan</h2>", unsafe_allow_html=True)
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.markdown("### Daftar User Aktif")
            df_u = pd.DataFrame(list(st.session_state["user_db"].items()), columns=['Username', 'Password'])
            st.table(df_u)
        with c2:
            st.markdown("### Tambah/Hapus")
            with st.expander("➕ Tambah Akses Baru"):
                nu = st.text_input("Username")
                np = st.text_input("Password", type="password")
                if st.button("Buat Akun"):
                    if nu and np: st.session_state["user_db"][nu] = np; st.rerun()
            
            with st.expander("❌ Cabut Akses"):
                list_rem = [u for u in st.session_state["user_db"].keys() if u != st.session_state["current_user"]]
                u_rem = st.selectbox("Pilih User:", ["-"] + list_rem)
                if st.button("Hapus Akun"):
                    if u_rem != "-": del st.session_state["user_db"][u_rem]; st.rerun()

    else: # Menu Dashboard & Stok
        # Row 1: Metrik Utama
        c1, c2, c3 = st.columns(3)
        with c1:
            val = int(df_f[df_f['jenis_mutasi']=='Masuk']['jumlah'].sum()) if not df_raw.empty else 0
            st.markdown(f"<div class='metric-card'><div class='metric-label'>📦 Total Masuk</div><div class='metric-value'>{val}</div></div>", unsafe_allow_html=True)
        with c2:
            val = int(df_f[df_f['jenis_mutasi']=='Keluar']['jumlah'].sum()) if not df_raw.empty else 0
            st.markdown(f"<div class='metric-card'><div class='metric-label'>📤 Total Keluar</div><div class='metric-value' style='color:#f87171;'>{val}</div></div>", unsafe_allow_html=True)
        with c3:
            stok_skr = df_raw.groupby(['SKU', 'Item', 'Unit'])['adj'].sum().reset_index(name='Stok') if not df_raw.empty else pd.DataFrame()
            val = len(stok_skr) if not stok_skr.empty else 0
            st.markdown(f"<div class='metric-card'><div class='metric-label'>🛒 Jenis Produk</div><div class='metric-value' style='color:#fbbf24;'>{val}</div></div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        # Row 2: Tabs Detail
        t_stok, t_log, t_graph = st.tabs(["📊 RINGKASAN STOK", "📜 HISTORI TRANSAKSI", "📈 ANALISIS TREN"])
        
        with t_stok:
            if not stok_skr.empty:
                st.dataframe(stok_skr.sort_values('Stok', ascending=False), use_container_width=True, hide_index=True)
            else: st.info("Belum ada data stok.")
            
        with t_log:
            if not df_raw.empty:
                # Modifikasi visual untuk status mutasi
                df_view = df_f[['id', 'tanggal', 'SKU', 'Item', 'jenis_mutasi', 'jumlah', 'Unit', 'Pembuat', 'Ket']].copy()
                st.dataframe(df_view, use_container_width=True, hide_index=True)
            else: st.info("Belum ada riwayat transaksi.")
            
        with t_graph:
            if not df_f.empty:
                c_a, c_b = st.columns(2)
                with c_a:
                    st.markdown("#### Fluktuasi Barang")
                    chart_data = df_f.groupby([df_f['tanggal'].dt.date, 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0)
                    st.area_chart(chart_data)
                with c_b:
                    st.markdown("#### Produk Paling Aktif")
                    top_items = df_f.groupby('Item')['jumlah'].sum().sort_values(ascending=False).head(5)
                    st.bar_chart(top_items)
            else: st.info("Data tidak cukup untuk menampilkan grafik.")
