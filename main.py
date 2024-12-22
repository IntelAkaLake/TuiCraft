import os
import subprocess
import threading
import queue
import shutil
import string
import random
from pathlib import Path
from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Input, Log
from textual.containers import Horizontal, Vertical

class BorderTitleApp(App[None]):
    CSS = """
    #instance-input {
        display: none;
    }
    #logs-container {
        display: none;
    }
    """

    def compose(self) -> ComposeResult:
        """Compose the UI."""
        header = Static(
            r"""
  _____     _  ___           __ _   
 |_   _|  _(_)/ __|_ _ __ _ / _| |_ 
   | || || | | (__| '_/ _` |  _|  _| 
   |_| \_,_|_|\___|_| \__,_|_|  \__| 
                                    
            """,
            id="header",
        )
        yield header

        APPDATA = os.getenv("APPDATA")
        BASE_PATH = Path(APPDATA) / "TuiCraft"
        LIBRARIES_PATH = BASE_PATH / "libraries"
        INSTANCES_PATH = BASE_PATH / "instances"
        ASSETS_PATH = BASE_PATH / "assets"
        
        BASE_PATH.mkdir(parents=True, exist_ok=True)
        LIBRARIES_PATH.mkdir(parents=True, exist_ok=True)
        INSTANCES_PATH.mkdir(parents=True, exist_ok=True)
        ASSETS_PATH.mkdir(parents=True, exist_ok=True)
        
        # Instances Section
        available_versions = [
            folder.name for folder in LIBRARIES_PATH.iterdir() if folder.is_dir()
        ]

        # Create a Vertical container with buttons for each version
        instances_section = Vertical(
            *[
                Button(version, id=f"instance-{version.replace('.', '_')}")
                for version in available_versions
            ],
            id="instances-container",
        )

        # Settings Section
        settings_section = Vertical(
            Button("New Instance", id="setting-instance"),
            Button("Download Fabric", id="setting-fabric"),
            Button("About", id="setting-about"),
            id="settings-container",
        )

        # Add both sections to a horizontal container
        container = Horizontal(instances_section, settings_section, id="root-container")
        yield container

        # Add an Input widget for instance (hidden initially)
        yield Input(
            placeholder="Type the Minecraft version and press Enter",
            id="instance-input",
        )

        # Add a Log widget for logs (hidden initially)
        logs_section = Vertical(
            Log(id="logs-widget", auto_scroll=True),
            Button("Back to Main", id="back-to-main"),
            id="logs-container",
        )
        yield logs_section

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id.startswith("instance-"):
            version = button_id.replace("instance-", "").replace("_", ".")[:-4]
            self.launch_instance(version)
        elif button_id == "setting-instance":
            self.show_instance_input()
        elif button_id == "setting-fabric":
            self.show_logs_section()
            self.download_fabric()
        elif button_id == "setting-about":
            os.system("start \"\" https://github.com/IntelAkaLake/TuiCraft/")
        elif button_id == "back-to-main":
            self.show_main_sections()

    def show_instance_input(self) -> None:
        """Show the instance input field."""
        input_widget = self.query_one("#instance-input")
        input_widget.styles.display = "block"
        input_widget.focus()

    def show_logs_section(self) -> None:
        """Show the logs section and hide the main sections."""
        instances = self.query_one("#instances-container", Vertical)
        settings = self.query_one("#settings-container", Vertical)
        logs = self.query_one("#logs-container", Vertical)
        header = self.query_one("#header")

        instances.styles.display = "none"
        settings.styles.display = "none"
        header.styles.display = "none"
        logs.styles.display = "block"

    def show_main_sections(self) -> None:
        """Show the main sections and hide the logs section."""
        instances = self.query_one("#instances-container", Vertical)
        settings = self.query_one("#settings-container", Vertical)
        logs = self.query_one("#logs-container", Vertical)
        header = self.query_one("#header")

        logs.styles.display = "none"
        header.styles.display = "block"
        instances.styles.display = "block"
        settings.styles.display = "block"

    def log_to_widget(self, message: str) -> None:
        """Log a message to the log widget."""
        logs_widget = self.query_one("#logs-widget", Log)
        logs_widget.write_line(message)

    def download_fabric(self) -> None:
        """Download the Fabric installer with real-time logging."""
        APPDATA = os.getenv("APPDATA")
        BASE_PATH = Path(APPDATA) / "TuiCraft"
        fabric_installer_path = Path(BASE_PATH) / "fabric-installer.jar"

        logs_widget = self.query_one("#logs-widget")
        logs_widget.clear()
        self.log_to_widget(f"Starting Fabric download to {fabric_installer_path}...")

        def run_subprocess():
            try:
                process = subprocess.Popen(
                    ["python", str(Path(__file__).parent / "download.py"), "fabric"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
                for line in iter(process.stdout.readline, ""):
                    if line:
                        self.log_to_widget(line.strip())
                for line in iter(process.stderr.readline, ""):
                    if line:
                        self.log_to_widget(f"[ERROR] {line.strip()}")
                process.stdout.close()
                process.stderr.close()
                process.wait()
                if process.returncode == 0:
                    self.log_to_widget("Fabric installer successfully ran!")
                else:
                    self.log_to_widget(f"Fabric installer failed with code {process.returncode}.")
            except Exception as e:
                self.log_to_widget(f"Error during download: {e}")

        threading.Thread(target=run_subprocess, daemon=True).start()

    def launch_instance(self, version: str) -> None:
        """Launch a Minecraft instance with real-time logging."""
        self.show_logs_section()  # Show the logs section to display launch logs
        logs_widget = self.query_one("#logs-widget", Log)
        logs_widget.clear()
        self.log_to_widget(f"Launching version: {version}")

        launch_script = Path(__file__).parent / "launch.py"

        def run_launch():
            try:
                process = subprocess.Popen(
                    ["python", str(launch_script), version],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                for line in iter(process.stdout.readline, ""):
                    if line.strip():
                        self.log_to_widget(line.strip())
                for line in iter(process.stderr.readline, ""):
                    if line.strip():
                        self.log_to_widget(f"[ERROR] {line.strip()}")
                process.stdout.close()
                process.stderr.close()
                process.wait()
                if process.returncode == 0:
                    self.log_to_widget(f"Instance {version} launched successfully!")
                else:
                    self.log_to_widget(f"Instance launch failed with code {process.returncode}.")
            except Exception as e:
                self.log_to_widget(f"Error during launch: {e}")

        threading.Thread(target=run_launch, daemon=True).start()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle when the user submits the input."""
        input_widget = event.input
        if input_widget.id == "instance-input":
            version = input_widget.value.strip()
            if version:
                self.download_instance(version)
            input_widget.styles.display = "none"

    def download_instance(self, version: str) -> None:
        """Download a specific Minecraft version."""
        self.show_logs_section()  # Show the logs section to display launch logs
        logs_widget = self.query_one("#logs-widget", Log)
        logs_widget.clear()
        self.log_to_widget(f"Downloading instance for version: {version}")

        def enqueue_output(stream, q):
            """Read lines from a stream and put them in a queue."""
            for line in iter(stream.readline, ''):
                q.put(line.strip())
            stream.close()

        def run_subprocess():
            try:
                process = subprocess.Popen(
                    ["python", str(Path(__file__).parent / "download.py"), version],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True  # Ensure text output
                )

                # Queues to store stdout and stderr lines
                stdout_queue = queue.Queue()
                stderr_queue = queue.Queue()

                # Start threads to read stdout and stderr
                threading.Thread(target=enqueue_output, args=(process.stdout, stdout_queue), daemon=True).start()
                threading.Thread(target=enqueue_output, args=(process.stderr, stderr_queue), daemon=True).start()

                # Poll the process for output
                while True:
                    try:
                        stdout_line = stdout_queue.get_nowait()
                    except queue.Empty:
                        stdout_line = None

                    try:
                        stderr_line = stderr_queue.get_nowait()
                    except queue.Empty:
                        stderr_line = None

                    if stdout_line:
                        self.log_to_widget(stdout_line)
                    if stderr_line:
                        self.log_to_widget(f"{stderr_line}")

                    # Break the loop when the process finishes
                    if process.poll() is not None and stdout_queue.empty() and stderr_queue.empty():
                        break

                if process.returncode == 0:
                    self.log_to_widget(f"Version {version} downloaded successfully!")
                    self.call_from_thread(self.refresh_instances)
                else:
                    self.log_to_widget(f"Download failed with code {process.returncode}.")
            except Exception as e:
                self.log_to_widget(f"Failed to download version {version}: {e}")

        # Run the subprocess in a thread to avoid blocking the UI
        threading.Thread(target=run_subprocess, daemon=True).start()

    def refresh_instances(self) -> None:
        """Refresh the instances list by scanning the libraries directory."""
        APPDATA = os.getenv("APPDATA")
        BASE_PATH = Path(APPDATA) / "TuiCraft"
        LIBRARIES_PATH = BASE_PATH / "libraries"
        
        for folder in BASE_PATH.iterdir():
            if folder.is_dir() and "__" in folder.name:
                shutil.rmtree(folder, ignore_errors=True)
        instances_section = self.query_one("#instances-container", Vertical)
        instances_section.remove_children()

        if not LIBRARIES_PATH.exists():
            self.log_to_widget(f"Library path does not exist: {LIBRARIES_PATH}")
            return

        available_versions = [
            folder.name for folder in LIBRARIES_PATH.iterdir() if folder.is_dir()
        ]
        
        characters = string.ascii_letters + string.digits  # All letters (upper and lower case) and digits

        for version in available_versions:
            button = Button(version, id=f"instance-{version.replace('.', '_')}__{''.join(random.choices(characters, k=2))}")
            instances_section.mount(button)
            
        for button in self.query(Button):
            button.styles.background = "#0d0b09"
            button.styles.border = "none"
            button.styles.color = "white"
            button.styles.text_align = "left"
            button.styles.min_width = 0
        self.log_to_widget("Instances refreshed.")

    def on_mount(self) -> None:
        """Styling and initial setup."""
        header = self.query_one("#header")
        header.styles.text_align = "left"
        header.styles.color = "#eae4e0"
        header.styles.background = "#0d0b09"

        root = self.query_one("#root-container")
        root.styles.background = "#0d0b09"

        instances = self.query_one("#instances-container")
        instances.styles.width = "70%"
        instances.styles.height = "100%"
        instances.styles.border = ("round", "#ac9889")
        instances.border_title = "Instances"
        instances.styles.border_title_align = "left"

        settings = self.query_one("#settings-container")
        settings.styles.width = "30%"
        settings.styles.height = "100%"
        settings.styles.border = ("round", "#ac9889")
        settings.border_title = "Settings"
        settings.styles.border_title_align = "left"

        uinput = self.query_one("#instance-input")
        uinput.styles.border = ("round", "#ac9889")
        uinput.border_title = "New Instance"
        uinput.styles.background = "#0d0b09"

        logs_section = self.query_one("#logs-container")
        logs_section.styles.border = ("round", "#ac9889")
        logs_section.border_title = "Logs"
        logs_section.styles.background = "#0d0b09"
        logs_section.styles.height = "99%"

        log = self.query_one("#logs-widget")
        log.styles.background = "black"

        for button in self.query(Button):
            button.styles.background = "#0d0b09"
            button.styles.border = "none"
            button.styles.color = "white"
            button.styles.text_align = "left"
            button.styles.min_width = 0

if __name__ == "__main__":
    app = BorderTitleApp()
    app.run()
