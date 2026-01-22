import streamlit as st
import mysql.connector
import pandas as pd

# Judul Aplikasi
st.title("📦 Sistem Mutasi Barang")

# Fungsi untuk koneksi menggunakan Secrets (Keamanan)
def init_connection():
    return mysql.connector.connect(
        host=st.secrets["tidb"]["host"],
        port=st.secrets["tidb"]["port"],
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        ssl_verify_cert=True
    )

conn = init_connection()

# Form Input di Sidebar
with st.sidebar:
    st.header("Input Barang")
    nama = st.text_input("Nama Barang")
    jenis = st.selectbox("Jenis", ["Masuk", "Keluar"])
    qty = st.number_input("Jumlah", min_value=1)
    submit = st.button("Simpan")

if submit:
    cursor = conn.cursor()
    cursor.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah) VALUES (%s, %s, %s)", (nama, jenis, qty))
    conn.commit()
    st.success("Data berhasil disimpan!")

# Menampilkan Data
st.subheader("Riwayat Transaksi")
df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
st.dataframe(df, use_container_width=True)
