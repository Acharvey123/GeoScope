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
- Click the "Fetch Imagery" button to retrieve and display satellite imagery for the selected area.

### 7. Deactivate the Virtual Environment

Once you are done, deactivate the virtual environment:

```bash
deactivate
```

## Additional Notes

- Ensure your `main.py` file contains the necessary logic for fetching and displaying Earth Engine data.
- If you encounter any issues, verify that all dependencies are correctly installed and that you are authenticated with Google Earth Engine.

