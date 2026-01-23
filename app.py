import streamlit as st
import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import pytz

# --- BAGIAN AWAL CODE TETAP SAMA (LOGIN & DATABASE) ---
# ... (Gunakan code sebelumnya sampai bagian Main Content) ...

# --- MODIFIKASI PADA BAGIAN TABEL STOK ---

    if not df_raw.empty:
        # ... (Proses filtering data tetap sama) ...

        # 1. ANALYTICS ROW (Tetap)
        # ... 

        # 2. STOCK TABLE DENGAN FITUR LABEL
        st.markdown("### 📊 Status Inventaris & Label")
        
        # Hitung stok sisa
        stok_rekap = df_raw.groupby(['SKU', 'Item Name', 'Unit'])['adj'].sum().reset_index()
        stok_rekap.columns = ['SKU', 'Produk', 'Satuan', 'Sisa Stok']

        # Layout untuk tabel dan preview label
        col_tabel, col_label = st.columns([2, 1])

        with col_tabel:
            st.write("Pilih Item untuk Lihat Preview Label:")
            # Gunakan st.dataframe untuk melihat data, tapi kita tambah selectbox untuk aksi cetak
            selected_item_sku = st.selectbox("Pilih SKU untuk Cetak Label", ["-- Pilih SKU --"] + list(stok_rekap['SKU']))
            
            st.dataframe(
                stok_rekap.style.apply(lambda x: ['background-color: #1e293b' if x.SKU == selected_item_sku else '' for _ in x], axis=1),
                use_container_width=True, hide_index=True
            )

        with col_label:
            if selected_item_sku != "-- Pilih SKU --":
                # Ambil detail item yang dipilih
                item_data = stok_rekap[stok_rekap['SKU'] == selected_item_sku].iloc[0]
                
                # --- UI GENERATOR LABEL (CSS INLINE) ---
                st.markdown(f"""
                <div style="background: white; color: black; padding: 20px; border-radius: 5px; border: 2px dashed #333; text-align: center; font-family: monospace;">
                    <h2 style="margin: 0; font-size: 24px; border-bottom: 2px solid black;">{item_data['SKU']}</h2>
                    <p style="margin: 10px 0 5px 0; font-size: 18px; font-weight: bold;">{item_data['Produk']}</p>
                    <div style="display: flex; justify-content: space-around; font-size: 14px; margin-top: 10px;">
                        <span>Satuan: {item_data['Satuan']}</span>
                        <span>Stok: {item_data['Sisa Stok']}</span>
                    </div>
                    <div style="margin-top: 15px; background: #eee; padding: 10px; font-size: 10px;">
                        INV-PRIME PRO SYSTEM<br>
                        Generated: {datetime.now().strftime('%Y-%m-%d')}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                st.caption("💡 Tips: Klik kanan pada kotak di atas lalu 'Print' atau gunakan Snipping Tool untuk cetak.")
                if st.button("Confirm Label Data"):
                    st.success(f"Label untuk {selected_item_sku} siap dicetak.")
            else:
                st.info("Pilih SKU di samping untuk generate label.")

        # 3. TRANSACTION LOG (Tetap sama)
        # ...
