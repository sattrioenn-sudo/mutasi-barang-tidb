import streamlit as st
import mysql.connector
import pandas as pd

# Judul Aplikasi
st.title("📦 Sistem Mutasi Barang")

# Fungsi koneksi dengan Cache agar lebih efisien
@st.cache_resource
def init_connection():
    try:
        return mysql.connector.connect(
            host=st.secrets["tidb"]["host"],
            port=int(st.secrets["tidb"]["port"]), # Pastikan port adalah integer
            user=st.secrets["tidb"]["user"],
            password=st.secrets["tidb"]["password"],
            database=st.secrets["tidb"]["database"],
            ssl_verify_cert=False, 
            use_pure=True
        )
    except Exception as e:
        st.error(f"Gagal terhubung ke database: {e}")
        return None

conn = init_connection()

# Pastikan koneksi berhasil sebelum menjalankan query
if conn:
    # Form Input di Sidebar
    with st.sidebar:
        st.header("Input Barang")
        nama = st.text_input("Nama Barang")
        jenis = st.selectbox("Jenis", ["Masuk", "Keluar"])
        qty = st.number_input("Jumlah", min_value=1)
        submit = st.button("Simpan")

    if submit:
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah) VALUES (%s, %s, %s)", (nama, jenis, qty))
            conn.commit()
            st.success("Data berhasil disimpan!")
            st.rerun() # Refresh data setelah input
        except Exception as e:
            st.error(f"Gagal menyimpan data: {e}")

    # Menampilkan Data
    st.subheader("Riwayat Transaksi")
    try:
        df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
        st.dataframe(df, use_container_width=True)
    except Exception as e:
        st.warning("Tabel belum ada atau data kosong.")
