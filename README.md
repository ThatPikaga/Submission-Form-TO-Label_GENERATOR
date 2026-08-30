# Submission Form → Label Generator

An automated print pipeline that converts **Microsoft Forms** exhibition submissions directly into a **print-ready, uniformly formatted PDF catalog** of gallery labels — replacing a time-consuming manual design process in Canva.

---

## Purpose

Event submissions arrive via Microsoft Forms. Instead of manually copying each response into Canva, this script:

1. **Scans** a local intake folder (`EXCEL_FILES_HERE/`) for exported form data (`.xlsx`, `.xls`, `.csv`).
2. **Parses** each row using the native Microsoft Forms column schema.
3. **Compiles** every submission into a strictly formatted exhibition label.
4. **Outputs** a cutter-aligned, multi-page PDF into `Generated_Labels/`.

---

## Technical Stack

| Component | Technology |
|---|---|
| Language | Python 3 (cross-platform: Windows & Arch Linux) |
| Data engine | `pandas` (with `openpyxl` for Excel files) |
| PDF engine | `reportlab` (raw point-based coordinate grid for unmoving layouts) |
| Environment | Local `venv` bootstrap (`run.sh`) to comply with **PEP 668** ecosystem safety rules |

---

## 📁 Project Structure

```text
What-Orana-Means-To-Me--Submission-Form-TO-Label_GENERATOR/
├── EXCEL_FILES_HERE/        # ← Drop exported MS Forms data files here
├── Generated_Labels/        # ← Auto-created; PDF output lands here
│   └── exhibition_labels_landscape.pdf
├── Generate_Labels.py       # Core pipeline script
├── run.sh                   # venv bootstrap + launcher (bash)
├── venv/                    # Auto-created by run.sh (do not commit)
└── README.md
```

---

## 🚀 Quick Start

### Linux / macOS (recommended)

```bash
chmod +x run.sh   # first time only
./run.sh
```

`run.sh` automatically creates the virtual environment (if missing), installs `pandas`, `openpyxl` and `reportlab`, activates the environment, and runs the generator.

### Windows / Manual

```bash
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # Linux/macOS
pip install pandas openpyxl reportlab
python Generate_Labels.py
```

`run.bat` automatically creates the virtual environment (if missing), installs `pandas`, `openpyxl` and `reportlab`, activates the environment, and runs the generator.

---

## Data Input Workflow

1. In Microsoft Forms, export the responses (**Excel** or **CSV**).
2. If using **CSV**, export/save it as **UTF-8** (in Excel: *Save As → CSV UTF-8 (Comma delimited)*). This avoids `UnicodeDecodeError: 'utf-8' codec can't decode byte 0xa0` issues.
3. Place the file inside `EXCEL_FILES_HERE/`.
4. Run `./run.sh`.

> The script accepts `.xlsx`, `.xls` **and** `.csv` files simultaneously.

### Column Schema (0-indexed)

The parser targets the native MS Forms export structure by exact index position:

| `iloc` Index | Field | MS Forms Question |
|---|---|---|
| `row.iloc[5]` | Artist Name | *Your full name (participant)* |
| `row.iloc[6]` | Year Group / Role | *Your year level / class* |
| `row.iloc[7]` | Medium | *What mediums did you use?* (trailing `;` auto-stripped) |
| `row.iloc[8]` | Artwork Title | *Title of your artwork* |
| `row.iloc[10]` | Dimensions | *What are the dimensions of your physical piece?* |
| `row.iloc[13]` | Artist Statement | *Artist Statement* (auto-wrapped, multi-line safe) |

> **Note:** Index `5` (participant name) is deliberately used instead of index `4`, because parent/guardian submissions leave column 4 blank.

---

## Visual Output Specifications

### Canvas & Grid
- **Sheet:** A4 forced into **Landscape** — `841.89 × 595.27` points.
- **Grid:** Strict mathematical **2×2 quadrant matrix** → exactly **4 labels per sheet**.
- **Quadrant size:** ≈ `420.94 × 297.64` points each.
- **Borders:** Every quadrant is locked inside a solid `1.0 pt` mid-grey (`RGB 0.5, 0.5, 0.5`) boundary frame for precise physical paper-cutter alignment.
- **Pagination:** Dynamic canvas page-breaks (`c.showPage()`) trigger exactly every 4 records, with logic preventing trailing blank sheets.

### Typography Hierarchy
| Element | Font | Size | Colour |
|---|---|---|---|
| Artist Name | Helvetica-Bold | 20 pt | Black |
| Year Group / Role | Helvetica | 11 pt | Matte grey (0.4) |
| Artwork Title | Helvetica-Oblique (italic) | 16 pt | Black, wrapped in quotes |
| Medium / Dimensions | Helvetica | 12 pt | Dark grey (0.2) |
| Artist Statement | Helvetica (wrapped) | 9 pt / 11 leading | Dark grey (0.2) |

Artist statements are rendered through ReportLab `Paragraph` + `Frame` objects so multi-line text wraps automatically and is strictly clipped inside its quadrant — never bleeding across the cutter borders.

---

## ⚙️ Configuration

Defined at the top of `Generate_Labels.py`:

```python
INPUT_FOLDER  = "EXCEL_FILES_HERE"
OUTPUT_FOLDER = "Generated_Labels"
PDF_OUTPUT    = os.path.join(OUTPUT_FOLDER, "exhibition_labels_landscape.pdf")
```

---

##  Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'pandas'` | Script run with system Python instead of the venv | Run `./run.sh`, or activate the venv first (`source venv/bin/activate`) |
| `[WARNING] No Excel files found...` | Data file not in `EXCEL_FILES_HERE/`, or wrong extension | Move the `.xlsx` / `.xls` / `.csv` file into the folder |
| `'utf-8' codec can't decode byte 0xa0` | CSV saved with Windows/Latin-1 encoding | Re-export the CSV as **UTF-8** |
| Blank artist name on some labels | Row is missing the participant name field | Check the form submission; the parser reads column 5 |

---

## ⚠️ Known Limitations

- The `iloc` index mapping assumes the current MS Forms question order. If questions are added/removed in the form, indices may shift (header-name-based mapping is a possible future upgrade).
- Extremely long artist statements are clipped at the frame boundary to preserve the strict physical layout.
- `run.sh` targets bash environments; Windows users should use the `run.bat` file.
