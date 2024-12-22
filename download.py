import os
import sys
import json
import requests
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
from bs4 import BeautifulSoup  # For parsing Fabric Maven repository
import subprocess  # For running the Fabric installer JAR

# Constants
VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
FABRIC_INSTALLER_URL = "https://maven.fabricmc.net/net/fabricmc/fabric-installer/"
APPDATA = os.getenv('APPDATA')
BASE_PATH = os.path.join(APPDATA, "TuiCraft")
LIBRARIES_PATH = os.path.join(BASE_PATH, "libraries")
ASSETS_PATH = os.path.join(BASE_PATH, "assets")

# Ensure directories exist
os.makedirs(LIBRARIES_PATH, exist_ok=True)
os.makedirs(ASSETS_PATH, exist_ok=True)


def download_file(url, save_path):
    """Function to download a file with progress."""
    if os.path.exists(save_path):
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
    """Function to organize file paths."""
    parts = file_path.replace("\\", "/").split("/")
    sub_path = os.path.join(base_path, *parts[:-1])  # Exclude the filename
    os.makedirs(sub_path, exist_ok=True)
    return os.path.join(sub_path, parts[-1])  # Full path including the file name


def download_files_parallel(file_list):
    """Function to download files in parallel."""
    with ThreadPoolExecutor() as executor:
        list(tqdm(executor.map(lambda file: download_file(*file), file_list), total=len(file_list)))


def get_latest_fabric_installer_url():
    """Fetch the latest Fabric installer JAR URL."""
    try:
        response = requests.get(FABRIC_INSTALLER_URL)
        response.raise_for_status()

        # Parse the HTML to find the latest version directory
        soup = BeautifulSoup(response.text, "html.parser")
        links = [a["href"].strip("/") for a in soup.find_all("a", href=True)]
        
        # Assume directories with version numbers are valid
        versions = [link for link in links if link.replace(".", "").isdigit()]
        if not versions:
            raise Exception("No valid Fabric versions found.")

        latest_version = sorted(versions, reverse=True)[0]
        fabric_installer_url = f"{FABRIC_INSTALLER_URL}{latest_version}/fabric-installer-{latest_version}.jar"
        return fabric_installer_url
    except Exception as e:
        raise Exception(f"Failed to determine the latest Fabric installer URL: {e}")


def get_fabric_installer(save_path):
    """Download the latest Fabric installer JAR if it doesn't already exist."""  
    try:
        if os.path.exists(save_path):
            print(f"Fabric installer already exists: {save_path}")
            return  # Skip download if the file already exists
        else:
            fabric_installer_url = get_latest_fabric_installer_url()
            download_file(fabric_installer_url, save_path)
            print(f"Fabric installer downloaded: {save_path}\n")
    except Exception as e:
        print(f"Failed to download Fabric installer: {e}\n")


def open_fabric_installer(save_path):
    """Open the Fabric installer JAR."""
    try:
        subprocess.run(["java", "-jar", save_path], check=True)
    except FileNotFoundError:
        return
    except Exception as e:
        return


def main():
    # Step 1: Parse command-line arguments
    if len(sys.argv) < 2:
        print("Usage: python download.py <version> OR python download.py fabric")
        sys.exit(1)

    option = sys.argv[1].lower()

    if option == "fabric":
        # Download Fabric installer
        fabric_installer_path = os.path.join(BASE_PATH, "fabric-installer.jar")
        get_fabric_installer(fabric_installer_path)
        open_fabric_installer(fabric_installer_path)
        sys.exit(0)

    # If not Fabric, assume it's a Minecraft version
    version_id = option

    # Step 2: Download the version manifest
    manifest_path = os.path.join(BASE_PATH, "version_manifest.json")
    response = requests.get(VERSION_MANIFEST_URL)
    if response.status_code == 200:
        with open(manifest_path, "wb") as file:
            file.write(response.content)
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
