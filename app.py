import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime
import pytz

# 1. Konfigurasi Halaman & Tema Dasar
st.set_page_config(page_title="INV-PRIME PRO", page_icon="🚀", layout="wide")

# 2. CSS UI Design Pro (Modern Developer Look)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 0% 0%, #0f172a 0%, #020617 100%); }
    
    /* Metric Card Custom */
    .metric-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 10px;
    }
    
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid rgba(255, 255, 255, 0.05); }
    
    .stButton>button {
        background: linear-gradient(90deg, #38bdf8 0%, #2563eb 100%);
        color: white; border-radius: 8px; border: none; font-weight: 600;
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

# 4. Inisialisasi Session State
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "current_user" not in st.session_state:
    st.session_state["current_user"] = ""

# --- LOGIKA TAMPILAN ---
if not st.session_state["logged_in"]:
    # TAMPILAN LOGIN
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("""
            <div style='background: rgba(30, 41, 59, 0.7); padding: 40px; border-radius: 24px; border: 1px solid rgba(255, 255, 255, 0.1); backdrop-filter: blur(20px);'>
                <h1 style='text-align:center; color:white; margin-bottom: 0;'>🚀</h1>
                <h2 style='text-align:center; color:white; margin-top: 0;'>INV-PRIME</h2>
                <p style='text-align:center; color:#94a3b8;'>Enterprise Inventory System</p>
            </div>
        """, unsafe_allow_html=True)
        with st.form("login_form"):
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN TO DASHBOARD", use_container_width=True):
                if "auth_users" in st.secrets:
                    users_list = st.secrets["auth_users"]
                    if u_input in users_list and str(p_input) == str(users_list[u_input]):
                        st.session_state["logged_in"] = True
                        st.session_state["current_user"] = u_input
                        st.rerun()
                    else: st.error("Invalid credentials")
                else: st.error("Secrets not configured!")

else:
    # TAMPILAN SETELAH LOGIN
    # 1. SIDEBAR
    with st.sidebar:
        st.markdown(f"""
            <div style='padding: 10px; background: rgba(56, 189, 248, 0.1); border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.2);'>
                <p style='margin:0; color:#94a3b8; font-size:12px;'>User Active</p>
                <p style='margin:0; color:#38bdf8; font-weight:700;'>{st.session_state['current_user'].upper()}</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        with st.expander("➕ Create Transaction", expanded=True):
            with st.form("input", clear_on_submit=True):
                sku = st.text_input("SKU", placeholder="BRG-001")
                n = st.text_input("Item Name")
                satuan = st.selectbox("Unit", ["Pcs", "Box", "Kg", "Liter", "Set"])
                j = st.selectbox("Action", ["Masuk", "Keluar"])
                q = st.number_input("Qty", min_value=1, step=1)
                if st.form_submit_button("SAVE TRANSACTION", use_container_width=True):
                    if n:
                        # 1. Ambil Waktu Jakarta
                        tz_jkt = pytz.timezone('Asia/Jakarta')
                        waktu_sekarang = datetime.now(tz_jkt).strftime('%Y-%m-%d %H:%M:%S')
                        
                        # 2. Ambil Nama User yang sedang Login
                        user_aktif = st.session_state.get('current_user', 'Unknown')
                        
                        # 3. PROSES PENGGABUNGAN (SKU + Nama + Satuan + USER)
                        # Hasilnya: [BRG-01] Kursi (Pcs) | User: admin
                        nama_lengkap = f"[{sku}] {n} ({satuan}) | User: {user_aktif}" if sku else f"{n} ({satuan}) | User: {user_aktif}"
                        
                        try:
                            conn = init_connection()
                            cur = conn.cursor()
                            query = "INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s, %s, %s, %s)"
                            cur.execute(query, (nama_lengkap, j, q, waktu_sekarang))
                            conn.commit()
                            conn.close()
                            st.success(f"Saved by {user_aktif}")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")

        with st.expander("🗑️ Danger Zone"):
            try:
                conn = init_connection()
                items_df = pd.read_sql("SELECT DISTINCT nama_barang FROM inventory", conn); conn.close()
                if not items_df.empty:
                    target = st.selectbox("Select Item to Delete:", items_df['nama_barang'])
                    conf = st.checkbox("Confirm delete")
                    if st.button("DELETE ITEM", use_container_width=True, disabled=not conf):
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("DELETE FROM inventory WHERE nama_barang = %s", (target,))
                        conn.commit(); conn.close()
                        st.rerun()
            except: st.write("No data")

        if st.button("LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # 2. HALAMAN UTAMA (Main Dashboard Content)
    st.markdown("<h1 style='color: white;'>Inventory Overview</h1>", unsafe_allow_html=True)
    
    try:
        conn = init_connection()
        df = pd.read_sql("SELECT * FROM inventory ORDER BY tanggal DESC", conn)
        conn.close()

        if not df.empty:
            df['tanggal'] = pd.to_datetime(df['tanggal'])
            # Perhitungan Stok
            df['adj'] = df.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
            stok_df = df.groupby('nama_barang')['adj'].sum().reset_index()
            stok_df.columns = ['Item', 'Stock']

            # METRICS
            m1, m2, m3 = st.columns(3)
            with m1: st.markdown(f"<div class='metric-card'><p style='color:#94a3b8;'>Total Entries</p><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
            with m2: st.markdown(f"<div class='metric-card'><p style='color:#94a3b8;'>Volume Movement</p><h2>{int(df['jumlah'].sum())}</h2></div>", unsafe_allow_html=True)
            with m3:
                top_item = stok_df.iloc[stok_df['Stock'].idxmax()]['Item'] if not stok_df.empty else "-"
                st.markdown(f"<div class='metric-card'><p style='color:#94a3b8;'>Highest Stock</p><h2 style='font-size:16px;'>{top_item}</h2></div>", unsafe_allow_html=True)

            st.write("---")

            # TABLES
            col_log, col_stock = st.columns([1.6, 1.4])
            with col_log:
                st.markdown("### 📜 Activity Log")
                st.dataframe(df[['tanggal', 'nama_barang', 'jenis_mutasi', 'jumlah']], use_container_width=True, hide_index=True,
                    column_config={
                        "tanggal": st.column_config.DatetimeColumn("Time", format="D MMM, HH:mm"),
                        "nama_barang": "Product",
                        "jenis_mutasi": "Status",
                        "jumlah": "Qty"
                    })
            
            with col_stock:
                st.markdown("### 📊 Saldo Stok")
                st.dataframe(stok_df, use_container_width=True, hide_index=True,
                    column_config={
                        "Item": "Product Detail",
                        "Stock": st.column_config.NumberColumn("Current Stock", format="%d 📦")
                    })
        else:
            st.info("No transaction data found. Please add your first item from the sidebar.")
    except Exception as e:
        st.error(f"Error: {e}")
