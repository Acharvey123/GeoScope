import streamlit as st
import folium
from streamlit_folium import st_folium
import geemap
import ee
import time
from PIL import Image
from io import BytesIO
import requests

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
        attr="Tiles &copy; Esri &mdash; Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community",
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

# New Search Feature
if st.sidebar.button("New Search"):
    # Reset session state
    st.session_state.clear()
    st.session_state["folium_map"] = folium.Map(location=[37.5, -94.5], zoom_start=6)
    st.experimental_rerun()

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
                st.session_state["current_page"] = 1
                st.session_state["sensor_config"] = config
                st.success("Imagery search complete!")
        else:
            st.error("No area of interest drawn. Please draw a rectangle on the map.")
    except Exception as e:
        st.error(f"Error fetching imagery: {e}")

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
                        folium_map.add_ee_layer(image, config["vis_params"], f"Imagery {img['id']}")
                        st.session_state["loaded_layers"].add(img["id"])

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
                    st.success(f"Export task for {img['id']} started! Check your Google Drive.")
                except Exception as e:
                    st.error(f"Error starting export: {e}")
