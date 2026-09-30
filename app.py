import json
import os
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Fakir - Pazaryeri Entegrasyon & Eşleştirme Editörü",
    layout="wide",
)

# Hafıza / Kayıt Dosyası
MAPPING_FILE = "manual_mappings.json"


def load_mappings():
  if os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
      return json.load(f)
  return {"Trendyol": {}, "Hepsiburada": {}, "N11": {}}


def save_mappings(mappings):
  with open(MAPPING_FILE, "w", encoding="utf-8") as f:
    json.dump(mappings, f, ensure_ascii=False, indent=4)


saved_data = load_mappings()
if "manual_mappings" not in st.session_state:
  st.session_state.manual_mappings = saved_data.get("manual_mappings", {
      "Trendyol": {},
      "Hepsiburada": {},
      "N11": {},
  })
if "acilacak_urunler" not in st.session_state:
  st.session_state.acilacak_urunler = saved_data.get("acilacak_urunler", {
      "Trendyol": {},
      "Hepsiburada": {},
      "N11": {},
  })

st.title("🛒 Fakir E-Ticaret | Pazaryeri Fiyat & Stok Uyumsuzluk Editörü")
st.markdown(
    "T-Soft ana verinizi pazar yeri excelleriyle karşılaştırın; fiyat ve stok"
    " hatalarını otomatik yakalayın."
)

# --- SOL MENÜ: DOSYA YÜKLEME ---
st.sidebar.header("📁 Excel Dosyalarını Yükleyin")
tsoft_file = st.sidebar.file_uploader(
    "⭐ 1. T-Soft Ürünleri (Ana Veri)", type=["xlsx", "xls", "csv"]
)

pazar_secimi = st.sidebar.selectbox(
    "Hedef Pazar Yeri Seçin", ["Trendyol", "Hepsiburada", "N11"]
)
pazar_file = st.sidebar.file_uploader(
    f"📦 2. {pazar_secimi} Raporu", type=["xlsx", "xls", "csv"]
)


def kolon_degeri_bul(row, keys):
  row_keys = [str(k).lower().strip() for k in row.keys()]
  for k in keys:
    if k.lower() in row_keys:
      actual_key = list(row.keys())[row_keys.index(k.lower())]
      val = row[actual_key]
      if pd.notna(val):
        return val
  return ""


if not tsoft_file:
  st.info("Lütfen sol menüden **T-Soft Ürünleri** Excel dosyasını yükleyin.")
