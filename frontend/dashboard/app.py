from __future__ import annotations

from datetime import datetime
from pathlib import Path
import sys

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

ROOT = Path(__file__).resolve().parents[2]
sys.path.append(str(ROOT))

from src.config import PROCESSED_DIR
from src.utils import read_table
from src.simulator.transfer_simulator import simulate_transfer, simulate_all_transfer_nodes
from src.incident.incident_report import active_incidents, report_incident

st.set_page_config(page_title='Intermodal AI Dashboard', layout='wide')
st.title('Intermodal AI System - DKI Jakarta')
st.caption('Prototype optimasi waiting time, transfer antarmoda, kepadatan, dan incident-aware ETA.')


def load_df(name: str) -> pd.DataFrame:
    path = PROCESSED_DIR / name
    if not path.exists():
        return pd.DataFrame()
    return read_table(path)

st.sidebar.header('Simulasi Transfer')
current_time = st.sidebar.text_input('Current time', '2026-05-23T07:20:00')
from_stop_id = st.sidebar.selectbox('Dari halte/stasiun', ['TJ_DUKUH_ATAS', 'TJ_SENAYAN', 'TJ_CAWANG'])
to_stop_id_options = {
    'TJ_DUKUH_ATAS': ['MRT_DUKUH_ATAS', 'KRL_SUDIRMAN'],
    'TJ_SENAYAN': ['MRT_SENAYAN'],
    'TJ_CAWANG': ['KRL_CAWANG'],
}
to_stop_id = st.sidebar.selectbox('Ke halte/stasiun', to_stop_id_options.get(from_stop_id, ['MRT_DUKUH_ATAS']))
first_eta = st.sidebar.slider('ETA moda pertama ke titik turun (menit)', 0, 30, 5)
load_factor = st.sidebar.slider('Load factor moda saat ini', 0.0, 1.2, 0.7, 0.05)

col1, col2, col3, col4 = st.columns(4)

try:
    result = simulate_transfer(from_stop_id, to_stop_id, current_time, first_eta, load_factor=load_factor)
    decision = result.get('decision', {})
    col1.metric('Walking time', f"{result.get('walking_time_minutes', 0):.0f} menit")
    col2.metric('Waiting time', f"{decision.get('waiting_time_minutes', 0) or 0} menit")
    col3.metric('Keputusan', decision.get('decision', '-'))
    col4.metric('Density asal', result.get('origin_density', {}).get('density_level', '-'))
    st.success(decision.get('message', 'Tidak ada pesan'))
    with st.expander('Lihat detail JSON'):
        st.json(result)
except Exception as exc:
    st.error(f'Gagal menjalankan simulasi: {exc}')

st.divider()
left, right = st.columns([1.4, 1])

with left:
    st.subheader('Peta halte/stasiun dan insiden')
    stops = load_df('stops.parquet')
    incidents = load_df('incidents.parquet')
    layers = []
    if not stops.empty:
        layers.append(pdk.Layer(
            'ScatterplotLayer',
            stops,
            get_position='[lon, lat]',
            get_radius=120,
            get_fill_color='[30, 120, 200, 170]',
            pickable=True,
        ))
    if not incidents.empty:
        active = incidents[incidents['status'].isin(['active', 'monitoring'])]
        if not active.empty:
            layers.append(pdk.Layer(
                'ScatterplotLayer',
                active,
                get_position='[lon, lat]',
                get_radius=180,
                get_fill_color='[220, 50, 50, 190]',
                pickable=True,
            ))
    st.pydeck_chart(pdk.Deck(
        map_style=None,
        initial_view_state=pdk.ViewState(latitude=-6.22, longitude=106.82, zoom=11, pitch=0),
        layers=layers,
        tooltip={'text': '{stop_name}\n{type}\n{severity}'},
    ))

with right:
    st.subheader('Simulasi semua transfer node')
    try:
        sim_all = simulate_all_transfer_nodes(current_time)
        st.dataframe(sim_all, use_container_width=True)
        if 'decision' in sim_all.columns:
            fig = px.histogram(sim_all, x='decision', title='Distribusi keputusan transfer')
            st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.warning(str(exc))

st.divider()
st.subheader('Lapor insiden oleh pengemudi/operator')
with st.form('incident_form'):
    c1, c2, c3 = st.columns(3)
    incident_type = c1.selectbox('Jenis insiden', ['traffic_jam', 'accident', 'flood', 'road_closure', 'other'])
    severity = c2.selectbox('Severity', ['low', 'medium', 'high'])
    route_id = c3.text_input('Route ID', 'TJ_1')
    c4, c5, c6 = st.columns(3)
    stop_id = c4.text_input('Stop ID', 'TJ_SENAYAN')
    lat = c5.number_input('Latitude', value=-6.225, format='%.6f')
    lon = c6.number_input('Longitude', value=106.803, format='%.6f')
    delay = st.slider('Estimasi delay impact (menit)', 0, 30, 4)
    desc = st.text_area('Deskripsi', 'Kemacetan padat menjelang titik transit.')
    submitted = st.form_submit_button('Kirim laporan insiden')
    if submitted:
        incident = report_incident(incident_type, severity, route_id, stop_id, lat, lon, delay, desc)
        st.success(f"Insiden tersimpan: {incident['incident_id']}")

with st.expander('Insiden aktif'):
    st.json(active_incidents())
