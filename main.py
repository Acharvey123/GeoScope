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
st.sidebar.write("Draw a rectangle on the map to define your area of interest.")

# Display the map and capture the drawn data
output = st_folium(folium_map, width=700, height=500, key="map")

# Date range selector
st.sidebar.title("Date Range")
start_date = st.sidebar.date_input("Start Date", value=None, key="start_date")
end_date = st.sidebar.date_input("End Date", value=None, key="end_date")

# Available imagery list
available_imagery = []

if st.button("Search Available Imagery"):
    try:
        if "all_drawings" in output and output["all_drawings"]:
            # Extract the rectangle GeoJSON
            drawn_geojson = output["all_drawings"][-1]
            coords = drawn_geojson["geometry"]["coordinates"][0]
            min_lon, min_lat = coords[0]
            max_lon, max_lat = coords[2]

            # Define the AOI
            aoi_geom = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])

            # Fetch available Sentinel-2 imagery within the date range
            if start_date and end_date:
                image_collection = ee.ImageCollection("COPERNICUS/S2") \
                    .filterBounds(aoi_geom) \
                    .filterDate(str(start_date), str(end_date))
                
                # Get list of available image IDs and dates
                available_imagery = image_collection.toList(image_collection.size()).getInfo()
                image_list = [
                    {"id": img["id"], "date": img["properties"]["system:time_start"]}
                    for img in available_imagery
                ]
                
                # Convert timestamp to human-readable dates
                for img in image_list:
                    img["date"] = time.strftime('%Y-%m-%d', time.gmtime(img["date"] / 1000))
                
                # Display available imagery
                st.session_state["imagery_options"] = image_list
            else:
                st.error("Please select a valid date range.")
        else:
            st.error("No area of interest drawn. Please draw a rectangle on the map.")
    except Exception as e:
        st.error(f"Error fetching imagery: {e}")

# Display the available imagery as a selectable list
if "imagery_options" in st.session_state:
    imagery_options = st.session_state["imagery_options"]
    if imagery_options:
        st.sidebar.write("Select imagery to load on the map:")
        selected_imagery = st.sidebar.radio(
            "Available Imagery",
            options=[f"{img['id']} ({img['date']})" for img in imagery_options]
        )
        
        if st.sidebar.button("Load Selected Imagery"):
            try:
                # Load the selected imagery
                selected_id = selected_imagery.split(" (")[0]
                selected_image = ee.Image(selected_id)

                # Visualization parameters
                vis_params = {
                    "bands": ["B4", "B3", "B2"],
                    "min": 0,
                    "max": 3000,
                    "gamma": 1.4,
                }

                # Add the selected imagery to the map
                def add_ee_layer(self, ee_object, vis_params, name):
                    map_id_dict = ee.Image(ee_object).getMapId(vis_params)
                    folium.raster_layers.TileLayer(
                        tiles=map_id_dict["tile_fetcher"].url_format,
                        attr="Map Data © Google Earth Engine",
                        name=name,
                        overlay=True,
                        control=True,
                    ).add_to(self)

                folium.Map.add_ee_layer = add_ee_layer
                folium_map.add_ee_layer(selected_image, vis_params, "Selected Sentinel-2 Imagery")

                # Update session state with the updated map
                st.session_state["folium_map"] = folium_map
                st.success("Imagery loaded successfully!")
            except Exception as e:
                st.error(f"Error loading selected imagery: {e}")
    else:
        st.sidebar.write("No imagery found for the selected date range.")
else:
    st.sidebar.write("Search for available imagery to see options.")

# Display the map again to persist the updates
st_folium(st.session_state["folium_map"], width=700, height=500, key="updated_map")