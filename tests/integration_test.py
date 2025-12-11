import requests
import shutil
import os
import zipfile

# Configuration
API_URL = "http://localhost:8000"
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures", "simple")
ZIP_PATH = "test_project.zip"

def create_zip():
    print(f"Zipping {FIXTURES_DIR}...")
    with zipfile.ZipFile(ZIP_PATH, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(FIXTURES_DIR):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, FIXTURES_DIR)
                zipf.write(file_path, arcname)

def run_scan():
    print(f"Uploading {ZIP_PATH} to {API_URL}/scan...")
    try:
        with open(ZIP_PATH, 'rb') as f:
            files = {'file': (ZIP_PATH, f, 'application/zip')}
            response = requests.post(f"{API_URL}/scan", files=files)
            
        if response.status_code == 200:
            data = response.json()
            print("\n✅ Scan Successful!")
            print(f"Total Monthly Cost: ${data['total_monthly_cost']}")
            print(f"Total Hourly Cost: ${data['total_hourly_cost']}")
            print("Resources:")
            for res in data['resources']:
                print(f" - {res['address']} ({res['type']}): ${res['total_monthly_cost']}/mo")
        else:
            print(f"❌ Scan Failed: {response.status_code} - {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection Error: Is the backend running on localhost:8000?")
    except Exception as e:
        print(f"❌ Error: {e}")

def cleanup():
    if os.path.exists(ZIP_PATH):
        os.remove(ZIP_PATH)

if __name__ == "__main__":
    create_zip()
    run_scan()
    cleanup()
