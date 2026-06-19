import sys
import os
import glob
import base64
import json
import requests
from PIL import Image
import io

if sys.platform.startswith('win'):
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"

def encode_image_to_base64(image_path, max_dim=1000):
    with Image.open(image_path) as img:
        if max(img.size) > max_dim:
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            print(f"  Resized image {image_path} to {img.size} to speed up CPU inference.")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_invoice_single_request(image_path):
    print(f"\nProcessing image: {image_path}")
    base64_image = encode_image_to_base64(image_path)
    
    prompt = (
        "You are an expert ERP billing assistant. Analyze the provided invoice image and extract the fields "
        "listed below. Output the result ONLY as a valid, raw JSON object. Do not wrap the JSON in markdown code blocks "
        "like ```json or write any introductory or explanatory text. Just output the raw JSON.\n\n"
        "Required JSON fields:\n"
        "- invoice_number (string)\n"
        "- seller_name (string)\n"
        "- seller_nip (string, digits only)\n"
        "- buyer_name (string)\n"
        "- buyer_nip (string, digits only)\n"
        "- issue_date (string, YYYY-MM-DD)\n"
        "- due_date (string, YYYY-MM-DD)\n"
        "- gross_amount (float or string, e.g., 1230.00)\n"
        "- bank_account (string, digits only)\n"
        "- currency (string, e.g., PLN)"
    )
    
    payload = {
        "model": "local-model",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.1,
        "max_tokens": 500
    }
    
    headers = {
        "Content-Type": "application/json"
    }
    
    print(f"Sending single JSON analysis request to LM Studio (processing image in-memory once)...")
    try:
        # Set timeout to None so the script will wait indefinitely for the CPU to finish processing
        response = requests.post(LM_STUDIO_URL, headers=headers, json=payload, timeout=None)
        if response.status_code == 200:
            result_json = response.json()
            return result_json['choices'][0]['message']['content'].strip()
        else:
            print(f"LM Studio API Error (Status {response.status_code}): {response.text}")
            return None
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to LM Studio Local Server.")
        print("Please make sure LM Studio Local Server is running at http://localhost:1234.")
        return None
    except Exception as e:
        print(f"Error during LM Studio request: {e}")
        return None

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    data_dir = os.path.join(project_root, "data")
    output_dir = os.path.join(project_root, "output")

    image_files = glob.glob(os.path.join(data_dir, "*.png"))
    image_files = [f for f in image_files if "venv" not in f]
    
    if not image_files:
        print(f"No PNG files found in: {data_dir}")
        return
        
    print(f"Starting Qwen 3 VL analysis on {len(image_files)} images...")
    
    try:
        # Check connection first
        requests.get("http://localhost:1234/v1/models", timeout=5)
    except requests.exceptions.ConnectionError:
        print("\n[ERROR] Could not connect to LM Studio Local Server.")
        print("Please make sure LM Studio Local Server is running at http://localhost:1234.")
        return

    all_parsed_data = []
    
    for img_path in image_files:
        print(f"\n--- Processing: {img_path} ---")
        result = analyze_invoice_single_request(img_path)
        
        if result:
            clean_result = result
            if result.startswith("```"):
                lines = result.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].startswith("```"):
                    lines = lines[:-1]
                clean_result = "\n".join(lines).strip()
                
            try:
                parsed = json.loads(clean_result)
                parsed["file_name"] = os.path.basename(img_path)
                print(f"Successfully extracted JSON from {img_path}")
                all_parsed_data.append(parsed)
            except Exception:
                print(f"Warning: Could not parse response as JSON for {img_path}. Raw output was:")
                print(result)
                
    # Save all results
    os.makedirs(output_dir, exist_ok=True)
    out_file = os.path.join(output_dir, "invoices_extracted_lmstudio_local.json")
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_parsed_data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved all outputs to {out_file}")

if __name__ == "__main__":
    main()

