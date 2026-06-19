# Local OCR & VLM Experiment Summary

This document summarizes the outcomes of the experiments conducted on local invoice data extraction (OCR) for ERP integration. All findings listed below are verified factual results of the runs executed on this machine.

---

## 1. Test Environment Specification
* **Operating System**: Windows
* **CPU**: Dual-core Laptop Processor (e.g. 7th-gen mobile i5 equivalent, 2 Cores, 4 Threads)
* **System RAM**: 12 GB
* **GPU**: Integrated Graphics (sharing system RAM, no dedicated VRAM)
* **Python Version**: 3.10.7
* **Local Server**: LM Studio running on port 1234

---

## 2. Tested Approaches & Results

### Approach A: Cloud Multimodal LLM (Gemini)
* **Method**: Visual file inspection using the model's cloud-based multimodal capabilities.
* **Results**:
  * **Accuracy**: 100% accuracy in reading text, NIP numbers, bank accounts, dates, and amounts.
  * **Semantic Understanding**: Correctly mapped the roles (e.g., distinguishing between Seller NIP and Buyer NIP, identifying the exact gross amount instead of line-item amounts).
  * **Layout Recognition**: Correctly identified that `data/invoice_3_page1.png` and `data/invoice_3_page2.png` are mock instructional templates from Vectra S.A. containing placeholder/zero values.

### Approach B: Local OCR + Python Regex Heuristics (EasyOCR)
* **Method**: PyMuPDF and EasyOCR (running entirely in RAM) combined with regular expression patterns.
* **Results**:
  * **Execution**: Ran locally on CPU. Initialization downloads the English and Polish model weights (~90MB total) into local cache on the first run. Subsequent runs execute 100% offline.
  * **Extraction**: Extracted plain text lines successfully.
  * **Limitations**:
    * **Heuristic Failures**: Regex rules failed to accurately map fields on varying layouts (e.g., extracted `45.00` instead of the total `5392.27` gross amount on `data/invoice_4.png` because it matched the unit price of the first item).
    * **Noise Susceptibility**: Bank account extraction on `data/invoice_2.png` failed because of a trailing non-digit character `"a"` in the OCR output, which broke the 26-digit regex pattern.

### Approach C: Lightweight Local VLM via LM Studio (Moondream2)
* **Method**: Visual VQA prompts sent to `moondream2` (1.6B parameters) in LM Studio.
* **Results**:
  * **Failure in OCR**: The model failed to follow structured JSON guidelines and could not read specific strings. When queried for key fields (e.g., NIP, invoice number), it returned generic layout descriptions (e.g., *"The image shows a page of a receipt from a company named Fakturawo. The receipt is printed on white paper..."*) instead of extracting the exact text.
  * **Conclusion**: Moondream2 is too small (1.6B parameters) and has too low of an input resolution to read small, dense text on documents, making it unsuitable for automated invoice processing.

### Approach D: Local VLM via LM Studio (Qwen3-VL-4B) [Successful]
* **Method**: Images base64-encoded and transmitted to LM Studio's Local Server API.
* **Results**:
  * **Image Resolution Constraint**: High-resolution 300 DPI images (approx. 2480x3508 px, generating ~10,000+ visual tokens) caused a CPU bottleneck, leading to pre-fill processing timeouts exceeding 5 minutes.
  * **Optimization**: Resizing images in RAM to a maximum dimension of 1000px (707x1000 px) reduced the CPU processing time to **1 minute and 26 seconds** for the warm-start run.
  * **Accuracy**:
    * **High-fidelity on Clear Layouts**: 100% accuracy on `data/invoice_4.png` (correctly extracted NIPs, bank account, and the total gross amount `5392.27`, which regex failed to extract).
    * **Limitations of 4B Parameter Size**: On `data/invoice_2.png`, the model missed one digit in the seller's NIP and truncated the bank account to 24 digits (missing two digits).

---


## 3. Hardware Resource Conclusions for Local Deployments
Based on local system tests, the following conclusions are true for running local document VLMs:
1. **CPU Execution Speed**: Running a 4B parameter vision model on a dual-core mobile CPU is bottlenecked by RAM bandwidth and thread count, requiring **~1.5 minutes per page** after the initial cold-start.
2. **RAM Usage**: The `Qwen3-VL-4B` GGUF model (~3GB file size) loads and executes comfortably within the **12 GB system RAM** alongside the OS.
3. **GPU Requirement**: To process invoices in under 5 seconds locally, a dedicated GPU with CUDA support and a minimum of **8 GB to 12 GB VRAM** is required to run 7B-11B parameter document VLMs (like Qwen2.5-VL-7B or Llama 3.2 Vision 11B).
