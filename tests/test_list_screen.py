#!/usr/bin/env python3
"""
Test script for the list screen implementation.
"""

import logging
import sys
import tkinter as tk
import customtkinter as ctk
from pathlib import Path
from data_manager_enhanced import DataManager
from image_manager import ImageManager
from list_screen import ListScreen

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class TestApp:
    """Test application for the list screen."""
    
    def __init__(self):
        # Set appearance mode
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("List Screen Test")
        self.root.geometry("800x600")
        
        # Initialize managers
        self.data_manager = DataManager(use_database=True)
        self.image_manager = ImageManager()
        
        self.setup_ui()
        logger.info("Test app initialized")
    
    def setup_ui(self):
        """Setup test UI."""
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="List Screen Test Application",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=20)
        
        # Load CSV button
        load_btn = ctk.CTkButton(
            main_frame,
            text="Load Test CSV",
            command=self.load_test_csv,
            width=200,
            height=40
        )
        load_btn.pack(pady=10)
        
        # Open list view button
        self.list_btn = ctk.CTkButton(
            main_frame,
            text="📋 Open List View",
            command=self.open_list_view,
            width=200,
            height=40,
            state="disabled"
        )
        self.list_btn.pack(pady=10)
        
        # Status
        self.status_label = ctk.CTkLabel(main_frame, text="Ready to load CSV")
        self.status_label.pack(pady=20)
    
    def load_test_csv(self):
        """Load the test CSV file."""
        try:
            # Try the real CSV first, then fall back to full sample
            csv_files = [
                "tests/duplicates_report_20250910_210302.csv",
                "sample_data_full.csv"
            ]
            
            csv_path = None
            for path in csv_files:
                if Path(path).exists():
                    csv_path = path
                    break
            
            if not csv_path:
                self.status_label.configure(text="No test CSV file found")
                return
            
            logger.info(f"Loading CSV: {csv_path}")
            success = self.data_manager.load_csv(csv_path)
            
            if success:
                summary = self.data_manager.get_overall_summary()
                self.status_label.configure(
                    text=f"Loaded: {summary['total_groups']} groups, {summary['total_images']} images"
                )
                self.list_btn.configure(state="normal")
                logger.info("CSV loaded successfully")
            else:
                self.status_label.configure(text="Failed to load CSV")
                
        except Exception as e:
            logger.error(f"Error loading CSV: {e}", exc_info=True)
            self.status_label.configure(text=f"Error: {str(e)}")
    
    def open_list_view(self):
        """Open the list view."""
        try:
            list_screen = ListScreen(
                parent=self.root,
                data_manager=self.data_manager,
                image_manager=self.image_manager,
                main_app=self
            )
            list_screen.show()
            
        except Exception as e:
            logger.error(f"Error opening list view: {e}", exc_info=True)
    
    def run(self):
        """Run the test app."""
        self.root.mainloop()


def main():
    """Run the list screen test."""
    logger.info("Starting List Screen Test")
    
    try:
        app = TestApp()
        app.run()
        return 0
        
    except Exception as e:
        logger.error(f"Test failed: {e}", exc_info=True)
        return 1
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        return 1


if __name__ == '__main__':
    sys.exit(main())