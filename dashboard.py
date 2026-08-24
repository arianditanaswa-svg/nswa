import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import altair as alt
import gspread
from google.oauth2.service_account import Credentials
# -----------------------------------------------------------------------------
# KONFIGURASI HALAMAN
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Kedelai Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=60)

def get_data(nama_sheet):
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scope
    )

    client = gspread.authorize(credentials)

    spreadsheet = client.open("REKAP DATA PER BULAN")
    sheet = spreadsheet.worksheet(nama_sheet)

    data = sheet.get_all_records()

    return pd.DataFrame(data)

try:
    df = get_data("MASTER")

    kolom_numerik = [
        'Tahun',
        'Luas Tanam (Ha)',
        'Luas Panen (Ha)',
        'Produksi (Ton)',
        'Produktivitas (Ku/Ha)'
    ]

    for kolom in kolom_numerik:
        df[kolom] = pd.to_numeric(df[kolom], errors='coerce').fillna(0)

    st.toast(
        f"Data berhasil dimuat! "
        f"{len(df)} baris."
    )

except Exception as e:
    st.error(f"Gagal mengambil data: {e}")
    st.stop()


# -----------------------------------------------------------------------------
# SIDEBAR
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🌱 Kedelai Dashboard")

    tahun_list_unique = sorted(df['Tahun'].unique().tolist())[::-1]
    selected_tahun = st.selectbox("Select year/tahun", tahun_list_unique, index=0)

    provinsi_options = ['Semua Provinsi'] + sorted(df['Provinsi'].unique().tolist())
    selected_provinsi = st.selectbox("Select provinsi", provinsi_options)

# Filter data sesuai tahun terpilih
df_tahun = df[df['Tahun'] == selected_tahun]

# Rata-rata produktivitas per provinsi untuk tahun terpilih
df_prov_avg = (
    df_tahun.groupby('Provinsi', as_index=False)['Produktivitas (Ku/Ha)']
    .mean()
    .sort_values('Produktivitas (Ku/Ha)', ascending=False)
)

national_avg = df_prov_avg['Produktivitas (Ku/Ha)'].mean()
above_avg_pct = round((df_prov_avg['Produktivitas (Ku/Ha)'] > national_avg).mean() * 100)
below_avg_pct = 100 - above_avg_pct

prov_tertinggi = df_prov_avg.iloc[0]
prov_terendah = df_prov_avg.iloc[-1]

# -----------------------------------------------------------------------------
# MAIN LAYOUT (3 Kolom)
# -----------------------------------------------------------------------------
col1, col2, col3 = st.columns([1.5, 3, 1.8], gap="medium")

# -----------------------------------------------------------------------------
# KOLOM 1: Produktivitas Tertinggi & Terendah + Capaian Persentase
# -----------------------------------------------------------------------------
with col1:
    
    st.markdown("### Produktivitas Tertinggi dan Terendah")

    st.metric(
        label=prov_tertinggi['Provinsi'],
        value=f"{prov_tertinggi['Produktivitas (Ku/Ha)']:.0f} Ku/Ha",
        delta="Tertinggi"
    )
    st.metric(
        label=prov_terendah['Provinsi'],
        value=f"{prov_terendah['Produktivitas (Ku/Ha)']:.0f} Ku/Ha",
        delta="Terendah",
        delta_color="inverse"
    )

    st.markdown("---")
    st.markdown("### Capaian Produktivitas dalam Persentase")

    fig_above = px.pie(values=[above_avg_pct, 100 - above_avg_pct], names=['Di atas rata-rata', 'Sisanya'],
                        hole=0.7, color_discrete_sequence=['#00CC96', '#222222'])
    fig_above.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=140)
    fig_above.add_annotation(text=f"{above_avg_pct} %", showarrow=False, font_size=20, font_color="white")

    st.caption("Di Atas Rata-rata Nasional")
    st.plotly_chart(fig_above, use_container_width=True)

    fig_below = px.pie(values=[below_avg_pct, 100 - below_avg_pct], names=['Di bawah rata-rata', 'Sisanya'],
                        hole=0.7, color_discrete_sequence=['#EF553B', '#222222'])
    fig_below.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10), height=140)
    fig_below.add_annotation(text=f"{below_avg_pct} %", showarrow=False, font_size=20, font_color="white")

    st.caption("Di Bawah Rata-rata Nasional")
    st.plotly_chart(fig_below, use_container_width=True)

# -----------------------------------------------------------------------------
# KOLOM 2: Persebaran Produktivitas & Grafik Produktivitas
# -----------------------------------------------------------------------------
with col2:
    st.markdown("### Persebaran Produktivitas")

    fig_treemap = px.treemap(
        df_prov_avg,
        path=['Provinsi'],
        values='Produktivitas (Ku/Ha)',
        color='Produktivitas (Ku/Ha)',
        color_continuous_scale='Greens'
    )
    fig_treemap.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=320)
    st.plotly_chart(fig_treemap, use_container_width=True)

    st.markdown("### Grafik Produktivitas")

    if selected_provinsi == 'Semua Provinsi':
        top5 = df_prov_avg.head(5)['Provinsi'].tolist()
        df_trend = df[df['Provinsi'].isin(top5)]
    else:
        df_trend = df[df['Provinsi'] == selected_provinsi]

    df_trend_year = (
        df_trend.groupby(['Tahun', 'Provinsi'], as_index=False)['Produktivitas (Ku/Ha)']
        .mean()
    )

    line_chart = alt.Chart(df_trend_year).mark_line(point=True).encode(
        x=alt.X('Tahun:O', title='Tahun'),
        y=alt.Y('Produktivitas (Ku/Ha):Q', title='Produktivitas (Ku/Ha)'),
        color=alt.Color('Provinsi:N', legend=alt.Legend(title="Provinsi")),
        tooltip=['Tahun', 'Provinsi', 'Produktivitas (Ku/Ha)']
    ).properties(height=220)

    st.altair_chart(line_chart, use_container_width=True)

# -----------------------------------------------------------------------------
# KOLOM 3: Ranking Provinsi & About
# -----------------------------------------------------------------------------
with col3:
    st.markdown("### Ranking Provinsi")

    st.dataframe(
        df_prov_avg.rename(columns={'Produktivitas (Ku/Ha)': 'Produktivitas'}),
        column_config={
            "Provinsi": "Provinsi",
            "Produktivitas": st.column_config.ProgressColumn(
                "Produktivitas (Ku/Ha)",
                format="%.0f",
                min_value=0,
                max_value=float(df_prov_avg['Produktivitas (Ku/Ha)'].max()) * 1.1,
            ),
        },
        hide_index=True,
        use_container_width=True,
        height=460
    )

    with st.expander("About", expanded=True):
        st.markdown("""
        * **Data:** Data mengikuti format spreadsheet produksi kedelai
        * **Produktivitas Tertinggi/Terendah:** Provinsi dengan rata-rata produktivitas tertinggi & terendah pada tahun terpilih
        * **Capaian Persentase:** Persentase provinsi yang berada di atas/bawah rata-rata nasional
        * **Persebaran Produktivitas:** Treemap menunjukkan proporsi produktivitas tiap provinsi
        * **Grafik Produktivitas:** Tren produktivitas per tahun untuk provinsi terpilih (atau top 5 jika "Semua Provinsi")
        """)
