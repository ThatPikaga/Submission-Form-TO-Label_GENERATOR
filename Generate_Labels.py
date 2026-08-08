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

        for index, row in df.iterrows():
            # Check row bounds to avoid processing structural trailing blanks
            # We need at least 14 columns to safely reach the Artist Statement (index 13)
            if len(row) < 14:
                continue

            # Target exact 0-indexed form data streams matching your sample layout
            artist = clean_text(row.iloc[5])      # Column 6: The actual display name
            role_year = clean_text(row.iloc[6])   # Column 7: Year Group or Parent Role
            medium = clean_text(row.iloc[7])      # Column 8: Medium category
            title = clean_text(row.iloc[8])       # Column 9: Artwork Title
            dimensions = clean_text(row.iloc[10]) # Column 11: Dimensions
            statement = clean_text(row.iloc[13])  # Column 14: Artist Statement
            
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
                # x = text_x, y = 15pts above bottom border, width = label_width - 80, height = 92pts
                max_width = label_width - 80
                f = Frame(text_x, y_start + 15, max_width, 92, showBoundary=0, leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
                
                # Draw the paragraph inside the frame
                f.addFromList([p], c)
            
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
