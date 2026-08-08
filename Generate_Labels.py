import glob
import os
import pandas as pd
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas

# --- CONFIGURATION ---
INPUT_FOLDER = "EXCEL_FILES_HERE"
PDF_OUTPUT = "exhibition_labels_landscape.pdf"

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
        print(f"[INFO] Created missing folder '{INPUT_FOLDER}'. Please drop your Excel files there and rerun.")
        return

    # Find all Excel files (.xlsx and .xls) inside the target directory
    excel_files = glob.glob(os.path.join(INPUT_FOLDER, "*.xlsx")) + glob.glob(os.path.join(INPUT_FOLDER, "*.xls"))

    if not excel_files:
        print(f"[WARNING] No Excel files found inside the '{INPUT_FOLDER}' folder.")
        return

    print(f"[INFO] Found {len(excel_files)} Excel file(s) to process.")

    # Initialize the PDF Canvas in Landscape Mode
    # A4 standard: 595.27 x 841.89 points -> Landscape: 841.89 x 595.27 points
    # NOTE: Argument is 'pagesize' (singular), not 'pagesizes'
    c = canvas.Canvas(PDF_OUTPUT, pagesize=landscape(A4))
    page_width, page_height = landscape(A4)

    # 2x2 Grid calculations for Landscape dimensions
    label_width = page_width / 2    # 420.94 points per label width
    label_height = page_height / 2  # 297.63 points per label height

    label_count = 0

    # Process files sequentially
    for file_path in excel_files:
        print(f"Reading data from: {os.path.basename(file_path)}")
        try:
            # header=0 is default, meaning the first row is treated as column names
            # and NOT processed as data, preventing a "header label" from being generated.
            df = pd.read_excel(file_path, engine='openpyxl')
        except Exception as e:
            print(f"  [ERROR] Skipping file. Could not read due to: {e}")
            continue

        for index, row in df.iterrows():
            # Check row bounds to avoid processing structural trailing blanks
            if len(row) < 11:
                continue

            # Target exact 0-indexed form data streams matching your sample layout
            artist = clean_text(row.iloc[5])      # Column 6: The actual display name
            role_year = clean_text(row.iloc[6])   # Column 7: Year Group or Parent Role
            medium = clean_text(row.iloc[7])      # Column 8: Medium category
            title = clean_text(row.iloc[8])       # Column 9: Artwork Title
            dimensions = clean_text(row.iloc[10]) # Column 11: Dimensions
            
            # Skip empty feedback rows 
            if not artist and not title:
                continue
                
            # --- PAGE BREAK LOGIC ---
            # If this is NOT the first label, and we just finished a page of 4, break to a new page.
            # Placing this at the start of the drawing sequence prevents trailing blank pages.
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
            
            # --- DRAW SOLID COMPLETED CARD BORDERS ---
            c.setLineWidth(1.0)              # Darker solid boundary frame line
            c.setStrokeColorRGB(0.5, 0.5, 0.5) # Clean mid-grey frame
            c.rect(x_start, y_start, label_width, label_height)
            
            label_count += 1
            
    # Finalize and compile 
    if label_count > 0:
        # save() automatically flushes the current page to the PDF. 
        # No need to call showPage() manually here, as doing so would add a blank trailing page.
        c.save()
        print(f"\n[SUCCESS] Extracted {label_count} total gallery labels into '{PDF_OUTPUT}'!")
    else:
        print("\n[INFO] Complete. No valid rows were compiled into labels.")

if __name__ == "__main__":
    generate_pdf_labels()
