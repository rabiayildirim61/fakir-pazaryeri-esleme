import json
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Fakir - Pazaryeri Entegrasyon & Eşleştirme Editörü",
    layout="wide",
)

# Dosya yolları
MAPPING_FILE = "manual_mappings.json"


# Hafıza (Manuel eşleştirmeler için) yükleme / kaydetme
def load_mappings():
  if os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {"trendyol": {}, "hb": {}, "n11": {}}


def save_mappings(mappings):
  with open(MAPPING_FILE, "w", encoding="utf-8") as f:
    json.dump(mappings, f, ensure_ascii=False, indent=4)


manual_mappings = load_mappings()

st.title("🛒 Fakir E-Ticaret | Pazaryeri Fiyat & Stok Uyumsuzluk Editörü")
st.markdown(
    "T-Soft ana verinizi Trendyol, Hepsiburada ve N11 excelleriyle karşılaştırın;"
    " fiyat/stok hatalarını görün ve manuel eşleştirmeleri hafızaya"
    " kaydedin."
)

# --- 1. DOSYA YÜKLEME ALANI ---
st.sidebar.header("📁 Excel Dosyalarını Yükleyin")
tsoft_file = st.sidebar.file_uploader("T-Soft Ürünleri (Ana Veri)", type=["xlsx"])
trendyol_file = st.sidebar.file_uploader("Trendyol Ürünleri", type=["xlsx"])
hb_file = st.sidebar.file_uploader("Hepsiburada Ürünleri", type=["xlsx"])
n11_file = st.sidebar.file_uploader("N11 Ürünleri", type=["xlsx"])

if not tsoft_file:
  st.info(
      "Lütfen sol menüden **T-Soft Ürünleri** Excel dosyasını yükleyerek"
      " başlayın."
  )
else:
  # T-Soft verisini oku
  df_tsoft = pd.read_excel(tsoft_file)

  # Sekmeler
  tab1, tab2, tab3, tab4 = st.tabs([
      "🛍️ Trendyol Karşılaştırma",
      "📦 Hepsiburada Karşılaştırma",
      "🛒 N11 Karşılaştırma",
      "🔗 Manuel Eşleştirme Hafızası",
  ])

  # --- TRENDYOL SEKMESİ ---
  with tab1:
    st.subheader("Trendyol Fiyat & Stok Karşılaştırması")
    if trendyol_file:
      df_ty = pd.read_excel(
          trendyol_file,
          sheet_name="Ürünler"
          if "Ürünler" in pd.ExcelFile(trendyol_file).sheet_names
          else 0,
      )
      st.markdown(f"**T-Soft Ürün Sayısı:** {len(df_tsoft)}")
      st.markdown(f"**Trendyol Ürün Sayısı:** {len(df_ty)}")

      merged_ty = pd.merge(
          df_tsoft,
          df_ty,
          left_on="Barkod",
          right_on="Barkod",
          how="outer",
          suffixes=("_tsoft", "_ty"),
          indicator=True,
      )
      st.dataframe(merged_ty.head(10))
    else:
      st.warning("Lütfen Trendyol Excel dosyasını yükleyin.")

  # --- HEPSİBURADA SEKMESİ ---
  with tab2:
    st.subheader("Hepsiburada Fiyat & Stok Karşılaştırması")
    if hb_file:
      df_hb = pd.read_excel(hb_file, sheet_name="Listelerim", header=1)
      st.write("Hepsiburada verisi yüklendi. Satır sayısı:", len(df_hb))
      st.dataframe(df_hb.head(10))
    else:
      st.warning("Lütfen Hepsiburada Excel dosyasını yükleyin.")

  # --- N11 SEKMESİ ---
  with tab3:
    st.subheader("N11 Fiyat & Stok Karşılaştırması")
    if n11_file:
      df_n11 = pd.read_excel(n11_file)
      st.write("N11 verisi yüklendi. Satır sayısı:", len(df_n11))
      st.dataframe(df_n11.head(10))
    else:
      st.warning("Lütfen N11 Excel dosyasını yükleyin.")

  # --- MANUEL EŞLEŞTİRME HAFIZASI ---
  with tab4:
    st.subheader("🔗 Manuel Eşleştirme Yönetimi (Kalıcı Hafıza)")
    st.markdown(
        "Otomatik eşleşmeyen ürünleri burada T-Soft barkodu ile pazaryeri"
        " kodu/barkodu olarak eşleştirebilirsiniz."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
      market = st.selectbox(
          "Pazaryeri Seçin", ["trendyol", "hb", "n11"], key="m_market"
      )
    with col2:
      tsoft_barcode = st.text_input("T-Soft Ürün Barkodu / Kodu")
    with col3:
      market_sku = st.text_input("Pazaryerindeki Karşılığı (Barkod / Kod)")

    if st.button("Eşleştirmeyi Kaydet"):
      if tsoft_barcode and market_sku:
        if market not in manual_mappings:
          manual_mappings[market] = {}
        manual_mappings[market][tsoft_barcode] = market_sku
        save_mappings(manual_mappings)
        st.success(
            f"Başarıyla kaydedildi! T-Soft: {tsoft_barcode} <-> Pazaryeri:"
            f" {market_sku}"
        )
      else:
        st.error("Lütfen her iki alanı da doldurun.")

    st.markdown("---")
    st.markdown("### Mevcut Kayıtlı Manuel Eşleştirmeler:")
    st.json(manual_mappings)
