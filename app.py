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
    
    # 1. Verileri Oku
    df_tsoft = pd.read_excel(tsoft_file)
    
    if selected_marketplace == "Trendyol":
        df_mp = pd.read_excel(trendyol_file, sheet_name=0)
        mp_sku_col = "Tedarikçi Stok Kodu"
        mp_name_col = "Ürün Adı"
        mp_price_col = "Trendyol'da Satılacak Fiyat (KDV Dahil)"
        mp_stock_col = "Ürün Stok Adedi"
        mp_barcode_col = "Barkod"
    elif selected_marketplace == "Hepsiburada":
        df_mp = pd.read_excel(hb_file, sheet_name="Listelerim")
        mp_sku_col = "Satıcı Stok Kodu" if "Satıcı Stok Kodu" in df_mp.columns else "SKU"
        mp_name_col = "Ürün Adı"
        mp_price_col = "Fiyat"
        mp_stock_col = "Stok"
        mp_barcode_col = "Barkod"
    else:
        df_mp = pd.read_excel(n11_file, sheet_name="Ürün Bilgileri Güncelle")
        mp_sku_col = "Stok Kodu " if "Stok Kodu " in df_mp.columns else "Stok Kodu"
        mp_name_col = "Ürün Adı " if "Ürün Adı " in df_mp.columns else "Ürün Adı"
        mp_price_col = "N11 Satış Fiyatı (KDV Dahil)"
        mp_stock_col = "Stok"
        mp_barcode_col = "Barcode"

    # Veri tiplerini string yapalım ki eşleşme kaçmasın
    df_tsoft["Barkod_str"] = df_tsoft["Barkod"].astype(str).str.strip().str.replace(".0", "", regex=False)
    df_tsoft["SKU_str"] = df_tsoft["Web Servis Kodu"].astype(str).str.strip()
    
    df_mp["MP_Barcode_str"] = df_mp[mp_barcode_col].astype(str).str.strip().str.replace(".0", "", regex=False)
    df_mp["MP_SKU_str"] = df_mp[mp_sku_col].astype(str).str.strip()

    st.subheader(f"📊 {selected_marketplace} - T-Soft Karşılaştırma Paneli")
    
    # Otomatik Barkod Eşleşmesi
    merged_df = pd.merge(df_tsoft, df_mp, left_on="Barkod_str", right_on="MP_Barcode_str", how="inner", suffixes=("_tsoft", "_mp"))
    
    # Eşleşmeyenler
    unmatched_mp = df_mp[~df_mp["MP_Barcode_str"].isin(df_tsoft["Barkod_str"])]

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("T-Soft Toplam Ürün", len(df_tsoft))
    with col2:
        st.metric(f"{selected_marketplace} Toplam Ürün", len(df_mp))
    with col3:
        st.metric("Otomatik Eşleşen Ürün", len(merged_df))
        
    st.markdown("---")
    
    # Sekmeler
    tab1, tab2, tab3 = st.tabs(["✅ Eşleşen Ürünler", "⏳ Eşleşme Bekleyenler & Manuel Eşleme", "📋 İş Planı & Etiketler"])
    
    with tab1:
        st.subheader("Otomatik Eşleşen Ürünler (T-Soft & Pazaryeri)")
        if len(merged_df) > 0:
            # Güvenli kolon seçimi
            available_cols = [c for c in ["SKU_str", "Ürün Adı_tsoft", "Barkod_str", "Stok", "KDV Dahil Fiyat"] if c in merged_df.columns]
            st.dataframe(merged_df[available_cols], use_container_width=True)
        else:
            st.warning("Barkod üzerinden otomatik eşleşen ürün bulunamadı.")
        
    with tab2:
        st.subheader("Eşleşme Bekleyen Ürünler")
        st.write("Barkodları eşleşmeyen pazar yeri ürünleri:")
        if len(unmatched_mp) > 0:
            st.dataframe(unmatched_mp[[mp_sku_col, mp_name_col, mp_barcode_col, mp_price_col, mp_stock_col]], use_container_width=True)
        else:
            st.success("Tüm pazar yeri ürünleri başarıyla eşleşmiş durumda!")
        
    with tab3:
        st.subheader("İş Planı ve Ürün Etiketleme Yönetimi")
        st.write("Eşleşme bekleyen veya kontrol edilmesi gereken ürünler için etiketleme alanı.")
        
else:
    st.warning("Lütfen sol menüden **T-Soft Ana Ürünler** dosyasını ve seçtiğin **Pazaryeri Raporunu** yükleyin.")
