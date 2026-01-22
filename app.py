import streamlit as st
import mysql.connector
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Inventory Prime v2", page_icon="🚀", layout="wide")

# 2. Ultra Modern CSS (Ditingkatkan agar sidebar lebih lega)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: radial-gradient(circle at top right, #1a1a2e, #16213e);
        color: #ffffff;
    }

    /* Metric Card Improvement */
    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }
    
    /* Sidebar Styling agar tidak sumpek */
    [data-testid="stSidebar"] {
        background-color: rgba(20, 20, 40, 0.8);
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Login Glassmorphism */
    .login-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(15px);
        padding: 3rem;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# 3. Connection Function
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

# 4. Auth Session
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- UI LOGIKA LOGIN ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; color:#4facfe; margin-bottom:0;'>INV-PRIME</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; opacity:0.6; margin-bottom:2rem;'>Secure Access Portal</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("UNLOCK SYSTEM", use_container_width=True):
                if u == st.secrets["auth"]["username"] and p == st.secrets["auth"]["password"]:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("Invalid Credentials")
        st.markdown("</div>", unsafe_allow_html=True)

# --- UI DASHBOARD UTAMA ---
else:
    # Sidebar Navigation
    with st.sidebar:
        st.markdown("<h2 style='color:#4facfe;'>🚀 INV-PRIME</h2>", unsafe_allow_html=True)
        st.write(f"User: `{st.secrets['auth']['username']}`")
        
        st.markdown("---")
        # INPUT DATA SECTION
        with st.expander("📥 Input Transaksi", expanded=True):
            with st.form("input_form", clear_on_submit=True):
                n = st.text_input("Nama Barang", placeholder="Contoh: Kursi")
                j = st.selectbox("Aksi", ["Masuk", "Keluar"])
                q = st.number_input("Qty", min_value=1, step=1)
                if st.form_submit_button("Simpan", use_container_width=True):
                    if n:
                        conn = init_connection()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah) VALUES (%s,%s,%s)", (n,j,q))
                        conn.commit()
                        conn.close()
                        st.rerun()

        # MANAGEMENT DATA SECTION (PERBAIKAN AGAR TIDAK NUMPUK)
        with st.expander("🗑️ Management"):
            try:
                conn = init_connection()
                items = pd.read_sql("SELECT DISTINCT nama_barang FROM inventory", conn)
                conn.close()
                
                if not items.empty:
                    target = st.selectbox("Pilih Barang:", items['nama_barang'])
                    
                    # Beri jarak agar tidak numpuk
                    st.write("---")
                    st.warning("Penghapusan bersifat permanen.")
                    conf = st.checkbox("Saya yakin hapus data")
                    
                    if st.button("🔥 HAPUS MASTER", use_container_width=True, disabled=not conf):
                        conn = init_connection()
                        cur = conn.cursor()
                        cur.execute("DELETE FROM inventory WHERE nama_barang = %s", (target,))
                        conn.commit()
                        conn.close()
                        st.rerun()
                else:
                    st.info("Belum ada data.")
            except: 
                pass

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # Dashboard Content
    st.markdown("<h1 style='margin-bottom:0;'>Real-time Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.6; margin-bottom:2rem;'>Inventory tracking powered by TiDB Cloud</p>", unsafe_allow_html=True)

    try:
        conn = init_connection()
        df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
        conn.close()

        if not df.empty:
            # Kalkulasi Metrics
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            stok_df = df.groupby('nama_barang')['adj'].sum().reset_index()
            stok_df.columns = ['Nama Barang', 'Saldo Stok']
            
            # Row 1: KPI Cards
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='metric-card'><p style='opacity:0.7; margin:0;'>Total Record</p><h2 style='color:#4facfe; margin:0;'>{len(df)}</h2></div>", unsafe_allow_html=True)
            with c2:
                top_item = stok_df.iloc[stok_df['Saldo Stok'].idxmax()]['Nama Barang']
                st.markdown(f"<div class='metric-card'><p style='opacity:0.7; margin:0;'>Item Terbanyak</p><h2 style='color:#00ff88; margin:0;'>{top_item}</h2></div>", unsafe_allow_html=True)
            with c3:
                vol = df['jumlah'].sum()
                st.markdown(f"<div class='metric-card'><p style='opacity:0.7; margin:0;'>Total Volume</p><h2 style='color:#ffaa00; margin:0;'>{vol}</h2></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Row 2: Tabel dengan Badge Otomatis
            col_main, col_sub = st.columns([1.8, 1.2])
            with col_main:
                st.subheader("📜 Log Transaksi Terkini")
                # Menampilkan dataframe dengan formatting warna otomatis pada kolom jenis_mutasi
                st.dataframe(
                    df[['tanggal', 'nama_barang', 'jenis_mutasi', 'jumlah']],
                    use_container_width=True,
                    height=450,
                    column_config={
                        "jenis_mutasi": st.column_config.SelectboxColumn(
                            "Status",
                            options=["Masuk", "Keluar"],
                            required=True,
                        ),
                        "jumlah": st.column_config.NumberColumn("Quantity", format="%d 📦")
                    }
                )
                
            with col_sub:
                st.subheader("📊 Saldo Gudang")
                st.dataframe(stok_df, use_container_width=True, height=450, hide_index=True)
        else:
            st.info("Database kosong. Silakan tambahkan data melalui sidebar.")

    except Exception as e:
        st.error(f"Koneksi Database Terputus: {e}")
