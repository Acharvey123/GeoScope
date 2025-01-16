import geemap
import ipyleaflet
from ipywidgets import HTML

# Create an interactive map centered on the United States
Map = geemap.Map(center=[37.0902, -95.7129], zoom=4)

# Create a draw control
draw_control = ipyleaflet.DrawControl(
    rectangle={'shapeOptions': {'color': '#ff0000'}},
    edit=True,
    remove=True
)

# Define a function to handle the rectangle drawing
def handle_draw(event, action, geo_json):
    if action == 'created' and geo_json['geometry']['type'] == 'Polygon':
        bounds = geo_json['geometry']['coordinates'][0]
        print("Rectangle Coordinates:", bounds)
        # Add your data querying logic here

# Attach the draw event handler to the map
draw_control.on_draw(handle_draw)
Map.add_control(draw_control)

# Display the map
Map


