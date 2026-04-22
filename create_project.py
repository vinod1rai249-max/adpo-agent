import os

# Base project folder
base_dir = "adpo_agent"

# Folder structure
folders = [
    base_dir,
    os.path.join(base_dir, "test_data"),
]

# Files to create
files = [
    "app.py",
    "agent.py",
    "lab_rules.py",
    "fhir_client.py",
    "audit.py",
    "seed_rules.py",
    "requirements.txt",
    "Dockerfile",
    os.path.join("test_data", "generate_test_data.py"),
    os.path.join("test_data", "load_test_data.py"),
]

# Create folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)
    print(f"Created folder: {folder}")

# Create files
for file in files:
    file_path = os.path.join(base_dir, file)
    
    # Ensure parent directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Create empty file if not exists
    if not os.path.exists(file_path):
        with open(file_path, "w") as f:
            pass
        print(f"Created file: {file_path}")
    else:
        print(f"Already exists: {file_path}")

print("\n✅ Project structure created successfully!")