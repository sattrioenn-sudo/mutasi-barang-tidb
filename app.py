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
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    
    * { font-family: 'Plus Jakarta Sans', sans-serif; }

    /* Background Full Dashboard */
    .stApp {
        background: radial-gradient(circle at 0% 0%, #0f172a 0%, #020617 100%);
    }

    /* Glassmorphism Card Style */
    div[data-testid="stMetricValue"] { font-size: 28px !important; color: #38bdf8 !important; }
    
    .metric-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px;
        border-radius: 16px;
        text-align: center;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
        border: 1px solid #38bdf8;
    }

    /* Custom Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0f172a;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Tombol & Input Style */
    .stButton>button {
        background: linear-gradient(90deg, #38bdf8 0%, #2563eb 100%);
        color: white;
        border-radius: 8px;
        border: none;
        font-weight: 600;
        transition: 0.3s;
    }
    .stButton>button:hover {
        box-shadow: 0 0 15px rgba(56, 189, 248, 0.5);
    }

    /* Tabel Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.1);
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

# --- UI LOGIN SCREEN ---
if not st.session_state["logged_in"]:
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
            u_input = st.text_input("Username", placeholder="Enter username...")
            p_input = st.text_input("Password", type="password", placeholder="Enter password...")
            if st.form_submit_button("LOGIN TO DASHBOARD", use_container_width=True):
                if "auth_users" in st.secrets:
                    users_list = st.secrets["auth_users"]
                    if u_input in users_list and str(p_input) == str(users_list[u_input]):
                        st.session_state["logged_in"] = True
                        st.session_state["current_user"] = u_input
                        st.rerun()
                    else: st.error("Invalid credentials")
                else: st.error("Secrets not configured!")

# --- UI DASHBOARD ---
else:
    with st.sidebar:
        st.markdown(f"""
            <div style='padding: 10px; background: rgba(56, 189, 248, 0.1); border-radius: 12px; border: 1px solid rgba(56, 189, 248, 0.2);'>
                <p style='margin:0; color:#94a3b8; font-size:12px;'>User Active</p>
                <p style='margin:0; color:#38bdf8; font-weight:700;'>{st.session_state['current_user'].upper()}</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        # --- TAB INPUT ---
        with st.expander("➕ Create Transaction", expanded=True):
            with st.form("input", clear_on_submit=True):
                sku = st.text_input("SKU", placeholder="BRG-001")
                n = st.text_input("Item Name", placeholder="Office Chair")
                satuan = st.selectbox("Unit", ["Pcs", "Box", "Kg", "Liter", "Set"])
                j = st.selectbox("Action", ["Masuk", "Keluar"])
                q = st.number_input("Qty", min_value=1, step=1)
                if st.form_submit_button("SAVE TRANSACTION", use_container_width=True):
                    if n:
                        tz_jkt = pytz.timezone('Asia/Jakarta')
                        waktu_sekarang = datetime.now(tz_jkt).strftime('%Y-%m-%d %H:%M:%S')
                        nama_lengkap = f"[{sku}] {n} ({satuan})" if sku else f"{n} ({satuan})"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (nama_lengkap, j, q, waktu_sekarang))
                        conn.commit(); conn.close()
                        st.success("Entry Saved!")
                        st.rerun()

        # --- FITUR HAPUS (YANG TADI HILANG) ---
        with st.expander("🗑️ Danger Zone"):
            try:
                conn = init_connection()
                # Ambil daftar barang unik untuk dihapus
                items_df = pd.read_sql("SELECT DISTINCT nama_barang FROM inventory", conn)
                conn.close()
                
                if not items_df.empty:
                    target = st.selectbox("Select Item to Delete:", items_df['nama_barang'])
                    st.warning("Action cannot be undone!")
                    conf = st.checkbox("I confirm to delete this item")
                    
                    if st.button("DELETE ALL DATA FOR THIS ITEM", use_container_width=True, disabled=not conf):
                        conn = init_connection()
                        cur = conn.cursor()
                        # Hapus semua transaksi untuk barang tersebut
                        cur.execute("DELETE FROM inventory WHERE nama_barang = %s", (target,))
                        conn.commit()
                        conn.close()
                        st.success(f"Deleted: {target}")
                        st.rerun()
                else:
                    st.info("No items found.")
            except Exception as e:
                st.error(f"Error Loading List: {e}")

        st.markdown("---")
        if st.button("LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()
