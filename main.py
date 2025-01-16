import geemap
import streamlit as st
import ee
import folium
from folium.plugins import Draw

# Initialize Earth Engine
ee.Initialize()

# Create a folium Map object
folium_map = folium.Map(location=[37.5, -94.5], zoom_start=6)

# Add the ESRI Imagery basemap using a folium TileLayer
esri_tile_layer = folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
    name="ESRI Imagery",
    overlay=True,
    control=True
)
esri_tile_layer.add_to(folium_map)

# Add the Draw control to the folium map
draw_control = Draw()
draw_control.add_to(folium_map)

# Sidebar for instructions
st.sidebar.title("Instructions")
st.sidebar.write("Draw a rectangle on the map to define your area of interest and click 'Fetch Imagery'.")

# Display the map with drawing control
map_html = folium_map._repr_html_()
st.components.v1.html(map_html, height=600)

# Button to trigger the fetching of imagery after drawing the rectangle
if st.button('Fetch Imagery'):
    # Normally, you would extract coordinates from the drawing here
    # In this case, we'll hardcode some coordinates to simulate a user draw

    # Example coordinates for the drawn area (replace these with the actual coordinates from JavaScript)
    min_lat, min_lon = 37.0, -95.0  # Bottom-left corner of the rectangle
    max_lat, max_lon = 38.0, -94.0  # Top-right corner of the rectangle

    # Create an Earth Engine geometry object from the bounding box
    aoi_geom = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

    # Fetch Sentinel-2 imagery from Earth Engine for the selected area
    image = ee.ImageCollection('COPERNICUS/S2') \
            .filterBounds(aoi_geom) \
            .filterDate('2022-01-01', '2022-12-31') \
            .median()  # Taking the median image for the year

    # Set visualization parameters
    vis_params = {
        'bands': ['B4', 'B3', 'B2'],  # Red, Green, Blue bands for true color
        'min': 0, 'max': 3000,
        'gamma': 1.4
    }
    
    # Function to add Earth Engine layers to the map
    def add_ee_layer(self, ee_object, vis_params, name):
        map_id_dict = ee.Image(ee_object).getMapId(vis_params)
        folium.raster_layers.TileLayer(
            tiles=map_id_dict['tile_fetcher'].url_format,
            attr='Map Data © Google Earth Engine',
            name=name,
            overlay=True,
            control=True
        ).add_to(self)

    # Add the custom method to the folium map
    folium.Map.add_ee_layer = add_ee_layer

    # Add the satellite image to the folium map
    folium_map.add_ee_layer(image, vis_params, 'Sentinel-2 Imagery')

    # Display the map again with the added imagery
    map_html = folium_map._repr_html_()
    st.components.v1.html(map_html, height=600)
    
    # Optionally, you could display a message or additional info about the imagery
    st.write("Satellite imagery fetched for the selected area of interest.")