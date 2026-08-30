import glob
import os
import pandas as pd
import xml.sax.saxutils as saxutils
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, Frame
from reportlab.lib.styles import ParagraphStyle

# --- CONFIGURATION ---
INPUT_FOLDER = "EXCEL_FILES_HERE"
OUTPUT_FOLDER = "Generated_Labels"
PDF_OUTPUT = os.path.join(OUTPUT_FOLDER, "exhibition_labels_landscape.pdf")

def clean_text(val):
    """Clean up NaN values, trailing spaces, and weird semicolons from MS Forms."""
    if pd.isna(val):
        return ""
    text = str(val).strip()
    if text.endswith(';'):
        text = text[:-1].strip() # Removes trailing semicolons from category selectors
    return text

def find_col(df, search_term):
    """Dynamically finds a column name containing the search term (case-insensitive)."""
    for col in df.columns:
        if pd.notna(col) and search_term.lower() in str(col).lower():
            return col
    return None

def generate_pdf_labels():
    # Ensure the input folder exists
    if not os.path.exists(INPUT_FOLDER):
        os.makedirs(INPUT_FOLDER)
        print(f"[INFO] Created missing folder '{INPUT_FOLDER}'. Please drop your data files there and rerun.")
        return

    # Ensure the output folder exists
    if not os.path.exists(OUTPUT_FOLDER):
        os.makedirs(OUTPUT_FOLDER)
        print(f"[INFO] Created missing output folder '{OUTPUT_FOLDER}'.")

    # Find all Excel (.xlsx, .xls) AND CSV (.csv) files
    data_files = (
        glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx")) + 
        glob.glob(os.path.join(INPUT_FOLDER, "*.xls")) + 
        glob.glob(os.path.join(INPUT_FOLDER, "*.csv"))
    )

    if not data_files:
        print(f"[WARNING] No Excel or CSV files found inside the '{INPUT_FOLDER}' folder.")
        return

    print(f"[INFO] Found {len(data_files)} file(s) to process.")

    # Initialize the PDF Canvas in Landscape Mode
    c = canvas.Canvas(PDF_OUTPUT, pagesize=landscape(A4))
    page_width, page_height = landscape(A4)

    # 2x2 Grid calculations for Landscape dimensions
    label_width = page_width / 2    
    label_height = page_height / 2  

    # Define paragraph style for the artist statement (multi-line text wrapping)
    statement_style = ParagraphStyle(
        name='Statement',
        fontName='Helvetica',
        fontSize=9,
        leading=11,
        textColor=(0.2, 0.2, 0.2)
    )

    label_count = 0

    # Process files sequentially
    for file_path in data_files:
        print(f"Reading data from: {os.path.basename(file_path)}")
        try:
            if file_path.lower().endswith('.csv'):
                df = pd.read_csv(file_path, encoding='utf-8')
            else:
                df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            print(f"  [ERROR] Skipping file. Could not read due to: {e}")
            continue

        # --- DYNAMIC COLUMN MAPPING ---
        # This prevents errors when MS Forms shifts columns (e.g., adding "Last modified time" in Excel exports)
        col_artist = find_col(df, "full name (participant)") or find_col(df, "Name")
        col_year = find_col(df, "year level")
        col_medium = find_col(df, "mediums")
        col_title = find_col(df, "Title of your artwork")
        col_dimensions = find_col(df, "dimensions")
        col_statement = find_col(df, "Artist Statement")
        col_auction = find_col(df, "silent auction")

        for index, row in df.iterrows():
            # Extract data using the dynamically found column names
            artist = clean_text(row[col_artist]) if col_artist else ""
            role_year = clean_text(row[col_year]) if col_year else ""
            medium = clean_text(row[col_medium]) if col_medium else ""
            title = clean_text(row[col_title]) if col_title else ""
            dimensions = clean_text(row[col_dimensions]) if col_dimensions else ""
            statement = clean_text(row[col_statement]) if col_statement else ""
            auction_consent = clean_text(row[col_auction]) if col_auction else ""

            # Determine auction status (green = for auction, red = not for auction)
            is_for_auction = "yes" in auction_consent.lower()
            
            # Skip empty feedback rows 
            if not artist and not title:
                continue
                
            # --- PAGE BREAK LOGIC ---
            if label_count > 0 and label_count % 4 == 0:
                c.showPage()

            # Grid layout position math (0, 1, 2, or 3 per page)
            grid_pos = label_count % 4
            col_idx = grid_pos % 2
            row_idx = grid_pos // 2
            
            # Coordinate definitions for landscape layout quadrants
            x_start = col_idx * label_width
            y_start = page_height - ((row_idx + 1) * label_height)
            
            # Text margin alignment metrics inside each grid boundary
            text_x = x_start + 40
            text_y_top = y_start + label_height - 65
            
            # --- DRAW TEXT VISUAL ELEMENTS ---
            # 1. Artist Name
            c.setFont("Helvetica-Bold", 20)  
            c.setFillColorRGB(0, 0, 0)
            c.drawString(text_x, text_y_top, artist)
            
            # 2. Year Group / Category Subheading
            c.setFont("Helvetica", 11)
            c.setFillColorRGB(0.4, 0.4, 0.4) 
            c.drawString(text_x, text_y_top - 20, role_year)
            
            # 3. Artwork Title
            c.setFont("Helvetica-Oblique", 16)
            c.setFillColorRGB(0, 0, 0)
            c.drawString(text_x, text_y_top - 55, f'"{title}"')
            
            # 4. Technical Specs (Medium & Size details)
            c.setFont("Helvetica", 12)
            c.setFillColorRGB(0.2, 0.2, 0.2)
            c.drawString(text_x, text_y_top - 82, medium)
            c.drawString(text_x, text_y_top - 102, dimensions)
            
            # 5. Artist Statement
            if statement:
                # Escape XML characters (<, >, &) so ReportLab doesn't crash on them
                # and convert newlines to <br/> for paragraph wrapping
                safe_text = saxutils.escape(statement).replace('\n', '<br/>').replace('\r', '')
                
                # Create the paragraph object
                p = Paragraph(safe_text, statement_style)
                
                # Define the text area (Frame) to prevent text from spilling over the bottom border
                max_width = label_width - 80
                f = Frame(text_x, y_start + 15, max_width, 92, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
                
                # Draw the paragraph inside the frame
                f.addFromList([p], c)

            # 6. Auction Status Indicator (Top-Right Corner)
            # Position the status dot in the top-right corner of the label
            circle_radius = 9
            circle_x = x_start + label_width - 35
            circle_y = y_start + label_height - 40

            if is_for_auction:
                # GREEN dot + "Available for Auction" label
                c.setFillColorRGB(0.1, 0.6, 0.1)  # Green
                c.circle(circle_x, circle_y, circle_radius, stroke=0, fill=1)

                c.setFont("Helvetica-Bold", 10)
                c.setFillColorRGB(0.1, 0.5, 0.1)  # Matching green text
                c.drawRightString(circle_x - circle_radius - 8, circle_y - 3, "Available for Auction")
            else:
                # RED dot only (not for auction)
                c.setFillColorRGB(0.8, 0.1, 0.1)  # Red
                c.circle(circle_x, circle_y, circle_radius, stroke=0, fill=1)
            
            # --- DRAW SOLID COMPLETED CARD BORDERS ---
            c.setLineWidth(1.0)              
            c.setStrokeColorRGB(0.5, 0.5, 0.5) 
            c.rect(x_start, y_start, label_width, label_height)
            
            label_count += 1
            
    # Finalize and compile 
    if label_count > 0:
        c.save()
        print(f"\n[SUCCESS] Extracted {label_count} total gallery labels into '{PDF_OUTPUT}'!")
    else:
        print("\n[INFO] Complete. No valid rows were compiled into labels.")

if __name__ == "__main__":
    generate_pdf_labels()
