import streamlit as st
import mysql.connector
import pandas as pd

# 1. Konfigurasi Halaman (Harus paling atas)
st.set_page_config(page_title="Inventory Prime Pro", page_icon="🚀", layout="wide")

# 2. CSS Khusus untuk Memperbaiki Teks Numpuk & Sidebar
st.markdown("""
    <style>
    /* Mengatur jarak baris di sidebar agar tidak rapat/numpuk */
    section[data-testid="stSidebar"] .stMarkdown p {
        line-height: 1.6 !important;
        margin-bottom: 10px !important;
    }
    
    /* Memaksa kontainer tabel agar punya padding yang pas */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }

    /* Memperbaiki tampilan judul di Dashboard */
    h1, h2, h3 {
        padding-top: 10px;
        padding-bottom: 10px;
    }

    /* Efek Card pada Metric agar tidak gepeng */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
    }
    .metric-card {
        flex: 1;
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Fungsi Database
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

# --- SISTEM LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    # Tampilan Login (Sederhana tapi Rapi)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.write("# 🔐 Login")
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk", use_container_width=True):
                if u == st.secrets["auth"]["username"] and p == st.secrets["auth"]["password"]:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("Kredensial Salah")
else:
    # --- DASHBOARD UTAMA ---
    with st.sidebar:
        st.title("🚀 INV-PRIME")
        st.write(f"Logged in: **{st.secrets['auth']['username']}**")
        st.markdown("---")
        
        with st.expander("📥 Input Transaksi", expanded=True):
            with st.form("input", clear_on_submit=True):
                # 1. Input Kode/SKU
                sku = st.text_input("Kode Barang (SKU)", placeholder="Contoh: BRG-001")
                
                # 2. Input Nama
                n = st.text_input("Nama Barang", placeholder="Contoh: Kursi")
                
                # 3. Input Satuan (Dropdown agar seragam)
                satuan = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Liter", "Set", "Meter"])
                
                # 4. Input Aksi & Qty
                j = st.selectbox("Aksi", ["Masuk", "Keluar"])
                q = st.number_input("Qty", min_value=1, step=1)
                
                if st.form_submit_button("Simpan", use_container_width=True):
                    if n:
                        # 1. Ambil Waktu Jakarta (WIB)
                        tz_jkt = pytz.timezone('Asia/Jakarta')
                        waktu_sekarang = datetime.now(tz_jkt).strftime('%Y-%m-%d %H:%M:%S')
                        # PROSES PENGGABUNGAN: [SKU] Nama (Satuan)
                        # Contoh hasil: [BRG-01] Kursi (Pcs)
                        nama_lengkap = f"[{sku}] {n} ({satuan})" if sku else f"{n} ({satuan})"
                        
                        try:
                            conn = init_connection()
                            cur = conn.cursor()
            
                            # 2. Masukkan waktu_sekarang secara manual ke kolom tanggal
                            # Ini akan menimpa (override) waktu default database
                            query = "INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s, %s, %s, %s)"
                            cur.execute(query, (nama_lengkap, j, q, waktu_sekarang))
            
                            conn.commit()
                            conn.close()
                            st.success(f"Tersimpan pada: {waktu_sekarang}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal simpan: {e}")
        with st.expander("🗑️ Management"):
            try:
                conn = init_connection()
                items = pd.read_sql("SELECT DISTINCT nama_barang FROM inventory", conn); conn.close()
                target = st.selectbox("Pilih Barang:", items['nama_barang'])
                conf = st.checkbox("Konfirmasi hapus")
                if st.button("Hapus Data", use_container_width=True, disabled=not conf):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE nama_barang = %s", (target,))
                    conn.commit(); conn.close()
                    st.rerun()
            except: st.write("Belum ada data")

        st.markdown("---")
        if st.button("Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- KONTEN ANALITIK ---
    st.title("Real-time Analytics")
    
    try:
        conn = init_connection()
        df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
        conn.close()

        if not df.empty:
            # Merapikan Format Tanggal agar tidak bertumpuk
            df['tanggal'] = pd.to_datetime(df['tanggal'])
            
            # Summary Data
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            stok_df = df.groupby('nama_barang')['adj'].sum().reset_index()
            stok_df.columns = ['Barang', 'Stok']

            # Row Metrics (Kartu Ringkasan)
            m1, m2, m3 = st.columns(3)
            m1.metric("Total Transaksi", len(df))
            m2.metric("Total Volume", f"{int(df['jumlah'].sum())} unit")
            if not stok_df.empty:
                m3.metric("Item Terbanyak", stok_df.iloc[stok_df['Stok'].idxmax()]['Barang'])

            st.write("###") # Spasi

            # TABEL UTAMA (PERBAIKAN KOLOM TANGGAL & TEXT)
            c_left, c_right = st.columns([1.7, 1.3])
            
            with c_left:
                st.subheader("📜 Log Aktivitas")
                st.dataframe(
                    df[['tanggal', 'nama_barang', 'jenis_mutasi', 'jumlah']],
                    use_container_width=True,
                    height=400,
                    hide_index=True,
                    column_config={
                        "tanggal": st.column_config.DatetimeColumn(
                            "Tanggal & Waktu",
                            format="D MMM YYYY, HH:mm", # Contoh: 22 Jan 2026, 10:15
                            width="medium" # Memberi ruang agar tidak numpuk
                        ),
                        "nama_barang": st.column_config.TextColumn("Nama Barang", width="medium"),
                        "jenis_mutasi": st.column_config.TextColumn("Status", width="small"),
                        "jumlah": st.column_config.NumberColumn("Qty", width="small")
                    }
                )
                
            with c_right:
                st.subheader("📊 Saldo Stok")
                st.dataframe(
                    stok_df, 
                    use_container_width=True, 
                    height=400, 
                    hide_index=True,
                    column_config={
                        "Barang": st.column_config.TextColumn("Nama Barang", width="large"),
                        "Stok": st.column_config.NumberColumn("Sisa", width="small")
                    }
                )
        else:
            st.info("Belum ada data mutasi barang.")
    except Exception as e:
        st.error(f"Error: {e}")
