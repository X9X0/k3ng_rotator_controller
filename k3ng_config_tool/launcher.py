#!/usr/bin/env python3
"""
K3NG Configuration Tool - Easy Launcher
Automatic setup, dependency management, and launcher
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def disable():
        """Disable colors on Windows if not supported"""
        if platform.system() == 'Windows':
            Colors.HEADER = ''
            Colors.OKBLUE = ''
            Colors.OKCYAN = ''
            Colors.OKGREEN = ''
            Colors.WARNING = ''
            Colors.FAIL = ''
            Colors.ENDC = ''
            Colors.BOLD = ''


class K3NGLauncher:
    """K3NG Configuration Tool Launcher"""

    def __init__(self):
        self.script_dir = Path(__file__).parent.absolute()
        self.venv_dir = self.script_dir / 'venv'
        self.system = platform.system()

        # Disable colors on Windows unless ANSICON is set
        if self.system == 'Windows' and 'ANSICON' not in os.environ:
            Colors.disable()

    def print_header(self):
        """Print welcome header"""
        print(f"{Colors.HEADER}{Colors.BOLD}")
        print("=" * 70)
        print("  K3NG Configuration & Testing Utility - Easy Launcher")
        print("=" * 70)
        print(f"{Colors.ENDC}")

    def print_step(self, step, message):
        """Print step message"""
        print(f"\n{Colors.OKCYAN}[{step}]{Colors.ENDC} {message}")

    def print_success(self, message):
        """Print success message"""
        print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

    def print_warning(self, message):
        """Print warning message"""
        print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

    def print_error(self, message):
        """Print error message"""
        print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

    def check_python_version(self):
        """Check if Python version is sufficient"""
        self.print_step("1/6", "Checking Python version...")

        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            self.print_error(f"Python 3.10+ required, found {version.major}.{version.minor}")
            print(f"\n{Colors.WARNING}Please install Python 3.10 or higher from:{Colors.ENDC}")
            print("  https://www.python.org/downloads/")
            sys.exit(1)

        self.print_success(f"Python {version.major}.{version.minor}.{version.micro} detected")

    def setup_venv(self):
        """Setup virtual environment if not exists"""
        self.print_step("2/6", "Setting up virtual environment...")

        if self.venv_dir.exists():
            self.print_success("Virtual environment already exists")
            return

        print(f"  Creating virtual environment at: {self.venv_dir}")
        try:
            subprocess.run(
                [sys.executable, '-m', 'venv', str(self.venv_dir)],
                check=True,
                capture_output=True
            )
            self.print_success("Virtual environment created")
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to create virtual environment: {e}")
            sys.exit(1)

    def get_venv_python(self):
        """Get path to virtual environment Python"""
        if self.system == 'Windows':
            return self.venv_dir / 'Scripts' / 'python.exe'
        else:
            return self.venv_dir / 'bin' / 'python'

    def get_venv_pip(self):
        """Get path to virtual environment pip"""
        if self.system == 'Windows':
            return self.venv_dir / 'Scripts' / 'pip.exe'
        else:
            return self.venv_dir / 'bin' / 'pip'

    def install_dependencies(self):
        """Install dependencies from requirements.txt"""
        self.print_step("3/6", "Checking dependencies...")

        requirements_file = self.script_dir / 'requirements.txt'
        if not requirements_file.exists():
            self.print_error("requirements.txt not found!")
            sys.exit(1)

        venv_pip = self.get_venv_pip()

        print("  Installing dependencies (this may take a few minutes)...")
        try:
            subprocess.run(
                [str(venv_pip), 'install', '-q', '-r', str(requirements_file)],
                check=True
            )
            self.print_success("All dependencies installed")
        except subprocess.CalledProcessError as e:
            self.print_error(f"Failed to install dependencies: {e}")
            sys.exit(1)

    def create_global_commands(self):
        """Create globally accessible commands"""
        self.print_step("4/6", "Creating global commands...")

        if self.system == 'Windows':
            self._create_windows_commands()
        else:
            self._create_unix_commands()

    def _create_windows_commands(self):
        """Create Windows batch files"""
        scripts_dir = self.venv_dir / 'Scripts'

        # k3ng-gui command
        gui_bat = scripts_dir / 'k3ng-gui.bat'
        gui_content = f'''@echo off
"{self.get_venv_python()}" "{self.script_dir / 'gui_main.py'}" %*
'''
        gui_bat.write_text(gui_content)

        # k3ng-cli command
        cli_bat = scripts_dir / 'k3ng-cli.bat'
        cli_content = f'''@echo off
"{self.get_venv_python()}" "{self.script_dir / 'main.py'}" %*
'''
        cli_bat.write_text(cli_content)

        # Add to PATH instructions
        scripts_path = str(scripts_dir)
        if scripts_path not in os.environ.get('PATH', ''):
            self.print_warning(f"Add to PATH for global access: {scripts_path}")
            print(f"  Run: setx PATH \"%PATH%;{scripts_path}\"")
        else:
            self.print_success("Commands available: k3ng-gui, k3ng-cli")

    def _create_unix_commands(self):
        """Create Unix shell scripts"""
        bin_dir = self.venv_dir / 'bin'

        # k3ng-gui command
        gui_script = bin_dir / 'k3ng-gui'
        gui_content = f'''#!/bin/bash
"{self.get_venv_python()}" "{self.script_dir / 'gui_main.py'}" "$@"
'''
        gui_script.write_text(gui_content)
        gui_script.chmod(0o755)

        # k3ng-cli command
        cli_script = bin_dir / 'k3ng-cli'
        cli_content = f'''#!/bin/bash
"{self.get_venv_python()}" "{self.script_dir / 'main.py'}" "$@"
'''
        cli_script.write_text(cli_content)
        cli_script.chmod(0o755)

        # Check if in PATH
        bin_path = str(bin_dir)
        path_env = os.environ.get('PATH', '')
        if bin_path not in path_env:
            self.print_warning(f"Add to PATH for global access: {bin_path}")
            shell = os.environ.get('SHELL', '/bin/bash')
            if 'bash' in shell:
                rc_file = Path.home() / '.bashrc'
            elif 'zsh' in shell:
                rc_file = Path.home() / '.zshrc'
            else:
                rc_file = Path.home() / '.profile'

            print(f"  Add to {rc_file}:")
            print(f'  export PATH="{bin_path}:$PATH"')
        else:
            self.print_success("Commands available: k3ng-gui, k3ng-cli")

    def create_desktop_shortcut(self):
        """Create desktop shortcut"""
        self.print_step("5/6", "Desktop shortcut creation...")

        response = input(f"{Colors.BOLD}Create desktop shortcut for GUI? (y/n): {Colors.ENDC}").lower()

        if response != 'y':
            print("  Skipped desktop shortcut creation")
            return

        if self.system == 'Windows':
            self._create_windows_shortcut()
        elif self.system == 'Darwin':  # macOS
            self._create_macos_shortcut()
        else:  # Linux
            self._create_linux_shortcut()

    def _create_windows_shortcut(self):
        """Create Windows desktop shortcut"""
        try:
            import winshell
            from win32com.client import Dispatch

            desktop = Path(winshell.desktop())
            shortcut_path = desktop / 'K3NG Configuration Tool.lnk'

            shell = Dispatch('WScript.Shell')
            shortcut = shell.CreateShortCut(str(shortcut_path))
            shortcut.Targetpath = str(self.get_venv_python())
            shortcut.Arguments = f'"{self.script_dir / "gui_main.py"}"'
            shortcut.WorkingDirectory = str(self.script_dir)
            shortcut.IconLocation = str(self.get_venv_python())
            shortcut.save()

            self.print_success(f"Desktop shortcut created: {shortcut_path}")
        except ImportError:
            self.print_warning("Install pywin32 for shortcut creation: pip install pywin32")
        except Exception as e:
            self.print_error(f"Failed to create shortcut: {e}")

    def _create_macos_shortcut(self):
        """Create macOS app bundle"""
        desktop = Path.home() / 'Desktop'
        app_dir = desktop / 'K3NG Configuration Tool.app'

        try:
            # Create app bundle structure
            contents = app_dir / 'Contents'
            macos = contents / 'MacOS'
            macos.mkdir(parents=True, exist_ok=True)

            # Create launcher script
            launcher = macos / 'k3ng-launcher'
            launcher_content = f'''#!/bin/bash
cd "{self.script_dir}"
"{self.get_venv_python()}" gui_main.py
'''
            launcher.write_text(launcher_content)
            launcher.chmod(0o755)

            # Create Info.plist
            info_plist = contents / 'Info.plist'
            plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>k3ng-launcher</string>
    <key>CFBundleName</key>
    <string>K3NG Configuration Tool</string>
    <key>CFBundleDisplayName</key>
    <string>K3NG Configuration Tool</string>
</dict>
</plist>
'''
            info_plist.write_text(plist_content)

            self.print_success(f"Desktop app created: {app_dir}")
        except Exception as e:
            self.print_error(f"Failed to create app bundle: {e}")

    def _create_linux_shortcut(self):
        """Create Linux desktop entry"""
        desktop = Path.home() / 'Desktop'
        desktop_file = desktop / 'k3ng-config-tool.desktop'

        try:
            content = f'''[Desktop Entry]
Version=1.0
Type=Application
Name=K3NG Configuration Tool
Comment=Configure and test K3NG rotator controller
Exec={self.get_venv_python()} {self.script_dir / "gui_main.py"}
Path={self.script_dir}
Terminal=false
Categories=Utility;Development;
'''
            desktop_file.write_text(content)
            desktop_file.chmod(0o755)

            self.print_success(f"Desktop shortcut created: {desktop_file}")
        except Exception as e:
            self.print_error(f"Failed to create desktop entry: {e}")

    def launch_menu(self):
        """Display launch menu"""
        self.print_step("6/6", "Ready to launch!")

        print(f"\n{Colors.BOLD}Choose an option:{Colors.ENDC}")
        print("  1. Launch GUI (Graphical Interface)")
        print("  2. Launch CLI (Command Line Interface)")
        print("  3. Exit")

        while True:
            choice = input(f"\n{Colors.BOLD}Enter choice (1-3): {Colors.ENDC}").strip()

            if choice == '1':
                self._launch_gui()
                break
            elif choice == '2':
                self._launch_cli()
                break
            elif choice == '3':
                print("\nGoodbye! Use 'k3ng-gui' or 'k3ng-cli' to launch later.")
                break
            else:
                self.print_warning("Invalid choice. Please enter 1, 2, or 3.")

    def _launch_gui(self):
        """Launch GUI application"""
        print(f"\n{Colors.OKGREEN}Launching K3NG Configuration Tool GUI...{Colors.ENDC}")
        venv_python = self.get_venv_python()
        gui_script = self.script_dir / 'gui_main.py'

        try:
            subprocess.run([str(venv_python), str(gui_script)])
        except KeyboardInterrupt:
            print("\n\nGUI closed.")
        except Exception as e:
            self.print_error(f"Failed to launch GUI: {e}")

    def _launch_cli(self):
        """Launch CLI application"""
        print(f"\n{Colors.OKGREEN}K3NG Configuration Tool CLI{Colors.ENDC}")
        print("Use 'k3ng-cli --help' for available commands")
        print()

        venv_python = self.get_venv_python()
        cli_script = self.script_dir / 'main.py'

        try:
            subprocess.run([str(venv_python), str(cli_script), '--help'])
        except Exception as e:
            self.print_error(f"Failed to launch CLI: {e}")

    def run(self):
        """Run the launcher"""
        try:
            self.print_header()
            self.check_python_version()
            self.setup_venv()
            self.install_dependencies()
            self.create_global_commands()
            self.create_desktop_shortcut()
            self.launch_menu()
        except KeyboardInterrupt:
            print(f"\n\n{Colors.WARNING}Setup interrupted by user.{Colors.ENDC}")
            sys.exit(1)
        except Exception as e:
            print(f"\n{Colors.FAIL}Unexpected error: {e}{Colors.ENDC}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


def main():
    """Main entry point"""
    launcher = K3NGLauncher()
    launcher.run()


if __name__ == '__main__':
    main()
