import streamlit as st
import geemap
import folium
from streamlit_folium import st_folium

# Create a folium map centered on the USA
Map = geemap.folium.Map(location=[37.0902, -95.7129], zoom_start=4)

# Add OpenStreetMap basemap using TileLayer
folium.TileLayer("OpenStreetMap").add_to(Map)

# Render the map in Streamlit
st_folium(Map, width=700)