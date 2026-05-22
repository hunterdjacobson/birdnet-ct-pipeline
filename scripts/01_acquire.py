import os
import sys
import time
import csv
import requests
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

XC_API_KEY = os.getenv("XC_API_KEY")

if not XC_API_KEY:
    print("Error: XC_API_KEY not found in .env file.")
    sys.exit(1)

# Project structure paths
BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
METADATA_DIR = BASE_DIR / "metadata"
LOG_FILE = METADATA_DIR / "ingestion_log.csv"

# Ensure directories exist
RAW_DIR.mkdir(parents=True, exist_ok=True)
METADATA_DIR.mkdir(parents=True, exist_ok=True)

# Species list
SPECIES = [
    {"common_name": "American Robin", "scientific_name": "Turdus migratorius", "species_code": "TURDMIGR"},
    {"common_name": "Black-capped Chickadee", "scientific_name": "Poecile atricapillus", "species_code": "POECATRI"},
    {"common_name": "Song Sparrow", "scientific_name": "Melospiza melodia", "species_code": "MELOMELO"},
    {"common_name": "American Crow", "scientific_name": "Corvus brachyrhynchos", "species_code": "CORVBRACH"},
    {"common_name": "Blue Jay", "scientific_name": "Cyanocitta cristata", "species_code": "CYANCRIS"},
    {"common_name": "White-throated Sparrow", "scientific_name": "Zonotrichia albicollis", "species_code": "ZONOALBI"},
    {"common_name": "Wood Thrush", "scientific_name": "Hylocichla mustelina", "species_code": "HYLOMUST"},
    {"common_name": "Ovenbird", "scientific_name": "Seiurus aurocapilla", "species_code": "SEIUAURO"},
    {"common_name": "Hermit Thrush", "scientific_name": "Catharus guttatus", "species_code": "CATHGUTT"},
    {"common_name": "American Redstart", "scientific_name": "Setophaga ruticilla", "species_code": "SETORUTI"},
]

HEADERS = [
    "xc_id", "species_code", "common_name", "scientific_name", "quality",
    "lat", "lng", "location", "date_recorded", "length_seconds",
    "filename_raw", "filename_wav", "download_status", "birdnet_processed", "qaqc_passed"
]

def init_log():
    """Initialize the ingestion log with headers if it doesn't exist."""
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(HEADERS)

def log_recording(data: dict):
    """Append a row to the ingestion log."""
    with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writerow(data)

def download_file(url: str, dest: Path) -> bool:
    """Download a file from a URL, validating it is audio content."""
    try:
        with requests.get(url, timeout=10, stream=True, allow_redirects=True) as r:
            r.raise_for_status()
            content_type = r.headers.get("Content-Type", "")
            if "text/html" in content_type:
                print(f"  Rejected: server returned HTML instead of audio (auth issue?)")
                return False
            with open(dest, "wb") as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        # Sanity check: real MP3s are at least 10KB
        if dest.stat().st_size < 10_000:
            print(f"  Rejected: file too small ({dest.stat().st_size} bytes), likely not audio")
            dest.unlink()
            return False
        return True
    except Exception as e:
        print(f"  Failed to download {url}: {e}")
        return False
    
def acquire_data():
    """Main function to acquire data from xeno-canto."""
    init_log()
    
    for sp in SPECIES:
        print(f"Searching for {sp['common_name']} ({sp['scientific_name']})...")
        
        # Split scientific name for genus and species
        genus, species = sp["scientific_name"].split(" ", 1)

        query = f'gen:{genus} sp:{species} cnt:"United States" q:A'
        params = {
            "query": query,
            "key": XC_API_KEY
        }
        
        try:
            response = requests.get("https://xeno-canto.org/api/3/recordings", params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            recordings = data.get("recordings", [])
        except Exception as e:
            print(f"Error fetching data for {sp['common_name']}: {e}")
            continue
        
        count = 0
        for rec in recordings:
            if count >= 8:
                break
            
            file_url = rec.get("file")
            if not file_url:
                continue
            
            if file_url.startswith("//"):
                file_url = "https:" + file_url

            # v3 requires the API key on the download URL itself
            if "?" in file_url:
                file_url = f"{file_url}&key={XC_API_KEY}"
            else:
                file_url = f"{file_url}?key={XC_API_KEY}"

            
            xc_id = rec.get("id")
            quality = rec.get("q", "Unknown")
            filename = f"{sp['species_code']}_{xc_id}_Q{quality}.mp3"
            dest_path = RAW_DIR / filename
            
            print(f"Downloading {sp['common_name']} {count+1}/8: {filename}")
            
            success = download_file(file_url, dest_path)
            
            log_data = {
                "xc_id": xc_id,
                "species_code": sp["species_code"],
                "common_name": sp["common_name"],
                "scientific_name": sp["scientific_name"],
                "quality": quality,
                "lat": rec.get("lat"),
                "lng": rec.get("lng"),
                "location": rec.get("loc"),
                "date_recorded": rec.get("date"),
                "length_seconds": rec.get("length"),
                "filename_raw": filename,
                "filename_wav": "",
                "download_status": "success" if success else "failed",
                "birdnet_processed": "",
                "qaqc_passed": ""
            }
            
            log_recording(log_data)
            
            if success:
                count += 1
            
            time.sleep(1) # 1-second sleep between requests

if __name__ == "__main__":
    acquire_data()
