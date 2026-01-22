import streamlit as st
import mysql.connector
import pandas as pd

# --- FUNGSI LOGIN ---
def login():
    st.title("🔐 Login Sistem Inventaris")
    
    with st.form("login_form"):
        user_input = st.text_input("Username")
        pass_input = st.text_input("Password", type="password")
        submit = st.form_submit_button("Login")
        
        if submit:
            # Mengambil data dari secrets
            correct_user = st.secrets["auth"]["username"]
            correct_pass = st.secrets["auth"]["password"]
            
            if user_input == correct_user and pass_input == correct_pass:
                st.session_state["logged_in"] = True
                st.rerun() # Refresh halaman setelah login berhasil
            else:
                st.error("Username atau Password salah!")

# Inisialisasi status login jika belum ada
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- LOGIKA TAMPILAN ---
if not st.session_state["logged_in"]:
    login()
else:
    # --- TOMBOL LOGOUT ---
    if st.sidebar.button("Log Out"):
        st.session_state["logged_in"] = False
        st.rerun()

    # --- KODE APLIKASI UTAMA ANDA (MASUKKAN DI SINI) ---
    st.title("📦 Sistem Mutasi Barang")
    
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

    # ... (Lanjutkan dengan sisa kode input dan tabel Anda yang sebelumnya) ...
    # Pastikan kode input sidebar dan tabel berada di dalam blok 'else' ini
