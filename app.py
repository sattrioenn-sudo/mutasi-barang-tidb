import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# 1. Konfigurasi Halaman
st.set_page_config(page_title="INV-PRIME PRO", page_icon="🚀", layout="wide")

# 2. CSS UI Design
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700&display=swap');
    * { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at 0% 0%, #0f172a 0%, #020617 100%); }
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid rgba(255, 255, 255, 0.05); }
    .stButton>button {
        background: linear-gradient(90deg, #38bdf8 0%, #2563eb 100%);
        color: white; border-radius: 8px; border: none; font-weight: 600;
    }
    .label-box {
        background: white; color: black; padding: 20px; border-radius: 5px; 
        border: 2px dashed #333; text-align: center; font-family: monospace;
    }
    .metric-card {
        background: rgba(255, 255, 255, 0.05); padding: 15px; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1);
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

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

# --- UTILS ---
def parse_inventory_name(val):
    parts = str(val).split('|')
    parts = [p.strip() for p in parts]
    while len(parts) < 6:
        parts.append("-")
    return parts

# --- LOGIN ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<h2 style='text-align:center; color:white;'>🔐 INV-PRIME LOGIN</h2>", unsafe_allow_html=True)
        with st.form("login_form"):
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            if st.form_submit_button("LOGIN", use_container_width=True):
                users = st.secrets["auth_users"]
                if u_input in users and str(p_input) == str(users[u_input]):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = u_input
                    st.rerun()
                else: st.error("Akses Ditolak")
else:
    # --- DATA ENGINE ---
    try:
        conn = init_connection()
        df_raw = pd.read_sql("SELECT id, nama_barang, jenis_mutasi, jumlah, tanggal FROM inventory", conn)
        conn.close()
    except Exception as e:
        st.error(f"Error Database: {e}")
        df_raw = pd.DataFrame()

    # --- SIDEBAR ---
    with st.sidebar:
        st.markdown(f"**User Active:** `{st.session_state['current_user'].upper()}`")
        
        st.markdown("---")
        st.markdown("### 🔍 Filter Laporan")
        today = datetime.now()
        start_date = st.date_input("Tanggal Mulai", today - timedelta(days=7))
        end_date = st.date_input("Tanggal Akhir", today)
        
        st.markdown("---")
        
        with st.expander("➕ Tambah Transaksi"):
            with st.form("input_form", clear_on_submit=True):
                sku_f = st.text_input("SKU")
                nama_f = st.text_input("Nama Barang")
                sat_f = st.selectbox("Satuan", ["Pcs", "Box", "Set", "Kg", "Ltr"])
                j_f = st.selectbox("Jenis", ["Masuk", "Keluar"])
                q_f = st.number_input("Qty", min_value=1)
                note_f = st.text_input("Ket")
                if st.form_submit_button("SIMPAN DATA", use_container_width=True):
                    if sku_f and nama_f:
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        u = st.session_state['current_user']
                        full = f"{sku_f} | {nama_f} | {sat_f} | {u} | {u} | {note_f if note_f else '-'}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("INSERT INTO inventory (nama_barang, jenis_mutasi, jumlah, tanggal) VALUES (%s,%s,%s,%s)", (full, j_f, q_f, now))
                        conn.commit(); conn.close(); st.rerun()

        with st.expander("📝 Edit Transaksi"):
            if not df_raw.empty:
                edit_id = st.selectbox("ID Edit", df_raw['id'].sort_values(ascending=False))
                row_edit = df_raw[df_raw['id'] == edit_id].iloc[0]
                p_old = parse_inventory_name(row_edit['nama_barang'])
                with st.form("edit_form"):
                    e_sku = st.text_input("SKU", value=p_old[0])
                    e_nama = st.text_input("Nama", value=p_old[1])
                    e_qty = st.number_input("Qty", value=int(row_edit['jumlah']))
                    e_note = st.text_input("Ket", value=p_old[5])
                    if st.form_submit_button("UPDATE"):
                        tz = pytz.timezone('Asia/Jakarta'); now = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
                        u = st.session_state['current_user']
                        full_upd = f"{e_sku} | {e_nama} | {p_old[2]} | {p_old[3]} | {u} | {e_note}"
                        conn = init_connection(); cur = conn.cursor()
                        cur.execute("UPDATE inventory SET nama_barang=%s, jumlah=%s, tanggal=%s WHERE id=%s", (full_upd, e_qty, now, int(edit_id)))
                        conn.commit(); conn.close(); st.rerun()

        with st.expander("🗑️ Hapus Transaksi"):
            if not df_raw.empty:
                del_id = st.selectbox("ID Hapus", df_raw['id'].sort_values(ascending=False))
                if st.button("KONFIRMASI HAPUS"):
                    conn = init_connection(); cur = conn.cursor()
                    cur.execute("DELETE FROM inventory WHERE id = %s", (int(del_id),))
                    conn.commit(); conn.close(); st.rerun()

        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            st.rerun()

    # --- DATA PROCESSING ---
    if not df_raw.empty:
        parsed = df_raw['nama_barang'].apply(parse_inventory_name)
        df_raw['SKU'] = parsed.str[0]; df_raw['Item Name'] = parsed.str[1]
        df_raw['Unit'] = parsed.str[2]; df_raw['Keterangan'] = parsed.str[5]
        df_raw['tanggal'] = pd.to_datetime(df_raw['tanggal'])
        df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)

        # Kalkulasi Laporan Opname
        df_awal = df_raw[df_raw['tanggal'].dt.date < start_date]
        stok_awal = df_awal.groupby(['SKU'])['adj'].sum().reset_index(name='Stok Awal')
        
        mask = (df_raw['tanggal'].dt.date >= start_date) & (df_raw['tanggal'].dt.date <= end_date)
        df_periode = df_raw.loc[mask].copy()
        
        mutasi_periode = df_periode.groupby(['SKU', 'jenis_mutasi'])['jumlah'].sum().unstack(fill_value=0).reset_index()
        if 'Masuk' not in mutasi_periode: mutasi_periode['Masuk'] = 0
        if 'Keluar' not in mutasi_periode: mutasi_periode['Keluar'] = 0
        mutasi_periode = mutasi_periode[['SKU', 'Masuk', 'Keluar']]

        all_sku = df_raw[['SKU', 'Item Name', 'Unit']].drop_duplicates('SKU')
        opname_df = pd.merge(all_sku, stok_awal, on='SKU', how='left').fillna(0)
        opname_df = pd.merge(opname_df, mutasi_periode, on='SKU', how='left').fillna(0)
        opname_df['Stok Akhir'] = opname_df['Stok Awal'] + opname_df['Masuk'] - opname_df['Keluar']

        # --- DASHBOARD UTAMA ---
        st.markdown("<h1 style='color: white;'>Inventory Command Center</h1>", unsafe_allow_html=True)

        # --- FITUR BARU 1: ALERT STOK KRITIS ---
        stok_kritis = opname_df[opname_df['Stok Akhir'] < 5]
        if not stok_kritis.empty:
            st.error(f"⚠️ **Peringatan Stok Kritis!** {len(stok_kritis)} item memiliki stok di bawah 5.")
            with st.expander("Lihat Detail Barang Mau Habis"):
                st.table(stok_kritis[['SKU', 'Item Name', 'Stok Akhir']])

        # --- FITUR BARU 2: METRIK & GRAFIK ---
        m1, m2, m3 = st.columns([1, 1, 2])
        with m1:
            st.metric("Total Masuk", int(opname_df['Masuk'].sum()))
        with m2:
            st.metric("Total Keluar", int(opname_df['Keluar'].sum()))
        with m3:
            # Grafik 5 Barang Paling Banyak Keluar
            top_keluar = opname_df.sort_values(by='Keluar', ascending=False).head(5)
            if top_keluar['Keluar'].sum() > 0:
                st.markdown("**Top 5 Barang Keluar (Fast Moving)**")
                st.bar_chart(top_keluar.set_index('Item Name')['Keluar'])

        # --- SECTION: LAPORAN OPNAME ---
        st.markdown(f"### 📋 Laporan Stock Opname ({start_date.strftime('%d %b')} - {end_date.strftime('%d %b %Y')})")
        st.dataframe(
            opname_df[['SKU', 'Item Name', 'Unit', 'Stok Awal', 'Masuk', 'Keluar', 'Stok Akhir']],
            use_container_width=True, hide_index=True
        )

        st.markdown("---")

        # --- SECTION: LABEL & LOG ---
        c1, c2 = st.columns([1, 2])
        with c1:
            st.markdown("### 🏷️ Cetak Label")
            t_sku = st.selectbox("Pilih SKU", ["-- Pilih --"] + list(opname_df['SKU']))
            if t_sku != "-- Pilih --":
                r_l = opname_df[opname_df['SKU'] == t_sku].iloc[0]
                st.markdown(f'''
                    <div class="label-box">
                        <h2>{r_l["SKU"]}</h2>
                        <p><b>{r_l["Item Name"]}</b></p>
                        <small>{r_l["Unit"]} | SALDO: {r_l["Stok Akhir"]}</small>
                    </div>
                ''', unsafe_allow_html=True)

        with c2:
            st.markdown("### 📜 Detail Mutasi Periode Ini")
            df_display = df_periode.sort_values(by='tanggal', ascending=False)
            df_display['Status'] = df_display['jenis_mutasi'].apply(lambda x: "🟢 MASUK" if x == 'Masuk' else "🔴 KELUAR")
            st.dataframe(
                df_display[['id', 'Status', 'tanggal', 'SKU', 'Item Name', 'jumlah', 'Keterangan']], 
                use_container_width=True, hide_index=True,
                column_config={"tanggal": st.column_config.DatetimeColumn("Waktu", format="D MMM, HH:mm")}
            )
    else:
        st.info("Belum ada data di database.")
