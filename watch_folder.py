#!/usr/bin/env python3

"""
Watch Folder Script for LocalSignTools
Automatically signs IPA files when they are added to a watch folder.
"""

import os
import sys
import time
import subprocess
import shutil
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

class WatchFolderSigner:
    def __init__(
        self,
        watch_folder: str,
        output_folder: str,
        profile: str,
        sign_args: str = "",
        bundle_id: Optional[str] = None,
        processed_folder: Optional[str] = None,
        failed_folder: Optional[str] = None,
        log_file: Optional[str] = None,
        poll_interval: float = 2.0,
        sign_tools_path: Optional[str] = None,
    ):
        self.watch_folder = Path(watch_folder).expanduser().resolve()
        self.output_folder = Path(output_folder).expanduser().resolve()
        self.profile = profile
        self.sign_args = sign_args
        self.bundle_id = bundle_id
        self.processed_folder = Path(processed_folder).expanduser().resolve() if processed_folder else None
        self.failed_folder = Path(failed_folder).expanduser().resolve() if failed_folder else None
        self.log_file = Path(log_file).expanduser().resolve() if log_file else None
        self.poll_interval = poll_interval
        self.sign_tools_path = Path(sign_tools_path).expanduser().resolve() if sign_tools_path else None
        
        # Track processed files to avoid reprocessing
        self.processed_files = set()
        
        # Ensure directories exist
        self.watch_folder.mkdir(parents=True, exist_ok=True)
        self.output_folder.mkdir(parents=True, exist_ok=True)
        if self.processed_folder:
            self.processed_folder.mkdir(parents=True, exist_ok=True)
        if self.failed_folder:
            self.failed_folder.mkdir(parents=True, exist_ok=True)
    
    def log(self, message: str, level: str = "INFO"):
        """Log a message to console and optionally to a file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{level}] {message}"
        print(log_message)
        
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(log_message + "\n")
            except Exception as e:
                print(f"Failed to write to log file: {e}")
    
    def find_sign_tools(self) -> Optional[Path]:
        """Find the SignTools executable."""
        # Try explicitly set path first (from config or argument)
        if self.sign_tools_path:
            if self.sign_tools_path.exists() and os.access(self.sign_tools_path, os.X_OK):
                return self.sign_tools_path
            else:
                self.log(f"Warning: Specified SignTools path does not exist or is not executable: {self.sign_tools_path}", "WARN")
        
        # Try environment variable
        if os.environ.get("SIGNTOOLS_PATH"):
            sign_tools_path = Path(os.environ["SIGNTOOLS_PATH"]).expanduser().resolve()
            if sign_tools_path.exists() and os.access(sign_tools_path, os.X_OK):
                return sign_tools_path
            else:
                self.log(f"Warning: SIGNTOOLS_PATH environment variable points to invalid path: {sign_tools_path}", "WARN")
        
        # Try relative to script directory
        script_dir = Path(__file__).parent.resolve()
        candidates = [
            script_dir / "SignTools",
            script_dir / "SignTools.app" / "Contents" / "MacOS" / "SignTools.bin",
            script_dir / "SignTools.app" / "Contents" / "MacOS" / "SignTools",
        ]
        
        for candidate in candidates:
            if candidate.exists() and os.access(candidate, os.X_OK):
                return candidate
        
        # Try parent directory (project root) if script is in a subdirectory
        parent_dir = script_dir.parent
        candidates = [
            parent_dir / "SignTools",
            parent_dir / "SignTools.app" / "Contents" / "MacOS" / "SignTools.bin",
            parent_dir / "SignTools.app" / "Contents" / "MacOS" / "SignTools",
        ]
        
        for candidate in candidates:
            if candidate.exists() and os.access(candidate, os.X_OK):
                return candidate
        
        # Try searching up the directory tree for project root (look for signer-cfg.yml or go.mod)
        current = script_dir
        for _ in range(5):  # Search up to 5 levels
            candidates = [
                current / "SignTools",
                current / "SignTools.app" / "Contents" / "MacOS" / "SignTools.bin",
                current / "SignTools.app" / "Contents" / "MacOS" / "SignTools",
            ]
            # Check if this looks like the project root (has signer-cfg.yml or go.mod)
            if (current / "signer-cfg.yml").exists() or (current / "go.mod").exists():
                for candidate in candidates:
                    if candidate.exists() and os.access(candidate, os.X_OK):
                        return candidate
            current = current.parent
        
        # Try in PATH
        which_result = shutil.which("SignTools")
        if which_result:
            return Path(which_result)
        
        # Try in current working directory
        cwd = Path.cwd()
        candidates = [
            cwd / "SignTools",
            cwd / "SignTools.app" / "Contents" / "MacOS" / "SignTools.bin",
            cwd / "SignTools.app" / "Contents" / "MacOS" / "SignTools",
        ]
        
        for candidate in candidates:
            if candidate.exists() and os.access(candidate, os.X_OK):
                return candidate
        
        return None
    
    def sign_ipa(self, ipa_path: Path) -> bool:
        """Sign an IPA file using the CLI mode."""
        # Resolve to absolute path for consistency
        abs_ipa_path = ipa_path.resolve()
        
        if abs_ipa_path in self.processed_files:
            return False
        
        self.log(f"Processing: {ipa_path.name}")
        self.processed_files.add(abs_ipa_path)
        
        # Generate output filename (use resolved path for consistency)
        output_name = abs_ipa_path.stem + "_signed.ipa"
        output_path = self.output_folder / output_name
        
        # Find SignTools executable
        sign_tools = self.find_sign_tools()
        if not sign_tools:
            self.log(f"Error: SignTools executable not found", "ERROR")
            self.log("Searched in:", "ERROR")
            self.log("  1. Explicitly specified path (config/argument)", "ERROR")
            self.log("  2. SIGNTOOLS_PATH environment variable", "ERROR")
            self.log("  3. Script directory", "ERROR")
            self.log("  4. Parent directory (project root)", "ERROR")
            self.log("  5. Project root (detected by signer-cfg.yml or go.mod)", "ERROR")
            self.log("  6. PATH environment variable", "ERROR")
            self.log("  7. Current working directory", "ERROR")
            self.log("", "ERROR")
            self.log("Please specify the path using one of the following methods:", "ERROR")
            self.log("  - Set SIGNTOOLS_PATH environment variable", "ERROR")
            self.log("  - Add 'sign_tools_path' to config file", "ERROR")
            self.log("  - Use --sign-tools-path argument", "ERROR")
            # Move to failed folder if specified, otherwise remove from processed_files
            if self.failed_folder:
                self.move_file(abs_ipa_path, self.failed_folder)
            else:
                self.processed_files.discard(abs_ipa_path)
            return False
        
        # Build command
        cmd = [
            str(sign_tools),
            "-headless",
            "-ipa", str(abs_ipa_path),
            "-profile", self.profile,
            "-output", str(output_path),
        ]
        
        if self.sign_args:
            cmd.extend(["-args", self.sign_args])
        
        if self.bundle_id:
            cmd.extend(["-bundle-id", self.bundle_id])
        
        # Execute signing
        try:
            self.log(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=1800,  # 30 minutes timeout
            )
            
            if result.returncode == 0:
                self.log(f"Successfully signed: {output_path.name}")
                # Move to processed folder if specified
                if self.processed_folder:
                    self.move_file(abs_ipa_path, self.processed_folder)
                else:
                    # If no processed folder, just remove from processed_files
                    # File remains in watch folder but won't be reprocessed
                    self.processed_files.discard(abs_ipa_path)
                return True
            else:
                self.log(f"Signing failed for {ipa_path.name}: {result.stderr}", "ERROR")
                self.log(f"Output: {result.stdout}", "ERROR")
                # Move to failed folder if specified, otherwise remove from processed_files
                if self.failed_folder:
                    self.move_file(abs_ipa_path, self.failed_folder)
                else:
                    self.processed_files.discard(abs_ipa_path)
                return False
                
        except subprocess.TimeoutExpired:
            self.log(f"Signing timed out for {ipa_path.name}", "ERROR")
            # Move to failed folder if specified, otherwise remove from processed_files
            if self.failed_folder:
                self.move_file(abs_ipa_path, self.failed_folder)
            else:
                self.processed_files.discard(abs_ipa_path)
            return False
        except Exception as e:
            self.log(f"Error signing {ipa_path.name}: {e}", "ERROR")
            # Move to failed folder if specified, otherwise remove from processed_files
            if self.failed_folder:
                self.move_file(abs_ipa_path, self.failed_folder)
            else:
                self.processed_files.discard(abs_ipa_path)
            return False
    
    def move_file(self, file_path: Path, dest_folder: Optional[Path]) -> bool:
        """Move a file to a destination folder, or delete if dest_folder is None.
        Returns True if file was moved/deleted successfully, False otherwise.
        Note: file_path should already be resolved to absolute path."""
        if not dest_folder:
            # If no destination folder specified, file remains in watch folder
            # Remove from processed_files so it can be retried
            abs_file_path = file_path.resolve()
            self.processed_files.discard(abs_file_path)
            return True
        
        # Ensure destination folder exists
        try:
            dest_folder.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            self.log(f"Failed to create destination folder {dest_folder}: {e}", "ERROR")
            return False
        
        try:
            # Resolve file path to absolute path before moving (if not already resolved)
            abs_file_path = file_path.resolve()
            
            # Check if file still exists
            if not abs_file_path.exists():
                self.log(f"File no longer exists: {abs_file_path.name}", "WARN")
                self.processed_files.discard(abs_file_path)
                return True
            
            dest_path = dest_folder / abs_file_path.name
            # If file exists, add timestamp
            if dest_path.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = dest_folder / f"{abs_file_path.stem}_{timestamp}{abs_file_path.suffix}"
            
            shutil.move(str(abs_file_path), str(dest_path))
            self.log(f"Moved {abs_file_path.name} to {dest_folder}")
            # Remove from processed_files after successful move
            self.processed_files.discard(abs_file_path)
            return True
        except FileNotFoundError:
            abs_file_path = file_path.resolve()
            self.log(f"File not found (may have been deleted): {abs_file_path.name}", "WARN")
            self.processed_files.discard(abs_file_path)
            return True
        except Exception as e:
            abs_file_path = file_path.resolve()
            self.log(f"Failed to move {abs_file_path.name}: {e}", "ERROR")
            # If move failed, remove from processed_files so it can be retried
            self.processed_files.discard(abs_file_path)
            return False
    
    def scan_and_process(self):
        """Scan the watch folder for new IPA files and process them."""
        if not self.watch_folder.exists():
            self.log(f"Watch folder does not exist: {self.watch_folder}", "ERROR")
            return
        
        # Find all .ipa files in the watch folder and resolve to absolute paths
        ipa_files = [f.resolve() for f in self.watch_folder.glob("*.ipa") if f.is_file()]
        
        # Filter out already processed files and files that are still being written
        for ipa_file in ipa_files:
            # Skip if already processed
            if ipa_file in self.processed_files:
                continue
            
            # Check if file is still being written (wait a bit for file to stabilize)
            try:
                file_size_before = ipa_file.stat().st_size
                time.sleep(0.5)
                file_size_after = ipa_file.stat().st_size
                
                if file_size_before != file_size_after:
                    # File is still being written, skip for now
                    continue
            except (OSError, FileNotFoundError):
                # File may have been deleted or moved, skip
                continue
            
            # Process the file
            self.sign_ipa(ipa_file)
    
    def run(self):
        """Start watching the folder."""
        # Verify SignTools is found at startup
        sign_tools = self.find_sign_tools()
        if not sign_tools:
            self.log("Error: SignTools executable not found at startup", "ERROR")
            self.log("Searched in:", "ERROR")
            self.log("  1. Explicitly specified path (config/argument)", "ERROR")
            self.log("  2. SIGNTOOLS_PATH environment variable", "ERROR")
            self.log("  3. Script directory", "ERROR")
            self.log("  4. Parent directory (project root)", "ERROR")
            self.log("  5. Project root (detected by signer-cfg.yml or go.mod)", "ERROR")
            self.log("  6. PATH environment variable", "ERROR")
            self.log("  7. Current working directory", "ERROR")
            self.log("", "ERROR")
            self.log("Please specify the path using one of the following methods:", "ERROR")
            self.log("  - Set SIGNTOOLS_PATH environment variable", "ERROR")
            self.log("  - Add 'sign_tools_path' to config file", "ERROR")
            self.log("  - Use --sign-tools-path argument", "ERROR")
            raise RuntimeError("SignTools executable not found")
        
        self.log(f"Starting Watch Folder Signer")
        self.log(f"SignTools: {sign_tools}")
        self.log(f"Watch folder: {self.watch_folder}")
        self.log(f"Output folder: {self.output_folder}")
        self.log(f"Profile: {self.profile}")
        self.log(f"Sign args: {self.sign_args or '(none)'}")
        self.log(f"Poll interval: {self.poll_interval} seconds")
        self.log("Press Ctrl+C to stop")
        self.log("")
        
        try:
            while True:
                self.scan_and_process()
                time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            self.log("Stopped by user")
        except Exception as e:
            self.log(f"Unexpected error: {e}", "ERROR")
            raise


def load_config(config_file: str) -> Dict:
    """Load configuration from a JSON file."""
    config_path = Path(config_file).expanduser().resolve()
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading config file: {e}")
        return {}


def main():
    parser = argparse.ArgumentParser(
        description="Watch Folder Script for LocalSignTools - Automatically signs IPA files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  %(prog)s -w ~/Desktop/WatchFolder -o ~/Desktop/Signed -p developer_account
  
  # With signing arguments
  %(prog)s -w ~/WatchFolder -o ~/Signed -p developer_account -a "-a -d"
  
  # With configuration file
  %(prog)s -c watch_config.json
        """
    )
    
    parser.add_argument(
        "-w", "--watch-folder",
        help="Folder to watch for IPA files (required)"
    )
    parser.add_argument(
        "-o", "--output-folder",
        help="Folder to save signed IPA files (required)"
    )
    parser.add_argument(
        "-p", "--profile",
        help="Profile name from data/profiles/ (required)"
    )
    parser.add_argument(
        "-a", "--args",
        default="",
        help="Signing arguments (e.g., '-a -d -m')"
    )
    parser.add_argument(
        "-b", "--bundle-id",
        help="Custom bundle ID (optional)"
    )
    parser.add_argument(
        "--processed-folder",
        help="Folder to move processed IPA files (optional, files are deleted if not specified)"
    )
    parser.add_argument(
        "--failed-folder",
        help="Folder to move failed IPA files (optional)"
    )
    parser.add_argument(
        "-l", "--log-file",
        help="Log file path (optional)"
    )
    parser.add_argument(
        "-i", "--poll-interval",
        type=float,
        default=2.0,
        help="Polling interval in seconds (default: 2.0)"
    )
    parser.add_argument(
        "-c", "--config",
        help="Configuration file (JSON format, overrides command line arguments)"
    )
    parser.add_argument(
        "--sign-tools-path",
        help="Path to SignTools executable (optional, auto-detected if not specified)"
    )
    
    args = parser.parse_args()
    
    # Load config file if provided
    config = {}
    if args.config:
        config = load_config(args.config)
    
    # Use config file values as defaults, command line args override
    watch_folder = args.watch_folder or config.get("watch_folder")
    output_folder = args.output_folder or config.get("output_folder")
    profile = args.profile or config.get("profile")
    sign_args = args.args or config.get("sign_args", "")
    bundle_id = args.bundle_id or config.get("bundle_id")
    processed_folder = args.processed_folder or config.get("processed_folder")
    failed_folder = args.failed_folder or config.get("failed_folder")
    log_file = args.log_file or config.get("log_file")
    poll_interval = args.poll_interval or config.get("poll_interval", 2.0)
    sign_tools_path = args.sign_tools_path or config.get("sign_tools_path")
    
    # Validate required arguments
    if not watch_folder or not output_folder or not profile:
        parser.error("watch_folder, output_folder, and profile are required (use -w, -o, -p or -c config file)")
    
    # Create and run the watch folder signer
    signer = WatchFolderSigner(
        watch_folder=watch_folder,
        output_folder=output_folder,
        profile=profile,
        sign_args=sign_args,
        bundle_id=bundle_id,
        processed_folder=processed_folder,
        failed_folder=failed_folder,
        log_file=log_file,
        poll_interval=poll_interval,
        sign_tools_path=sign_tools_path,
    )
    
    signer.run()


if __name__ == "__main__":
    main()
