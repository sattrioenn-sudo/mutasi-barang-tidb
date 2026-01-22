import streamlit as st
import mysql.connector

st.title("Cek Koneksi TiDB")

# 1. Fungsi untuk ambil kunci dari Secrets dan hubungkan ke TiDB
def buat_koneksi():
    return mysql.connector.connect(
        host=st.secrets["tidb"]["host"],
        port=st.secrets["tidb"]["port"],
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        ssl_verify_cert=False, # Penting agar tidak error SSL
        use_pure=True          # Agar lebih stabil di internet
    )

# 2. Jalankan fungsi koneksi
try:
    conn = buat_koneksi()
    st.success("✅ Berhasil! Aplikasi sudah terhubung ke TiDB.")
    conn.close()
except Exception as e:
    st.error(f"❌ Gagal Terhubung. Error: {e}")
