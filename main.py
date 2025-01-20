import streamlit as st
import folium
from streamlit_folium import st_folium
import geemap
import ee
import time
from PIL import Image
from io import BytesIO
import requests
from folium.plugins import Draw
from image_filter import sort_by_date, sort_by_coverage

# Initialize session state variables
if "sensor_config" not in st.session_state:
    st.session_state["sensor_config"] = None
if "aoi_geom" not in st.session_state:
    st.session_state["aoi_geom"] = None
if "imagery_options" not in st.session_state:
    st.session_state["imagery_options"] = []
if "loaded_layers" not in st.session_state:
    st.session_state["loaded_layers"] = set()
if "current_page" not in st.session_state:
    st.session_state["current_page"] = 1  # Default to the first page

# Initialize Earth Engine
ee.Initialize()

from folium.plugins import Draw

# Initialize map in session state
if "folium_map" not in st.session_state:
    st.session_state["folium_map"] = folium.Map(location=[37.5, -94.5], zoom_start=6)

folium_map = st.session_state["folium_map"]

# Define base maps
base_maps = {
    "OpenStreetMap": "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    "ESRI Imagery": "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
}

# Add sidebar toggle for base maps
selected_base_map = st.sidebar.radio(
    "Select Base Map",
    options=list(base_maps.keys()),
    index=0,
)

# Update the map with the selected base map
if "current_base_map" not in st.session_state or st.session_state["current_base_map"] != selected_base_map:
    # Clear all layers and reset the map
    st.session_state["folium_map"] = folium.Map(location=[37.5, -94.5], zoom_start=6)

    # Add the selected base map
    folium.TileLayer(
        tiles=base_maps[selected_base_map],
        name=selected_base_map,
        attr=f"Tiles &copy; {selected_base_map}",
        overlay=False,
        control=False,
    ).add_to(st.session_state["folium_map"])

    # Add the Draw Control
    draw_control = Draw(
        draw_options={"rectangle": True, "polygon": False, "circle": False, "marker": False}
    )
    draw_control.add_to(st.session_state["folium_map"])

    # Save the current base map selection
    st.session_state["current_base_map"] = selected_base_map

folium_map = st.session_state["folium_map"]

# Sidebar for instructions
st.sidebar.title("Instructions")
st.sidebar.write("Draw a rectangle on the map to define your area of interest. Next choose date range and imagery type. When finished browse results and load or export!")

# Sidebar for currently loaded imagery
st.sidebar.title("Currently Loaded Imagery")

if "loaded_layers" in st.session_state and st.session_state["loaded_layers"]:
    for loaded_id in st.session_state["loaded_layers"]:
        with st.sidebar.expander(f"Imagery: {loaded_id}", expanded=True):
            st.write(f"ID: {loaded_id}")

            # Option to export imagery from this sidebar
            if st.button(f"Export {loaded_id}", key=f"sidebar_export_{loaded_id}"):
                try:
                    image = ee.Image(loaded_id)
                    config = st.session_state["sensor_config"]
                    aoi_geom = st.session_state["aoi_geom"]
                    
                    # Start export task
                    task = ee.batch.Export.image.toDrive(
                        image=image,
                        description=f"Export_{loaded_id.replace('/', '_')[:100]}",
                        folder="GeoScope",
                        fileNamePrefix=f"Image_{loaded_id.replace('/', '_')[:100]}",
                        scale=config["scale"],
                        region=aoi_geom.getInfo()["coordinates"],
                        maxPixels=1e13,
                    )
                    task.start()

                    st.sidebar.success(f"Export task for {loaded_id} started! Check your Google Drive.")
                except Exception as e:
                    st.sidebar.error(f"Error exporting {loaded_id}: {e}")
else:
    st.sidebar.info("No imagery currently loaded.")

# Display the map and capture the drawn data
output = st_folium(
    folium_map,
    width=850,  # Adjust width to fit your layout
    height=650,  # Increase height to accommodate the LayerControl widget
    key="map",
)

# Add sorting buttons below the map
col1, col2 = st.columns(2)  # Create two columns for the buttons
with col1:
    if st.button("Sort Imagery by Date"):
        available_imagery = st.session_state.get("imagery_options", [])
        if available_imagery:
            sorted_by_date = sort_by_date(available_imagery)
            st.session_state["imagery_options"] = sorted_by_date
            st.success("Imagery sorted by date (oldest to newest).")
        else:
            st.error("No imagery available to sort. Please search for imagery first.")

