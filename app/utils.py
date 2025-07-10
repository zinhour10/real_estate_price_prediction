import folium
import os
from .shared import stored_coords
import requests

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

def find_variable_name(html, name_start):
    variable_pattern = 'var '
    pattern = variable_pattern + name_start
    starting_index = html.find(pattern) + 4
    tmp_html = html[starting_index:]
    ending_index = tmp_html.find(" =")+ starting_index
    return html[starting_index:ending_index]

def find_popup_slice(html):
    pattern = "function latLngPop(e)"
    starting_index = html.find(pattern)
    tmp_html = html[starting_index:]
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
    ending_index = starting_index + index
    return starting_index, ending_index
def custom_code(popup_variable_name, map_variable_name):
    return f"""
        // custom code
            window.map = {map_variable_name};
            window.addEventListener('message', function(event) {{
            if (event.data && event.data.type === 'moveToLocation') {{
                var lat = event.data.lat;
                var lng = event.data.lng;
                if (typeof L !== 'undefined' && window.map) {{
                    window.map.setView([lat, lng], 16); // or your preferred zoom
                    latLngPop({{ latlng: {{ lat: lat, lng: lng }} }});

                }}
            }}
        }});

        // --- Add custom search box to map container ---
        var searchDiv = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom', {map_variable_name}.getContainer());
        searchDiv.style.position = 'absolute';
        searchDiv.style.top = '10px';
        searchDiv.style.left = '50px';
        searchDiv.style.zIndex = 1000;
        searchDiv.innerHTML = `
            <input id="custom-map-search" type="text" placeholder="Search location..." style="padding:4px 8px; border-radius:4px; border:1px solid #ccc; width:220px;"/>
            <ul id="custom-search-suggestions" style="background:white; border:1px solid #ccc; border-radius:4px; margin:0; padding:0; list-style:none; position:absolute; width:220px; display:none; max-height:180px; overflow-y:auto;"></ul>
        `;

        // Prevent map dragging when interacting with search
        var searchInput = searchDiv.querySelector('#custom-map-search');
        var suggestions = searchDiv.querySelector('#custom-search-suggestions');
        L.DomEvent.disableClickPropagation(searchDiv);

        // --- AJAX search with Nominatim ---
        var searchTimeout = null;
        searchInput.addEventListener('keyup', function(e) {{
            clearTimeout(searchTimeout);
            var query = this.value.trim();
            if (!query) {{
                suggestions.innerHTML = '';
                suggestions.style.display = 'none';
                return;
            }}
            searchTimeout = setTimeout(function() {{
                fetch('https://nominatim.openstreetmap.org/search?format=json&q=' + encodeURIComponent(query))
                    .then(res => res.json())
                    .then(data => {{
                        suggestions.innerHTML = '';
                        if (data.length === 0) {{
                            suggestions.style.display = 'none';
                            return;
                        }}
                        data.slice(0, 7).forEach(function(place) {{
                            var li = document.createElement('li');
                            li.textContent = place.display_name;
                            li.style.padding = '6px 8px';
                            li.style.cursor = 'pointer';
                            li.onmouseover = function() {{ li.style.background = '#e0e7ff'; }};
                            li.onmouseout = function() {{ li.style.background = ''; }};
                            li.onclick = function() {{
                                var lat = parseFloat(place.lat);
                                var lon = parseFloat(place.lon);
                                {map_variable_name}.setView([lat, lon], 16);
                                suggestions.innerHTML = '';
                                suggestions.style.display = 'none';
                                searchInput.value = place.display_name;
                            }};
                            suggestions.appendChild(li);
                        }});
                        suggestions.style.display = 'block';
                    }});
            }}, 250);
        }});

        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {{
            if (!searchDiv.contains(e.target)) {{
                suggestions.innerHTML = '';
                suggestions.style.display = 'none';
            }}
        }});

        // --- Only one marker logic ---
        window.lastAddedMarker = null;

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
                                    // Remove old marker if exists
                                    if (window.lastAddedMarker) {{
                                        {map_variable_name}.removeLayer(window.lastAddedMarker);
                                    }}
                                    // Add new marker and save reference
                                    window.lastAddedMarker = L.marker([${{e.latlng.lat}}, ${{e.latlng.lng}}]).addTo({map_variable_name});
                                    // Fetch features and fill form fields
                                    fetch('/get-features')
                                        .then(response => response.json())
                                        .then(data => {{
                                            function setDropdown(selectId, value, labelPrefix) {{
                                                var select = window.parent.document.getElementById(selectId);
                                                if (select) {{
                                                    select.innerHTML = '';
                                                    var defaultOption = document.createElement('option');
                                                    defaultOption.selected = true;
                                                    defaultOption.disabled = true;
                                                    defaultOption.textContent = 'Choose a ' + labelPrefix;
                                                    select.appendChild(defaultOption);
                                                    // Add the new value as an option and select it
                                                    if (value) {{
                                                        var opt = document.createElement('option');
                                                        opt.value = value;
                                                        opt.textContent = value;
                                                        opt.selected = true;
                                                        select.appendChild(opt);
                                                    }}
                                                }}
                                            }}
                                            setDropdown('address_subdivision', data.address_subdivision, 'City');
                                            setDropdown('address_locality', data.address_locality, 'District');
                                            setDropdown('address_line_2', data.address_line_2, 'Commune');
                                            
                                            var latInput = window.parent.document.getElementById('latitude');
                                            var lonInput = window.parent.document.getElementById('longitude');
                                            if (latInput && data.latitude !== undefined) {{
                                                latInput.value = data.latitude;
                                            }}
                                            if (lonInput && data.longitude !== undefined) {{
                                                lonInput.value = data.longitude;
                                            }}
                                            
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
def custom_code_detail(popup_variable_name, map_variable_name):
    return f"""
        // custom code
            

            window.map = {map_variable_name};
            window.addEventListener('message', function(event) {{
            if (event.data && event.data.type === 'moveToLocation') {{
                var lat = event.data.lat;
                var lng = event.data.lng;
                if (typeof L !== 'undefined' && window.map) {{
                    window.map.setView([lat, lng], 16); // or your preferred zoom
                    latLngPop({{ latlng: {{ lat: lat, lng: lng }} }});

                }}
            }}
        }});

        // --- Add custom search box to map container ---
        var searchDiv = L.DomUtil.create('div', 'leaflet-bar leaflet-control leaflet-control-custom', {map_variable_name}.getContainer());
        searchDiv.style.position = 'absolute';
        searchDiv.style.top = '10px';
        searchDiv.style.left = '50px';
        searchDiv.style.zIndex = 1000;
        searchDiv.innerHTML = `
            <input id="custom-map-search" type="text" placeholder="Search location..." style="padding:4px 8px; border-radius:4px; border:1px solid #ccc; width:220px;"/>
            <ul id="custom-search-suggestions" style="background:white; border:1px solid #ccc; border-radius:4px; margin:0; padding:0; list-style:none; position:absolute; width:220px; display:none; max-height:180px; overflow-y:auto;"></ul>
        `;

        // Prevent map dragging when interacting with search
        var searchInput = searchDiv.querySelector('#custom-map-search');
        var suggestions = searchDiv.querySelector('#custom-search-suggestions');
        L.DomEvent.disableClickPropagation(searchDiv);

        // --- AJAX search with Nominatim ---
        var searchTimeout = null;
        searchInput.addEventListener('keyup', function(e) {{
            clearTimeout(searchTimeout);
            var query = this.value.trim();
            if (!query) {{
                suggestions.innerHTML = '';
                suggestions.style.display = 'none';
                return;
            }}
            searchTimeout = setTimeout(function() {{
                fetch('https://nominatim.openstreetmap.org/search?format=json&q=' + encodeURIComponent(query))
                    .then(res => res.json())
                    .then(data => {{
                        suggestions.innerHTML = '';
                        if (data.length === 0) {{
                            suggestions.style.display = 'none';
                            return;
                        }}
                        data.slice(0, 7).forEach(function(place) {{
                            var li = document.createElement('li');
                            li.textContent = place.display_name;
                            li.style.padding = '6px 8px';
                            li.style.cursor = 'pointer';
                            li.onmouseover = function() {{ li.style.background = '#e0e7ff'; }};
                            li.onmouseout = function() {{ li.style.background = ''; }};
                            li.onclick = function() {{
                                var lat = parseFloat(place.lat);
                                var lon = parseFloat(place.lon);
                                {map_variable_name}.setView([lat, lon], 16);
                                suggestions.innerHTML = '';
                                suggestions.style.display = 'none';
                                searchInput.value = place.display_name;
                            }};
                            suggestions.appendChild(li);
                        }});
                        suggestions.style.display = 'block';
                    }});
            }}, 250);
        }});

        // Hide suggestions when clicking outside
        document.addEventListener('click', function(e) {{
            if (!searchDiv.contains(e.target)) {{
                suggestions.innerHTML = '';
                suggestions.style.display = 'none';
            }}
        }});
        
        // end custom code
    """
def add_popup():
    popup = folium.LatLngPopup()
    return popup

def create_folium_map():
    vmap = folium.Map(center_coord, zoom_start=9)
    add_popup().add_to(vmap)
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
    return "map.html"
def get_prediction():
    response = requests.get("http://127.0.0.1:5000/run-model")
    return response.json()

def get_nearby_properties():
    response = requests.get("http://127.0.0.1:5000/nearby-properties")
    return response.json()

def create_folium_map_for_detial():
    prediction = get_prediction()
    print("Prediction Data:", prediction)  # Debug print
    
    # Set center coordinates based on prediction
    center_coord = [prediction.get('lat', 11.5736576), prediction.get('lon', 104.923136)]
    
    vmap = folium.Map(location=center_coord, zoom_start=15)
    
    # Add marker with more visible properties
    folium.Marker(
        location=[prediction['lat'], prediction['lon']],
        tooltip="Click for details",
        popup=f"""
            <b>Property Details</b><br>
            Price: ${prediction['price']:,.2f}<br>
            Price/m²: ${prediction['price_per_m2']:,.2f}<br>
            Land Area: {prediction['land_area']}
        """,
        icon=folium.Icon(color="red", icon="home", prefix="fa"),
    ).add_to(vmap)
    nearby_data = get_nearby_properties()
    if nearby_data.get('status') != 'success' or not nearby_data.get('results', {}).get('nearby_properties'):
        print("Warning: No nearby properties found or API error")
        # Save basic map anyway
        map_path = os.path.join("app", "static", "map_detail.html")
        vmap.save(map_path)
        return map_path    
    nearby_properties = nearby_data['results']['nearby_properties']
    for idx, prop in enumerate(nearby_properties):
        # Different colors based on distance
        distance = prop.get('distance_km', float('inf'))
        if distance < 0.5:
            color = "green"
        elif distance < 1:
            color = "blue"
        else:
            color = "orange"
        folium.Marker(
            location=[prop['latitude'], prop['longitude']],
            tooltip=f"Nearby Property #{idx+1}",
            popup=f"""
                <b>Nearby Property</b><br>
                Price: ${prop['price']:,.2f}<br>
                Price/m²: ${prop['price_per_m2']:,.2f}<br>
                Land Area: {prop['land_area']} m²<br>
                Distance: {distance:.2f} km<br>
                ID: {prop['h_id']}<br>
                <a href="/property-details/{prop['h_id']}" target="_blank">More Details</a>
            """,
            icon=folium.Icon(color=color, icon="home", prefix="fa"),
        ).add_to(vmap)
        # folium.PolyLine(
        #     locations=[
        #         [prediction['lat'], prediction['lon']],
        #         [prop['latitude'], prop['longitude']]
        #     ],
        #     color="gray",
        #     weight=1.5,
        #     opacity=0.5,
        #     tooltip=f"{distance:.2f} km"
        # ).add_to(vmap)
    
    
    
    map_path = os.path.join("app", "static", "map_detail.html")
    vmap.save(map_path)
    print(f"Map saved to: {map_path}")  # Debug print
    
    return "map_detail.html"