else:
  # T-Soft verisini oku
  try:
    df_tsoft = pd.read_excel(tsoft_file)
  except Exception:
    df_tsoft = pd.read_csv(tsoft_file)

  if not pazar_file:
    st.warning(
        f"Lütfen sol menüden **{pazar_secimi}** Excel dosyasını da yükleyin."
    )
  else:
    # Pazar yeri verisini oku
    try:
      xls = pd.ExcelFile(pazar_file)
      sheet_name = (
          "Listelerim" if "Listelerim" in xls.sheet_names else xls.sheet_names[0]
      )
      df_pazar = pd.read_excel(pazar_file, sheet_name=sheet_name)
    except Exception:
      df_pazar = pd.read_csv(pazar_file)

    # Haritalama sözlükleri oluştur
    pazar_barkod_map = {}
    pazar_kod_map = {}
    pazar_isim_map = {}
    pazar_rows = df_pazar.to_dict(orient="records")

    for idx, p_row in enumerate(pazar_rows):
      p_barkod = str(kolon_degeri_bul(p_row, ["barkod", "barcode"])).strip()
      p_kod = str(
          kolon_degeri_bul(
              p_row, [
                  "web servis kodu",
                  "stok kodu",
                  "sku",
                  "stokkodu",
                  "merchant sku",
              ]
          )
      ).strip()
      p_isim = str(
          kolon_degeri_bul(p_row, ["ürün adı", "urun adi", "title"])
      ).strip().lower()

      if p_barkod:
        for b in p_barkod.split(";"):
          if b.strip():
            pazar_barkod_map[b.strip()] = idx
      if p_kod:
        pazar_kod_map[p_kod] = idx
      if p_isim:
        pazar_isim_map[p_isim] = idx

    eslesen_sayisi = 0
    hata_sayisi = 0
    acilicak_sayisi = 0
    eslesmeyen_sayisi = 0

    hatali_tablo = []
    eslesmeyen_tablo = []
    acilicak_tablo = []

    tsoft_rows = df_tsoft.to_dict(orient="records")

    for t_idx, t_row in enumerate(tsoft_rows):
      t_barkod = str(kolon_degeri_bul(t_row, ["barkod", "barcode"])).strip()
      t_kod = str(
          kolon_degeri_bul(t_row, ["web servis kodu", "stok kodu", "sku"])
      ).strip()
      t_isim = str(
          kolon_degeri_bul(t_row, ["ürün adı", "urun adi", "title"])
      ).strip()
      t_stok = (
          pd.to_numeric(
              kolon_degeri_bul(t_row, ["stok", "stok miktari", "miktar"]),
              errors="coerce",
          )
          or 0
      )
      t_fiyat = (
          pd.to_numeric(
              kolon_degeri_bul(
                  t_row, ["kdv dahil fiyat", "satis fiyati", "fiyat"]
              ),
              errors="coerce",
          )
          or 0
      )
      t_unique_key = t_kod or t_barkod or t_isim

      # İş planında açılacaklar kontrolü
      if t_unique_key in st.session_state.acilacak_urunler[pazar_secimi]:
        acilicak_sayisi += 1
        acilicak_tablo.append({
            "İsim": t_isim,
            "Kod": t_kod,
            "Barkod": t_barkod,
            "Stok": t_stok,
            "Fiyat": t_fiyat,
            "Index": t_idx,
        })
        continue

      eslesen_idx = None
      yontem = ""

      # 1. Manuel hafıza
      if (
          t_unique_key
          in st.session_state.manual_mappings[pazar_secimi]
      ):
        eslesen_idx = st.session_state.manual_mappings[pazar_secimi][
            t_unique_key
        ]
        yontem = "Buluttan / Hafızadan Eşleşti"
      # 2. Barkod eşleşmesi
      elif t_barkod and t_barkod in pazar_barkod_map:
        eslesen_idx = pazar_barkod_map[t_barkod]
        yontem = "Barkod ile"
      # 3. Stok kodu eşleşmesi
      elif t_kod and t_kod in pazar_kod_map:
        eslesen_idx = pazar_kod_map[t_kod]
        yontem = "Stok Kodu ile"
      # 4. İsim eşleşmesi
      elif t_isim and t_isim.lower() in pazar_isim_map:
        eslesen_idx = pazar_isim_map[t_isim.lower()]
        yontem = "Ürün Adı ile"

      if (
          eslesen_idx is not None
          and 0 <= eslesen_idx < len(pazar_rows)
      ):
        eslesen_sayisi += 1
        p_row = pazar_rows[eslesen_idx]
        p_stok = (
            pd.to_numeric(
                kolon_degeri_bul(p_row, ["stok", "stok miktari", "miktar"]),
                errors="coerce",
            )
            or 0
        )
        p_fiyat = (
            pd.to_numeric(
                kolon_degeri_bul(
                    p_row, ["kdv dahil fiyat", "satis fiyati", "fiyat"]
                ),
                errors="coerce",
            )
            or 0
        )

        hatalar = []
        if t_stok <= 0 and p_stok > 0:
          hatalar.append("Stok Hatası: T-Soft'ta 0, Pazar Yerinde Açık!")
        if t_fiyat > 0 and p_fiyat > 0 and abs(t_fiyat - p_fiyat) > 1:
          hatalar.append(f"Fiyat Uyumsuzluğu (T-Soft: {t_fiyat} - Pazar: {p_fiyat})")

        if hatalar:
          hata_sayisi += 1
          hatali_tablo.append({
              "Yöntem": yontem,
              "Ürün Adı": t_isim,
              "T-Soft Bilgi": f"Stok: {t_stok} | Fiyat: {t_fiyat} TL",
              "Pazar Bilgi": f"Stok: {p_stok} | Fiyat: {p_fiyat} TL",
              "Hata": " | ".join(hatalar),
          })
      else:
        eslesmeyen_sayisi += 1
        eslesmeyen_tablo.append({
            "Ürün": t_isim,
            "Kod": t_kod,
            "Barkod": t_barkod,
            "Stok": t_stok,
            "Fiyat": t_fiyat,
            "Key": t_unique_key,
        })

    # --- ÖZET GÖSTERGELERİ ---
    st.subheader(f"📊 {pazar_secimi} Karşılaştırma Özeti")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("T-Soft Ürün", len(tsoft_rows))
    col2.metric("Eşleşen", eslesen_sayisi)
    col3.metric("Kritik Hata", hata_sayisi, delta_color="inverse")
    col4.metric("İş Planında Açılacak", acilicak_sayisi)
    col5.metric("Bekleyen / Eşleşmeyen", eslesmeyen_sayisi)

    st.markdown("---")

    # --- TABLO 1: KRİTİK HATALAR ---
    st.subheader("⚠ T-Soft'a Göre Hatalı / Uyumsuz Ürünler")
    if hatali_tablo:
      st.dataframe(pd.DataFrame(hatali_tablo), use_container_width=True)
    else:
      st.success("Tebrikler! Eşleşen ürünlerde hiçbir hata bulunamadı. 🎉")

    # --- TABLO 2: İŞ PLANINDA AÇILACAKLAR ---
    st.subheader("🚧 İş Planında / Açılacak Ürünler")
    if acilicak_tablo:
      df_acil = pd.DataFrame(acilicak_tablo)
      st.dataframe(df_acil, use_container_width=True)

      col_c1, col_c2 = st.columns([3, 1])
      with col_c1:
        cikarilacak_urun = st.selectbox(
            "Listeden Çıkarmak İstediğin Ürünü Seç",
            options=df_acil["Key"].tolist() if "Key" in df_acil else [],
        )
      with col_c2:
        if st.button("Listeden Çıkar"):
          # Bulun ve sil
          keys_to_del = [
              k
              for k, v in st.session_state.acilacak_urunler[
                  pazar_secimi
              ].items()
              if k == cikarilacak_urun
          ]
          for k in keys_to_del:
            del st.session_state.acilacak_urunler[pazar_secimi][k]
          save_mappings({
              "manual_mappings": st.session_state.manual_mappings,
              "acilacak_urunler": st.session_state.acilacak_urunler,
          })
          st.success("Ürün listeden çıkarıldı!")
          st.rerun()
    else:
      st.info("İş planında açılacak olarak işaretlenen ürün bulunmuyor.")

    # --- TABLO 3: OTOMATİK EŞLEŞMEYENLER & MANUEL EŞLEŞTİRME ---
    st.subheader(
        "🔍 Otomatik Eşleşmeyenler & Manuel Eşleştirme / İş Planına Ekleme"
    )
    if eslesmeyen_tablo:
      secenekler = ["-- Pazar Yerinden Eşleşen Ürünü Seç --", "🚧 İŞ PLANINA EKLE (Açılacak Ürün)"] + [
          f"{kolon_degeri_bul(r, ['ürün adı', 'title'])} (SKU: {kolon_degeri_bul(r, ['merchant sku', 'stok kodu', 'sku'])})"
          for r in pazar_rows
      ]

      for item in eslesmeyen_tablo[:30]:  # Performans için ilk 30 tanesini göster
        with st.expander(
            f"❌ {item['Ürün']} (Kod: {item['Kod'] or '-'} | Barkod:"
            f" {item['Barkod'] or '-'})"
        ):
          secim = st.selectbox(
              "Bu ürünü pazaryerinde hangi ürünle eşleştirmek istersin?",
              secenekler,
              key=f"sel_{item['Key']}",
          )
          if st.button("Kaydet ve Hafızaya Ekle", key=f"btn_{item['Key']}"):
            if "İŞ PLANINA EKLE" in secim:
              st.session_state.acilacak_urunler[pazar_secimi][
                  item["Key"]
              ] = True
              if item["Key"] in st.session_state.manual_mappings[pazar_secimi]:
                del st.session_state.manual_mappings[pazar_secimi][item["Key"]]
              st.success("Ürün iş planına açılacak olarak eklendi! 🚧")
            elif "--" not in secim:
              p_index = secenekler.index(secim) - 2
              st.session_state.manual_mappings[pazar_secimi][
                  item["Key"]
              ] = p_index
              if item["Key"] in st.session_state.acilacak_urunler[pazar_secimi]:
                del st.session_state.acilacak_urunler[pazar_secimi][item["Key"]]
              st.success("Eşleşme başarıyla kaydedildi! ☁️")

            save_mappings({
                "manual_mappings": st.session_state.manual_mappings,
                "acilacak_urunler": st.session_state.acilacak_urunler,
            })
            st.rerun()
    else:
      st.success("Harika! Eşleşmeyen bekleyen ürün kalmadı.")
