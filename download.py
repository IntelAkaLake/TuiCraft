import os
import sys
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

# Constants
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
APPDATA = os.getenv('APPDATA')
BASE_PATH = os.path.join(APPDATA, "TuiCraft")
LIBRARIES_PATH = os.path.join(BASE_PATH, "libraries")
ASSETS_PATH = os.path.join(BASE_PATH, "assets")

# Ensure directories exist
os.makedirs(LIBRARIES_PATH, exist_ok=True)
os.makedirs(ASSETS_PATH, exist_ok=True)

def download_file(url, save_path):
    """Function to download a file with progress"""
    if os.path.exists(save_path):
        print(f"File already exists: {save_path}")
        return
    try:
        with requests.get(url, stream=True, timeout=10) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            with open(save_path, "wb") as file, tqdm(
                desc=f"Downloading {os.path.basename(save_path)}",
                total=total_size,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
                    bar.update(len(chunk))
        print(f"Downloaded: {save_path}")
    except Exception as e:
        print(f"Failed to download {url}: {e}")

def organize_file_path(base_path, file_path):
    """Function to organize file paths"""
    parts = file_path.replace("\\", "/").split("/")
    sub_path = os.path.join(base_path, *parts[:-1])  # Exclude the filename
    os.makedirs(sub_path, exist_ok=True)
    return os.path.join(sub_path, parts[-1])  # Full path including the file name

def download_files_parallel(file_list):
    """Function to download files in parallel"""
    with ThreadPoolExecutor() as executor:
        list(tqdm(executor.map(lambda file: download_file(*file), file_list), total=len(file_list)))

def main():
    # Step 1: Parse version from command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python download.py <version>")
        sys.exit(1)

    version_id = sys.argv[1]
    print(f"Selected version: {version_id}")

    # Step 2: Download the version manifest
    manifest_path = os.path.join(BASE_PATH, "version_manifest.json")
    response = requests.get(VERSION_MANIFEST_URL)
    if response.status_code == 200:
        with open(manifest_path, "wb") as file:
            file.write(response.content)
        print(f"Version manifest downloaded and saved to {manifest_path}")
    else:
        raise Exception("Failed to download version manifest")

    # Step 3: Parse the version manifest
    with open(manifest_path, "r") as file:
        data = json.load(file)

    versions = {version["id"]: version["url"] for version in data.get("versions", [])}

    if version_id not in versions:
        print(f"Version {version_id} not found in manifest. Exiting.")
        sys.exit(1)

    version_url = versions[version_id]
    response = requests.get(version_url)
    if response.status_code == 200:
        version_data = response.json()
        print(f"Version data for {version_id} retrieved.")
    else:
        raise Exception("Failed to retrieve version data")

    # Step 4: Download the Minecraft JAR
    client_url = version_data["downloads"]["client"]["url"]
    version_libraries_path = os.path.join(LIBRARIES_PATH, version_id)
    client_path = os.path.join(version_libraries_path, f"{version_id}.jar")
    os.makedirs(version_libraries_path, exist_ok=True)
    download_file(client_url, client_path)

    # Step 5: Download libraries
    libraries = version_data.get("libraries", [])
    library_files = []
    for library in libraries:
        downloads = library.get("downloads", {})
        artifact = downloads.get("artifact", {})
        if artifact:
            library_url = artifact["url"]
            path_parts = artifact["path"].split("/")
            library_path = organize_file_path(version_libraries_path, "/".join(path_parts))
            library_files.append((library_url, library_path))

    print("Downloading libraries...")
    download_files_parallel(library_files)

    # Step 6: Download assets
    version_assets_path = os.path.join(ASSETS_PATH, version_id)
    asset_index_url = version_data["assetIndex"]["url"]
    asset_index_path = os.path.join(version_assets_path, "indexes", f"{version_id}.json")
    os.makedirs(os.path.dirname(asset_index_path), exist_ok=True)
    download_file(asset_index_url, asset_index_path)

    with open(asset_index_path, "r") as file:
        assets_data = json.load(file)

    asset_files = []
    for asset_name, asset_info in assets_data["objects"].items():
        hash_value = asset_info["hash"]
        subdir = hash_value[:2]
        asset_url = f"https://resources.download.minecraft.net/{subdir}/{hash_value}"
        asset_path = os.path.join(version_assets_path, "objects", subdir, hash_value)
        os.makedirs(os.path.dirname(asset_path), exist_ok=True)
        asset_files.append((asset_url, asset_path))

    print("Downloading assets...")
    download_files_parallel(asset_files)
    print(f"All files for version {version_id} have been downloaded!")

if __name__ == "__main__":
    main()
