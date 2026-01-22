import streamlit as st
import mysql.connector
import pandas as pd

# Konfigurasi Halaman
st.set_page_config(page_title="Inventory Secure System", layout="wide")

# --- 1. FUNGSI KONEKSI (MENGGUNAKAN DATABASE YANG SUDAH ADA) ---
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

# --- 2. SISTEM LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

def login():
    st.markdown("<h2 style='text-align: center;'>🔐 Login Sistem Mutasi</h2>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user_input = st.text_input("Username")
            pass_input = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Masuk", use_container_width=True)
            
            if submitted:
                # Mengambil username & password dari Streamlit Secrets
                if user_input == st.secrets["auth"]["username"] and pass_input == st.secrets["auth"]["password"]:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("Username atau password salah!")

# --- 3. LOGIKA TAMPILAN ---
if not st.session_state["logged_in"]:
    login()
else:
    # --- HEADER & LOGOUT ---
    col_title, col_logout = st.columns([10, 2])
    with col_title:
        st.title("📦 Aplikasi Mutasi Barang")
    with col_logout:
        if st.button("Keluar / Log Out"):
            st.session_state["logged_in"] = False
            st.rerun()
    
    st.markdown("---")

    # --- BAGIAN INPUT (SIDEBAR) ---
    with st.sidebar:
        st.header("Input Transaksi")
        nama_barang = st.text_input("Nama Barang")
        jenis_mutasi = st.selectbox("Jenis Mutasi", ["Masuk", "Keluar"])
        jumlah = st.number_input("Jumlah", min_value=1, step=1)
        
        if st.button("Simpan ke Database"):
            if nama_barang:
                try:
                    conn = init_connection()
                    cursor = conn.cursor()
                    # Menggunakan tabel 'inventory' yang sudah ada
                    query = "INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah) VALUES (%s, %s, %s)"
                    cursor.execute(query, (nama_barang, jenis_mutasi, jumlah))
                    conn.commit()
                    conn.close()
                    st.success(f"Berhasil mencatat {nama_barang}!")
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Isi nama barang terlebih dahulu")

    # --- BAGIAN TAMPILAN DATA (DARI DATABASE SEBELUMNYA) ---
    try:
        conn = init_connection()
        df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
        conn.close()

        if not df.empty:
            # Ringkasan Stok
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            stok = df.groupby('nama_barang')['adj'].sum().reset_index()
            stok.columns = ['Nama Barang', 'Stok Akhir']

            c1, c2 = st.columns([2, 1])
            with c1:
                st.subheader("📜 Riwayat")
                st.dataframe(df[['tanggal', 'nama_barang', 'jenis_mutasi', 'jumlah']], use_container_width=True)
            with c2:
                st.subheader("📊 Saldo Stok")
                st.table(stok)
        else:
            st.info("Database kosong. Belum ada data mutasi.")
            
    except Exception as e:
        st.error(f"Gagal mengambil data: {e}")
