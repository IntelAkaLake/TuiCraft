from textual.app import App, ComposeResult
from textual.widgets import Button, Static, Input
from textual.containers import Horizontal, Vertical
import os
import subprocess
from pathlib import Path

class BorderTitleApp(App[None]):

    # Hide input version
    CSS = """
    #instance-input {
        display: none;
    }
    """

    def __init__(self):
        super().__init__()
        self.instance_input_visible = False

    def compose(self) -> ComposeResult:
        header = Static(
            r"""
  _____     _  ___           __ _   
 |_   _|  _(_)/ __|_ _ __ _ / _| |_ 
   | || || | | (__| '_/ _` |  _|  _|
   |_| \_,_|_|\___|_| \__,_|_|  \__|
                                    
            """,
            id="header")
        yield header

        APPDATA = os.getenv("APPDATA")
        BASE_PATH = Path(APPDATA) / "TuiCraft"
        LIBRARIES_PATH = BASE_PATH / "libraries"

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

    def on_key(self, event) -> None:
        """Handle key presses."""
        if event.key == "r":
            self.refresh_instances()
            self.log("Ctrl+R detected: Instances refreshed.")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id.startswith("instance-"):
            version = button_id.replace("instance-", "").replace("_", ".")  # Extract version
            self.launch_instance(version)
        elif button_id == "setting-instance":
            self.show_instance_input()
        elif button_id == "setting-about":
            self.log("Selected setting: About")

    def launch_instance(self, version: str) -> None:
        """Launch a Minecraft instance."""
        self.log(f"Launching version: {version}")
        launch_script = Path(__file__).parent / "launch.py"

        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        try:
            subprocess.Popen(
                ["cmd", "/K", "python", str(launch_script), version],
                startupinfo=startupinfo,
                creationflags=subprocess.CREATE_NEW_CONSOLE,  # Launch in a new terminal window
            )
        except Exception as e:
            self.log(f"Failed to launch instance {version}: {e}")

    def show_instance_input(self) -> None:
        """Show the Input widget for new instance."""
        input_widget = self.query_one("#instance-input", Input)
        input_widget.styles.display = "block"
        input_widget.focus()
        self.instance_input_visible = True

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle when the user submits the input."""
        input_widget = event.input
        if input_widget.id == "instance-input":
            version = input_widget.value.strip()
            if version:
                download_script = Path(__file__).parent / "download.py"
                try:
                    subprocess.Popen(
                    ["cmd", "/K", "python", str(download_script), version],
                    creationflags=subprocess.CREATE_NEW_CONSOLE,  # Launch in a new terminal window
                    )
                except Exception as e:
                    self.log(f"Failed to launch instance {version}: {e}")
            input_widget.styles.display = "none"
            self.instance_input_visible = False

    def refresh_instances(self) -> None:
        """Refresh the instances list by scanning the libraries directory."""
        """I Tried everything to get this work but it doesnt. Ditching."""

        # Paths
        APPDATA = os.getenv("APPDATA")
        BASE_PATH = Path(APPDATA) / "TuiCraft"
        LIBRARIES_PATH = BASE_PATH / "libraries"

        # Find the container for instances
        instances_section = self.query_one("#instances-container", Vertical)

        # Remove all existing buttons
        instances_section.remove_children()

        # Check if LIBRARIES_PATH exists
        if not LIBRARIES_PATH.exists():
            self.log(f"Library path does not exist: {LIBRARIES_PATH}")
            return

        # Rescan the libraries directory for available versions
        available_versions = [
            folder.name for folder in LIBRARIES_PATH.iterdir() if folder.is_dir()
        ]

        # Create and add buttons for the available versions
        for version in available_versions:
            button = Button(version, id=f"instance-{version.replace('.', '_')}_new")
            instances_section.mount(button)

        self.log("Instances refreshed.")


    def on_mount(self) -> None:
        """Styling"""
        
        # Styling for the header
        header = self.query_one("#header")
        header.styles.text_align = "left"
        header.styles.color = "#eae4e0"
        header.styles.font_size = "large"
        header.styles.background = "#0d0b09"

        # Set background for the whole app
        # Maybe doesnt work IDK
        root = self.query_one("#root-container")
        root.styles.background = "#0d0b09"

        # Styling for Instances Section
        instances = self.query_one("#instances-container")
        instances.styles.width = "70%"
        instances.styles.height = "100%"
        instances.styles.border = ("round", "#ac9889")
        instances.border_title = "Instances"
        instances.styles.border_title_align = "left"

        # Styling for Settings Section
        settings = self.query_one("#settings-container")
        settings.styles.width = "30%"
        settings.styles.height = "100%"
        settings.styles.border = ("round", "#ac9889")
        settings.border_title = "Settings"
        settings.styles.border_title_align = "left"

        # Styling for the instance Input
        uinput = self.query_one("#instance-input")
        uinput.styles.border = ("round", "#ac9889")
        uinput.border_title = "New Instance"
        uinput.styles.background = "#0d0b09"

        uinput.styles.focused_background = "#0d0b09"

        # Styling for Buttons
        for button in self.query(Button):
            button.styles.background = "#0d0b09"
            button.styles.border = "none"
            button.styles.color = "white"
            button.styles.text_align = "left"
            button.styles.min_width = 0

            # IDK if this does anything
            button.styles.focused_color = "#0d0b09"
            button.styles.focused_border = "none"

# Add/Needs implementation for Linux
def win_cfolder():
    """Makes the TuiCraft folder in %AppData"""
    appdata_path = os.getenv("APPDATA")
    if appdata_path is None:
        raise EnvironmentError("Could not locate the AppData directory.")
    new_folder_path = os.path.join(appdata_path, "TuiCraft")
    if not os.path.exists(new_folder_path):
        os.makedirs(new_folder_path)
    return new_folder_path

if __name__ == "__main__":
    app = BorderTitleApp()
    win_cfolder()
    app.run()