with col2:
    if st.button("Sort Imagery by Coverage"):
        if "aoi_geom" in st.session_state:
            aoi_geom = st.session_state["aoi_geom"]
            available_imagery = st.session_state.get("imagery_options", [])
            if available_imagery:
                sorted_by_coverage = sort_by_coverage(available_imagery, aoi_geom)
                st.session_state["imagery_options"] = sorted_by_coverage
                st.success("Imagery sorted by AOI coverage.")
            else:
                st.error("No imagery available to sort. Please search for imagery first.")
        else:
            st.error("Please draw an Area of Interest (AOI) first.")

# Sidebar for date range and sensor selection
st.sidebar.title("Date Range and Sensor Selection")
start_date = st.sidebar.date_input("Start Date", value=None, key="start_date")
end_date = st.sidebar.date_input("End Date", value=None, key="end_date")

sensor = st.sidebar.selectbox(
    "Choose a Sensor",
    ["Sentinel-2", "Landsat", "MODIS", "NAIP", "Sentinel-1"],
    index=0,
)

# Sensor-specific configurations
sensor_config = {
    "Sentinel-2": {
        "collection": "COPERNICUS/S2",
        "bands": ["B4", "B3", "B2"],
        "scale": 10,
        "vis_params": {"bands": ["B4", "B3", "B2"], "min": 0, "max": 3000, "gamma": 1.4},
    },
    "Landsat": {
        "collection": "LANDSAT/LC08/C02/T1_L2",
        "bands": ["SR_B4", "SR_B3", "SR_B2"],
        "scale": 30,
        "vis_params": {"bands": ["SR_B4", "SR_B3", "SR_B2"], "min": 0, "max": 3000, "gamma": 1.4},
    },
    "MODIS": {
        "collection": "MODIS/006/MOD13A2",
        "bands": ["NDVI"],
        "scale": 250,
        "vis_params": {"bands": ["NDVI"], "min": 0, "max": 8000, "palette": ["blue", "green", "red"]},
    },
    "NAIP": {
        "collection": "USDA/NAIP/DOQQ",
        "bands": ["R", "G", "B"],
        "scale": 1,
        "vis_params": {"bands": ["R", "G", "B"], "min": 0, "max": 255},
    },
    "Sentinel-1": {
        "collection": "COPERNICUS/S1",
        "bands": ["VV"],
        "scale": 10,
        "vis_params": {"bands": ["VV"], "min": -25, "max": 0},
    },
}

# Set sensor_config in session state
st.session_state["sensor_config"] = sensor_config[sensor]

# Search Available Imagery Button
if st.sidebar.button("Search Available Imagery"):
    try:
        if "all_drawings" in output and output["all_drawings"]:
            # Logic for searching imagery
            drawn_geojson = output["all_drawings"][-1]
            coords = drawn_geojson["geometry"]["coordinates"][0]
            min_lon, min_lat = coords[0]
            max_lon, max_lat = coords[2]

            # Define the AOI
            aoi_geom = ee.Geometry.Rectangle([min_lon, min_lat, max_lon, max_lat])
            st.session_state["aoi_geom"] = aoi_geom  # Save AOI for later use

            # Progress bar
            st.info("Searching for available imagery...")
            progress = st.progress(0)

            # Simulate progress
            for i in range(1, 6):
                time.sleep(0.2)  # Simulate delay
                progress.progress(i * 20)

            # Fetch imagery based on the selected sensor
            config = sensor_config[sensor]
            image_collection = ee.ImageCollection(config["collection"]) \
                .filterBounds(aoi_geom) \
                .filterDate(str(start_date), str(end_date)) \
                .select(config["bands"])

            # Check if the collection is empty
            collection_size = image_collection.size().getInfo()
            if collection_size == 0:
                st.warning("No imagery found for the selected AOI, date range, and sensor. Please try another combination.")
            else:
                # Get list of available image IDs and dates
                available_imagery = image_collection.toList(collection_size).getInfo()
                image_list = [
                    {"id": img["id"], "date": time.strftime('%Y-%m-%d', time.gmtime(img["properties"]["system:time_start"] / 1000))}
                    for img in available_imagery
                ]
                st.session_state["imagery_options"] = image_list
                st.success("Imagery search complete!")
        else:
            st.error("No area of interest drawn. Please draw a rectangle on the map.")
    except Exception as e:
        st.error(f"Error fetching imagery: {e}")

