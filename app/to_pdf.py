from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime
import requests
import os
from pathlib import Path

# Define Times New Roman font names
TIMES_ROMAN = "Times-Roman"
TIMES_BOLD = "Times-Bold"

distance_columns = ['near_Koh_Pich_in_km', 'near_Russian_Market_in_km', 'near_AEON_Mall_1_in_km', 'near_AEON_Mall_2_in_km', 'near_AEON_Mall_3_in_km', 'near_Bassac_Lane_in_km', 'near_Koh_Norea_in_km', 'near_Camko_City_in_km', 'near_Olympic_Stadium_in_km', 'near_Phsar_Tmey_in_km', 'near_Boeng_Keng_Kang_1_in_km', 'near_Wat_Phnom_in_km', 'near_Chroy_Changvar_Bridge_in_km', 'near_Vattanac_Tower_in_km', 'near_Royal_Palace_in_km', 'near_Sisowath_Riverside_Park_in_km', 'near_Phnom_Penh_Airport_in_km', 'near_Phsar_Chas_in_km', 'near_Phsar_kandal_in_km']
amenity_columns = ['n_cafe_5km', 'n_gas_station_5km', 'n_hospital_5km', 'n_hotel_5km', 'n_mart_5km', 'n_pre_school_5km', 'n_secondary_school_5km', 'n_primary_school_5km', 'n_university_5km', 'n_seven_eleven_5km', 'n_resturant_5km', 'n_super_market_5km', 'n_borey_5km', 'n_bank_5km', 'n_atm_5km']
road_columns = ['f_bridleway', 'f_corridor', 'f_cycleway', 'f_disused', 'f_footway', 'f_motorway', 'f_path', 'f_pedestrian', 'f_primary', 'f_residential', 'f_road', 'f_secondary', 'f_service', 'f_steps', 'f_tertiary', 'f_track', 'f_trunk', 'f_trunk_link', 'f_unclassified', 'f_unused']

def generate_valuation_notes(property_feature):
    notes = []
    
    # 1. Proximity to key landmarks
    nearby_landmarks = []
    for col in distance_columns:
        if col in property_feature:
            landmark_name = col.replace('near_', '').replace('_in_km', '').replace('_', ' ')
            distance = property_feature[col]
            
            if distance <= 0.1:
                nearby_landmarks.append(f"Immediate proximity to {landmark_name} ({distance:.2f} km)")
            elif distance <= 0.5:
                nearby_landmarks.append(f"Walking distance to {landmark_name} ({distance:.2f} km)")
            elif distance <= 1.0:
                nearby_landmarks.append(f"Close to {landmark_name} ({distance:.2f} km)")
    
    if nearby_landmarks:
        notes.extend(nearby_landmarks)
    
    # 2. Specific amenities within 1km - NEW REQUIREMENT
    amenities_1km = []
    # Define the amenities you want to include in 1km radius
    desired_amenities = {
        'n_atm_in_1km': 'ATM',
        'n_bank_in_1km': 'Bank',
        'n_super_market_in_1km': 'Super Market',
        'n_resturant_in_1km': 'Restaurant',
        'n_cafe_in_1km': 'Cafe',
        'n_hospital_in_1km': 'Hospital',
        'n_mart_in_1km': 'Mart',
        'n_hotel_in_1km': 'Hotel',
        'n_university_in_1km': 'University',
        'n_primary_school_in_1km': 'Primary School',
        'n_secondary_school_in_1km': 'Secondary School'
    }
    
    # Check and add each desired amenity
    for col, display_name in desired_amenities.items():
        if col in property_feature:
            count = property_feature[col]
            if count > 0:
                amenities_1km.append(f"{count} {display_name}")
    
    if amenities_1km:
        notes.append(f"Amenities within 1km: {', '.join(amenities_1km)}")
    
    # 3. Combined school count within 5km (keeps original functionality)
    school_types = ['pre_school', 'primary_school', 'secondary_school']
    school_count = sum(property_feature.get(f'n_{school}_5km', 0) for school in school_types)
    if school_count > 30:
        notes.append(f"{school_count} schools within 5km")
    
    # 4. Transportation access
    road_types = []
    important_roads = ['primary', 'secondary', 'motorway', 'trunk']
    
    for col in road_columns:
        if col in property_feature and property_feature[col] > 0:
            road_type = col.split('_', 1)[1] if '_' in col else col
            if road_type in important_roads:
                road_types.append(road_type.replace('_', ' '))
    
    if road_types:
        notes.append(f"Good access to: {', '.join(road_types)} roads")
    
    # 5. Property density
    population = property_feature.get('population', 0)
    if population > 10000:
        notes.append(f"High population density area ({population:,.0f} people)")
    
    # 6. Market comparison
    hex_price = property_feature.get('h_id_price_mean')
    if hex_price:
        notes.append(f"Area average land price: ${hex_price:,.2f} per m²")
    
    return notes

