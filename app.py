import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import pytz

# 1. Konfigurasi Halaman (Harus paling atas)
st.set_page_config(page_title="Inventory Prime Pro", page_icon="🚀", layout="wide")

# 2. Inisialisasi Session State (Mencegah Error KeyNotFound)
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""

# 3. CSS Khusus
st.markdown("""
    <style>
    section[data-testid="stSidebar"] .stMarkdown p {
        line-height: 1.6 !important;
        margin-bottom: 10px !important;
    }
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# 4. Fungsi Database
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
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1.2, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:#4facfe;'>🔐 INV-PRIME ACCESS</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            submit = st.form_submit_button("AUTHENTICATE", use_container_width=True)
            
            if submit:
                # Cek apakah kunci [auth_users] ada di secrets
                if "auth_users" in st.secrets:
                    users_list = st.secrets["auth_users"]
                    # Verifikasi username dan password
                    if u_input in users_list and str(p_input) == str(users_list[u_input]):
                        st.session_state["logged_in"] = True
                        st.session_state["current_user"] = u_input
                        st.rerun()
                    else:
                        st.error("Username atau Password salah!")
                else:
                    # Pesan ini hanya muncul jika kamu lupa setting di Dashboard Streamlit
                    st.error("Error: Konfigurasi [auth_users] tidak ditemukan di Dashboard Secrets.")
# --- DASHBOARD UTAMA (Muncul jika sudah login) ---
else:
    with st.sidebar:
        st.title("🚀 INV-PRIME")
        st.write(f"Logged in as: **{st.session_state['current_user']}**")
        st.markdown("---")
        
        with st.expander("📥 Input Transaksi", expanded=True):
            with st.form("input", clear_on_submit=True):
                sku = st.text_input("Kode Barang (SKU)", placeholder="Contoh: BRG-001")
                n = st.text_input("Nama Barang", placeholder="Contoh: Kursi")
                satuan = st.selectbox("Satuan", ["Pcs", "Box", "Kg", "Liter", "Set", "Meter"])
                j = st.selectbox("Aksi", ["Masuk", "Keluar"])
                q = st.number_input("Qty", min_value=1, step=1)
                
                if st.form_submit_button("Simpan", use_container_width=True):
                    if n:
                        tz_jkt = pytz.timezone('Asia/Jakarta')
                        waktu_sekarang = datetime.now(tz_jkt).strftime('%Y-%m-%d %H:%M:%S')
                        # Format: [SKU] Nama (Satuan) | User
                        nama_lengkap = f"[{sku}] {n} ({satuan})" if sku else f"{n} ({satuan})"
                        
                        try:
                            conn = init_connection()
                            cur = conn.cursor()
                            query = "INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s, %s, %s, %s)"
                            cur.execute(query, (nama_lengkap, j, q, waktu_sekarang))
                            conn.commit()
                            conn.close()
                            st.success("Data Berhasil Disimpan!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        with st.expander("🗑️ Management"):
            try:
                conn = init_connection()
                items = pd.read_sql("SELECT DISTINCT nama_barang FROM inventory", conn); conn.close()
                if not items.empty:
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
            st.session_state["current_user"] = ""
            st.rerun()

    # --- KONTEN ANALITIK ---
    st.title("Real-time Analytics")
    
    try:
        conn = init_connection()
        df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
        conn.close()

        if not df.empty:
            df['tanggal'] = pd.to_datetime(df['tanggal'])
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            stok_df = df.groupby('nama_barang')['adj'].sum().reset_index()
            stok_df.columns = ['Barang', 'Stok']

            m1, m2, m3 = st.columns(3)
            m1.metric("Total Transaksi", len(df))
            m2.metric("Total Volume", f"{int(df['jumlah'].sum())} unit")
            if not stok_df.empty:
                m3.metric("Item Terbanyak", stok_df.iloc[stok_df['Stok'].idxmax()]['Barang'])

            st.write("###")
            c_left, c_right = st.columns([1.7, 1.3])
            
            with c_left:
                st.subheader("📜 Log Aktivitas")
                st.dataframe(
                    df[['tanggal', 'nama_barang', 'jenis_mutasi', 'jumlah']],
                    use_container_width=True, height=400, hide_index=True,
                    column_config={
                        "tanggal": st.column_config.DatetimeColumn("Waktu (WIB)", format="D MMM YYYY, HH:mm", width="medium"),
                        "nama_barang": st.column_config.TextColumn("Nama Barang", width="medium"),
                        "jenis_mutasi": st.column_config.TextColumn("Status", width="small"),
                        "jumlah": st.column_config.NumberColumn("Qty", width="small")
                    }
                )
                
            with c_right:
                st.subheader("📊 Saldo Stok")
                st.dataframe(
                    stok_df, use_container_width=True, height=400, hide_index=True,
                    column_config={
                        "Barang": st.column_config.TextColumn("Nama Barang", width="large"),
                        "Stok": st.column_config.NumberColumn("Sisa", width="small")
                    }
                )
        else:
            st.info("Belum ada data mutasi barang.")
    except Exception as e:
        st.error(f"Gagal memuat data: {e}")
