import streamlit as st
import mysql.connector
import pandas as pd

# 1. Page Configuration
st.set_page_config(page_title="Inventory Prime v2", page_icon="🚀", layout="wide")

# 2. CSS Adjustment (Perbaikan teks sidebar & table)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Inter', sans-serif; }
    
    .stApp {
        background: radial-gradient(circle at top right, #1a1a2e, #16213e);
        color: #ffffff;
    }

    /* Memastikan teks sidebar tidak numpuk */
    [data-testid="stSidebar"] .stMarkdown p {
        line-height: 1.2;
        font-size: 14px;
    }
    
    /* Spasi antar elemen sidebar */
    .st-expander { margin-bottom: 10px !important; }

    .metric-card {
        background: rgba(255, 255, 255, 0.03);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
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

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- LOGIKA LOGIN ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        with st.form("login_form"):
            st.markdown("<h2 style='text-align:center;'>🔐 Access Portal</h2>", unsafe_allow_html=True)
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                if u == st.secrets["auth"]["username"] and p == st.secrets["auth"]["password"]:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else: st.error("Salah password bro")

# --- DASHBOARD UTAMA ---
else:
    with st.sidebar:
        st.markdown("<h2 style='color:#4facfe; margin-bottom:0;'>🚀 INV-PRIME</h2>", unsafe_allow_html=True)
        st.caption(f"Status: Online | User: {st.secrets['auth']['username']}")
        
        st.markdown("---")
        with st.expander("📥 Input Transaksi", expanded=True):
            with st.form("input_form", clear_on_submit=True):
                n = st.text_input("Nama Barang")
                j = st.selectbox("Aksi", ["Masuk", "Keluar"])
                q = st.number_input("Qty", min_value=1)
                if st.form_submit_button("Simpan", use_container_width=True):
                    if n:
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah) VALUES (%s,%s,%s)", (n,j,q))
                        conn.commit(); conn.close()
                        st.rerun()

        with st.expander("🗑️ Management"):
            try:
                conn = init_connection()
                items = pd.read_sql("SELECT DISTINCT nama_barang FROM inventory", conn); conn.close()
                target = st.selectbox("Pilih Barang:", items['nama_barang'])
                conf = st.checkbox("Konfirmasi Hapus")
                if st.button("🔥 Hapus Data", use_container_width=True, disabled=not conf):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE nama_barang = %s", (target,))
                    conn.commit(); conn.close()
                    st.rerun()
            except: st.write("Belum ada data")

        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- CONTENT AREA ---
    st.title("Real-time Analytics")
    
    try:
        conn = init_connection()
        # Ambil data
        df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
        conn.close()

        if not df.empty:
            # 1. Perbaikan Tanggal (Convert ke datetime agar bisa diformat)
            df['tanggal'] = pd.to_datetime(df['tanggal'])
            
            # 2. Hitung Stok
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            stok_df = df.groupby('nama_barang')['adj'].sum().reset_index()
            stok_df.columns = ['Barang', 'Stok']

            # 3. Row Metrics
            m1, m2, m3 = st.columns(3)
            with m1: st.markdown(f"<div class='metric-card'><p>Total Record</p><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
            with m2: 
                top = stok_df.iloc[stok_df['Stok'].idxmax()]['Barang']
                st.markdown(f"<div class='metric-card'><p>Item Terbanyak</p><h2 style='color:#00ff88;'>{top}</h2></div>", unsafe_allow_html=True)
            with m3: st.markdown(f"<div class='metric-card'><p>Total Volume</p><h2>{df['jumlah'].sum()}</h2></div>", unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)

            # 4. Row Tabel (SOLUSI UNTUK TEXT NUMPUK)
            col_left, col_right = st.columns([1.8, 1.2])
            
            with col_left:
                st.subheader("📜 Log Transaksi Terkini")
                st.dataframe(
                    df[['tanggal', 'nama_barang', 'jenis_mutasi', 'jumlah']],
                    use_container_width=True,
                    height=400,
                    hide_index=True,
                    column_config={
                        "tanggal": st.column_config.DatetimeColumn(
                            "Waktu Transaksi",
                            format="D MMM YYYY, HH:mm", # Merapikan Tanggal (Contoh: 22 Jan 2026)
                            width="medium"
                        ),
                        "nama_barang": st.column_config.TextColumn("Nama Barang", width="medium"),
                        "jenis_mutasi": st.column_config.TextColumn("Status", width="small"),
                        "jumlah": st.column_config.NumberColumn("Qty", width="small", format="%d 📦")
                    }
                )
                
            with col_right:
                st.subheader("📊 Saldo Gudang")
                st.dataframe(
                    stok_df, 
                    use_container_width=True, 
                    height=400, 
                    hide_index=True,
                    column_config={
                        "Barang": st.column_config.TextColumn("Barang", width="large"),
                        "Stok": st.column_config.NumberColumn("Total Stok", width="small")
                    }
                )
        else:
            st.info("Data masih kosong.")
    except Exception as e:
        st.error(f"Gagal memuat: {e}")
