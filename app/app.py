from flask import Flask, render_template, request, jsonify
import pandas as pd
import plotly.express as px
import os

app = Flask(__name__)

# Path to your CSV file
CSV_FILE = r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\processed\land_dataset_final_v2.csv'

@app.route('/')
def index():
    # Load data from CSV
    if os.path.exists(CSV_FILE):
        df = pd.read_csv(CSV_FILE)
    else:
        # Create sample data if file doesn't exist
        data = {
            'latitude': [40.7128, 40.7214, 40.7312, 40.7410, 40.7510],
            'longitude': [-74.0060, -74.0123, -74.0215, -74.0322, -74.0422],
            'price_per_m2': [1000, 1500, 2000, 2500, 3000],
            }
        df = pd.DataFrame(data)
        df.to_csv(CSV_FILE, index=False)
    
    # Create the map figure
    fig = px.scatter_mapbox(
        df,
        lat="latitude",
        lon="longitude",
        color="price_per_m2",
        hover_data=["price_per_m2"],
        zoom=10,
        height=600
    )
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r":0,"t":0,"l":0,"b":0},
        clickmode='event+select'
    )
    
    # Convert to HTML
    map_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
    
    return render_template('test.html', map_html=map_html)

@app.route('/delete_points', methods=['POST'])
def delete_points():
    try:
        # Get indices to delete from request
        indices = request.json.get('indices', [])
        
        # Load current data
        df = pd.read_csv(CSV_FILE)
        
        # Delete selected points
        df = df.drop(indices)
        
        # Save updated data
        df.to_csv(CSV_FILE, index=False)
        
        return jsonify({
            'status': 'success',
            'message': f'Deleted {len(indices)} points',
            'remaining': len(df)
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400

if __name__ == '__main__':
    app.run(debug=True)