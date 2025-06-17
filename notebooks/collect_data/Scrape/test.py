import csv
import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime
from urllib.parse import urljoin

def load_ids_from_csv(csv_path, id_column='property_id'):
    """Load property IDs from existing CSV file"""
    ids = []
    with open(csv_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if id_column in row and row[id_column].strip():
                ids.append(row[id_column].strip())
    return ids

def scrape_property_page(property_id):
    """Scrape property data with robust error handling"""
    result = { 
        'property_id': property_id,
        'url': f"https://www.realestate.com.kh/{property_id}/",
        'scrape_timestamp': datetime.now().isoformat(),
        'error': None,
        'title': '',
        'price': '',
        'currency': 'USD',
        'description': '',
        'property_type': '',
        'address': '',
        'location': '',
        'bedrooms': '',
        'bathrooms': '',
        'floor_area': '',
        'land_area': '',
        'floor_number': '',
        'total_floors': '',
        'unit_number': '',
        'listing_date': '',
        'latitude': '',
        'longitude': '',
        'agent_name': '',
        'agent_phone': '',
        'agent_company': '',
        'agent_profile_url': '',
        'num_images': 0,
        'num_amenities': 0
    }
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(result['url'], headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extract from JSON-LD schema
        script = soup.find('script', type='application/ld+json')
        if script:
            try:
                data = json.loads(script.string)
                result.update({
                    'title': data.get('name', ''),
                    'price': str(data.get('offers', {}).get('price', '')),
                    'currency': data.get('offers', {}).get('priceCurrency', 'USD'),
                    'description': data.get('description', '').replace('\n', ' ').strip(),
                    'property_type': data.get('@type', ''),
                    'address': data.get('address', {}).get('streetAddress', '')
                })
            except json.JSONDecodeError:
                pass
        
        # 2. Extract property features
        features = {}
        for div in soup.select('div.property-detail-feature'):
            label = div.find('span', class_='label')
            value = div.find('span', class_='value')
            if label and value:
                key = label.text.strip().lower().replace(' ', '_')
                features[key] = value.text.strip()
        
        # Map features to result fields
        feature_map = {
            'bedrooms': ['bedrooms', 'bed'],
            'bathrooms': ['bathrooms', 'bath'],
            'floor_area': ['size', 'floor_area', 'building_size'],
            'land_area': ['land_size', 'land_area', 'plot_size'],
            'floor_number': ['floor_number', 'floor'],
            'total_floors': ['total_floors', 'floors'],
            'unit_number': ['unit_number', 'unit']
        }
        
        for field, keys in feature_map.items():
            for key in keys:
                if key in features:
                    result[field] = features[key]
                    break
        
        # 3. Extract location
        location_div = soup.find('div', class_='property-location')
        if location_div:
            result['location'] = location_div.text.strip()
        elif result['address']:
            result['location'] = result['address']
        
        # 4. Extract agent info
        agent_div = soup.find('div', class_='agent-info')
        if agent_div:
            result.update({
                'agent_name': agent_div.find('h4').text.strip() if agent_div.find('h4') else '',
                'agent_phone': agent_div.find('a', href=lambda x: x and 'tel:' in x).text.strip() if agent_div.find('a', href=lambda x: x and 'tel:' in x) else '',
                'agent_company': agent_div.find('div', class_='agent-company').text.strip() if agent_div.find('div', class_='agent-company') else '',
                'agent_profile_url': urljoin(result['url'], agent_div.find('a', class_='agent-profile-link')['href']) if agent_div.find('a', class_='agent-profile-link') else ''
            })
        
        # 5. Extract images
        images = [urljoin(result['url'], img['src']) for img in soup.select('div.property-gallery img[src]') if 'placeholder' not in img['src']]
        result['num_images'] = len(images)
        
        # 6. Extract amenities
        amenities = [li.text.strip() for li in soup.select('div.property-amenities li')]
        result['num_amenities'] = len(amenities)
        
        # 7. Extract listing date
        date_div = soup.find('div', class_='property-date')
        if date_div and 'listed' in date_div.text.lower():
            result['listing_date'] = date_div.text.split('listed')[-1].strip()
        
        # 8. Extract coordinates
        map_div = soup.find('div', class_='property-map')
        if map_div:
            result.update({
                'latitude': map_div.get('data-lat', ''),
                'longitude': map_div.get('data-lng', '')
            })
            
    except requests.exceptions.RequestException as e:
        result['error'] = f"Request Error: {str(e)}"
    except Exception as e:
        result['error'] = f"Scraping Error: {str(e)}"
    
    return result

def scrape_properties_from_csv(input_csv, output_csv, id_column='property_id'):
    """Read IDs from CSV, scrape each property, and save results"""
    print(f"Loading property IDs from {input_csv}...")
    property_ids = load_ids_from_csv(input_csv, id_column)
    
    if not property_ids:
        print("No property IDs found in the input file.")
        return
    
    print(f"Found {len(property_ids)} properties to scrape. Starting...")
    
    scraped_data = []
    for i, pid in enumerate(property_ids, 1):
        print(f"\nScraping property {i}/{len(property_ids)}: ID {pid}")
        data = scrape_property_page(pid)
        scraped_data.append(data)
        
        if data.get('error'):
            print(f"  ! Error: {data['error']}")
        else:
            print(f"  ✓ Success: {data.get('title', 'No title')}")
        
        # Be polite with delays
        if i < len(property_ids):
            time.sleep(1.5)  # Adjust based on your needs
    
    # Save results
    if scraped_data:
        print(f"\nSaving results to {output_csv}...")
        with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = list(scraped_data[0].keys())
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(scraped_data)
        print("Done!")
    else:
        print("No data to save.")

# Example usage
if __name__ == "__main__":
    # Configure these paths
    INPUT_CSV = r'D:\CADT\Internship\Internship-I\real_estate_price_prediction\data\raw\realestates_kh_1.csv'  # Your existing CSV with property IDs
    OUTPUT_CSV = 'scraped_properties_full.csv'  # New file with complete data
    ID_COLUMN = 'id'  # Column name containing the IDs in your CSV
    
    scrape_properties_from_csv(INPUT_CSV, OUTPUT_CSV, ID_COLUMN)