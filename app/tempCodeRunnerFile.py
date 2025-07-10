     try:
            logo = Image(logo_path, width=1.5*inch, height=1*inch)
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
    