def generate_property_valuation_pdf(output_buffer, property_feature, predict, comparison, logo_path):
    # Create PDF document
    doc = SimpleDocTemplate(output_buffer, pagesize=letter)
    
    # Story will hold all the elements of the document
    story = []
    # --- ADD LOGO SECTION HERE ---
    # Add logo at the top (centered)
    if logo_path and os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=2*inch, height=1*inch)
            logo.hAlign = 'CENTER'
            story.append(logo)
            story.append(Spacer(1, 0.1*inch))
        except Exception as e:
            print(f"Error loading logo: {e}")
            # Add a placeholder text instead
            story.append(Paragraph("<strong>COMPANY LOGO</strong>", title_style))
    else:
        print("Logo path not provided or file not found")
        # Add a placeholder text instead
        story.append(Paragraph("<strong>COMPANY LOGO</strong>", title_style))
        
    # Get sample styles and customize them
    styles = getSampleStyleSheet()
    
    # Custom styles with Times New Roman font
    title_style = ParagraphStyle(
        name='Title',
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName=TIMES_BOLD
    )
    
    date_style = ParagraphStyle(
        name='Date',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=24,
        fontName=TIMES_ROMAN
    )
    
    section_style = ParagraphStyle(
        name='Section',
        fontSize=12,
        leading=16,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=12,
        fontName=TIMES_BOLD
    )
    
    item_style = ParagraphStyle(
        name='Item',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        leftIndent=40,
        spaceAfter=8,
        fontName=TIMES_ROMAN
    )
    
    # Add title
    story.append(Paragraph("<strong>PROPERTY VALUATION REPORT</strong>", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", date_style))
    
    # Property details section
    story.append(Paragraph("PROPERTY DETAILS", section_style))
    story.append(Paragraph(f"Address: {property_feature['address_line_2']}, {property_feature['address_locality']}, {property_feature['address_subdivision']}", item_style))
    story.append(Paragraph(f"Property Type: Land", item_style))
    story.append(Paragraph(f"Land Area: {predict['land_area']} m2", item_style))
    
    # Valuation summary section
    story.append(Paragraph("VALUATION SUMMARY", section_style))
    story.append(Paragraph(f"Market Value Estimate: ${predict['price']:,.0f}", item_style))
    story.append(Paragraph(f"Valuation Method: Real Estate Price Prediction", item_style))
    story.append(Paragraph(f"Valuation Date: {datetime.now().strftime('%B %d, %Y')}", item_style))
    story.append(Paragraph(f"Confidence Level: 50%", item_style))
    
    # Comparative market analysis
    story.append(Paragraph("COMPARATIVE MARKET ANALYSIS", section_style))
    
    # Define styles for table cells with Times New Roman
    cell_style = ParagraphStyle(
        name='TableCell',
        fontSize=9,
        leading=11,
        alignment=TA_LEFT,
        wordWrap=True,
        spaceBefore=2,
        spaceAfter=2,
        fontName=TIMES_ROMAN
    )
    
    header_cell_style = ParagraphStyle(
        name='HeaderCell',
        fontSize=9,
        leading=11,
        alignment=TA_CENTER,
        wordWrap=True,
        spaceBefore=2,
        spaceAfter=2,
        fontName=TIMES_BOLD
    )
    
    # Create table data structure
    table_data = []
    headers = ["Attribute"] + [f"Comparable {i+1}" for i in range(3)]
    table_data.append([Paragraph(header, header_cell_style) for header in headers])
    
    # Initialize lists for each attribute
    addresses = [Paragraph("Address", cell_style)]
    prices = [Paragraph("Price", cell_style)]
    price_per_m2 = [Paragraph("Price/m²", cell_style)]
    sizes = [Paragraph("Land Area", cell_style)]
    distances = [Paragraph("Distance", cell_style)]
    populations = [Paragraph("Population", cell_style)]
    
    comparables = comparison[:3]
    
    # Process each comparable property
    for comp in comparables:
        # Address
        address_line_2 = comp.get('address_line_2', 'N/A')
        address_locality = comp.get('address_locality', 'N/A')
        address_subdivision = comp.get('address_subdivision', 'N/A')
        address = f"{address_line_2}, {address_locality}, {address_subdivision}"
        addresses.append(Paragraph(address, cell_style))
        
        # Price
        price = comp.get('price')
        if isinstance(price, (int, float)):
            prices.append(Paragraph(f"${price:,.0f}", cell_style))
        else:
            prices.append(Paragraph("N/A", cell_style))
        
        # Price per m²
        land_area = comp.get('land_area')
        if isinstance(price, (int, float)) and isinstance(land_area, (int, float)) and land_area > 0:
            ppm2 = price / land_area
            price_per_m2.append(Paragraph(f"${ppm2:,.0f}/m²", cell_style))
        else:
            price_per_m2.append(Paragraph("N/A", cell_style))
        
        # Land Area
        size = comp.get('land_area')
        if isinstance(size, (int, float)):
            sizes.append(Paragraph(f"{size:,.0f} m²", cell_style))
        else:
            sizes.append(Paragraph("N/A", cell_style))
        
        # Distance
        distance = comp.get('distance_km')
        if isinstance(distance, (int, float)):
            distances.append(Paragraph(f"{distance:.2f} km", cell_style))
        else:
            distances.append(Paragraph("N/A", cell_style))
        
        # Population
        pop = comp.get('population', 'N/A')
        if isinstance(pop, (int, float)):
            populations.append(Paragraph(f"{pop:,.0f}", cell_style))
        else:
            populations.append(Paragraph("N/A", cell_style))
    
    # Pad with empty entries if less than 3 comparables
    for _ in range(3 - len(comparables)):
        addresses.append(Paragraph("N/A", cell_style))
        prices.append(Paragraph("N/A", cell_style))
        price_per_m2.append(Paragraph("N/A", cell_style))
        sizes.append(Paragraph("N/A", cell_style))
        distances.append(Paragraph("N/A", cell_style))
        populations.append(Paragraph("N/A", cell_style))
    
    # Add rows to table data
    table_data.append(addresses)
    table_data.append(prices)
    table_data.append(price_per_m2)
    table_data.append(sizes)
    table_data.append(distances)
    table_data.append(populations)
    
    # Create table with adjusted column widths
    col_widths = [
        1.2 * inch,  # Attribute column
        (doc.width - 1.2 * inch) / 3.0, 
        (doc.width - 1.2 * inch) / 3.0,
        (doc.width - 1.2 * inch) / 3.0
    ]
    
    table = Table(table_data, colWidths=col_widths)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTNAME', (0,0), (-1,-1), TIMES_ROMAN),  # Set entire table to Times-Roman
        ('FONTNAME', (0,0), (-1,0), TIMES_BOLD),    # Set header row to Times-Bold
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ALIGN', (0,0), (0,-1), 'LEFT'),
        ('ALIGN', (1,0), (-1,-1), 'CENTER'),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('FONTWEIGHT', (0,0), (-1,0), 'BOLD'),
        ('LEFTPADDING', (0,0), (-1,-1), 3),
        ('RIGHTPADDING', (0,0), (-1,-1), 3),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.2*inch))
    
    # Valuation notes
    story.append(Paragraph("VALUATION NOTES", section_style))
    valuation_notes = generate_valuation_notes(property_feature)
    for note in valuation_notes:
        story.append(Paragraph(note, item_style))
    
    # Build the document
    doc.build(story)
    output_buffer.seek(0)
    
# script_dir = Path(__file__).parent.absolute()

# # Construct the absolute path to the logo
# img_path = script_dir / 'static' / 'img' / 'wing_logo.png'

# property_data = requests.get('http://127.0.0.1:5000/get-features').json()
# predict = requests.get('http://127.0.0.1:5000/run-model').json()
# comparison = requests.get('http://127.0.0.1:5000/nearby-properties').json()

# # Generate the PDF
# generate_property_valuation_pdf('Property_Valuation_Report2.pdf', property_data, predict, comparison, img_path)
# print("Property valuation PDF generated successfully!")