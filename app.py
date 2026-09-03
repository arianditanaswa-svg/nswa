import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Konfigurasi Halaman
st.set_page_config(page_title="SUB-KED | Monitoring KEDELAI", layout="wide")

st.title("🌱 Monitoring & Provitas Kedelai (SUB-KED)")
st.caption("Transparansi progres capaian 6 Tahun Kedelai Setiap Kabupaten secara Real-time")

# Koordinat Pusat Provinsi di Indonesia (Untuk Pemetaan Peta Otomatis)
# Koordinat Pusat Provinsi di Indonesia (Termasuk Provinsi Baru)
PROVINCE_COORDS = {
    'Aceh': {'lat': 4.6951, 'lon': 96.7494},
    'Sumatera Utara': {'lat': 2.1154, 'lon': 99.5451},
    'Sumatera Barat': {'lat': -0.7399, 'lon': 100.8000},
    'Riau': {'lat': 0.5071, 'lon': 101.4478},
    'Jambi': {'lat': -1.4852, 'lon': 103.6169},
    'Sumatera Selatan': {'lat': -3.3199, 'lon': 104.9147},
    'Bengkulu': {'lat': -3.8004, 'lon': 102.2655},
    'Lampung': {'lat': -4.5586, 'lon': 105.4068},
    'Kepulauan Bangka Belitung': {'lat': -2.7411, 'lon': 106.4406},
    'Kepulauan Riau': {'lat': 3.9456, 'lon': 108.1428},
    'DKI Jakarta': {'lat': -6.2088, 'lon': 106.8456},
    'Jawa Barat': {'lat': -6.9175, 'lon': 107.6191},
    'Jawa Tengah': {'lat': -7.1509, 'lon': 110.1403},
    'DI Yogyakarta': {'lat': -7.7956, 'lon': 110.3695},
    'Jawa Timur': {'lat': -7.5360, 'lon': 112.2384},
    'Banten': {'lat': -6.4058, 'lon': 106.0640},
    'Bali': {'lat': -8.4095, 'lon': 115.1889},
    'Nusa Tenggara Barat': {'lat': -8.6529, 'lon': 117.3616},
    'Nusa Tenggara Timur': {'lat': -8.6573, 'lon': 121.0794},
    'Kalimantan Barat': {'lat': -0.2787, 'lon': 111.4753},
    'Kalimantan Tengah': {'lat': -1.6815, 'lon': 113.3824},
    'Kalimantan Selatan': {'lat': -3.0926, 'lon': 115.2838},
    'Kalimantan Timur': {'lat': 0.5387, 'lon': 116.4194},
    'Kalimantan Utara': {'lat': 2.8953, 'lon': 116.4891},
    'Sulawesi Utara': {'lat': 0.6246, 'lon': 123.9750},
    'Sulawesi Tengah': {'lat': -1.4300, 'lon': 121.4456},
    'Sulawesi Selatan': {'lat': -3.6687, 'lon': 119.9740},
    'Sulawesi Tenggara': {'lat': -4.1449, 'lon': 122.1746},
    'Gorontalo': {'lat': 0.6999, 'lon': 122.4467},
    'Sulawesi Barat': {'lat': -2.8441, 'lon': 119.2321},
    'Maluku': {'lat': -3.2385, 'lon': 130.1453},
    'Maluku Utara': {'lat': 1.5709, 'lon': 127.8087},
    'Papua Barat': {'lat': -1.3361, 'lon': 133.1747},
    'Papua Barat Daya': {'lat': -1.1500, 'lon': 131.2500},
    'Papua': {'lat': -2.5000, 'lon': 140.7000},
    'Papua Tengah': {'lat': -3.5500, 'lon': 135.5000},
    'Papua Pegunungan': {'lat': -4.1000, 'lon': 138.9500},
    'Papua Selatan': {'lat': -7.5000, 'lon': 139.0000}
}

# 2. Fungsi Mengambil & Clean Data dari Google Sheets
@st.cache_data(ttl=60)
def load_data():
    gsheet_csv_url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vR5jNm9uTcmhlGW8n6UaDyoP7xAIHwvWwR_qkOF2tGo3uu2Invv8QsaJuHDwJtEeFiostLmB7wpeQgC/pub?gid=1963553011&single=true&output=csv"
    df = pd.read_csv(gsheet_csv_url)
    
    # 1. Ubah kolom teks agar tidak error jika ada sel kosong
    string_cols = ['PROVINSI', 'KABUPATEN/KOTA', 'BULAN']
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].fillna('-').astype(str)
    
    # 2. Cleaning data angka
    numeric_cols = ['LUAS TANAM (Ha)', 'LUAS PANEN (Ha)', 'PRODUKSI (Ton)']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace('-', '0').str.replace(',', ''), errors='coerce').fillna(0)
            
    return df

# Memuat Data
try:
    df = load_data()
except Exception:
    # Data Contoh (Dummy) Jika Link Belum Dimasukkan
    data = {
        'TAHUN': [2020, 2020, 2021, 2021, 2022],
        'BULAN': ['Januari', 'Agustus', 'Januari', 'Februari', 'Maret'],
        'PROVINSI': ['Aceh', 'Aceh', 'Jawa Barat', 'Jawa Tengah', 'Jawa Timur'],
        'KABUPATEN/KOTA': ['Kabupaten Aceh Selatan', 'Kabupaten Aceh Tenggara', 'Kabupaten Bandung', 'Kabupaten Grobogan', 'Kabupaten Pasuruan'],
        'LUAS TANAM (Ha)': [100, 250, 500, 800, 650],
        'LUAS PANEN (Ha)': [90, 240, 480, 780, 630],
        'PRODUKSI (Ton)': [135, 360, 720, 1170, 945]
    }
    df = pd.DataFrame(data)

