import sys
import os
import glob
import re
import json
import fitz  # PyMuPDF
import easyocr

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# Regex patterns for ERP extraction
NIP_PATTERN = re.compile(r'\b(?:\d[\s-]?){10}\b')
ACCOUNT_PATTERN = re.compile(r'\b\d{2}(?:[\s-]?\d{4}){6}\b|\b\d{26}\b')
DATE_PATTERN = re.compile(r'\b\d{4}[-./]\d{2}[-./]\d{2}\b|\b\d{2}[-./]\d{2}[-./]\d{4}\b')
MONEY_PATTERN = re.compile(r'\b\d+(?:[\s\xa0]\d{3})*[,.]\d{2}\b')

def clean_digits(val):
    return re.sub(r'[^\d]', '', val)

def parse_text_lines(lines):
    data = {
        "invoice_number": None,
        "seller_nip": None,
        "buyer_nip": None,
        "dates": [],
        "gross_amount": None,
        "bank_account": None
    }
    
    # Try to find NIPs
    nips = []
    for line in lines:
        found_nips = NIP_PATTERN.findall(line)
        for fn in found_nips:
            cleaned = clean_digits(fn)
            if cleaned not in nips:
                nips.append(cleaned)
                
    if len(nips) >= 1:
        data["seller_nip"] = nips[0]
    if len(nips) >= 2:
        data["buyer_nip"] = nips[1]

    # Try to find Bank Account
    for line in lines:
        found_accounts = ACCOUNT_PATTERN.findall(line)
        if found_accounts:
            data["bank_account"] = re.sub(r'[\s-]', '', found_accounts[0])
            break

    # Try to find Dates
    dates = []
    for line in lines:
        found_dates = DATE_PATTERN.findall(line)
        for fd in found_dates:
            normalized = fd.replace('.', '-').replace('/', '-')
            if normalized not in dates:
                dates.append(normalized)
    data["dates"] = dates

    # Try to find Invoice Number
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if "faktura" in line_lower or "numer:" in line_lower or "fv/" in line_lower:
            match = re.search(r'(?:vat|nr|numer|fv|fvt)?[:\s]+([A-Z0-9/\-_]{4,})', line, re.IGNORECASE)
            if match:
                data["invoice_number"] = match.group(1)
                break
            elif i + 1 < len(lines):
                next_line = lines[i + 1]
                match_next = re.search(r'^([A-Z0-9/\-_]{4,})$', next_line, re.IGNORECASE)
                if match_next:
                    data["invoice_number"] = match_next.group(1)
                    break

    # Try to find Gross Amount
    for i, line in enumerate(lines):
        line_lower = line.lower()
        if "do zapłaty" in line_lower or "razem" in line_lower or "brutto" in line_lower:
            money_match = MONEY_PATTERN.findall(line)
            if money_match:
                data["gross_amount"] = money_match[-1]
                break
            else:
                found = False
                for offset in range(1, 3):
                    if i + offset < len(lines):
                        next_line = lines[i + offset]
                        money_match_next = MONEY_PATTERN.findall(next_line)
                        if money_match_next:
                            data["gross_amount"] = money_match_next[-1]
                            found = True
                            break
                if found:
                    break

    return data

def process_pdf_in_memory(pdf_path, reader, zoom=300/72):
    """Processes a PDF file entirely in memory page-by-page."""
    results = []
    doc = fitz.open(pdf_path)
    matrix = fitz.Matrix(zoom, zoom)
    
    for page_idx in range(len(doc)):
        page = doc.load_page(page_idx)
        # Render the page to a pixmap
        pix = page.get_pixmap(matrix=matrix)
        # Convert pixmap to PNG bytes directly in RAM
        img_bytes = pix.tobytes("png")
        
        # Run EasyOCR directly on the in-memory bytes
        lines = reader.readtext(img_bytes, detail=0)
        parsed = parse_text_lines(lines)
        parsed["source_file"] = os.path.basename(pdf_path)
        parsed["page_number"] = page_idx + 1
        results.append(parsed)
        
    doc.close()
    return results

def process_png_in_memory(png_path, reader):
    """Reads a PNG file and processes it in memory."""
    with open(png_path, "rb") as f:
        img_bytes = f.read()
    
    # Run EasyOCR directly on the bytes loaded into RAM
    lines = reader.readtext(img_bytes, detail=0)
    parsed = parse_text_lines(lines)
    parsed["source_file"] = os.path.basename(png_path)
    parsed["page_number"] = 1
    return [parsed]

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "data")
    output_dir = os.path.join(project_root, "output")

    print("Initializing EasyOCR (running entirely in RAM)...")
    reader = easyocr.Reader(['pl', 'en'])
    
    all_parsed_data = []
    
    # 1. Process all PDFs in the data folder (if any)
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    if pdf_files:
        print(f"Found {len(pdf_files)} PDF files to process in-memory.")
        for pdf_path in pdf_files:
            print(f"Processing PDF in-memory: {pdf_path}...")
            try:
                pdf_results = process_pdf_in_memory(pdf_path, reader)
                all_parsed_data.extend(pdf_results)
            except Exception as e:
                print(f"  Error processing PDF {pdf_path}: {e}")
                
    # 2. Process all PNGs in the data folder (if any)
    png_files = glob.glob(os.path.join(data_dir, "*.png"))
    # Exclude venv directory pngs if any
    png_files = [f for f in png_files if "venv" not in f]
    
    if png_files:
        print(f"Found {len(png_files)} PNG files to process in-memory.")
        for png_path in png_files:
            print(f"Processing PNG in-memory: {png_path}...")
            try:
                png_results = process_png_in_memory(png_path, reader)
                all_parsed_data.extend(png_results)
            except Exception as e:
                print(f"  Error processing PNG {png_path}: {e}")

    # Output structured data to JSON
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "invoices_extracted_easyocr_local.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_parsed_data, f, ensure_ascii=False, indent=2)
        
    print(f"\nAll processing done. Saved final ERP data to {out_file}")
    
    # Print the extracted data to console
    print("\n--- Extracted Data in RAM ---")
    print(json.dumps(all_parsed_data, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
