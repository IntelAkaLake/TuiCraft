import os
import subprocess
from pathlib import Path
import argparse

def launch_minecraft(
    java_path,
    base_dir,
    libraries_dir,
    version,
    username="User",
    uuid="00000000-0000-0000-0000-000000000000",
    access_token="OFFLINE_ACCESS_TOKEN",
):
    """
    Launch Minecraft in offline mode (non-demo) using LWJGL and additional dependencies.

    Args:
        java_path (str): Path to the Java executable.
        base_dir (str): Path to the base directory (where `assets` and game files are located).
        libraries_dir (str): Path to the folder containing additional JAR files.
        version (str): Minecraft version to launch.
        username (str): The player's username (default: "User"). Requires Implementation for custom username.
    """
    # Resolve paths
    base_dir = Path(base_dir).resolve()
    libraries_dir = Path(libraries_dir).resolve()
    version_dir = libraries_dir / version
    minecraft_dir = base_dir / "instances" / version / ".minecraft"
    assets_dir = base_dir / "assets" / version

    # Ensure the instance and assets directories exist
    os.makedirs(minecraft_dir, exist_ok=True)
    os.makedirs(assets_dir, exist_ok=True)

    # Validate the version directory
    if not version_dir.exists() or not version_dir.is_dir():
        raise FileNotFoundError(f"Version folder not found: {version_dir}")

    # Locate the client.jar file
    client_jar_path = version_dir / f"{version}.jar"
    if not client_jar_path.exists():
        raise FileNotFoundError(f"Client JAR not found in version folder: {client_jar_path}")

    # Collect all JAR files from the version's subdirectory
    jar_files = [str(jar) for jar in version_dir.rglob("*.jar")]

    # Java classpath
    classpath = os.pathsep.join(jar_files)

    # Java arguments. Requires custom implementations
    java_args = [
        "-Xmx2G",  # Max 2GB of RAM
        "-Xms1G",  # Min 1GB of RAM
        "-cp",
        classpath,
        "net.minecraft.client.main.Main",
    ]

    # Minecraft arguments
    mc_args = [
        f"--username={username}",
        f"--uuid={uuid}",
        f"--accessToken={access_token}",
        f"--version={version}",
        f"--gameDir={minecraft_dir}",
        f"--assetsDir={assets_dir}",
        f"--userType=mojang",
        f"--assetIndex={version}",
    ]

    # Combine Java and Minecraft arguments
    full_command = [java_path] + java_args + mc_args + ["--debug"]
    print(full_command)
    # Set environment variables
    env = os.environ.copy()
    env["MINECRAFT_LAUNCHER"] = "PythonLauncher"

    # Launch Minecraft
    try:
        process = subprocess.Popen(
            full_command,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate()
        print("Minecraft Output:\n", stdout.decode())
        print("Minecraft Errors:\n", stderr.decode())
    except Exception as e:
        print(f"Failed to launch Minecraft: {e}")


if __name__ == "__main__":
    # Use argparse to accept the version as a command-line argument
    parser = argparse.ArgumentParser(description="Launch Minecraft instance.")
    parser.add_argument("version", help="Minecraft version to launch.")
    args = parser.parse_args()

    APPDATA = os.getenv("APPDATA")
    BASE_PATH = Path(APPDATA) / "TuiCraft"
    LIBRARIES_PATH = BASE_PATH / "libraries"

    # Launch the specified version
    launch_minecraft(
        java_path="java",
        base_dir=BASE_PATH,
        libraries_dir=LIBRARIES_PATH,
        version=args.version,
    )