# New Search Feature
if st.sidebar.button("New Search"):
    # Reset session state
    st.session_state.clear()
    st.session_state["folium_map"] = folium.Map(location=[37.5, -94.5], zoom_start=6)
    st.rerun()

# Available imagery list
available_imagery = []

# Pagination controls and imagery preview
if "imagery_options" in st.session_state and "aoi_geom" in st.session_state:
    imagery_options = st.session_state["imagery_options"]
    aoi_geom = st.session_state["aoi_geom"]
    config = st.session_state["sensor_config"]
    page_size = 10
    total_pages = (len(imagery_options) - 1) // page_size + 1
    current_page = st.session_state["current_page"]

    # Pagination navigation
    col1, col2, col3 = st.columns([1, 2, 1])
    if current_page > 1:
        if col1.button("Previous"):
            st.session_state["current_page"] -= 1
    if current_page < total_pages:
        if col3.button("Next"):
            st.session_state["current_page"] += 1

    # Display imagery for the current page
    start_idx = (current_page - 1) * page_size
    end_idx = min(start_idx + page_size, len(imagery_options))
    current_imagery = imagery_options[start_idx:end_idx]

    for img in current_imagery:
        with st.container():
            col1, col2 = st.columns([1, 3])
            col1.write(f"ID: {img['id']}")
            col1.write(f"Date: {img['date']}")

            # Generate a thumbnail for the imagery
            image = ee.Image(img["id"])
            thumbnail_url = image.getThumbURL({
                "region": aoi_geom.getInfo(),
                "bands": config["bands"],
                "min": config["vis_params"].get("min"),
                "max": config["vis_params"].get("max"),
                "dimensions": "200x200",
            })

            # Fetch and display the thumbnail
            response = requests.get(thumbnail_url)
            if response.status_code == 200:
                thumbnail_response = BytesIO(response.content)
                thumbnail = Image.open(thumbnail_response)
                col2.image(thumbnail, caption="Preview")
            else:
                col2.error("Failed to load preview.")

            # Load imagery onto the map
            if st.button(f"Load {img['id']}", key=f"load_{img['id']}"):
                try:
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
                    if "loaded_layers" not in st.session_state:
                        st.session_state["loaded_layers"] = set()

                    if img["id"] not in st.session_state["loaded_layers"]:
                        # Add progress bar for imagery loading
                        with st.spinner("Loading imagery..."):
                            progress_bar = st.progress(0)
                            time.sleep(0.5)  # Simulating delay for loading
                            folium_map.add_ee_layer(image, config["vis_params"], f"Imagery {img['id']}")
                            for progress in range(1, 11):
                                progress_bar.progress(progress * 10)
                                time.sleep(0.1)  # Simulate progress
                        st.session_state["loaded_layers"].add(img["id"])

                    # Explicitly update the map session state
                    st.session_state["folium_map"] = folium_map
                    st.success(f"Imagery {img['id']} loaded onto the map!")
                except Exception as e:
                    st.error(f"Error loading imagery: {e}")




            # Export imagery
            if st.button(f"Export {img['id']}", key=f"export_{img['id']}"):
                try:
                    task = ee.batch.Export.image.toDrive(
                        image=image,
                        description=f"Export_{img['id'].replace('/', '_')[:100]}",
                        folder="GeoScope",
                        fileNamePrefix=f"Image_{img['id'].replace('/', '_')[:100]}",
                        scale=config["scale"],
                        region=aoi_geom.getInfo()["coordinates"],
                        maxPixels=1e13,
                    )
                    task.start()

                    # Add progress bar for export
                    st.info("Exporting imagery... this may take a while.")
                    progress_bar = st.progress(0)
                    for progress in range(1, 11):
                        progress_bar.progress(progress * 10)
                        time.sleep(1)  # Simulate export progress

                    st.success(f"Export task for {img['id']} started! Check your Google Drive.")
                except Exception as e:
                    st.error(f"Error starting export: {e}")

