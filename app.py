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
                data = json.load(f)
                if not isinstance(data, dict):
                    return {"mappings": {}, "action_plan": {}}
                if "mappings" not in data:
                    data["mappings"] = {}
                if "action_plan" not in data:
                    data["action_plan"] = {}
                return data
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
    
    # Verileri Oku
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

    # Veri tiplerini string yapalım
    df_tsoft["Barkod_str"] = df_tsoft["Barkod"].astype(str).str.strip().str.replace(".0", "", regex=False)
    df_tsoft["SKU_str"] = df_tsoft["Web Servis Kodu"].astype(str).str.strip()
    
    df_mp["MP_Barcode_str"] = df_mp[mp_barcode_col].astype(str).str.strip().str.replace(".0", "", regex=False)
    df_mp["MP_SKU_str"] = df_mp[mp_sku_col].astype(str).str.strip()

    st.subheader(f"📊 {selected_marketplace} - T-Soft Karşılaştırma Paneli")
    
    # Otomatik Barkod Eşleşmesi
    merged_df = pd.merge(df_tsoft, df_mp, left_on="Barkod_str", right_on="MP_Barcode_str", how="inner", suffixes=("_tsoft", "_mp"))
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
            available_cols = [c for c in ["SKU_str", "Ürün Adı_tsoft", "Barkod_str", "Stok", "KDV Dahil Fiyat"] if c in merged_df.columns]
            st.dataframe(merged_df[available_cols], use_container_width=True)
        else:
            st.warning("Barkod üzerinden otomatik eşleşen ürün bulunamadı.")
        
    with tab2:
        st.subheader("Eşleşme Bekleyen Ürünler ve Manuel Hafıza")
        st.write("T-Soft dosyanızda barkodu bulunmayan ürünler için listeden seçebilir veya doğrudan manuel T-Soft Web Servis Kodu (SKU) yazarak eşleştirebilirsiniz.")
        
        if len(unmatched_mp) > 0:
            for idx, row in unmatched_mp.iterrows():
                mp_sku = row[mp_sku_col]
                mp_name = row[mp_name_col]
                mp_barcode = row[mp_barcode_col]
                
                with st.expander(f"📌 [{mp_sku}] {mp_name}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.write(f"**Pazaryeri Barkod:** {mp_barcode}")
                        st.write(f"**Pazaryeri Fiyat:** {row[mp_price_col]} | **Stok:** {row[mp_stock_col]}")
                    with c2:
                        match_mode = st.radio("Eşleme Yöntemi", ["Listeden Seç", "Manuel SKU Yaz"], key=f"mode_{mp_sku}", horizontal=True)
                        
                        chosen_sku = ""
                        if match_mode == "Listeden Seç":
                            tsoft_options = df_tsoft["SKU_str"] + " - " + df_tsoft["Ürün Adı"]
                            selected_tsoft = st.selectbox("T-Soft Eşleşmesi Seç", tsoft_options, key=f"select_{mp_sku}")
                            chosen_sku = selected_tsoft.split(" - ")[0]
                        else:
                            chosen_sku = st.text_input("T-Soft Web Servis Kodu (SKU) Gir", value=str(mp_sku), key=f"text_{mp_sku}")
                        
                        if st.button("🔗 Manuel Eşle ve Kaydet", key=f"btn_{mp_sku}"):
                            if "mappings" not in st.session_state.data:
                                st.session_state.data["mappings"] = {}
                            if selected_marketplace not in st.session_state.data["mappings"]:
                                st.session_state.data["mappings"][selected_marketplace] = {}
                            st.session_state.data["mappings"][selected_marketplace][str(mp_sku)] = chosen_sku
                            save_mappings(st.session_state.data)
                            st.success(f"Başarıyla eşleştirildi ve hafızaya kaydedildi: {mp_sku} -> {chosen_sku}")
                            st.rerun()
                            
                    action_tag = st.selectbox("İş Planı Etiketi", ["Seçiniz...", "Ürün Açılacak", "Fiyat Kontrol Edilecek", "Stok Güncellenecek", "İncelenecek"], key=f"action_{mp_sku}")
                    if action_tag != "Seçiniz...":
                        if "action_plan" not in st.session_state.data:
                            st.session_state.data["action_plan"] = {}
                        st.session_state.data["action_plan"][str(mp_sku)] = {"marketplace": selected_marketplace, "name": mp_name, "tag": action_tag}
                        save_mappings(st.session_state.data)
        else:
            st.success("Tüm pazar yeri ürünleri başarıyla eşleşmiş durumda!")
        
    with tab3:
        st.subheader("İş Planı ve Ürün Etiketleme Yönetimi")
        action_plans = st.session_state.data.get("action_plan", {})
        if action_plans:
            plan_df = pd.DataFrame.from_dict(action_plans, orient="index")
            st.dataframe(plan_df, use_container_width=True)
        else:
            st.info("Henüz iş planına eklenmiş bir ürün bulunmuyor.")
        
else:
    st.warning("Lütfen sol menüden **T-Soft Ana Ürünler** dosyasını ve seçtiğin **Pazaryeri Raporunu** yükleyin.")
