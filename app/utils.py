import folium
import os
# In utils.py
from .shared import stored_coords

import folium.map
import folium.vector_layers

center_coord = [11.5750454,104.9240291]
marker_coord = [11.5750454,104.9240291]

marker_radius = 25

location_marker_coord = [11.575256, 104.917721]

line_coord = [
    marker_coord,
    location_marker_coord
]
polygon_coord = [
    [11.574690125966656, 104.91149747106513],
    [11.575450856336046, 104.91615660779154],
    [11.572542170228179, 104.90843705772524],
    [11.574690125966656, 104.91149747106513]
]

def find_map_variable_name(html):
    pattern = "var map_"
    
    starting_index = html.find(pattern) + 4
    tmp_html = html[starting_index:]
    ending_index = tmp_html.find(" =")+ starting_index
    return html[starting_index:ending_index]

def find_popup_slice(html):
    '''
    Find the starting and ending index of popup function
    '''
    pattern = "function latLngPop(e)"
    
    # starting index
    starting_index = html.find(pattern)
    
    #
    tmp_html = html[starting_index:]
    
    #
    found = 0
    index = 0
    opening_found = False
    while not opening_found or found > 0:
        if tmp_html[index] == "{":
            found += 1
            opening_found = True
        elif tmp_html[index] == "}":
            found -= 1
        index += 1
    
    # determine the ending index of popup function
    ending_index = starting_index + index
    
    return starting_index, ending_index

def find_popup_variable_name(html):
    pattern = "var lat_lng"
    
    starting_index = html.find(pattern) + 4
    tmp_html = html[starting_index:]
    ending_index = tmp_html.find(" =")+ starting_index
    return html[starting_index:ending_index]

def find_variable_name(html, name_start):
    variable_pattern = 'var '
    pattern = variable_pattern + name_start
    
    starting_index = html.find(pattern) + 4
    tmp_html = html[starting_index:]
    ending_index = tmp_html.find(" =")+ starting_index
    return html[starting_index:ending_index]

def custom_code(popup_variable_name, map_variable_name):
    return f"""
        //custom code
        function latLngPop(e) {{
            {popup_variable_name}
                .setLatLng(e.latlng)
                .setContent(
                    `<div style='font-family:Arial,sans-serif;'>
                        <span style='font-weight:bold; color:#1976d2; font-size:1.1em;'>
                            Latitude: ${{e.latlng.lat.toFixed(6)}}<br>
                            Longitude: ${{e.latlng.lng.toFixed(6)}}
                        </span><br>
                        <button type='button' style='margin-top:8px; padding:4px 10px; background:#1976d2; color:white; border:none; border-radius:4px; cursor:pointer'
                            onclick="event.stopPropagation(); event.preventDefault();
                                fetch('/store-coord', {{
                                    method: 'POST',
                                    headers: {{
                                        'Accept': 'application/json',
                                        'Content-Type': 'application/json'
                                    }},
                                    body: JSON.stringify({{
                                        latitude: ${{e.latlng.lat}},
                                        longitude: ${{e.latlng.lng}}
                                    }})
                                }}).then(response => response.json()).then(data => {{
                                    L.marker([${{e.latlng.lat}}, ${{e.latlng.lng}}]).addTo({map_variable_name});
                                    // Fetch features and fill form fields
                                    fetch('/get-features')
                                        .then(response => response.json())
                                        .then(data => {{
                                            if(window.parent.document.getElementById('address_line_2'))
                                                window.parent.document.getElementById('address_line_2').value = data.address_line_2 || '';
                                            if(window.parent.document.getElementById('address_locality'))
                                                window.parent.document.getElementById('address_locality').value = data.address_locality || '';
                                            if(window.parent.document.getElementById('address_subdivision'))
                                                window.parent.document.getElementById('address_subdivision').value = data.address_subdivision || '';
                                        }});
                                    console.log(data);
                                }});">
                            Add
                        </button>
                    </div>`
                )
                .openOn({map_variable_name});
            console.log("Latitude: " + e.latlng.lat.toFixed(4));
            console.log("Longitude: " + e.latlng.lng.toFixed(4));
        }}
        // end custom code
    """
    
def use_coords_with_model():
    lat = stored_coords.get('lat')
    lon = stored_coords.get('lon')
    if lat is not None and lon is not None:
        # Use lat/lon with your model here
        print(f"Using coordinates: {lat}, {lon}")
    else:
        print("No coordinates stored yet.")

# add line folium map
def add_line():
    add_line = folium.PolyLine(
        line_coord,
        color = "blue",
        weight = "10",
        opacity = 0.8
    )
    return add_line

def add_polygon():
    add_ploygon = folium.PolyLine(
        polygon_coord,
        color = "blue",
        weight = "10",
        opacity = 0.8
    )
    return add_ploygon
# add marker
def add_Circle_marker():
    dot = folium.vector_layers.Circle(
        location=marker_coord,
        tooltip="The circle has radius {marker_radius}",
        radius= marker_radius,
        color = "red",
        fill = True,
        fill_color = "red"
    )
    return dot
def add_marker():
    mark = folium.Marker(
        location=marker_coord
    )
    return mark

# add location marker
def add_location_marker():
    location_marker = folium.Marker(
        location=location_marker_coord,
        tooltip= "Wat Phnom"
    )
    return location_marker

#add popup
def add_popup():
    popup = folium.LatLngPopup()
    return popup

def open_folium_map(project_map_url):
    driver = None

# creat_folium map
def create_folium_map():
    vmap = folium.Map(center_coord, zoom_start=9)
    add_popup().add_to(vmap)
    # add_marker().add_to(vmap)
    map_path = os.path.join("app", "static", "map.html")
    vmap.save(map_path)
    # reading folium file
    html = None
    with open(map_path, 'r') as mapfile:
        html = mapfile.read()
        
    # Find variable names
    map_variable_name = find_variable_name(html, "map_")
    popup_variable_name = find_variable_name(html, "lat_lng_popup_")

    
    # determine popup slice
    popup_slice = find_popup_slice(html)
    pstart, pend = find_popup_slice(html)
    
    # inject code
    with open(map_path, 'w') as mapfile:
        mapfile.write(
            html[:pstart] + \
            custom_code(popup_variable_name, map_variable_name) + \
            html[pend:]
        )
    # print(html[pstart:pend])
    # print(map_variable_name)
    # print(popup_variable_name)
    
    return "map.html"







# creat_folium map

# open the folium map

# run webserver that listens to sent coordinate

# close the folium map

# print all collected coords

# def generate_map():
#     # Create map centered on Bangkok
#     m = folium.Map(location=[13.736717, 100.523186], zoom_start=6)

#     # Add a sample marker
#     folium.Marker(
#         location=[13.736717, 100.523186],
#         tooltip="Bangkok",
#         popup="Capital of Thailand"
#     ).add_to(m)

#     # Save to app/static/map.html
#     map_path = os.path.join("app", "static", "map.html")
#     m.save(map_path)
#     return "map.html"

