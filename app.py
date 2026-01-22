import streamlit as st
import mysql.connector
import socket

st.title("Diagnosa Koneksi TiDB")

# Cek 1: Apakah internet Streamlit bisa mengenali nama host?
host_to_check = st.secrets["tidb"]["host"]
st.write(f"Mencoba mencari alamat: `{host_to_check}`...")

try:
    ip_address = socket.gethostbyname(host_to_check)
    st.success(f"✅ Nama Host dikenali! IP Address: {ip_address}")
    
    # Cek 2: Jika nama host dikenali, coba hubungkan database
    try:
        conn = mysql.connector.connect(
            host=st.secrets["tidb"]["host"],
            port=int(st.secrets["tidb"]["port"]),
            user=st.secrets["tidb"]["user"],
            password=st.secrets["tidb"]["password"],
            database=st.secrets["tidb"]["database"],
            ssl_verify_cert=False,
            use_pure=True
        )
        st.success("✅ Koneksi Database Berhasil!")
        conn.close()
    except Exception as db_err:
        st.error(f"❌ Nama host benar, tapi gagal login: {db_err}")

except socket.gaierror:
    st.error("❌ ERROR: Alamat Host tidak ditemukan di internet. Periksa kembali penulisan HOST di Secrets.")
