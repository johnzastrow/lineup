import tkinter as tk
from PIL import Image, ImageTk
import customtkinter as ctk
from pathlib import Path
import logging
from typing import Dict, Optional, Tuple
import threading
import json
from hashlib import md5


class ImageManager:
    """Handles image loading, thumbnail generation, and caching."""
    
    def __init__(self, cache_dir: str = ".image_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # In-memory cache for loaded images
        self.image_cache: Dict[str, ImageTk.PhotoImage] = {}
        self.thumbnail_cache: Dict[str, ImageTk.PhotoImage] = {}
        
        # Cache metadata
        self.cache_metadata_file = self.cache_dir / "cache_metadata.json"
        self.cache_metadata = self._load_cache_metadata()
        
        # Thumbnail settings
        self.thumbnail_size = (150, 150)
        self.preview_size = (400, 400)
        
        logging.info(f"ImageManager initialized with cache dir: {self.cache_dir}")
    
    def _load_cache_metadata(self) -> Dict:
        """Load cache metadata from disk."""
        if self.cache_metadata_file.exists():
            try:
                with open(self.cache_metadata_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logging.warning(f"Could not load cache metadata: {e}")
        
        return {}
    
    def _save_cache_metadata(self):
        """Save cache metadata to disk."""
        try:
            with open(self.cache_metadata_file, 'w') as f:
                json.dump(self.cache_metadata, f)
        except Exception as e:
            logging.warning(f"Could not save cache metadata: {e}")
    
    def _get_cache_key(self, file_path: str, size: Tuple[int, int]) -> str:
        """Generate cache key for a file and size."""
        content = f"{file_path}_{size[0]}x{size[1]}"
        return md5(content.encode()).hexdigest()
    
    def _get_cached_thumbnail_path(self, cache_key: str) -> Path:
        """Get the path for a cached thumbnail."""
        return self.cache_dir / f"{cache_key}.png"
    
    def load_thumbnail(self, file_path: str, callback=None) -> Optional[ImageTk.PhotoImage]:
        """Load or generate thumbnail for an image."""
        if not Path(file_path).exists():
            return None
        
        cache_key = self._get_cache_key(file_path, self.thumbnail_size)
        
        # Check in-memory cache first
        if cache_key in self.thumbnail_cache:
            if callback:
                callback(self.thumbnail_cache[cache_key])
            return self.thumbnail_cache[cache_key]
        
        # Check disk cache
        cached_path = self._get_cached_thumbnail_path(cache_key)
        file_stat = Path(file_path).stat()
        
        if (cached_path.exists() and 
            cache_key in self.cache_metadata and 
            self.cache_metadata[cache_key].get('mtime') == file_stat.st_mtime):
            
            try:
                # Load from disk cache
                image = Image.open(cached_path)
                photo_image = ImageTk.PhotoImage(image)
                self.thumbnail_cache[cache_key] = photo_image
                
                if callback:
                    callback(photo_image)
                return photo_image
                
            except Exception as e:
                logging.warning(f"Could not load cached thumbnail for {file_path}: {e}")
        
        # Generate new thumbnail
        if callback:
            # Generate asynchronously
            thread = threading.Thread(
                target=self._generate_thumbnail_async,
                args=(file_path, cache_key, callback)
            )
            thread.daemon = True
            thread.start()
            return None
        else:
            # Generate synchronously
            return self._generate_thumbnail(file_path, cache_key)
    
    def _generate_thumbnail(self, file_path: str, cache_key: str) -> Optional[ImageTk.PhotoImage]:
        """Generate thumbnail synchronously."""
        try:
            with Image.open(file_path) as image:
                # Convert to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                # Generate thumbnail
                image.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save to disk cache
                cached_path = self._get_cached_thumbnail_path(cache_key)
                image.save(cached_path, 'PNG')
                
                # Update metadata
                file_stat = Path(file_path).stat()
                self.cache_metadata[cache_key] = {
                    'file_path': file_path,
                    'mtime': file_stat.st_mtime,
                    'size': self.thumbnail_size
                }
                self._save_cache_metadata()
                
                # Create PhotoImage
                photo_image = ImageTk.PhotoImage(image)
                self.thumbnail_cache[cache_key] = photo_image
                
                return photo_image
                
        except Exception as e:
            logging.error(f"Could not generate thumbnail for {file_path}: {e}")
            return None
    
    def _generate_thumbnail_async(self, file_path: str, cache_key: str, callback):
        """Generate thumbnail asynchronously and call callback."""
        photo_image = self._generate_thumbnail(file_path, cache_key)
        if photo_image and callback:
            # Schedule callback on main thread
            callback(photo_image)
    
    def load_preview_image(self, file_path: str) -> Optional[ImageTk.PhotoImage]:
        """Load a larger preview image."""
        if not Path(file_path).exists():
            return None
        
        cache_key = self._get_cache_key(file_path, self.preview_size)
        
        # Check in-memory cache
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        
        try:
            with Image.open(file_path) as image:
                # Convert to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                # Resize for preview
                image.thumbnail(self.preview_size, Image.Resampling.LANCZOS)
                
                # Create PhotoImage
                photo_image = ImageTk.PhotoImage(image)
                self.image_cache[cache_key] = photo_image
                
                return photo_image
                
        except Exception as e:
            logging.error(f"Could not load preview image for {file_path}: {e}")
            return None
    
    def get_image_info(self, file_path: str) -> Dict:
        """Get basic information about an image file."""
        if not Path(file_path).exists():
            return {'error': 'File not found'}
        
        try:
            with Image.open(file_path) as image:
                file_stat = Path(file_path).stat()
                
                return {
                    'width': image.width,
                    'height': image.height,
                    'mode': image.mode,
                    'format': image.format,
                    'file_size': file_stat.st_size,
                    'file_size_mb': round(file_stat.st_size / 1024 / 1024, 2)
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def clear_cache(self):
        """Clear all caches."""
        self.image_cache.clear()
        self.thumbnail_cache.clear()
        
        # Clear disk cache
        try:
            for cache_file in self.cache_dir.glob("*.png"):
                cache_file.unlink()
            
            self.cache_metadata.clear()
            self._save_cache_metadata()
            
            logging.info("Image cache cleared")
            
        except Exception as e:
            logging.error(f"Could not clear cache: {e}")


class ImageWidget(ctk.CTkFrame):
    """Custom widget for displaying an image with selection and master highlighting."""
    
    def __init__(self, parent, image_data, image_manager, thumbnail_size=150, main_app=None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.image_data = image_data  # Row from DataFrame
        self.image_manager = image_manager
        self.is_selected = False
        self.is_master = image_data.get('IsMaster', False)
        self.file_exists = image_data.get('FileExists', False)
        self.thumbnail_size = thumbnail_size
        self.main_app = main_app
        
        self.setup_ui()
        self.load_thumbnail()
    
    def setup_ui(self):
        """Setup the image widget UI."""
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        
        # Image label
        self.image_label = ctk.CTkLabel(
            self,
            text="Loading...",
            width=self.thumbnail_size,
            height=self.thumbnail_size
        )
        self.image_label.grid(row=0, column=0, padx=5, pady=5)
        
        # File name label
        file_name = Path(self.image_data['File']).name
        
        self.name_label = ctk.CTkLabel(
            self,
            text=file_name,
            width=self.thumbnail_size,
            font=ctk.CTkFont(size=max(8, min(12, self.thumbnail_size // 15))),
            wraplength=self.thumbnail_size - 10  # Enable text wrapping
        )
        self.name_label.grid(row=1, column=0, padx=5, pady=(0, 5))
        
        # Master indicator
        if self.is_master:
            self.master_label = ctk.CTkLabel(
                self,
                text="★ MASTER",
                text_color="gold",
                font=ctk.CTkFont(size=10, weight="bold")
            )
            self.master_label.grid(row=2, column=0, padx=5, pady=(0, 5))
        
        # File status
        if not self.file_exists:
            self.status_label = ctk.CTkLabel(
                self,
                text="❌ Missing",
                text_color="red",
                font=ctk.CTkFont(size=10)
            )
            self.status_label.grid(row=3, column=0, padx=5, pady=(0, 5))
        
        # Bind click events
        self.bind("<Button-1>", self.on_click)
        self.image_label.bind("<Button-1>", self.on_click)
        self.name_label.bind("<Button-1>", self.on_click)
        
        # Update border for master status
        self.update_appearance()
    
    def load_thumbnail(self):
        """Load thumbnail image."""
        if not self.file_exists:
            self.image_label.configure(text="❌\nMissing\nFile")
            return
        
        def thumbnail_callback(photo_image):
            if photo_image:
                self.image_label.configure(image=photo_image, text="")
        
        thumbnail = self.image_manager.load_thumbnail(
            self.image_data['Path'],
            callback=thumbnail_callback
        )
        
        if thumbnail:
            self.image_label.configure(image=thumbnail, text="")
    
    def on_click(self, event):
        """Handle click events."""
        self.toggle_selection()
    
    def toggle_selection(self):
        """Toggle selection state."""
        self.is_selected = not self.is_selected
        self.update_appearance()
        
        # Notify main app of selection change
        if self.main_app and hasattr(self.main_app, 'on_image_selection_changed'):
            self.main_app.on_image_selection_changed(self)
    
    def set_selected(self, selected: bool):
        """Set selection state."""
        self.is_selected = selected
        self.update_appearance()
    
    def update_appearance(self):
        """Update widget appearance based on state."""
        if self.is_selected:
            border_color = "red" if not self.is_master else "orange"
            border_width = 3
        elif self.is_master:
            border_color = "gold"
            border_width = 2
        else:
            border_color = "green"
            border_width = 1
        
        self.configure(border_width=border_width, border_color=border_color)


class ImageViewerWindow:
    """Full-size image viewer window with navigation."""
    
    def __init__(self, parent, image_widgets, current_index, image_manager, data_manager=None, current_group=None, main_app=None):
        self.parent = parent
        self.image_widgets = image_widgets
        self.current_index = current_index
        self.image_manager = image_manager
        self.data_manager = data_manager
        self.current_group = current_group
        self.main_app = main_app
        
        # Create window
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Image Viewer")
        self.window.geometry("800x600")
        self.window.minsize(400, 300)
        
        # Make window modal
        self.window.transient(parent)
        self.window.grab_set()
        
        # Center window on parent
        self.center_window()
        
        self.setup_ui()
        self.bind_keys()
        self.load_current_image()
    
    def center_window(self):
        """Center the window on the parent."""
        self.window.update_idletasks()
        
        # Get parent window position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        # Get this window size
        window_width = self.window.winfo_width()
        window_height = self.window.winfo_height()
        
        # Calculate center position
        x = parent_x + (parent_width - window_width) // 2
        y = parent_y + (parent_height - window_height) // 2
        
        self.window.geometry(f"{window_width}x{window_height}+{x}+{y}")
    
    def setup_ui(self):
        """Setup the viewer UI."""
        # Main frame
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Group info bar (top)
        if self.data_manager and self.current_group:
            self.group_info_frame = ctk.CTkFrame(self.main_frame)
            self.group_info_frame.pack(fill="x", padx=5, pady=5)
            
            # Group navigation
            self.prev_group_btn = ctk.CTkButton(
                self.group_info_frame,
                text="◀ Prev Group",
                command=self.previous_group,
                width=100
            )
            self.prev_group_btn.pack(side="left", padx=5)
            
            # Group info display
            self.group_info_label = ctk.CTkLabel(
                self.group_info_frame,
                text="",
                font=ctk.CTkFont(size=14, weight="bold")
            )
            self.group_info_label.pack(side="left", expand=True, padx=20)
            
            # Next group button
            self.next_group_btn = ctk.CTkButton(
                self.group_info_frame,
                text="Next Group ▶",
                command=self.next_group,
                width=100
            )
            self.next_group_btn.pack(side="right", padx=5)
        
        # Image info bar
        self.info_frame = ctk.CTkFrame(self.main_frame)
        self.info_frame.pack(fill="x", padx=5, pady=5)
        
        # Image counter
        self.counter_label = ctk.CTkLabel(
            self.info_frame,
            text="",
            font=ctk.CTkFont(size=12)
        )
        self.counter_label.pack(side="left", padx=10)
        
        # File name
        self.filename_label = ctk.CTkLabel(
            self.info_frame,
            text="",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.filename_label.pack(side="left", padx=10)
        
        # Master indicator
        self.master_indicator = ctk.CTkLabel(
            self.info_frame,
            text="",
            text_color="gold",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.master_indicator.pack(side="right", padx=10)
        
        # Navigation buttons frame
        self.nav_frame = ctk.CTkFrame(self.main_frame)
        self.nav_frame.pack(fill="x", padx=5, pady=5)
        
        # Previous button
        self.prev_btn = ctk.CTkButton(
            self.nav_frame,
            text="◀ Previous (←)",
            command=self.previous_image,
            width=120
        )
        self.prev_btn.pack(side="left", padx=5)
        
        # Next button
        self.next_btn = ctk.CTkButton(
            self.nav_frame,
            text="Next (→) ▶",
            command=self.next_image,
            width=120
        )
        self.next_btn.pack(side="right", padx=5)
        
        # Action buttons frame
        self.action_frame = ctk.CTkFrame(self.nav_frame)
        self.action_frame.pack(side="bottom", fill="x", pady=5)
        
        # Delete button
        self.delete_btn = ctk.CTkButton(
            self.action_frame,
            text="Delete Image",
            command=self.delete_current_image,
            width=100,
            fg_color="red",
            hover_color="darkred"
        )
        self.delete_btn.pack(side="left", padx=5)
        
        # Move button
        self.move_btn = ctk.CTkButton(
            self.action_frame,
            text="Move Image",
            command=self.move_current_image,
            width=100
        )
        self.move_btn.pack(side="left", padx=5)
        
        # Close button
        self.close_btn = ctk.CTkButton(
            self.action_frame,
            text="Close (Esc)",
            command=self.close,
            width=100
        )
        self.close_btn.pack(side="right", padx=5)
        
        # Image display frame
        self.image_frame = ctk.CTkFrame(self.main_frame)
        self.image_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Image label (scrollable)
        self.image_scroll = ctk.CTkScrollableFrame(self.image_frame)
        self.image_scroll.pack(fill="both", expand=True)
        
        self.image_label = ctk.CTkLabel(
            self.image_scroll,
            text="Loading...",
            font=ctk.CTkFont(size=16)
        )
        self.image_label.pack(expand=True, fill="both")
    
    def bind_keys(self):
        """Bind keyboard shortcuts."""
        self.window.bind("<Left>", lambda e: self.previous_image())
        self.window.bind("<Right>", lambda e: self.next_image())
        self.window.bind("<Escape>", lambda e: self.close())
        self.window.bind("<Return>", lambda e: self.close())
        
        # Make sure window has focus for key events
        self.window.focus_set()
    
    def load_current_image(self):
        """Load and display the current image."""
        if not self.image_widgets or self.current_index >= len(self.image_widgets):
            return
        
        current_widget = self.image_widgets[self.current_index]
        image_data = current_widget.image_data
        
        # Update group info if available
        if self.data_manager and self.current_group:
            group_summary = self.data_manager.get_group_summary(self.current_group)
            group_list = self.data_manager.get_group_list()
            current_group_index = group_list.index(self.current_group) + 1 if self.current_group in group_list else 0
            
            group_info_text = f"Group {self.current_group} ({current_group_index}/{len(group_list)}) - {group_summary.get('existing_images', 0)} images"
            if group_summary.get('match_reasons'):
                group_info_text += f" - {group_summary['match_reasons']}"
            
            self.group_info_label.configure(text=group_info_text)
            
            # Update group navigation buttons
            self.prev_group_btn.configure(state="normal" if current_group_index > 1 else "disabled")
            self.next_group_btn.configure(state="normal" if current_group_index < len(group_list) else "disabled")
        
        # Update info labels
        self.counter_label.configure(
            text=f"Image {self.current_index + 1} of {len(self.image_widgets)}"
        )
        
        file_path = Path(image_data['File'])
        self.filename_label.configure(text=file_path.name)
        
        # Show master indicator
        if current_widget.is_master:
            self.master_indicator.configure(text="★ MASTER")
        else:
            self.master_indicator.configure(text="")
        
        # Update navigation buttons
        self.prev_btn.configure(state="normal" if self.current_index > 0 else "disabled")
        self.next_btn.configure(state="normal" if self.current_index < len(self.image_widgets) - 1 else "disabled")
        
        # Update move button text based on pre-selected directory
        self.update_move_button_text()
        
        # Load full-size image
        if current_widget.file_exists:
            self.load_full_image(image_data['Path'])
        else:
            self.image_label.configure(
                image=None,
                text="❌ File Not Found\n\n" + str(file_path)
            )
    
    def load_full_image(self, file_path: str):
        """Load and display full-size image."""
        try:
            # Get window size for optimal display
            self.window.update_idletasks()
            max_width = self.image_frame.winfo_width() - 40
            max_height = self.image_frame.winfo_height() - 40
            
            if max_width <= 1 or max_height <= 1:
                max_width = 600
                max_height = 400
            
            with Image.open(file_path) as image:
                # Convert to RGB if necessary
                if image.mode in ('RGBA', 'LA', 'P'):
                    image = image.convert('RGB')
                
                # Calculate size to fit window while maintaining aspect ratio
                img_width, img_height = image.size
                scale_width = max_width / img_width
                scale_height = max_height / img_height
                scale = min(scale_width, scale_height, 1.0)  # Don't upscale
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # Resize image
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Create PhotoImage and display
                photo_image = ImageTk.PhotoImage(resized_image)
                self.image_label.configure(image=photo_image, text="")
                
                # Keep reference to prevent garbage collection
                self.image_label.image = photo_image
                
                # Update window title with image info
                self.window.title(f"Image Viewer - {Path(file_path).name} ({img_width}×{img_height})")
                
        except Exception as e:
            logging.error(f"Could not load image {file_path}: {e}")
            self.image_label.configure(
                image=None,
                text=f"❌ Error Loading Image\n\n{str(e)}"
            )
    
    def previous_image(self):
        """Navigate to previous image."""
        if self.current_index > 0:
            self.current_index -= 1
            self.load_current_image()
    
    def next_image(self):
        """Navigate to next image."""
        if self.current_index < len(self.image_widgets) - 1:
            self.current_index += 1
            self.load_current_image()
    
    def update_move_button_text(self):
        """Update move button text based on pre-selected directory."""
        if hasattr(self, 'move_btn') and self.main_app:
            if self.main_app.move_to_directory and self.main_app.move_to_directory.exists():
                self.move_btn.configure(text="Move to Pre-selected")
            else:
                self.move_btn.configure(text="Move Image")
    
    def previous_group(self):
        """Navigate to previous group."""
        if not (self.data_manager and self.current_group and self.main_app):
            return
            
        group_list = self.data_manager.get_group_list()
        if self.current_group not in group_list:
            return
            
        current_index = group_list.index(self.current_group)
        if current_index > 0:
            new_group = group_list[current_index - 1]
            self.switch_to_group(new_group)
    
    def next_group(self):
        """Navigate to next group."""
        if not (self.data_manager and self.current_group and self.main_app):
            return
            
        group_list = self.data_manager.get_group_list()
        if self.current_group not in group_list:
            return
            
        current_index = group_list.index(self.current_group)
        if current_index < len(group_list) - 1:
            new_group = group_list[current_index + 1]
            self.switch_to_group(new_group)
    
    def switch_to_group(self, new_group: str):
        """Switch to a different group and update the viewer."""
        # Update main app to display new group
        self.main_app.select_group(new_group)
        
        # Update this viewer with new group data
        self.current_group = new_group
        self.image_widgets = self.main_app.image_widgets
        self.current_index = 0  # Start with first image in new group
        
        # Reload the display
        self.load_current_image()
    
    def delete_current_image(self):
        """Delete the currently displayed image."""
        if not self.image_widgets or self.current_index >= len(self.image_widgets):
            return
            
        from tkinter import messagebox
        import logging
        
        current_widget = self.image_widgets[self.current_index]
        file_path = current_widget.image_data['Path']
        
        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete this image?\n\n{Path(file_path).name}\n\n"
            f"This action cannot be undone.",
            parent=self.window
        )
        
        if result:
            try:
                Path(file_path).unlink()
                logging.info(f"Deleted file: {file_path}")
                
                messagebox.showinfo(
                    "Deletion Complete",
                    f"Successfully deleted {Path(file_path).name}",
                    parent=self.window
                )
                
                # Navigate to next image or close if this was the last one
                if len(self.image_widgets) == 1:
                    # This was the last image, close viewer and refresh main app
                    self.close()
                    if self.main_app:
                        self.main_app.select_group(self.current_group)
                elif self.current_index >= len(self.image_widgets) - 1:
                    # This was the last image in the list, go to previous
                    self.current_index = len(self.image_widgets) - 2
                    # Refresh from main app
                    if self.main_app:
                        self.main_app.select_group(self.current_group)
                        self.image_widgets = self.main_app.image_widgets
                    self.load_current_image()
                else:
                    # Refresh from main app and stay at current index
                    if self.main_app:
                        self.main_app.select_group(self.current_group)
                        self.image_widgets = self.main_app.image_widgets
                    self.load_current_image()
                    
            except Exception as e:
                logging.error(f"Failed to delete {file_path}: {e}")
                messagebox.showerror(
                    "Deletion Error",
                    f"Failed to delete file:\n{str(e)}",
                    parent=self.window
                )
    
    def move_current_image(self):
        """Move the currently displayed image."""
        if not self.image_widgets or self.current_index >= len(self.image_widgets):
            return
            
        from tkinter import filedialog, messagebox
        import logging
        
        current_widget = self.image_widgets[self.current_index]
        file_path = Path(current_widget.image_data['Path'])
        
        # Use main app's pre-selected directory or ask for one
        dest_path = None
        if self.main_app and self.main_app.move_to_directory and self.main_app.move_to_directory.exists():
            dest_path = self.main_app.move_to_directory
        else:
            dest_dir = filedialog.askdirectory(
                title="Select destination directory", 
                parent=self.window
            )
            if not dest_dir:
                return
            dest_path = Path(dest_dir)
            
            # Update main app's global directory setting
            if self.main_app:
                self.main_app.move_to_directory = dest_path
                display_text = str(dest_path)
                if len(display_text) > 30:
                    display_text = "..." + display_text[-27:]
                
                self.main_app.moveto_display.configure(
                    text=display_text,
                    text_color="green"
                )
                self.main_app.update_selection_ui()  # Update button text
                logging.info(f"Move To directory updated from image viewer: {dest_path}")
            
        if not dest_path.exists():
            messagebox.showerror("Error", "Selected directory does not exist.", parent=self.window)
            return
        
        # Move the file
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
            logging.info(f"Moved file: {file_path} -> {dest_file}")
            
            messagebox.showinfo(
                "Move Complete",
                f"Successfully moved {file_path.name} to:\n{dest_path}",
                parent=self.window
            )
            
            # Navigate to next image or close if this was the last one
            if len(self.image_widgets) == 1:
                # This was the last image, close viewer and refresh main app
                self.close()
                if self.main_app:
                    self.main_app.select_group(self.current_group)
            elif self.current_index >= len(self.image_widgets) - 1:
                # This was the last image in the list, go to previous
                self.current_index = len(self.image_widgets) - 2
                # Refresh from main app
                if self.main_app:
                    self.main_app.select_group(self.current_group)
                    self.image_widgets = self.main_app.image_widgets
                self.load_current_image()
            else:
                # Refresh from main app and stay at current index
                if self.main_app:
                    self.main_app.select_group(self.current_group)
                    self.image_widgets = self.main_app.image_widgets
                self.load_current_image()
                
        except Exception as e:
            logging.error(f"Failed to move {file_path}: {e}")
            messagebox.showerror(
                "Move Error",
                f"Failed to move file:\n{str(e)}",
                parent=self.window
            )
    
    def close(self):
        """Close the viewer window."""
        # Remove from main app's tracking list
        if self.main_app and hasattr(self.main_app, 'active_image_viewers'):
            try:
                self.main_app.active_image_viewers.remove(self)
            except ValueError:
                pass  # Already removed
        
        self.window.grab_release()
        self.window.destroy()
    
    def show(self):
        """Show the viewer window."""
        self.window.deiconify()
        self.window.lift()
        self.window.focus_set()