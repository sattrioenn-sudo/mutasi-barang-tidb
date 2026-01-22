import streamlit as st
import mysql.connector
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Inventory Prime", page_icon="🚀", layout="wide")

# 2. Ultra Modern CSS
st.markdown("""
    <style>
    /* Mengatur Font dan Background */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: radial-gradient(circle at top right, #1a1a2e, #16213e);
        color: #ffffff;
    }

    /* Card Style untuk Metrics */
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
        transition: 0.3s;
    }
    .metric-card:hover {
        background: rgba(255, 255, 255, 0.1);
        border-color: #4facfe;
    }

    /* Glassmorphism Login Container */
    .login-container {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(20px);
        padding: 40px;
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
    }
    
    /* Status Badge */
    .badge-masuk { background-color: #28a745; color: white; padding: 4px 8px; border-radius: 6px; font-size: 12px; }
    .badge-keluar { background-color: #dc3545; color: white; padding: 4px 8px; border-radius: 6px; font-size: 12px; }
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

# 4. Session State for Auth
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- UI LOGIKA LOGIN ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center; color:#4facfe;'>🚀 INVENTORY PRIME</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; opacity:0.7;'>Enterprise Resources Monitoring</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("AUTHENTICATE", use_container_width=True):
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
        st.markdown("<h2 style='color:#4facfe;'>INV-PRIME</h2>", unsafe_allow_html=True)
        st.write(f"Active Session: `{st.secrets['auth']['username']}`")
        if st.button("🚪 Secure Logout"):
            st.session_state["logged_in"] = False
            st.rerun()
        
        st.markdown("---")
        with st.expander("📥 Input Data Baru", expanded=True):
            with st.form("input_form", clear_on_submit=True):
                n = st.text_input("Nama Barang")
                j = st.selectbox("Aksi", ["Masuk", "Keluar"])
                q = st.number_input("Qty", min_value=1)
                if st.form_submit_button("Submit Transaction"):
                    if n:
                        conn = init_connection()
                        cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah) VALUES (%s,%s,%s)", (n,j,q))
                        conn.commit()
                        conn.close()
                        st.rerun()

        with st.expander("🗑️ Management Data"):
            try:
                conn = init_connection()
                items = pd.read_sql("SELECT DISTINCT nama_barang FROM inventory", conn)
                conn.close()
                target = st.selectbox("Pilih Master Barang", items['nama_barang'])
                if st.button("Hapus Seluruh Data Barang"):
                    conn = init_connection()
                    cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE nama_barang = %s", (target,))
                    conn.commit()
                    conn.close()
                    st.rerun()
            except: pass

    # Dashboard Content
    st.markdown("<h1 style='margin-bottom:0;'>Real-time Analytics</h1>", unsafe_allow_html=True)
    st.markdown("<p style='opacity:0.6;'>Monitoring mutasi barang langsung dari database TiDB Cloud</p>", unsafe_allow_html=True)

    try:
        conn = init_connection()
        df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
        conn.close()

        if not df.empty:
            # Kalkulasi Data Inovatif
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            stok_df = df.groupby('nama_barang')['adj'].sum().reset_index()
            
            # Baris Metrics (KPI Cards)
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"<div class='metric-card'><h3>Total Transaksi</h3><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
            with c2:
                top_item = stok_df.iloc[stok_df['adj'].idxmax()]['nama_barang'] if not stok_df.empty else "-"
                st.markdown(f"<div class='metric-card'><h3>Stok Terbanyak</h3><h2>{top_item}</h2></div>", unsafe_allow_html=True)
            with c3:
                total_qty = df['jumlah'].sum()
                st.markdown(f"<div class='metric-card'><h3>Volume Barang</h3><h2>{total_qty}</h2></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # Baris Tabel Transaksi & Stok
            col_main, col_sub = st.columns([2, 1])
            with col_main:
                st.markdown("### 📜 Log Aktivitas Terbaru")
                # Memberikan warna pada status
                df_display = df[['tanggal', 'nama_barang', 'jenis_mutasi', 'jumlah']].copy()
                st.dataframe(df_display, use_container_width=True, height=400)
                
            with col_sub:
                st.markdown("### 📊 Ringkasan Inventaris")
                stok_df.columns = ['Nama Barang', 'Saldo Akhir']
                st.table(stok_df)
        else:
            st.info("Sistem siap. Belum ada aktivitas yang terdeteksi.")

    except Exception as e:
        st.error(f"System Error: {e}")
