import streamlit as st
import mysql.connector
import pandas as pd

# Konfigurasi Halaman
st.set_page_config(page_title="Inventory System", layout="wide")

# --- FUNGSI DATABASE ---
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

# --- ANTARMUKA PENGGUNA (UI) ---
st.title("📦 Sistem Mutasi Barang (TiDB + Streamlit)")
st.markdown("---")

# Sidebar untuk Input Data
with st.sidebar:
    st.header("Tambah Mutasi")
    nama_barang = st.text_input("Nama Barang", placeholder="Contoh: Laptop")
    jenis_mutasi = st.selectbox("Jenis Mutasi", ["Masuk", "Keluar"])
    jumlah = st.number_input("Jumlah", min_value=1, step=1)
    
    if st.button("Simpan Transaksi"):
        if nama_barang:
            try:
                conn = init_connection()
                cursor = conn.cursor()
                query = "INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah) VALUES (%s, %s, %s)"
                cursor.execute(query, (nama_barang, jenis_mutasi, jumlah))
                conn.commit()
                conn.close()
                st.success(f"Berhasil mencatat {nama_barang} {jenis_mutasi}!")
            except Exception as e:
                st.error(f"Gagal menyimpan: {e}")
        else:
            st.warning("Nama barang tidak boleh kosong!")

# --- MENAMPILKAN DATA & RINGKASAN ---
try:
    conn = init_connection()
    # Ambil semua data dari tabel
    df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
    conn.close()

    if not df.empty:
        # Menghitung stok saat ini (Summary)
        # Kita beri nilai negatif untuk barang 'Keluar' agar bisa dijumlahkan
        df['penyesuaian'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
        stok_summary = df.groupby('nama_barang')['penyesuaian'].sum().reset_index()
        stok_summary.columns = ['Nama Barang', 'Stok Saat Ini']

        # Tampilan Dashboard
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📜 Riwayat Transaksi")
            st.dataframe(df[['tanggal', 'nama_barang', 'jenis_mutasi', 'jumlah']], use_container_width=True)
            
        with col2:
            st.subheader("📊 Total Stok")
            st.table(stok_summary)
    else:
        st.info("Belum ada data mutasi. Silakan input melalui sidebar.")

except Exception as e:
    st.error(f"Gagal memuat data: {e}")
