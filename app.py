import streamlit as st
import pandas as pd
import json
import os

st.set_page_config(page_title="Fakir Pazaryeri Entegrasyon & Eşleştirme Paneli", layout="wide")

MAPPING_FILE = "manual_mappings.json"

def load_mappings():
    if os.path.exists(MAPPING_FILE):
        try:
            with open(MAPPING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {"mappings": {}, "action_plan": {}}
    return {"mappings": {}, "action_plan": {}}

def save_mappings(data):
    with open(MAPPING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

if "data" not in st.session_state:
    st.session_state.data = load_mappings()

st.title("🛒 Fakir Pazaryeri Ürün, Fiyat ve Stok Eşleştirme Paneli")
st.markdown("---")

st.sidebar.header("📁 Dosya Yükleme Alanı")
tsoft_file = st.sidebar.file_uploader("1. T-Soft Ana Ürünler Excel", type=["xlsx", "xls"])
trendyol_file = st.sidebar.file_uploader("2. Trendyol Raporu", type=["xlsx", "xls"])
hb_file = st.sidebar.file_uploader("3. Hepsiburada Raporu ('Listelerim')", type=["xlsx", "xls"])
n11_file = st.sidebar.file_uploader("4. N11 Raporu", type=["xlsx", "xls"])

selected_marketplace = st.sidebar.selectbox("Pazaryeri Seçin", ["Trendyol", "Hepsiburada", "N11"])

if tsoft_file and ((selected_marketplace == "Trendyol" and trendyol_file) or 
                   (selected_marketplace == "Hepsiburada" and hb_file) or 
                   (selected_marketplace == "N11" and n11_file)):
    
    # Load T-Soft
    df_tsoft = pd.read_excel(tsoft_file)
    
    # Load Marketplace
    if selected_marketplace == "Trendyol":
        df_mp = pd.read_excel(trendyol_file, sheet_name=0)
    elif selected_marketplace == "Hepsiburada":
        df_mp = pd.read_excel(hb_file, sheet_name="Listelerim")
    else:
        df_mp = pd.read_excel(n11_file, sheet_name="Ürün Bilgileri Güncelle")
        
    st.subheader(f"📊 {selected_marketplace} - T-Soft Karşılaştırma Paneli")
    
    # Basic info display
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"T-Soft Ürün Sayısı: {len(df_tsoft)}")
    with col2:
        st.info(f"{selected_marketplace} Ürün Sayısı: {len(df_mp)}")
        
    st.markdown("### 🔍 Eşleşme Durumu ve İş Planı Yönetimi")
    st.write("Burada otomatik barkod/SKU eşleşmeleri görünür ve eşleşmeyenler için manuel eşleştirme yapabilirsiniz.")
    
    # Sample view for demonstration
    st.dataframe(df_tsoft.head(5))
    
else:
    st.warning("Lütfen sol menüden **T-Soft Ana Ürünler** dosyasını ve seçtiğiniz **Pazaryeri Raporunu** yükleyin.")
