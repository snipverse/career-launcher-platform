import json

DATA_FILE = 'resumes.json'

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def clean_data():
    resumes = load_data()
    initial_count = len(resumes)

    # Keep only those that have both name and email
    cleaned = [r for r in resumes if "name" in r and "email" in r and r["email"].strip() and r["name"].strip()]
    
    removed_count = initial_count - len(cleaned)
    save_data(cleaned)

    print(f"✅ Cleanup Complete: {removed_count} invalid entries removed.")
    print(f"📄 Total valid resumes left: {len(cleaned)}")

if __name__ == "__main__":
    clean_data()
