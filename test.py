from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors
from reportlab.lib.units import inch
from datetime import datetime

def generate_property_valuation_pdf(output_filename, property_data):
    # Create PDF document
    doc = SimpleDocTemplate(output_filename, pagesize=letter)
    
    # Story will hold all the elements of the document
    story = []
    
    # Get sample styles and customize them
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        name='Title',
        fontSize=16,
        leading=20,
        alignment=TA_CENTER,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    date_style = ParagraphStyle(
        name='Date',
        fontSize=10,
        leading=14,
        alignment=TA_CENTER,
        spaceAfter=24
    )
    
    section_style = ParagraphStyle(
        name='Section',
        fontSize=12,
        leading=16,
        alignment=TA_LEFT,
        spaceBefore=12,
        spaceAfter=12,
        fontName='Helvetica-Bold'
    )
    
    item_style = ParagraphStyle(
        name='Item',
        fontSize=10,
        leading=14,
        alignment=TA_LEFT,
        leftIndent=40,
        spaceAfter=8
    )
    
    # Add title
    story.append(Paragraph("<strong>PROPERTY VALUATION REPORT</strong>", title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", date_style))
    
    # Property details section
    story.append(Paragraph("PROPERTY DETAILS", section_style))
    story.append(Paragraph(f"Address: {property_data['address']}", item_style))
    story.append(Paragraph(f"Property Type: {property_data['property_type']}", item_style))
    story.append(Paragraph(f"Land Area: {property_data['land_area']}", item_style))
    
    # Valuation summary section
    story.append(Paragraph("VALUATION SUMMARY", section_style))
    story.append(Paragraph(f"Market Value Estimate: ${property_data['market_value']:,.2f}", item_style))
    story.append(Paragraph(f"Valuation Method: {property_data['valuation_method']}", item_style))
    story.append(Paragraph(f"Valuation Date: {property_data['valuation_date']}", item_style))
    story.append(Paragraph(f"Confidence Level: {property_data['confidence_level']}%", item_style))
    
    # Comparative market analysis
    story.append(Paragraph("COMPARATIVE MARKET ANALYSIS", section_style))
    
    # Create table with 3 columns
    table_data = [
        ["Comparable 1", "Comparable 2", "Comparable 3"],
        [property_data['comp1'], property_data['comp2'], property_data['comp3']]
    ]
    
    table = Table(table_data, colWidths=[doc.width/3.0]*3)
    table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 1, colors.black),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ]))
    
    story.append(table)
    story.append(Spacer(1, 0.2*inch))
    
    # Valuation notes
    story.append(Paragraph("VALUATION NOTES", section_style))
    for note in property_data['valuation_notes']:
        story.append(Paragraph(note, item_style))
    
    # Build the document
    doc.build(story)

# Sample property data
property_data = {
    'address': '123 Main Street, Anytown, CA 90210',
    'property_type': 'Residential Land',
    'land_area': '0.5 acres',
    'market_value': 350000,
    'valuation_method': 'Sales Comparison Approach',
    'valuation_date': datetime.now().strftime('%B %d, %Y'),
    'confidence_level': 85,
    'comp1': '120 Main St: $340,000\n(0.45 acres)',
    'comp2': '125 Main St: $360,000\n(0.55 acres)',
    'comp3': '130 Main St: $355,000\n(0.52 acres)',
    'valuation_notes': [
        "This valuation is based on recent sales of comparable properties.",
        "The land is zoned for residential use with potential for single-family development.",
        "No significant encumbrances or easements were identified.",
        "Market conditions as of the valuation date were considered stable."
    ]
}

# Generate the PDF
generate_property_valuation_pdf('Property_Valuation_Report.pdf', property_data)
print("Property valuation PDF generated successfully!")