# Local Offline Invoice OCR & ERP Parser

> [!IMPORTANT]
> **Work in Progress (WIP)**  

A privacy-focused, 100% offline Python pipeline designed to parse invoice scans, run OCR, and extract structured ERP-ready metadata (JSON) using local Vision Language Models (VLMs) and traditional OCR tools. 

No data leaves your local machine, making this approach compliant with strict data protection regulations (GDPR/RODO).

---

## Features
* **In-Memory Processing**: Renders PDF document pages to image byte arrays in RAM (via `PyMuPDF`), bypassing intermediate disk-writing to maintain extreme privacy and clean directories.
* **Lightweight Local OCR**: Uses `EasyOCR` (based on PyTorch) to run lightweight text extraction offline.
* **Local VLM Orchestration**: Integrates with **LM Studio's Local API Server** to leverage advanced visual models (such as `Qwen3-VL-4B`) for structured JSON data extraction.
* **CPU-Inference Optimizations**:
  * **Dynamic Resizing**: Automatically resizes high-resolution images to a maximum dimension of 1000px in RAM, reducing the visual token count by over 90% (drastically speeding up CPU pre-fill time).
  * **Single-Request Batching**: Requests the entire ERP schema as a single JSON object in one completion call, paying the visual prompt processing cost only once.

---

## File Structure & Scripts
* [src/convert_pdfs_to_images.py](src/convert_pdfs_to_images.py): Converts high-resolution PDFs into standalone 300 DPI PNG scans in the `data/` folder.
* [src/extract_with_easyocr.py](src/extract_with_easyocr.py): Performs traditional OCR in-memory using `EasyOCR` and extracts fields via regex.
* [src/extract_with_lmstudio.py](src/extract_with_lmstudio.py): Connects to LM Studio Local Server, resizes images in `data/`, and performs structured JSON VQA.
* [ocr_experiment_summary.md](ocr_experiment_summary.md): Factual performance report comparing cloud vs. local OCR methods.
* **Sample Invoices**: Included public test scans (`data/invoice_1.png`, etc.) representing typical layouts (see [Legal Disclaimer](#legal-disclaimer) below).

---

## Getting Started

### 1. Installation & Environment Setup
Clone the repository and set up a Python virtual environment:
```powershell
# Create venv
python -m venv venv

# Activate venv (Windows PowerShell)
.\venv\Scripts\Activate.ps1

# Install required packages
pip install -r requirements.txt
```

### 2. Run Local OCR (EasyOCR)
To run the traditional local OCR parser which processes all PNGs in the `data/` folder:
```powershell
python src/extract_with_easyocr.py
```
This output is saved to `output/invoices_extracted_easyocr_local.json`.

### 3. Run Local VLM (LM Studio Integration)
To use advanced VLM extraction:
1. Launch **LM Studio** and download the vision model `Qwen3-VL-4B`.
2. Navigate to the **Local Server** tab in LM Studio, select the loaded model, and click **Start Server** (running on port `1234`).
3. Run the client script:
```powershell
python src/extract_with_lmstudio.py
```
This outputs structured data for all local invoices to `output/invoices_extracted_lmstudio_local.json`.

---

## Benchmarks & Insights
Detailed analysis is available in [ocr_experiment_summary.md](ocr_experiment_summary.md). 

On a standard dual-core laptop CPU (e.g. 7th-gen mobile i5 equivalent with **12 GB RAM**):
* **EasyOCR**: Fast execution (~20s per file), but susceptible to regex parsing errors on diverse layouts.
* **Qwen 3 VL (4B)**: Extremely accurate semantic parsing (correctly resolved names, dates, NIPs, and total gross amounts). 
  * *Unoptimized (Original 300 DPI image)*: Timed out (>5 mins) due to processing thousands of visual tokens.
  * *Optimized (1000px Max Dim + Single JSON Request)*: Completed in **1m 26s** per file. On a GPU, this would take under **3 seconds**.

---

## Legal Disclaimer
The sample invoice scans included in the `data/` directory (e.g., `invoice_1.png`, `invoice_2.png`, etc.) are mock templates and publicly available educational samples collected from the internet for testing, research, and demonstration purposes only. They are owned by their respective creators or publishers. No copyright infringement is intended. 

If you are the owner of any of these documents and object to their inclusion in this public repository, please contact the repository owner or open an issue, and they will be removed immediately.
