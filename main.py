import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import logging
from pathlib import Path
from data_manager_enhanced import DataManager
from image_manager import ImageManager, ImageWidget, ImageViewerWindow
from list_screen import ListScreen

# Configure enhanced logging
def setup_logging():
    """Setup comprehensive logging configuration."""
    # Create logs directory if it doesn't exist
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'lineup_debug.log'),
            logging.FileHandler(log_dir / 'lineup_info.log', mode='w'),
            logging.StreamHandler()
        ]
    )
    
    # Set different levels for different handlers
    handlers = logging.getLogger().handlers
    if len(handlers) >= 3:
        handlers[0].setLevel(logging.DEBUG)    # Debug log file
        handlers[1].setLevel(logging.INFO)     # Info log file  
        handlers[2].setLevel(logging.WARNING)  # Console (warnings and errors only)
    
    # Create application logger
    app_logger = logging.getLogger('lineup')
    app_logger.setLevel(logging.DEBUG)
    
    return app_logger

# Setup logging
logger = setup_logging()

class LineupApp:
    def __init__(self):
        # Set appearance mode and color theme
        ctk.set_appearance_mode("system")  # Modes: system, light, dark
        ctk.set_default_color_theme("blue")  # Themes: blue, green, dark-blue
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Lineup - Photo Duplicate Manager")
        self.root.geometry("1200x800")
        self.root.minsize(800, 600)
        
        # Initialize data
        self.data_manager = DataManager()
        self.image_manager = ImageManager()
        self.current_csv_file = None  # Track current CSV file for reload
        self.current_database_file = None  # Track current database file
        self.current_group = None
        self.selected_images = set()
        self.image_widgets = []
        self.move_to_directory = None
        self.active_image_viewers = []  # Track open image viewers
        self.group_buttons = {}  # Track group buttons for visual feedback
        self.auto_select_enabled = True  # Auto-select non-masters by default
        self.hide_single_groups = True  # Hide groups with 1 or fewer images
        
        self.setup_ui()
        logger.info("Lineup application initialized successfully")
        logger.debug(f"Window geometry: {self.root.geometry()}")
        logger.debug(f"Appearance mode: system, Color theme: blue")
    
    def setup_ui(self):
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top toolbar
        self.toolbar = ctk.CTkFrame(self.main_frame)
        self.toolbar.pack(fill="x", padx=5, pady=5)
        
        # Load CSV button
        self.load_btn = ctk.CTkButton(
            self.toolbar,
            text="Load CSV File",
            command=self.load_csv_file,
            width=120
        )
        self.load_btn.pack(side="left", padx=5)
        
        # Database menu
        self.database_menu = ctk.CTkOptionMenu(
            self.toolbar,
            values=["Load Database...", "Browse for Database..."],
            command=self.handle_database_selection,
            width=140
        )
        self.database_menu.pack(side="left", padx=5)
        self.database_menu.set("Load Database...")

        # Initialize recent databases
        self.recent_databases = []
        self.load_recent_databases()

        # Reload button
        self.reload_btn = ctk.CTkButton(
            self.toolbar,
            text="Reload",
            command=self.reload_csv_file,
            width=80,
            state="disabled"
        )
        self.reload_btn.pack(side="left", padx=5)
        
        # Views dropdown menu
        self.views_menu = ctk.CTkOptionMenu(
            self.toolbar,
            values=["Select View...", "📋 List View", "📊 Statistics", "🔍 Search"],
            command=self.handle_view_selection,
            width=120,
            state="disabled"
        )
        self.views_menu.pack(side="left", padx=5)
        self.views_menu.set("Select View...")
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.toolbar,
            text="No CSV file loaded"
        )
        self.status_label.pack(side="left", padx=20)
        
        # Operation status label
        self.operation_status_label = ctk.CTkLabel(
            self.toolbar,
            text="",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="green"
        )
        self.operation_status_label.pack(side="left", padx=10)
        
        # Move To directory selector
        self.moveto_frame = ctk.CTkFrame(self.toolbar)
        self.moveto_frame.pack(side="right", padx=5)
        
        # Move To label
        self.moveto_label = ctk.CTkLabel(
            self.moveto_frame,
            text="Move To:",
            font=ctk.CTkFont(size=12)
        )
        self.moveto_label.pack(side="left", padx=(5, 0))
        
        # Selected directory display
        self.moveto_display = ctk.CTkLabel(
            self.moveto_frame,
            text="No directory selected",
            font=ctk.CTkFont(size=10),
            text_color="gray",
            width=200
        )
        self.moveto_display.pack(side="left", padx=5)
        
        # Browse button for Move To directory
        self.moveto_btn = ctk.CTkButton(
            self.moveto_frame,
            text="Browse...",
            command=self.select_move_directory,
            width=80
        )
        self.moveto_btn.pack(side="left", padx=5)
        
        # Clear button for Move To directory
        self.moveto_clear_btn = ctk.CTkButton(
            self.moveto_frame,
            text="Clear",
            command=self.clear_move_directory,
            width=60
        )
        self.moveto_clear_btn.pack(side="left", padx=(0, 5))
        
        # Group navigation buttons
        self.nav_frame = ctk.CTkFrame(self.toolbar)
        self.nav_frame.pack(side="left", padx=20)
        
        self.prev_group_btn = ctk.CTkButton(
            self.nav_frame,
            text="◀ Previous Group (P)",
            command=self.go_to_previous_group,
            width=130,
            state="disabled"
        )
        self.prev_group_btn.pack(side="left", padx=2)
        
        self.next_group_btn = ctk.CTkButton(
            self.nav_frame,
            text="Next Group ▶ (N)",
            command=self.go_to_next_group,
            width=130,
            state="disabled"
        )
        self.next_group_btn.pack(side="left", padx=2)
        
        # Hide single groups toggle
        self.hide_single_switch = ctk.CTkSwitch(
            self.toolbar,
            text="Hide Single Groups",
            command=self.toggle_hide_single_groups
        )
        self.hide_single_switch.pack(side="right", padx=5)
        self.hide_single_switch.select()  # Default to enabled
        
        # Auto-select toggle
        self.auto_select_switch = ctk.CTkSwitch(
            self.toolbar,
            text="Auto-select Duplicates",
            command=self.toggle_auto_select
        )
        self.auto_select_switch.pack(side="right", padx=5)
        self.auto_select_switch.select()  # Default to enabled
        
        # Dark mode toggle
        self.dark_mode_switch = ctk.CTkSwitch(
            self.toolbar,
            text="Dark Mode",
            command=self.toggle_dark_mode
        )
        self.dark_mode_switch.pack(side="right", padx=5)
        
        # Main content area (will be populated when CSV is loaded)
        self.content_frame = ctk.CTkFrame(self.main_frame)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Welcome message
        self.welcome_label = ctk.CTkLabel(
            self.content_frame,
            text="Welcome to Lineup\n\nLoad a CSV file to begin managing your photo duplicates",
            font=ctk.CTkFont(size=16)
        )
        self.welcome_label.pack(expand=True)
    
    def load_csv_file(self):
        logger.debug("Opening CSV file selection dialog")
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                logger.info(f"Loading CSV file: {file_path}")
                logger.debug(f"File size: {Path(file_path).stat().st_size} bytes")
                
                # Load data using DataManager
                if self.data_manager.load_csv(file_path):
                    self.current_csv_file = file_path  # Store for reload functionality
                    summary = self.data_manager.get_overall_summary()
                    
                    # Update status
                    status_text = f"Loaded: {Path(file_path).name} ({summary['total_groups']} groups, {summary['total_images']} images)"
                    self.status_label.configure(text=status_text)
                    
                    # Enable reload and list view buttons
                    self.reload_btn.configure(state="normal")
                    self.views_menu.configure(state="normal")
                    
                    logger.info(f"CSV loaded successfully: {summary['total_groups']} groups, {summary['total_images']} images, {summary['missing_images']} missing")
                    logger.debug(f"Summary: {summary}")
                    
                    # Update UI
                    self.setup_content_ui()
                    
                    # Show warning if there are missing files
                    if summary['missing_images'] > 0:
                        logger.warning(f"Found {summary['missing_images']} missing image files")
                        messagebox.showwarning(
                            "Missing Files",
                            f"Warning: {summary['missing_images']} image files could not be found.\n"
                            f"These will be marked as unavailable."
                        )
                
            except Exception as e:
                logger.error(f"Error loading CSV file: {e}", exc_info=True)
                messagebox.showerror("Error", f"Failed to load CSV file:\n{str(e)}")
        else:
            logger.debug("CSV file selection cancelled by user")
    
    def reload_csv_file(self):
        """Reload the currently loaded CSV file and refresh all screens."""
        if not self.current_csv_file:
            logger.warning("No CSV file to reload")
            messagebox.showwarning("No File", "No CSV file is currently loaded to reload.")
            return
        
        try:
            logger.info(f"Reloading CSV file: {self.current_csv_file}")
            
            # Check if file still exists
            if not Path(self.current_csv_file).exists():
                logger.error(f"CSV file no longer exists: {self.current_csv_file}")
                messagebox.showerror("File Not Found", f"The CSV file no longer exists:\n{self.current_csv_file}")
                return
            
            # Store current group for restoration if possible
            previous_group = self.current_group
            
            # Close any active image viewers
            for viewer in self.active_image_viewers.copy():
                if hasattr(viewer, 'window') and viewer.window.winfo_exists():
                    viewer.close()
            self.active_image_viewers.clear()
            
            # Reload data using DataManager
            if self.data_manager.load_csv(self.current_csv_file):
                summary = self.data_manager.get_overall_summary()
                
                # Update status
                status_text = f"Reloaded: {Path(self.current_csv_file).name} ({summary['total_groups']} groups, {summary['total_images']} images)"
                self.status_label.configure(text=status_text)
                
                logger.info(f"CSV reloaded successfully: {summary['total_groups']} groups, {summary['total_images']} images, {summary['missing_images']} missing")
                
                # Update UI
                self.setup_content_ui()
                
                # Try to restore previous group selection if it still exists
                if previous_group and previous_group in self.data_manager.get_group_list():
                    # Check if group should be displayed with current filters
                    group_summary = self.data_manager.get_group_summary(previous_group)
                    if not (self.hide_single_groups and group_summary['existing_images'] <= 1):
                        self.select_group(previous_group)
                        logger.debug(f"Restored selection to group {previous_group}")
                    else:
                        logger.debug(f"Previous group {previous_group} now hidden by filters")
                
                # Show operation status
                self.show_operation_status("CSV file reloaded successfully", "green")
                
                # Show warning if there are missing files
                if summary['missing_images'] > 0:
                    logger.warning(f"Found {summary['missing_images']} missing image files after reload")
                    messagebox.showwarning(
                        "Missing Files",
                        f"Warning: {summary['missing_images']} image files could not be found.\n"
                        f"These will be marked as unavailable."
                    )
            else:
                logger.error(f"Failed to reload CSV file: {self.current_csv_file}")
                messagebox.showerror("Reload Error", f"Failed to reload the CSV file:\n{self.current_csv_file}")
                
        except Exception as e:
            logger.error(f"Error reloading CSV file: {e}", exc_info=True)
            messagebox.showerror("Reload Error", f"Failed to reload CSV file:\n{str(e)}")

    def load_database_file(self):
        """Load a previously created database file to resume work."""
        from tkinter import filedialog

        try:
            logger.info("User requested to load database file")

            # Select database file
            db_file = filedialog.askopenfilename(
                title="Select Lineup Database",
                filetypes=[
                    ("Lineup Database", "*.db"),
                    ("SQLite Database", "*.sqlite"),
                    ("All files", "*.*")
                ],
                defaultextension=".db"
            )

            if db_file:
                logger.info(f"Loading database file: {db_file}")

                # Close any active image viewers
                for viewer in self.active_image_viewers.copy():
                    if hasattr(viewer, 'window') and viewer.window.winfo_exists():
                        viewer.close()
                self.active_image_viewers.clear()

                # Clear current data
                self.clear_current_data()

                # Initialize data manager with the selected database
                self.data_manager = DataManager(use_database=True)

                # Update the database manager to use the selected file
                if self.data_manager.db_manager:
                    # Disconnect from current database
                    self.data_manager.db_manager.disconnect()

                    # Update database path and reconnect
                    self.data_manager.db_manager.db_path = Path(db_file)
                    self.data_manager.db_manager.connect()

                    # Update legacy attributes for backward compatibility
                    self.data_manager._update_legacy_attributes()

                    # Check if database has data
                    if self.data_manager.has_data():
                        # Get database summary
                        summary = self.data_manager.get_overall_summary()

                        # Update UI state
                        self.current_csv_file = None  # No CSV file, using database
                        self.current_database_file = db_file

                        # Add to recent databases
                        self.add_to_recent_databases(db_file)

                        # Enable controls
                        self.views_menu.configure(state="normal")
                        self.auto_select_switch.configure(state="normal")
                        self.hide_single_switch.configure(state="normal")

                        # Update status
                        self.status_label.configure(
                            text=f"Database: {Path(db_file).name} - {summary.get('total_groups', 0)} groups, "
                                 f"{summary.get('total_images', 0)} images"
                        )

                        # Load first group
                        groups = self.data_manager.get_group_list()
                        if groups:
                            self.current_group = groups[0]
                            self.load_group(self.current_group)
                            self.show_operation_status(f"Database loaded successfully", "green")

                            # Show summary with any missing files
                            if summary.get('missing_images', 0) > 0:
                                messagebox.showwarning(
                                    "Missing Files",
                                    f"Database loaded successfully!\n\n"
                                    f"Total groups: {summary['total_groups']}\n"
                                    f"Total images: {summary['total_images']}\n\n"
                                    f"Warning: {summary['missing_images']} image files could not be found.\n"
                                    f"These will be filtered out from the display."
                                )
                            else:
                                messagebox.showinfo(
                                    "Database Loaded",
                                    f"Database loaded successfully!\n\n"
                                    f"Total groups: {summary['total_groups']}\n"
                                    f"Total images: {summary['total_images']}"
                                )
                        else:
                            messagebox.showwarning("Empty Database", "The selected database contains no image groups.")
                            self.status_label.configure(text="Database loaded but contains no data")
                    else:
                        messagebox.showerror("Invalid Database",
                                           "The selected database appears to be empty or invalid.")
                        self.status_label.configure(text="Failed to load database")
                else:
                    messagebox.showerror("Database Error", "Failed to initialize database manager.")

            else:
                logger.debug("Database file selection cancelled by user")

        except Exception as e:
            logger.error(f"Error loading database file: {e}", exc_info=True)
            messagebox.showerror("Database Error", f"Failed to load database file:\n{str(e)}")
            self.status_label.configure(text="Failed to load database")

    def clear_current_data(self):
        """Clear current data and reset UI state."""
        self.current_group = None
        self.selected_images.clear()
        self.image_widgets.clear()

        # Clear the image display area
        for widget in self.image_scroll_frame.winfo_children():
            widget.destroy()

        # Reset UI state
        self.views_menu.configure(state="disabled")
        self.reload_btn.configure(state="disabled")
        self.auto_select_switch.configure(state="disabled")
        self.hide_single_switch.configure(state="disabled")

    def handle_database_selection(self, selection):
        """Handle database menu selection."""
        if selection == "Browse for Database...":
            self.load_database_file()
        elif selection.endswith(".db") or selection.endswith(".sqlite"):
            # Direct database file selection
            self.load_specific_database(selection)

        # Reset menu to default
        self.database_menu.set("Load Database...")

    def load_recent_databases(self):
        """Load the list of recent databases."""
        try:
            recent_file = Path.home() / ".lineup_recent_databases.txt"
            if recent_file.exists():
                with open(recent_file, 'r') as f:
                    self.recent_databases = [line.strip() for line in f.readlines() if line.strip()]
                    # Keep only existing files
                    self.recent_databases = [db for db in self.recent_databases if Path(db).exists()]
                    # Limit to 5 most recent
                    self.recent_databases = self.recent_databases[:5]

                self.update_database_menu()
        except Exception as e:
            logger.warning(f"Failed to load recent databases: {e}")

    def save_recent_databases(self):
        """Save the list of recent databases."""
        try:
            recent_file = Path.home() / ".lineup_recent_databases.txt"
            with open(recent_file, 'w') as f:
                for db in self.recent_databases:
                    f.write(f"{db}\n")
        except Exception as e:
            logger.warning(f"Failed to save recent databases: {e}")

    def add_to_recent_databases(self, db_path):
        """Add a database to the recent list."""
        db_path = str(Path(db_path).resolve())

        # Remove if already in list
        if db_path in self.recent_databases:
            self.recent_databases.remove(db_path)

        # Add to front
        self.recent_databases.insert(0, db_path)

        # Keep only 5 most recent
        self.recent_databases = self.recent_databases[:5]

        # Update UI and save
        self.update_database_menu()
        self.save_recent_databases()

    def update_database_menu(self):
        """Update the database menu with recent databases."""
        menu_items = ["Load Database...", "Browse for Database..."]

        if self.recent_databases:
            menu_items.append("──────────────")  # Separator
            for db_path in self.recent_databases:
                display_name = Path(db_path).name
                if len(display_name) > 25:
                    display_name = display_name[:22] + "..."
                menu_items.append(display_name)

        self.database_menu.configure(values=menu_items)

    def load_specific_database(self, db_name):
        """Load a specific database from the recent list."""
        # Find the full path
        full_path = None
        for db_path in self.recent_databases:
            if Path(db_path).name == db_name or db_name in db_path:
                full_path = db_path
                break

        if full_path and Path(full_path).exists():
            self.load_database_file_direct(full_path)
        else:
            messagebox.showerror("Database Not Found", f"The database '{db_name}' could not be found.")

    def load_database_file_direct(self, db_file):
        """Load a database file directly without file dialog."""
        try:
            logger.info(f"Loading database file directly: {db_file}")

            # Close any active image viewers
            for viewer in self.active_image_viewers.copy():
                if hasattr(viewer, 'window') and viewer.window.winfo_exists():
                    viewer.close()
            self.active_image_viewers.clear()

            # Clear current data
            self.clear_current_data()

            # Initialize data manager with the selected database
            self.data_manager = DataManager(use_database=True)

            # Update the database manager to use the selected file
            if self.data_manager.db_manager:
                # Disconnect from current database
                self.data_manager.db_manager.disconnect()

                # Update database path and reconnect
                self.data_manager.db_manager.db_path = Path(db_file)
                self.data_manager.db_manager.connect()

                # Update legacy attributes for backward compatibility
                self.data_manager._update_legacy_attributes()

                # Check if database has data
                if self.data_manager.has_data():
                    # Get database summary
                    summary = self.data_manager.get_overall_summary()

                    # Update UI state
                    self.current_csv_file = None  # No CSV file, using database
                    self.current_database_file = db_file

                    # Add to recent databases
                    self.add_to_recent_databases(db_file)

                    # Enable controls
                    self.views_menu.configure(state="normal")
                    self.auto_select_switch.configure(state="normal")
                    self.hide_single_switch.configure(state="normal")

                    # Update status
                    self.status_label.configure(
                        text=f"Database: {Path(db_file).name} - {summary.get('total_groups', 0)} groups, "
                             f"{summary.get('total_images', 0)} images"
                    )

                    # Load first group
                    groups = self.data_manager.get_group_list()
                    if groups:
                        self.current_group = groups[0]
                        self.load_group(self.current_group)
                        self.show_operation_status(f"Database loaded successfully", "green")
                    else:
                        messagebox.showwarning("Empty Database", "The selected database contains no image groups.")
                        self.status_label.configure(text="Database loaded but contains no data")
                else:
                    messagebox.showerror("Invalid Database",
                                       "The selected database appears to be empty or invalid.")
                    self.status_label.configure(text="Failed to load database")
            else:
                messagebox.showerror("Database Error", "Failed to initialize database manager.")

        except Exception as e:
            logger.error(f"Error loading database file: {e}", exc_info=True)
            messagebox.showerror("Database Error", f"Failed to load database file:\n{str(e)}")
            self.status_label.configure(text="Failed to load database")

    def open_list_view(self):
        """Open the advanced list view screen."""
        try:
            logger.info("Opening list view screen")
            
            # Create and show the list screen
            list_screen = ListScreen(
                parent=self.root,
                data_manager=self.data_manager,
                image_manager=self.image_manager,
                main_app=self
            )
            list_screen.show()
            
        except Exception as e:
            logger.error(f"Error opening list view: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to open list view:\n{str(e)}")
    
    def setup_content_ui(self):
        """Setup the main content UI after CSV is loaded."""
        logger.debug("Setting up content UI after CSV load")
        
        # Clear all existing content from content_frame
        widget_count = len(self.content_frame.winfo_children())
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        logger.debug(f"Cleared {widget_count} existing UI widgets")
        
        # Reset UI state
        self.current_group = None
        self.selected_images.clear()
        self.image_widgets.clear()
        self.group_buttons.clear()
        logger.debug("Reset UI state for new CSV data")
        
        # Create group navigation panel
        self.nav_frame = ctk.CTkFrame(self.content_frame)
        self.nav_frame.pack(side="left", fill="y", padx=(0, 5))
        
        # Group list
        nav_title = ctk.CTkLabel(self.nav_frame, text="Photo Groups", font=ctk.CTkFont(size=14, weight="bold"))
        nav_title.pack(pady=10)
        
        # Scrollable frame for groups
        self.group_list_frame = ctk.CTkScrollableFrame(self.nav_frame, width=200)
        self.group_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Populate group list
        self.populate_group_list()
        
        # Main display area
        self.display_frame = ctk.CTkFrame(self.content_frame)
        self.display_frame.pack(side="right", fill="both", expand=True)
        
        # Default message
        self.select_message = ctk.CTkLabel(
            self.display_frame,
            text="Select a group from the left to view images",
            font=ctk.CTkFont(size=14)
        )
        self.select_message.pack(expand=True)
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
    
    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the main application."""
        # Bind keyboard events to the root window
        self.root.bind('<KeyPress-d>', lambda e: self.keyboard_delete())
        self.root.bind('<KeyPress-D>', lambda e: self.keyboard_delete())
        self.root.bind('<KeyPress-m>', lambda e: self.keyboard_move())
        self.root.bind('<KeyPress-M>', lambda e: self.keyboard_move())
        self.root.bind('<KeyPress-n>', lambda e: self.keyboard_next_group())
        self.root.bind('<KeyPress-N>', lambda e: self.keyboard_next_group())
        self.root.bind('<KeyPress-p>', lambda e: self.keyboard_previous_group())
        self.root.bind('<KeyPress-P>', lambda e: self.keyboard_previous_group())
        
        # Make sure the window can receive focus for keyboard events
        self.root.focus_set()
        
        logger.debug("Keyboard shortcuts initialized: D=Delete, M=Move, N=Next Group, P=Previous Group")
    
    def keyboard_delete(self):
        """Handle keyboard shortcut for delete."""
        if hasattr(self, 'delete_btn') and self.delete_btn.cget('state') == 'normal':
            logger.info("Keyboard shortcut: Delete (D) pressed")
            self.delete_selected_images()
    
    def keyboard_move(self):
        """Handle keyboard shortcut for move."""
        if hasattr(self, 'move_btn') and self.move_btn.cget('state') == 'normal':
            logger.info("Keyboard shortcut: Move (M) pressed")
            self.move_selected_images()
    
    def keyboard_next_group(self):
        """Handle keyboard shortcut for next group."""
        if hasattr(self, 'next_group_btn') and self.next_group_btn.cget('state') == 'normal':
            logger.info("Keyboard shortcut: Next Group (N) pressed")
            self.go_to_next_group()
    
    def keyboard_previous_group(self):
        """Handle keyboard shortcut for previous group."""
        if hasattr(self, 'prev_group_btn') and self.prev_group_btn.cget('state') == 'normal':
            logger.info("Keyboard shortcut: Previous Group (P) pressed")
            self.go_to_previous_group()
    
    def populate_group_list(self):
        """Populate the group list with buttons."""
        logger.debug("Populating group list")
        
        # Clear existing buttons
        self.group_buttons.clear()
        for widget in self.group_list_frame.winfo_children():
            widget.destroy()
        
        groups = self.data_manager.get_group_list()
        logger.debug(f"Processing {len(groups)} total groups")
        
        displayed_groups = 0
        for group_id in groups:
            summary = self.data_manager.get_group_summary(group_id)
            
            # Skip groups with 1 or fewer images if hiding is enabled
            if self.hide_single_groups and summary['existing_images'] <= 1:
                logger.debug(f"Hiding group {group_id} with {summary['existing_images']} image(s)")
                continue
            
            # Create group button
            btn_text = f"Group {group_id}\n{summary['existing_images']}/{summary['total_images']} images"
            
            group_btn = ctk.CTkButton(
                self.group_list_frame,
                text=btn_text,
                command=lambda gid=group_id: self.select_group(gid),
                height=50,
                fg_color="gray25",  # Default unselected color
                hover_color="gray35"
            )
            group_btn.pack(fill="x", pady=2)
            
            # Store button reference
            self.group_buttons[group_id] = group_btn
            displayed_groups += 1
        
        logger.debug(f"Displayed {displayed_groups} groups (hiding single groups: {self.hide_single_groups})")
        
        # Update navigation button states
        self.update_navigation_buttons()
    
    def update_group_selection_visual(self, selected_group_id: str):
        """Update visual feedback for group selection."""
        logger.debug(f"Updating group visual feedback for selected group: {selected_group_id}")
        
        for group_id, button in self.group_buttons.items():
            if group_id == selected_group_id:
                # Highlight selected group
                button.configure(
                    fg_color="#1f538d",  # Blue for selected
                    hover_color="#14375e"
                )
            else:
                # Reset other groups to default
                button.configure(
                    fg_color="gray25",
                    hover_color="gray35"
                )
    
    def select_group(self, group_id: str):
        """Select and display a specific group."""
        logger.info(f"Selecting group: {group_id}")
        
        # Update visual feedback for group buttons
        self.update_group_selection_visual(group_id)
        
        self.current_group = group_id
        
        # Get group info for logging
        summary = self.data_manager.get_group_summary(group_id)
        logger.debug(f"Group {group_id} summary: {summary}")
        
        # Clear display area
        for widget in self.display_frame.winfo_children():
            widget.destroy()
        
        # Show group info
        summary = self.data_manager.get_group_summary(group_id)
        
        info_label = ctk.CTkLabel(
            self.display_frame,
            text=f"Group {group_id} - {summary['existing_images']}/{summary['total_images']} images available\n"
                 f"Match Reasons: {summary['match_reasons']}",
            font=ctk.CTkFont(size=12)
        )
        info_label.pack(pady=10)
        
        # Action buttons frame
        self.action_frame = ctk.CTkFrame(self.display_frame)
        self.action_frame.pack(fill="x", padx=5, pady=5)
        
        # Selection info
        self.selection_label = ctk.CTkLabel(
            self.action_frame,
            text="No images selected"
        )
        self.selection_label.pack(side="left", padx=5)
        
        # Action buttons
        self.delete_btn = ctk.CTkButton(
            self.action_frame,
            text="Delete Selected (D)",
            command=self.delete_selected_images,
            state="disabled"
        )
        self.delete_btn.pack(side="right", padx=5)
        
        self.move_btn = ctk.CTkButton(
            self.action_frame,
            text="Move Selected (M)",
            command=self.move_selected_images,
            state="disabled"
        )
        self.move_btn.pack(side="right", padx=5)
        
        # Scrollable frame for images
        self.image_scroll_frame = ctk.CTkScrollableFrame(self.display_frame)
        self.image_scroll_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Display images
        self.display_group_images(group_id)
    
    def display_group_images(self, group_id: str):
        """Display all images for the selected group."""
        group_data = self.data_manager.get_group(group_id)
        if group_data is None:
            return
        
        # Clear previous widgets
        self.image_widgets.clear()
        for widget in self.image_scroll_frame.winfo_children():
            widget.destroy()
        
        # Calculate optimal grid layout based on available space
        self.root.update_idletasks()  # Ensure geometry is calculated
        available_width = self.image_scroll_frame.winfo_width()
        if available_width <= 1:  # Not yet rendered
            available_width = 800  # Default fallback
        
        # Calculate dynamic thumbnail size and columns
        min_thumb_size = 250
        max_thumb_size = 800  # Increased from 400 to better use screen space
        min_columns = 2
        max_columns = 8  # Increased from 6 to allow more flexible layouts
        
        # Try different column counts to find optimal size
        best_columns = min_columns
        best_thumb_size = min_thumb_size

        for cols in range(min_columns, max_columns + 1):
            padding = 10 * (cols + 1)  # Account for padding
            available_per_image = (available_width - padding) / cols

            if available_per_image >= min_thumb_size:
                thumb_size = min(available_per_image, max_thumb_size)
                if thumb_size > best_thumb_size:
                    best_columns = cols
                    best_thumb_size = thumb_size

        # If we have a very wide screen, prefer larger thumbnails over more columns
        if available_width > 1600 and best_thumb_size < max_thumb_size:
            # Recalculate with preference for larger thumbnails
            for cols in range(min_columns, best_columns + 1):
                padding = 10 * (cols + 1)
                available_per_image = (available_width - padding) / cols
                thumb_size = min(available_per_image, max_thumb_size)
                if thumb_size >= best_thumb_size * 1.2:  # At least 20% larger
                    best_columns = cols
                    best_thumb_size = thumb_size
                    break
        
        # Update image manager thumbnail size
        self.image_manager.thumbnail_size = (int(best_thumb_size), int(best_thumb_size))
        
        # Create grid layout for images
        columns = best_columns
        row = 0
        col = 0
        
        for idx, (_, image_data) in enumerate(group_data.iterrows()):
            # Create image widget with dynamic size
            image_widget = ImageWidget(
                self.image_scroll_frame,
                image_data,
                self.image_manager,
                thumbnail_size=int(best_thumb_size),
                main_app=self
            )
            
            image_widget.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            self.image_widgets.append(image_widget)
            
            # Bind double-click for full-size viewer
            image_widget.bind("<Double-Button-1>", lambda e, idx=idx: self.open_image_viewer(idx))
            image_widget.image_label.bind("<Double-Button-1>", lambda e, idx=idx: self.open_image_viewer(idx))
            
            # Update grid position
            col += 1
            if col >= columns:
                col = 0
                row += 1
        
        # Configure grid weights for responsive layout
        for i in range(columns):
            self.image_scroll_frame.grid_columnconfigure(i, weight=1)
        
        # Auto-select non-master images for easy processing (if enabled)
        if self.auto_select_enabled:
            self.auto_select_non_masters()
        else:
            self.selected_images.clear()
        
        # Update selection UI
        self.update_selection_ui()
    
    def auto_select_non_masters(self):
        """Automatically select non-master images for easy processing."""
        logger.debug(f"Auto-selecting non-master images in group {self.current_group}")
        
        self.selected_images.clear()
        selected_count = 0
        
        for image_widget in self.image_widgets:
            if not image_widget.is_master and image_widget.file_exists:
                image_widget.set_selected(True)
                self.selected_images.add(image_widget)
                selected_count += 1
        
        if selected_count > 0:
            logger.info(f"Auto-selected {selected_count} non-master images in group {self.current_group}")
            self.show_operation_status(f"Auto-selected {selected_count} non-master image(s)", "blue")
            
            # Check if auto-selection selected all images except master (warning condition)
            total_existing = sum(1 for w in self.image_widgets if w.file_exists)
            if selected_count == total_existing - 1 and total_existing > 1:
                logger.warning(f"Auto-selected all non-master images in group {self.current_group} - only master will remain")
                self.show_operation_status("⚠️ Auto-selected all duplicates - only master will remain", "orange")
        else:
            logger.debug(f"No non-master images to auto-select in group {self.current_group}")
        
        # Update button states after auto-selection
        self.update_selection_ui()
    
    def open_image_viewer(self, image_index: int):
        """Open full-size image viewer with navigation."""
        if not self.image_widgets or image_index >= len(self.image_widgets):
            return
        
        # Create image viewer window
        viewer = ImageViewerWindow(
            self.root,
            self.image_widgets,
            image_index,
            self.image_manager,
            self.data_manager,
            self.current_group,
            self
        )
        # Track the viewer
        self.active_image_viewers.append(viewer)
        viewer.show()
    
    def on_image_selection_changed(self, image_widget):
        """Handle image selection changes."""
        if image_widget.is_selected:
            self.selected_images.add(image_widget)
            
            # If master image is selected, unselect all other images in the group
            if image_widget.is_master:
                logger.info(f"Master image selected, unselecting all other images in group {self.current_group}")
                for widget in self.image_widgets:
                    if widget != image_widget and widget.is_selected:
                        widget.set_selected(False)
                        self.selected_images.discard(widget)
                self.show_operation_status("Master selected - cleared other selections", "orange")
        else:
            self.selected_images.discard(image_widget)
        
        # Check if all images in the group are selected (warning condition)
        if len(self.selected_images) == len(self.image_widgets) and len(self.image_widgets) > 1:
            logger.warning(f"All images selected in group {self.current_group} - this will leave no images in the group")
            self.show_operation_status("⚠️ WARNING: All images selected - group will be empty!", "red")
        
        self.update_selection_ui()
    
    def update_selection_ui(self):
        """Update UI based on current selection."""
        count = len(self.selected_images)
        
        if count == 0:
            self.selection_label.configure(text="No images selected")
            self.delete_btn.configure(state="disabled")
            self.move_btn.configure(state="disabled")
        else:
            # Check if all selected images are non-masters
            non_master_count = sum(1 for widget in self.selected_images if not widget.is_master)
            if non_master_count == count:
                self.selection_label.configure(text=f"{count} duplicate(s) selected")
            else:
                self.selection_label.configure(text=f"{count} image(s) selected")
            
            self.delete_btn.configure(state="normal")
            self.move_btn.configure(state="normal")
            
        # Update move button text based on pre-selected directory
        if hasattr(self, 'move_btn'):
            if self.move_to_directory and self.move_to_directory.exists():
                self.move_btn.configure(text="Move to Pre-selected (M)")
            else:
                self.move_btn.configure(text="Move Selected (M)")
    
    def delete_selected_images(self):
        """Delete selected images."""
        if not self.selected_images:
            return
        
        # Confirm deletion
        count = len(self.selected_images)
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {count} selected image(s)?\n\n"
            f"This action cannot be undone."
        )
        
        if result:
            deleted_files = []
            failed_files = []
            
            for image_widget in list(self.selected_images):
                file_path = image_widget.image_data['Path']
                try:
                    Path(file_path).unlink()
                    deleted_files.append(file_path)
                    logging.info(f"Deleted file: {file_path}")
                except Exception as e:
                    failed_files.append(f"{file_path}: {e}")
                    logging.error(f"Failed to delete {file_path}: {e}")
            
            # Show results
            if deleted_files:
                messagebox.showinfo(
                    "Deletion Complete",
                    f"Successfully deleted {len(deleted_files)} file(s)."
                )
            
            if failed_files:
                messagebox.showerror(
                    "Deletion Errors",
                    f"Failed to delete {len(failed_files)} file(s):\n\n" +
                    "\n".join(failed_files[:5]) +  # Show first 5 errors
                    (f"\n... and {len(failed_files) - 5} more" if len(failed_files) > 5 else "")
                )
            
            # Show operation status and refresh
            self.show_operation_status(f"Deleted {len(deleted_files)} file(s)", "red")
            self.refresh_current_group()
    
    def move_selected_images(self):
        """Move selected images to a specified directory."""
        if not self.selected_images:
            return
        
        # Use pre-selected directory or ask for one
        if self.move_to_directory and self.move_to_directory.exists():
            dest_path = self.move_to_directory
        else:
            # Select destination directory
            dest_dir = filedialog.askdirectory(title="Select destination directory")
            if not dest_dir:
                return
            
            dest_path = Path(dest_dir)
            if not dest_path.exists():
                messagebox.showerror("Error", "Selected directory does not exist.")
                return
        
        # Move files
        moved_files = []
        failed_files = []
        
        for image_widget in list(self.selected_images):
            file_path = Path(image_widget.image_data['Path'])
            dest_file = dest_path / file_path.name
            
            try:
                # Handle name conflicts
                counter = 1
                while dest_file.exists():
                    stem = file_path.stem
                    suffix = file_path.suffix
                    dest_file = dest_path / f"{stem}_{counter}{suffix}"
                    counter += 1
                
                file_path.rename(dest_file)
                moved_files.append(str(dest_file))
                logging.info(f"Moved file: {file_path} -> {dest_file}")
                
            except Exception as e:
                failed_files.append(f"{file_path.name}: {e}")
                logging.error(f"Failed to move {file_path}: {e}")
        
        # Show results
        if moved_files:
            messagebox.showinfo(
                "Move Complete",
                f"Successfully moved {len(moved_files)} file(s) to:\n{dest_dir}"
            )
        
        if failed_files:
            messagebox.showerror(
                "Move Errors",
                f"Failed to move {len(failed_files)} file(s):\n\n" +
                "\n".join(failed_files[:5]) +
                (f"\n... and {len(failed_files) - 5} more" if len(failed_files) > 5 else "")
            )
        
        # Show operation status and refresh
        self.show_operation_status(f"Moved {len(moved_files)} file(s)", "green")
        self.refresh_current_group()
    
    def select_move_directory(self):
        """Select directory for moving files."""
        logger.debug("Opening move directory selection dialog")
        directory = filedialog.askdirectory(title="Select Move To Directory")
        if directory:
            self.move_to_directory = Path(directory)
            logger.info(f"Move To directory set: {self.move_to_directory}")
            logger.debug(f"Directory exists: {self.move_to_directory.exists()}")
            
            # Truncate display text if path is too long
            display_text = str(self.move_to_directory)
            if len(display_text) > 30:
                display_text = "..." + display_text[-27:]
            
            self.moveto_display.configure(
                text=display_text,
                text_color="green"
            )
            # Update move button text
            self.update_selection_ui()
            # Notify any open image viewers
            self.notify_viewers_directory_changed()
        else:
            logger.debug("Move directory selection cancelled by user")
    
    def clear_move_directory(self):
        """Clear the selected move directory."""
        logger.info("Clearing Move To directory")
        self.move_to_directory = None
        self.moveto_display.configure(
            text="No directory selected",
            text_color="gray"
        )
        # Update move button text
        self.update_selection_ui()
        # Notify any open image viewers
        self.notify_viewers_directory_changed()
        logger.debug("Move To directory cleared and UI updated")
    
    def notify_viewers_directory_changed(self):
        """Notify all active image viewers that the move directory has changed."""
        # Clean up closed viewers
        self.active_image_viewers = [viewer for viewer in self.active_image_viewers 
                                   if hasattr(viewer, 'window') and viewer.window.winfo_exists()]
        
        # Notify remaining viewers
        for viewer in self.active_image_viewers:
            if hasattr(viewer, 'update_move_button_text'):
                viewer.update_move_button_text()
    
    def show_operation_status(self, message: str, color: str = "green"):
        """Show operation status message temporarily."""
        logger.info(f"Operation status: {message}")
        self.operation_status_label.configure(text=message, text_color=color)
        
        # Clear the message after 3 seconds
        self.root.after(3000, lambda: self.operation_status_label.configure(text=""))
    
    def refresh_current_group(self):
        """Refresh the current group display after file operations."""
        if self.current_group:
            logger.debug(f"Refreshing display for group {self.current_group}")
            # Revalidate file paths in data manager
            self.data_manager.validate_file_paths()
            # Repopulate group list (counts may have changed)
            self.populate_group_list()
            
            # Check if we should move to next group
            self.move_to_next_group_after_action()
            
            # If still on same group, refresh display
            if self.current_group and self.current_group in self.group_buttons:
                self.select_group(self.current_group)
    
    def get_next_available_group(self, current_group: str) -> str:
        """Get the next available group for navigation."""
        available_groups = list(self.group_buttons.keys())
        if not available_groups:
            return None
            
        try:
            current_index = available_groups.index(current_group)
            # Try next group first
            if current_index + 1 < len(available_groups):
                return available_groups[current_index + 1]
            # If at end, try first group
            elif len(available_groups) > 1:
                return available_groups[0]
        except ValueError:
            # Current group not in available groups, return first available
            pass
        
        # Return first available group or None
        return available_groups[0] if available_groups else None
    
    def move_to_next_group_after_action(self):
        """Move to next available group after performing an action."""
        if not self.current_group:
            return
            
        # Always move to next group after an action for efficient workflow
        next_group = self.get_next_available_group(self.current_group)
        if next_group and next_group != self.current_group:
            logger.info(f"Auto-navigating from group {self.current_group} to {next_group} after action")
            self.select_group(next_group)
            self.show_operation_status(f"Advanced to group {next_group}", "blue")
        else:
            # Check if current group should be hidden due to single image rule
            summary = self.data_manager.get_group_summary(self.current_group)
            if self.hide_single_groups and summary['existing_images'] <= 1:
                # Refresh the group list to hide the now-single group
                self.populate_group_list()
                available_groups = list(self.group_buttons.keys())
                if available_groups:
                    self.select_group(available_groups[0])
                    self.show_operation_status(f"Moved to group {available_groups[0]} (previous group hidden)", "blue")
                else:
                    self.show_operation_status("All groups processed!", "green")
    
    def toggle_auto_select(self):
        """Toggle auto-selection of non-master images."""
        self.auto_select_enabled = self.auto_select_switch.get()
        logger.info(f"Auto-select duplicates {'enabled' if self.auto_select_enabled else 'disabled'}")
        
        # If currently viewing a group, apply the new setting
        if self.current_group and self.image_widgets:
            if self.auto_select_enabled:
                self.auto_select_non_masters()
            else:
                # Clear all selections
                for widget in self.selected_images.copy():
                    widget.set_selected(False)
                self.selected_images.clear()
                self.show_operation_status("Auto-selection disabled", "gray")
            
            self.update_selection_ui()
    
    def toggle_hide_single_groups(self):
        """Toggle hiding of groups with 1 or fewer images."""
        self.hide_single_groups = self.hide_single_switch.get()
        logger.info(f"Hide single groups {'enabled' if self.hide_single_groups else 'disabled'}")
        
        # Count total and single groups for user feedback
        if hasattr(self, 'data_manager') and self.data_manager.has_data():
            all_groups = self.data_manager.get_group_list()
            single_groups = [g for g in all_groups if self.data_manager.get_group_summary(g)['existing_images'] <= 1]
            
            if self.hide_single_groups:
                status_msg = f"Hiding {len(single_groups)} single-image groups ({len(all_groups) - len(single_groups)} groups shown)"
                status_color = "blue"
            else:
                status_msg = f"Showing all {len(all_groups)} groups ({len(single_groups)} single-image groups included)"
                status_color = "green"
            
            self.show_operation_status(status_msg, status_color)
        
        # Repopulate group list with new filter
        if hasattr(self, 'group_list_frame'):
            current_group = self.current_group
            self.populate_group_list()
            
            # If current group is now hidden, select the first available group
            if current_group and current_group not in self.group_buttons:
                available_groups = list(self.group_buttons.keys())
                if available_groups:
                    self.select_group(available_groups[0])
                    logger.info(f"Current group {current_group} was hidden, switched to {available_groups[0]}")
                else:
                    # No groups to display
                    self.current_group = None
                    # Clear display area
                    for widget in self.display_frame.winfo_children():
                        widget.destroy()
                    
                    no_groups_label = ctk.CTkLabel(
                        self.display_frame,
                        text="No groups to display with current filter settings",
                        font=ctk.CTkFont(size=14)
                    )
                    no_groups_label.pack(expand=True)
            elif current_group:
                # Re-select current group to update visual feedback
                self.update_group_selection_visual(current_group)
    
    def go_to_previous_group(self):
        """Navigate to the previous group."""
        if not self.current_group or not self.group_buttons:
            return
        
        # Get list of available groups
        available_groups = list(self.group_buttons.keys())
        
        if self.current_group in available_groups:
            current_index = available_groups.index(self.current_group)
            # Go to previous group (wrap to end if at beginning)
            if current_index > 0:
                previous_group = available_groups[current_index - 1]
            else:
                previous_group = available_groups[-1]  # Wrap to last group
            
            logger.info(f"Navigating from group {self.current_group} to previous group {previous_group}")
            self.select_group(previous_group)
            self.show_operation_status(f"Navigated to previous group: {previous_group}", "blue")
    
    def go_to_next_group(self):
        """Navigate to the next group."""
        if not self.current_group or not self.group_buttons:
            return
        
        # Get list of available groups
        available_groups = list(self.group_buttons.keys())
        
        if self.current_group in available_groups:
            current_index = available_groups.index(self.current_group)
            # Go to next group (wrap to beginning if at end)
            if current_index < len(available_groups) - 1:
                next_group = available_groups[current_index + 1]
            else:
                next_group = available_groups[0]  # Wrap to first group
            
            logger.info(f"Navigating from group {self.current_group} to next group {next_group}")
            self.select_group(next_group)
            self.show_operation_status(f"Navigated to next group: {next_group}", "blue")
    
    def update_navigation_buttons(self):
        """Update the state of navigation buttons based on available groups."""
        if not hasattr(self, 'prev_group_btn') or not hasattr(self, 'next_group_btn'):
            return
            
        # Enable buttons if there are multiple groups available
        has_groups = len(self.group_buttons) > 1
        state = "normal" if has_groups else "disabled"
        
        self.prev_group_btn.configure(state=state)
        self.next_group_btn.configure(state=state)

    def toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        if self.dark_mode_switch.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
    
    def handle_view_selection(self, selection):
        """Handle selection from the views dropdown menu."""
        logger.info(f"View selection: {selection}")
        
        if selection == "📋 List View":
            self.open_list_view()
        elif selection == "📊 Statistics":
            self.show_statistics_view()
        elif selection == "🔍 Search":
            self.show_search_view()
        elif selection == "Select View...":
            # Default option - do nothing
            return
        
        # Reset menu to default after action
        self.views_menu.set("Select View...")
    
    def show_statistics_view(self):
        """Show overall statistics for the loaded data."""
        if not self.data_manager.has_data():
            self.show_operation_status("No data loaded", "red")
            return
        
        summary = self.data_manager.get_overall_summary()
        stats_message = (
            f"Dataset Statistics:\n"
            f"• Total Groups: {summary['total_groups']}\n"
            f"• Total Images: {summary['total_images']}\n"
            f"• Missing Images: {summary['missing_images']}\n"
            f"• Available Images: {summary['total_images'] - summary['missing_images']}\n"
            f"• Groups with Multiple Images: {len([g for g in self.data_manager.get_group_list() if self.data_manager.get_group_summary(g)['existing_images'] > 1])}"
        )
        
        # Show in a dialog
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Dataset Statistics")
        dialog.geometry("400x300")
        dialog.transient(self.root)
        dialog.grab_set()
        
        label = ctk.CTkLabel(dialog, text=stats_message, font=ctk.CTkFont(size=12), justify="left")
        label.pack(padx=20, pady=20)
        
        close_btn = ctk.CTkButton(dialog, text="Close", command=dialog.destroy)
        close_btn.pack(pady=10)
        
        logger.info("Statistics view displayed")
    
    def show_search_view(self):
        """Show search functionality - placeholder for future implementation."""
        self.show_operation_status("Search functionality - use List View for now", "blue")
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    app = LineupApp()
    app.run()


if __name__ == "__main__":
    main()
