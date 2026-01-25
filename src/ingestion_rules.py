import os
import re
import shutil

# STRYDA V2 INGESTION LOGIC
# STRICT ENFORCEMENT OF /protocols/INGESTION_V2.md

FORBIDDEN_PATTERNS = [r"\((\d+)\)", r"Download", r"Brochure", r"%20"]
TARGET_FOLDERS = {
    "WARRANTY": "/app/storage/00_General_Resources/",
    "CARE": "/app/storage/00_General_Resources/",
    "COLORSTEEL": "/app/storage/00_Material_Suppliers/NZ_Steel/",
    "COLORCOTE": "/app/storage/00_Material_Suppliers/Pacific_Coil/"
}

def sanitize_filename(filename):
    """
    Rule 2: Strip garbage, hashes, and trademarks.
    """
    clean = filename.replace("™", "").replace("®", "").replace("%20", "_")
    # Remove hash-like patterns (e.g., 66e3b2...)
    clean = re.sub(r"[a-f0-9]{8,}", "", clean)
    return clean.strip()

def enforce_naming_convention(brand, product, doc_type, extension=".pdf"):
    """
    Rule 1: [Manufacturer] - [Product] - [Type].pdf
    """
    safe_brand = sanitize_filename(brand)
    safe_product = sanitize_filename(product)
    safe_type = sanitize_filename(doc_type)
    return f"{safe_brand} - {safe_product} - {safe_type}{extension}"

def route_file(filepath, filename):
    """
    Rule 3: Sorting based on keywords.
    """
    upper_name = filename.upper()
    
    # 1. Check Universal Resources
    for key, dest in TARGET_FOLDERS.items():
        if key in upper_name:
            return dest
            
    # 2. Check Hidden Data (Rule 4)
    if "ACCESSORIES" in upper_name:
        # If it's an accessory file, we might rename it later to include '& Installation'
        pass

    return "/app/storage/01_Unsorted/"

if __name__ == "__main__":
    print("✅ V2 INGESTION RULES LOADED. Ready to sanitize.")
