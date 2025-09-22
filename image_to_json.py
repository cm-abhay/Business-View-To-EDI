#!/usr/bin/env python3
"""
Image to Text Extraction Tool (Single File)

This script extracts text and structured data from a single image using the Docling library.
It outputs the extracted data only into `combined_extraction_results.json`.
"""

import os
import json
import platform
from pathlib import Path

from docling.document_converter import DocumentConverter



def collect_texts(obj, texts):
    """Recursively collect all text elements from the JSON data."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "text" and isinstance(v, str):
                texts.append(v)
            else:
                collect_texts(v, texts)
    elif isinstance(obj, list):
        for item in obj:
            collect_texts(item, texts)


def extract_structured_data(docling_json):
    """Extract structured data from the Docling JSON output."""
    texts = docling_json.get("texts", [])
    groups = docling_json.get("groups", [])
    tables = docling_json.get("tables", [])

    results = {
        "key_value_data": [],
        "sections": [],
        "tables": [],
        "raw_texts": []
    }

    text_map = {t["self_ref"]: t for t in texts}

    for group in groups:
        group_data = []
        for child in group.get("children", []):
            text = text_map.get(child["$ref"], {}).get("text", "")
            if text:
                group_data.append(text)

        if group_data:
            kv_pairs = []
            i = 0
            while i < len(group_data):
                key = group_data[i]
                value = group_data[i+1] if i+1 < len(group_data) else ""
                kv_pairs.append((key, value))
                i += 2
            results["key_value_data"].extend(kv_pairs)

    for t in texts:
        if t.get("label") == "section_header":
            results["sections"].append(t.get("text", ""))
        results["raw_texts"].append(t.get("text", ""))

    for table in tables:
        table_data = []
        cells = table.get("data", {}).get("table_cells", [])
        row_cells = {}
        for cell in cells:
            row_idx = cell.get("start_row_offset_idx", 0)
            if row_idx not in row_cells:
                row_cells[row_idx] = []
            row_cells[row_idx].append(cell)

        for row_idx in sorted(row_cells.keys()):
            row = row_cells[row_idx]
            sorted_row = sorted(row, key=lambda c: c.get("start_col_offset_idx", 0))
            row_data = [cell.get("text", "") for cell in sorted_row]
            table_data.append(row_data)

        results["tables"].append(table_data)

    return results


def extract_text_from_image(image_path):
    """Extract text and structured data from a single image."""
    print(f"Processing image: {image_path}")

    try:
        converter = DocumentConverter()
        doc = converter.convert(image_path).document
        data = doc.export_to_dict()

        texts = []
        collect_texts(data, texts)
        all_text = " ".join(texts)

        structured_data = extract_structured_data(data)

        return {
            "raw_text": all_text,
            "structured_data": structured_data,
        }

    except Exception as e:
        print(f"❌ Error processing {image_path}: {str(e)}")
        return None


def process_file(file_path):
    """Process a single image file."""
    # converter = setup_vlm_converter()
    result = extract_text_from_image(file_path)

    if result:
        results = {os.path.basename(file_path): result}
        combined_output = "combined_extraction_results.json"
        with open(combined_output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=4, ensure_ascii=False)
        print(f"✅ Results written to {combined_output}")
    else:
        print("❌ No results generated.")


def main():
    """Main entry point."""
    file_path = "BusinessViews/Invoice/I1.png"

    if not os.path.isfile(file_path):
        print(f"❌ File not found: {file_path}")
        return

    process_file(file_path)


if __name__ == "__main__":
    main()
