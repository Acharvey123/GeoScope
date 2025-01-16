import streamlit as st
import folium
from streamlit_folium import st_folium
import geemap
import ee
import json
import time

# Initialize Earth Engine
ee.Initialize()

# Create a folium Map object
if "folium_map" not in st.session_state:
    st.session_state["folium_map"] = folium.Map(location=[37.5, -94.5], zoom_start=6)

folium_map = st.session_state["folium_map"]

# Add the ESRI Imagery basemap using a folium TileLayer (if not added)
if "esri_layer_added" not in st.session_state:
    esri_tile_layer = folium.TileLayer(
        tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        attr="Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
        name="ESRI Imagery",
        overlay=True,
        control=True,
    )
    esri_tile_layer.add_to(folium_map)
    st.session_state["esri_layer_added"] = True

# Add the Draw control to the folium map (rectangle only)
if "draw_control_added" not in st.session_state:
    from folium.plugins import Draw

    draw_control = Draw(
        draw_options={"rectangle": True, "polygon": False, "circle": False, "marker": False}
    )
    draw_control.add_to(folium_map)
    st.session_state["draw_control_added"] = True

# Sidebar for instructions
st.sidebar.title("Instructions")
st.sidebar.write("Draw a rectangle on the map to define your area of interest and click 'Fetch Imagery'.")

# Display the map and capture the drawn data
output = st_folium(folium_map, width=700, height=500, key="map")

# Button to process the geometry and fetch imagery
if st.button("Fetch Imagery"):
    try:
        if "all_drawings" in output and output["all_drawings"]:
            st.info("Processing the selected area...")
            progress = st.progress(0)

            # Simulate a progress bar for user feedback
            for i in range(1, 11):
                time.sleep(0.3)  # Simulates processing time
                progress.progress(i * 10)

            # Extract the rectangle GeoJSON
            drawn_geojson = output["all_drawings"][-1]
            coords = drawn_geojson["geometry"]["coordinates"][0]
            min_lon, min_lat = coords[0]
            max_lon, max_lat = coords[2]

            # Define the AOI
            aoi_geom = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

            # Fetch Sentinel-2 imagery
            image = ee.ImageCollection("COPERNICUS/S2") \
                .filterBounds(aoi_geom) \
                .filterDate("2022-01-01", "2022-12-31") \
                .median()

            # Visualization parameters
            vis_params = {
                "bands": ["B4", "B3", "B2"],
                "min": 0,
                "max": 3000,
                "gamma": 1.4,
            }

            # Add Earth Engine layers
            def add_ee_layer(self, ee_object, vis_params, name):
                map_id_dict = ee.Image(ee_object).getMapId(vis_params)
                folium.raster_layers.TileLayer(
                    tiles=map_id_dict["tile_fetcher"].url_format,
                    attr="Map Data © Google Earth Engine",
                    name=name,
                    overlay=True,
                    control=True,
                ).add_to(self)

            # Add the Earth Engine layer to the folium map
            folium.Map.add_ee_layer = add_ee_layer
            folium_map.add_ee_layer(image, vis_params, "Sentinel-2 Imagery")

            # Update session state with the updated map
            st.session_state["folium_map"] = folium_map
            st.success("Imagery fetched successfully!")
        else:
            st.error("No area of interest drawn. Please draw a rectangle on the map.")
    except Exception as e:
        st.error(f"Error processing GeoJSON: {e}")

# Display the map again to persist the updates
st_folium(st.session_state["folium_map"], width=700, height=500, key="updated_map")