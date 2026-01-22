import streamlit as st
import mysql.connector
import pandas as pd

# 1. Konfigurasi Dasar
st.set_page_config(page_title="Inventory Pro System", page_icon="📦", layout="wide")

# 2. Custom CSS untuk Tampilan Keren (Glassmorphism)
st.markdown("""
    <style>
    /* Background utama */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    /* Container Login */
    .login-box {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 16px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 40px;
        color: white;
    }
    
    /* Custom Button */
    .stButton>button {
        width: 100%;
        border-radius: 20px;
        border: none;
        background-color: #4facfe;
        color: white;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00f2fe;
        transform: scale(1.02);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Fungsi Koneksi (Database Tetap Sama)
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

# 4. Logika Session State (Status Login)
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- HALAMAN LOGIN ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("""
            <div class='login-box'>
                <h1 style='text-align: center; margin-bottom: 0;'>📦 INV-PRO</h1>
                <p style='text-align: center; opacity: 0.8;'>Sistem Mutasi Barang Terpadu</p>
            </div>
        """, unsafe_allow_html=True)
        
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            btn_login = st.form_submit_button("MASUK KE SISTEM")
            
            if btn_login:
                if user_input == st.secrets["auth"]["username"] and pass_input == st.secrets["auth"]["password"]:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("Akses Ditolak: Kredensial Salah")

# --- HALAMAN UTAMA (SESUDAH LOGIN) ---
else:
    # Sidebar Area
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/408/408710.png", width=100)
        st.title("Control Panel")
        st.write(f"User: **{st.secrets['auth']['username']}**")
        
        if st.button("🚪 Logout"):
            st.session_state["logged_in"] = False
            st.rerun()
        
        st.markdown("---")
        st.header("➕ Tambah Mutasi")
        with st.form("input_form", clear_on_submit=True):
            nama = st.text_input("Nama Barang")
            jenis = st.selectbox("Jenis", ["Masuk", "Keluar"])
            qty = st.number_input("Jumlah", min_value=1)
            btn_simpan = st.form_submit_button("Simpan Data")
            
            if btn_simpan and nama:
                conn = init_connection()
                curr = conn.cursor()
                curr.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah) VALUES (%s,%s,%s)", (nama, jenis, qty))
                conn.commit()
                conn.close()
                st.success("Tercatat!")
                st.rerun()

        st.markdown("---")
        st.header("🗑️ Hapus Master")
        try:
            conn = init_connection()
            df_list = pd.read_sql("SELECT DISTINCT nama_barang FROM inventory", conn)
            conn.close()
            
            item_hapus = st.selectbox("Pilih Barang", df_list['nama_barang'])
            if st.button("Hapus Permanen"):
                conn = init_connection()
                curr = conn.cursor()
                curr.execute("DELETE FROM inventory WHERE nama_barang = %s", (item_hapus,))
                conn.commit()
                conn.close()
                st.warning(f"{item_hapus} Dihapus")
                st.rerun()
        except:
            st.write("Belum ada data")

    # Main Content Area
    st.markdown("<h2 style='color: white;'>📊 Dashboard Monitor</h2>", unsafe_allow_html=True)
    
    try:
        conn = init_connection()
        df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
        conn.close()

        if not df.empty:
            # Kalkulasi Stok
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            stok_df = df.groupby('nama_barang')['adj'].sum().reset_index()
            stok_df.columns = ['Barang', 'Stok Saat Ini']

            # Tampilan Metric & Tabel
            m1, m2 = st.columns([2, 1])
            with m1:
                st.markdown("### Riwayat Transaksi")
                st.dataframe(df[['tanggal', 'nama_barang', 'jenis_mutasi', 'jumlah']], use_container_width=True)
            with m2:
                st.markdown("### Ringkasan Stok")
                st.table(stok_df)
        else:
            st.info("Belum ada data di TiDB")
    except Exception as e:
        st.error(f"Error Database: {e}")
