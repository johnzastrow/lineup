import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
import logging
from pathlib import Path
from data_manager import DataManager
from image_manager import ImageManager, ImageWidget, ImageViewerWindow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lineup.log'),
        logging.StreamHandler()
    ]
)

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
        self.current_group = None
        self.selected_images = set()
        self.image_widgets = []
        self.move_to_directory = None
        self.active_image_viewers = []  # Track open image viewers
        
        self.setup_ui()
        logging.info("Lineup application initialized")
    
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
        
        # Status label
        self.status_label = ctk.CTkLabel(
            self.toolbar,
            text="No CSV file loaded"
        )
        self.status_label.pack(side="left", padx=20)
        
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
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                logging.info(f"Loading CSV file: {file_path}")
                
                # Load data using DataManager
                if self.data_manager.load_csv(file_path):
                    summary = self.data_manager.get_overall_summary()
                    
                    # Update status
                    status_text = f"Loaded: {Path(file_path).name} ({summary['total_groups']} groups, {summary['total_images']} images)"
                    self.status_label.configure(text=status_text)
                    
                    # Update UI
                    self.setup_content_ui()
                    
                    # Show warning if there are missing files
                    if summary['missing_images'] > 0:
                        messagebox.showwarning(
                            "Missing Files",
                            f"Warning: {summary['missing_images']} image files could not be found.\n"
                            f"These will be marked as unavailable."
                        )
                
            except Exception as e:
                logging.error(f"Error loading CSV file: {e}")
                messagebox.showerror("Error", f"Failed to load CSV file:\n{str(e)}")
    
    def setup_content_ui(self):
        """Setup the main content UI after CSV is loaded."""
        # Clear all existing content from content_frame
        for widget in self.content_frame.winfo_children():
            widget.destroy()
        
        # Reset UI state
        self.current_group = None
        self.selected_images.clear()
        self.image_widgets.clear()
        
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
    
    def populate_group_list(self):
        """Populate the group list with buttons."""
        groups = self.data_manager.get_group_list()
        
        for group_id in groups:
            summary = self.data_manager.get_group_summary(group_id)
            
            # Create group button
            btn_text = f"Group {group_id}\n{summary['existing_images']}/{summary['total_images']} images"
            
            group_btn = ctk.CTkButton(
                self.group_list_frame,
                text=btn_text,
                command=lambda gid=group_id: self.select_group(gid),
                height=50
            )
            group_btn.pack(fill="x", pady=2)
    
    def select_group(self, group_id: str):
        """Select and display a specific group."""
        self.current_group = group_id
        logging.info(f"Selected group: {group_id}")
        
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
            text="Delete Selected",
            command=self.delete_selected_images,
            state="disabled"
        )
        self.delete_btn.pack(side="right", padx=5)
        
        self.move_btn = ctk.CTkButton(
            self.action_frame,
            text="Move Selected",
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
        min_thumb_size = 200
        max_thumb_size = 400
        min_columns = 2
        max_columns = 6
        
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
        
        # Reset selection
        self.selected_images.clear()
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
        else:
            self.selected_images.discard(image_widget)
        
        self.update_selection_ui()
    
    def update_selection_ui(self):
        """Update UI based on current selection."""
        count = len(self.selected_images)
        
        if count == 0:
            self.selection_label.configure(text="No images selected")
            self.delete_btn.configure(state="disabled")
            self.move_btn.configure(state="disabled")
        else:
            self.selection_label.configure(text=f"{count} image(s) selected")
            self.delete_btn.configure(state="normal")
            self.move_btn.configure(state="normal")
            
        # Update move button text based on pre-selected directory
        if hasattr(self, 'move_btn'):
            if self.move_to_directory and self.move_to_directory.exists():
                self.move_btn.configure(text="Move to Pre-selected")
            else:
                self.move_btn.configure(text="Move Selected")
    
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
            
            # Refresh the display
            self.select_group(self.current_group)
    
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
        
        # Refresh the display
        self.select_group(self.current_group)
    
    def select_move_directory(self):
        """Select directory for moving files."""
        directory = filedialog.askdirectory(title="Select Move To Directory")
        if directory:
            self.move_to_directory = Path(directory)
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
            logging.info(f"Move To directory set: {self.move_to_directory}")
    
    def clear_move_directory(self):
        """Clear the selected move directory."""
        self.move_to_directory = None
        self.moveto_display.configure(
            text="No directory selected",
            text_color="gray"
        )
        # Update move button text
        self.update_selection_ui()
        # Notify any open image viewers
        self.notify_viewers_directory_changed()
        logging.info("Move To directory cleared")
    
    def notify_viewers_directory_changed(self):
        """Notify all active image viewers that the move directory has changed."""
        # Clean up closed viewers
        self.active_image_viewers = [viewer for viewer in self.active_image_viewers 
                                   if hasattr(viewer, 'window') and viewer.window.winfo_exists()]
        
        # Notify remaining viewers
        for viewer in self.active_image_viewers:
            if hasattr(viewer, 'update_move_button_text'):
                viewer.update_move_button_text()
    
    def toggle_dark_mode(self):
        """Toggle between light and dark mode."""
        if self.dark_mode_switch.get():
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")
    
    def run(self):
        """Run the application."""
        self.root.mainloop()


def main():
    app = LineupApp()
    app.run()


if __name__ == "__main__":
    main()
