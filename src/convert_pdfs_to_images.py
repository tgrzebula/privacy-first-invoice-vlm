import os
import glob
import fitz  # PyMuPDF

def convert_pdfs_to_scans():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "data")
    
    pdf_files = glob.glob(os.path.join(data_dir, "*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in: {data_dir}")
        return

    print(f"Found {len(pdf_files)} PDF files to convert.")
    
    # 300 DPI rendering matrix
    # Default DPI is 72, so zoom factor is 300 / 72 = 4.16666...
    zoom = 300 / 72
    matrix = fitz.Matrix(zoom, zoom)
    
    for pdf_path in pdf_files:
        basename = os.path.splitext(os.path.basename(pdf_path))[0]
        print(f"Processing {pdf_path}...")
        try:
            doc = fitz.open(pdf_path)
            num_pages = len(doc)
            print(f"  Pages: {num_pages}")
            
            for page_idx in range(num_pages):
                page = doc.load_page(page_idx)
                pix = page.get_pixmap(matrix=matrix)
                
                # Determine output filename (saving to data/ folder)
                if num_pages == 1:
                    out_name = os.path.join(data_dir, f"{basename}_scan.png")
                else:
                    out_name = os.path.join(data_dir, f"{basename}_scan_p{page_idx + 1}.png")
                
                pix.save(out_name)
                print(f"  Saved: {out_name}")
                
            doc.close()
        except Exception as e:
            print(f"  Error processing {pdf_path}: {e}")

if __name__ == "__main__":
    convert_pdfs_to_scans()