# 3. Sidebar Filter
st.sidebar.header("🔍 Filter Data")

list_tahun = ["Semua TAHUN"] + sorted(list(df['TAHUN'].dropna().unique()))
tahun_selected = st.sidebar.selectbox("Pilih Tahun", list_tahun)

list_prov = ["Semua Provinsi"] + sorted(list(df['PROVINSI'].dropna().unique()))
prov_selected = st.sidebar.selectbox("Pilih Provinsi", list_prov)

filtered_df = df.copy()
if tahun_selected != "Semua TAHUN":
    filtered_df = filtered_df[filtered_df['TAHUN'] == tahun_selected]
if prov_selected != "Semua Provinsi":
    filtered_df = filtered_df[filtered_df['PROVINSI'] == prov_selected]

list_kab = ["Semua Kabupaten/Kota"] + sorted(list(filtered_df['KABUPATEN/KOTA'].dropna().unique()))
kab_selected = st.sidebar.selectbox("Pilih Kabupaten/Kota", list_kab)

if kab_selected != "Semua Kabupaten/Kota":
    filtered_df = filtered_df[filtered_df['KABUPATEN/KOTA'] == kab_selected]

# 4. Perhitungan Total KPI
tot_tanam = filtered_df['LUAS TANAM (Ha)'].sum()
tot_panen = filtered_df['LUAS PANEN (Ha)'].sum()
tot_produksi = filtered_df['PRODUKSI (Ton)'].sum()
provitas = (tot_produksi * 10 / tot_panen) if tot_panen > 0 else 0

# Display KPI Cards (dibuat 2x2 agar angka besar tidak terpotong)
col1, col2 = st.columns(2)
col1.metric("🌾 Total Luas Tanam", f"{tot_tanam:,.2f} Ha")
col2.metric("🚜 Total Luas Panen", f"{tot_panen:,.2f} Ha")

col3, col4 = st.columns(2)
col3.metric("📦 Total Produksi", f"{tot_produksi:,.2f} Ton")
col4.metric("📊 Rata-rata Provitas", f"{provitas:,.2f} Ku/Ha")
st.markdown("---")

# 5. PETA PERSEBARAN REALISASI & PRODUKTIVITAS
st.subheader("🗺️ Peta Persebaran Realisasi & Provitas Kedelai")

# Menyiapkan Data Ringkasan untuk Peta
map_data = filtered_df.groupby(['PROVINSI', 'KABUPATEN/KOTA'], as_index=False).agg({
    'LUAS TANAM (Ha)': 'sum',
    'LUAS PANEN (Ha)': 'sum',
    'PRODUKSI (Ton)': 'sum'
})

# Hitung Provitas per Kabupaten/Kota
map_data['PROVITAS (Ku/Ha)'] = (map_data['PRODUKSI (Ton)'] * 10 / map_data['LUAS PANEN (Ha)']).fillna(0)

# Petakan Koordinat LAT & LON dari PROVINCE_COORDS
map_data['LAT'] = map_data['PROVINSI'].map(lambda x: PROVINCE_COORDS.get(x, {}).get('lat', None))
map_data['LON'] = map_data['PROVINSI'].map(lambda x: PROVINCE_COORDS.get(x, {}).get('lon', None))

# Hapus baris yang tidak memiliki koordinat
map_data = map_data.dropna(subset=['LAT', 'LON'])

if not map_data.empty:
    # -------------------------------------------------------------
    # DINAMIS: Hitung Titik Tengah & Level Zoom Sesuai Filter
    # -------------------------------------------------------------
    avg_lat = map_data['LAT'].mean()
    avg_lon = map_data['LON'].mean()
    
    # Jika memilih spesifik provinsi, buat zoom lebih dekat (6.5), jika semua provinsi zoom jauh (3.8)
    zoom_level = 6.5 if prov_selected != "Semua Provinsi" else 3.8

    fig_map = px.scatter_map(
        map_data,
        lat="LAT",
        lon="LON",
        size="LUAS TANAM (Ha)",
        color="PROVITAS (Ku/Ha)",
        color_continuous_scale="Viridis",
        hover_name="KABUPATEN/KOTA",
        hover_data={
            "PROVINSI": True,
            "LUAS TANAM (Ha)": ":,.2f",
            "LUAS PANEN (Ha)": ":,.2f",
            "PRODUKSI (Ton)": ":,.2f",
            "PROVITAS (Ku/Ha)": ":,.2f",
            "LAT": False,
            "LON": False
        },
        center={"lat": avg_lat, "lon": avg_lon},  # <-- MEMINDAHKAN FOKUS PETA OTOMATIS
        zoom=zoom_level,                          # <-- ZOOM DINAMIS
        height=500,
        map_style="open-street-map"
    )
    
    st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("Tidak ada data lokasi yang dapat ditampilkan untuk kombinasi filter ini.")
    
# 6. Grafik Bar Provitas Per Kabupaten
st.subheader("📈 Grafis Produktivitas (Ku/Ha) Per Kabupaten/Kota")
if not map_data.empty:
    fig_bar = px.bar(
        map_data, 
        x='KABUPATEN/KOTA', 
        y='PROVITAS (Ku/Ha)', 
        color='PROVINSI',
        title="Tingkat Produktivitas (Ku/Ha) Tiap Kabupaten",
        labels={'PROVITAS (Ku/Ha)': 'Provitas (Ku/Ha)', 'KABUPATEN/KOTA': 'Kabupaten/Kota'},
        text_auto='.2f'
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# 7. Tabel Rincian Data Detail
st.subheader("📋 Rincian Data Detail")
st.dataframe(filtered_df, use_container_width=True)