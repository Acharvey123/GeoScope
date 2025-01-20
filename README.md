# GeoScope Project Setup

This README provides step-by-step instructions for setting up and running the GeoScope project.

## Prerequisites

Ensure you have the following installed on your machine:

- Python 3.10+
- Git

## Setup Instructions

### 1. Clone the Repository

Clone the GeoScope repository to your local machine:

```bash
git clone https://github.com/your-username/GeoScope.git
cd GeoScope
```

### 2. Set Up a Virtual Environment

Create and activate a virtual environment to manage dependencies:

```bash
python3 -m venv geoscope_env
source geoscope_env/bin/activate  # On Windows: geoscope_env\Scripts\activate
```

### 3. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

Ensure the `requirements.txt` file includes the following dependencies (add if missing):

```plaintext
streamlit
geemap
earthengine-api
folium
```

### 4. Set Up Google Earth Engine (GEE)

#### a. Install the Earth Engine CLI

Install the Earth Engine Command Line Interface (CLI):

```bash
pip install earthengine-api
```

#### b. Authenticate with GEE

Run the following command to authenticate your Google Earth Engine account:

```bash
earthengine authenticate
```

This will open a browser window prompting you to log in with your Google account and grant access. After completing the authentication, you will be given a verification code to paste back into your terminal.

### 5. Run the Streamlit App

Launch the Streamlit app by running:

```bash
streamlit run main.py
```

### 6. Usage

- Open the app in your web browser (the terminal will provide a local URL).
- Use the drawing tools to define your area of interest on the map.
- Select date range you need imagery for, and the sensor you want to search for.
- Click the "Search Available Imagery" button to retrieve and display satellite imagery for the selected area.
- Browse through available imagery and select "Load Image" to view on map.
- You can filter imagery by percent coverage of the AOI, as well as by capture date.
- If satisfied, you can export the image to your Google Drive with the "Export" button. This may take a few minutes to show up in your drive, especially for large images.
- To restart your search, you can click the "New Search" button.

### 7. Deactivate the Virtual Environment

Once you are done, deactivate the virtual environment:

```bash
deactivate
```

## Additional Notes

- Ensure your `main.py` file contains the necessary logic for fetching and displaying Earth Engine data.
- If you encounter any issues, verify that all dependencies are correctly installed and that you are authenticated with Google Earth Engine.
- This app is still very much a WIP, so dont be surprised if you encounter any bugs.

## TODO

- Fix map zoom issues when loading layers / toggeling basemap (currently when adding a layer or selecting basemap the map zooms to default location, will fix to zoom to active layer)
- Add support to toggle loaded imagery on and off
- Add image processing options so you can view different indices (NDVI, NDWI etc.)
- General UI improvements
