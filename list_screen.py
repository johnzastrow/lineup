import tkinter as tk
import customtkinter as ctk
from tkinter import ttk, messagebox
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from pathlib import Path
import pandas as pd
from PIL import Image, ImageTk
from data_manager_enhanced import DataManager
from image_manager import ImageManager, ImageViewerWindow

# Get logger for this module
logger = logging.getLogger('lineup.list_screen')


class ListScreen:
    """Advanced list screen for photo duplicate management with pagination, filtering, and sorting."""
    
    def __init__(self, parent, data_manager: DataManager, image_manager: ImageManager, main_app=None):
        self.parent = parent
        self.data_manager = data_manager
        self.image_manager = image_manager
        self.main_app = main_app
        
        # List screen state
        self.current_page = 0
        self.page_size = 20  # Configurable page size
        self.sort_column = None
        self.sort_ascending = True
        self.filters = {}
        self.search_query = ""
        self.search_column = "all"
        self.selected_rows = set()
        self.total_records = 0
        self.filtered_data = pd.DataFrame()
        self.current_page_data = pd.DataFrame()
        
        # UI components
        self.window = None
        self.data_frame = None
        self.tree_view = None
        self.page_label = None
        self.stats_labels = {}
        self.filter_widgets = {}
        
        # Configuration
        self.show_only_groups_with_multiple = False
        self.highlight_masters = True
        
        logger.info("List screen initialized")
    
    def show(self):
        """Display the list screen as a modal window."""
        try:
            # Create modal window
            self.window = ctk.CTkToplevel(self.parent)
            self.window.title("Photo List - Lineup")
            self.window.geometry("1400x900")
            self.window.minsize(1200, 700)
            
            # Make it modal
            self.window.transient(self.parent)
            self.window.grab_set()
            
            # Setup UI
            self.setup_ui()
            
            # Load initial data
            self.refresh_data()
            
            # Center the window
            self.window.update_idletasks()
            x = (self.window.winfo_screenwidth() // 2) - (1400 // 2)
            y = (self.window.winfo_screenheight() // 2) - (900 // 2)
            self.window.geometry(f"1400x900+{x}+{y}")
            
            logger.info("List screen displayed")
            
        except Exception as e:
            logger.error(f"Error showing list screen: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to open list screen:\n{str(e)}")
    
    def setup_ui(self):
        """Setup the list screen user interface."""
        # Main container
        main_container = ctk.CTkFrame(self.window)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top toolbar
        self.setup_toolbar(main_container)
        
        # Filter panel
        self.setup_filter_panel(main_container)
        
        # Data grid
        self.setup_data_grid(main_container)
        
        # Bottom panel with pagination and statistics
        self.setup_bottom_panel(main_container)
        
        logger.debug("List screen UI setup complete")
    
    def setup_toolbar(self, parent):
        """Setup the top toolbar with controls."""
        toolbar = ctk.CTkFrame(parent)
        toolbar.pack(fill="x", padx=5, pady=(0, 5))
        
        # Title
        title_label = ctk.CTkLabel(
            toolbar,
            text="Photo List View",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        title_label.pack(side="left", padx=10)
        
        # Refresh button
        refresh_btn = ctk.CTkButton(
            toolbar,
            text="🔄 Refresh",
            command=self.refresh_data,
            width=100
        )
        refresh_btn.pack(side="left", padx=5)
        
        # Page size selector
        page_size_label = ctk.CTkLabel(toolbar, text="Page Size:")
        page_size_label.pack(side="left", padx=(20, 5))
        
        self.page_size_var = tk.StringVar(value=str(self.page_size))
        page_size_combo = ctk.CTkComboBox(
            toolbar,
            values=["10", "20", "50", "100"],
            variable=self.page_size_var,
            command=self.on_page_size_changed,
            width=80
        )
        page_size_combo.pack(side="left", padx=5)
        
        # Toggle switches
        self.multi_groups_var = tk.BooleanVar(value=self.show_only_groups_with_multiple)
        multi_groups_switch = ctk.CTkSwitch(
            toolbar,
            text="Show Only Multi-Image Groups",
            variable=self.multi_groups_var,
            command=self.on_filter_changed
        )
        multi_groups_switch.pack(side="right", padx=5)
        
        self.highlight_masters_var = tk.BooleanVar(value=self.highlight_masters)
        highlight_switch = ctk.CTkSwitch(
            toolbar,
            text="Highlight Masters",
            variable=self.highlight_masters_var,
            command=self.on_highlight_changed
        )
        highlight_switch.pack(side="right", padx=5)
        
        # Action buttons
        action_frame = ctk.CTkFrame(toolbar)
        action_frame.pack(side="right", padx=10)
        
        self.move_btn = ctk.CTkButton(
            action_frame,
            text="Move Selected",
            command=self.move_selected,
            state="disabled",
            width=120
        )
        self.move_btn.pack(side="left", padx=2)
        
        self.delete_btn = ctk.CTkButton(
            action_frame,
            text="Delete Selected",
            command=self.delete_selected,
            state="disabled",
            width=120
        )
        self.delete_btn.pack(side="left", padx=2)
    
    def setup_filter_panel(self, parent):
        """Setup the filter and search panel."""
        filter_frame = ctk.CTkFrame(parent)
        filter_frame.pack(fill="x", padx=5, pady=5)
        
        # Search controls
        search_label = ctk.CTkLabel(filter_frame, text="Search:")
        search_label.pack(side="left", padx=5)
        
        # Search column selector
        self.search_column_var = tk.StringVar(value="all")
        search_column_combo = ctk.CTkComboBox(
            filter_frame,
            values=["all", "File", "Path", "CameraMake", "CameraModel", "IPTCKeywords", "MatchReasons"],
            variable=self.search_column_var,
            command=self.on_search_changed,
            width=120
        )
        search_column_combo.pack(side="left", padx=5)
        
        # Search type selector
        self.search_type_var = tk.StringVar(value="contains")
        search_type_combo = ctk.CTkComboBox(
            filter_frame,
            values=["contains", "does not contain", "equals", "starts with"],
            variable=self.search_type_var,
            command=self.on_search_changed,
            width=120
        )
        search_type_combo.pack(side="left", padx=5)
        
        # Search entry
        self.search_entry = ctk.CTkEntry(
            filter_frame,
            placeholder_text="Search terms...",
            width=200
        )
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search_changed)
        
        # Search button
        search_btn = ctk.CTkButton(
            filter_frame,
            text="Search",
            command=self.on_search_changed,
            width=80
        )
        search_btn.pack(side="left", padx=5)
        
        # Clear filters button
        clear_btn = ctk.CTkButton(
            filter_frame,
            text="Clear Filters",
            command=self.clear_filters,
            width=100
        )
        clear_btn.pack(side="left", padx=5)
        
        # Filter status
        self.filter_status_label = ctk.CTkLabel(
            filter_frame,
            text="",
            font=ctk.CTkFont(size=10)
        )
        self.filter_status_label.pack(side="right", padx=5)
    
    def setup_data_grid(self, parent):
        """Setup the main data grid with treeview."""
        grid_frame = ctk.CTkFrame(parent)
        grid_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Create treeview with scrollbars
        tree_frame = tk.Frame(grid_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Define columns based on TODO requirements
        self.columns = [
            ("select", "☑", 40),
            ("thumbnail", "📷", 60),
            ("GroupID", "Group ID", 80),
            ("Path", "File Path", 300),
            ("Master", "Master", 60),
            ("QualityScore", "Score", 60),
            ("Width", "Width", 70),
            ("Height", "Height", 70),
            ("Size", "Size (KB)", 90),
            ("Created", "Date Created", 120),
            ("Algorithm", "Algorithm", 80),
            ("FileType", "Type", 60),
            ("CameraMake", "Camera", 100),
            ("SimilarityScore", "Similarity", 80),
            ("MatchReasons", "Match Reasons", 200)
        ]
        
        # Create treeview
        self.tree_view = ttk.Treeview(
            tree_frame,
            columns=[col[0] for col in self.columns],
            show="headings",
            height=20
        )
        
        # Configure columns
        for col_id, col_name, col_width in self.columns:
            self.tree_view.heading(col_id, text=col_name, command=lambda c=col_id: self.sort_by_column(c))
            self.tree_view.column(col_id, width=col_width, minwidth=col_width//2)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree_view.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree_view.xview)
        self.tree_view.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Pack scrollbars and treeview
        self.tree_view.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # Bind events
        self.tree_view.bind("<Button-1>", self.on_tree_click)
        self.tree_view.bind("<Double-1>", self.on_tree_double_click)
        
        logger.debug("Data grid setup complete")
    
    def setup_bottom_panel(self, parent):
        """Setup the bottom panel with pagination and statistics."""
        bottom_frame = ctk.CTkFrame(parent)
        bottom_frame.pack(fill="x", padx=5, pady=5)
        
        # Pagination controls
        nav_frame = ctk.CTkFrame(bottom_frame)
        nav_frame.pack(side="left", padx=10, pady=5)
        
        self.first_page_btn = ctk.CTkButton(
            nav_frame,
            text="⏮ First",
            command=self.go_to_first_page,
            width=80,
            state="disabled"
        )
        self.first_page_btn.pack(side="left", padx=2)
        
        self.prev_page_btn = ctk.CTkButton(
            nav_frame,
            text="◀ Prev",
            command=self.go_to_previous_page,
            width=80,
            state="disabled"
        )
        self.prev_page_btn.pack(side="left", padx=2)
        
        # Page number entry
        self.page_entry = ctk.CTkEntry(nav_frame, width=60, justify="center")
        self.page_entry.pack(side="left", padx=5)
        self.page_entry.bind("<Return>", self.go_to_page)
        
        self.page_label = ctk.CTkLabel(nav_frame, text="of 0")
        self.page_label.pack(side="left", padx=5)
        
        self.next_page_btn = ctk.CTkButton(
            nav_frame,
            text="Next ▶",
            command=self.go_to_next_page,
            width=80,
            state="disabled"
        )
        self.next_page_btn.pack(side="left", padx=2)
        
        self.last_page_btn = ctk.CTkButton(
            nav_frame,
            text="Last ⏭",
            command=self.go_to_last_page,
            width=80,
            state="disabled"
        )
        self.last_page_btn.pack(side="left", padx=2)
        
        # Statistics panel
        stats_frame = ctk.CTkFrame(bottom_frame)
        stats_frame.pack(side="right", padx=10, pady=5)
        
        # Statistics labels
        stats_labels = [
            ("total_groups", "Total Groups:"),
            ("total_records", "Total Records:"),
            ("selected_records", "Selected:"),
            ("selected_groups", "Selected Groups:"),
            ("selected_masters", "Selected Masters:"),
            ("selected_non_masters", "Selected Non-Masters:")
        ]
        
        for i, (key, label) in enumerate(stats_labels):
            row = i // 3
            col = i % 3
            
            label_widget = ctk.CTkLabel(stats_frame, text=label, font=ctk.CTkFont(size=10))
            label_widget.grid(row=row*2, column=col, sticky="w", padx=5, pady=1)
            
            value_widget = ctk.CTkLabel(stats_frame, text="0", font=ctk.CTkFont(size=10, weight="bold"))
            value_widget.grid(row=row*2+1, column=col, sticky="w", padx=5, pady=1)
            
            self.stats_labels[key] = value_widget
        
        # Select all checkbox
        select_frame = ctk.CTkFrame(bottom_frame)
        select_frame.pack(side="left", padx=20, pady=5)
        
        self.select_all_var = tk.BooleanVar()
        self.select_all_checkbox = ctk.CTkCheckBox(
            select_frame,
            text="Select All on Page",
            variable=self.select_all_var,
            command=self.toggle_select_all
        )
        self.select_all_checkbox.pack()
        
        logger.debug("Bottom panel setup complete")
    
    def refresh_data(self):
        """Refresh the data from the data manager and update the display."""
        try:
            logger.info("Refreshing list screen data")
            
            # Get all data from data manager
            all_data = self.get_all_data()
            
            if all_data.empty:
                logger.warning("No data available to display")
                self.filtered_data = pd.DataFrame()
                self.update_display()
                return
            
            # Apply filters
            self.filtered_data = self.apply_filters(all_data)
            
            # Update pagination
            self.total_records = len(self.filtered_data)
            self.current_page = 0  # Reset to first page
            
            # Update display
            self.update_display()
            
            logger.info(f"Data refreshed: {self.total_records} records after filtering")
            
        except Exception as e:
            logger.error(f"Error refreshing data: {e}", exc_info=True)
            messagebox.showerror("Error", f"Failed to refresh data:\n{str(e)}")
    
    def get_all_data(self) -> pd.DataFrame:
        """Get all data from the data manager."""
        try:
            all_data = []
            
            # Get data from each group
            for group_id in self.data_manager.get_group_list():
                group_data = self.data_manager.get_group(group_id)
                if not group_data.empty:
                    all_data.append(group_data)
            
            if all_data:
                combined_data = pd.concat(all_data, ignore_index=True)
                logger.debug(f"Retrieved {len(combined_data)} total records from {len(all_data)} groups")
                return combined_data
            else:
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error getting all data: {e}", exc_info=True)
            return pd.DataFrame()
    
    def apply_filters(self, data: pd.DataFrame) -> pd.DataFrame:
        """Apply current filters to the data."""
        if data.empty:
            return data
        
        filtered_data = data.copy()
        filter_count = 0
        
        try:
            # Apply multi-group filter
            if self.show_only_groups_with_multiple:
                group_counts = filtered_data['GroupID'].value_counts()
                multi_groups = group_counts[group_counts > 1].index
                filtered_data = filtered_data[filtered_data['GroupID'].isin(multi_groups)]
                filter_count += 1
                logger.debug(f"Multi-group filter applied: {len(filtered_data)} records remain")
            
            # Apply search filter
            search_text = self.search_entry.get() if hasattr(self, 'search_entry') else ""
            if search_text.strip():
                search_column = self.search_column_var.get() if hasattr(self, 'search_column_var') else "all"
                search_type = self.search_type_var.get() if hasattr(self, 'search_type_var') else "contains"
                
                filtered_data = self.apply_search_filter(filtered_data, search_text, search_column, search_type)
                filter_count += 1
                logger.debug(f"Search filter applied: {len(filtered_data)} records remain")
            
            # Update filter status
            if hasattr(self, 'filter_status_label'):
                if filter_count > 0:
                    self.filter_status_label.configure(
                        text=f"{filter_count} filter(s) active - {len(filtered_data)} of {len(data)} records shown"
                    )
                else:
                    self.filter_status_label.configure(text="No filters active")
            
            return filtered_data
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}", exc_info=True)
            return data
    
    def apply_search_filter(self, data: pd.DataFrame, search_text: str, column: str, search_type: str) -> pd.DataFrame:
        """Apply search filter to the data."""
        search_text = search_text.lower()
        
        if column == "all":
            # Search all text columns
            text_columns = ['File', 'Path', 'Name', 'CameraMake', 'CameraModel', 'IPTCKeywords', 'IPTCCaption', 'XMPKeywords', 'XMPTitle', 'MatchReasons']
            mask = pd.Series([False] * len(data))
            
            for col in text_columns:
                if col in data.columns:
                    col_mask = self.apply_search_to_column(data[col], search_text, search_type)
                    mask = mask | col_mask
        else:
            # Search specific column
            if column in data.columns:
                mask = self.apply_search_to_column(data[column], search_text, search_type)
            else:
                mask = pd.Series([True] * len(data))  # No filter if column doesn't exist
        
        return data[mask]
    
    def apply_search_to_column(self, series: pd.Series, search_text: str, search_type: str) -> pd.Series:
        """Apply search to a specific column."""
        # Convert to string and lowercase
        str_series = series.astype(str).str.lower()
        
        if search_type == "contains":
            return str_series.str.contains(search_text, na=False)
        elif search_type == "does not contain":
            return ~str_series.str.contains(search_text, na=False)
        elif search_type == "equals":
            return str_series == search_text
        elif search_type == "starts with":
            return str_series.str.startswith(search_text, na=False)
        else:
            return pd.Series([True] * len(series))
    
    def update_display(self):
        """Update the display with current page data."""
        try:
            # Calculate pagination
            total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
            self.current_page = min(self.current_page, total_pages - 1)
            
            # Get current page data
            start_idx = self.current_page * self.page_size
            end_idx = min(start_idx + self.page_size, self.total_records)
            
            if not self.filtered_data.empty and start_idx < len(self.filtered_data):
                self.current_page_data = self.filtered_data.iloc[start_idx:end_idx].copy()
            else:
                self.current_page_data = pd.DataFrame()
            
            # Update treeview
            self.populate_treeview()
            
            # Update pagination controls
            self.update_pagination_controls(total_pages)
            
            # Update statistics
            self.update_statistics()
            
            # Update action buttons
            self.update_action_buttons()
            
        except Exception as e:
            logger.error(f"Error updating display: {e}", exc_info=True)
    
    def populate_treeview(self):
        """Populate the treeview with current page data."""
        # Clear existing items
        for item in self.tree_view.get_children():
            self.tree_view.delete(item)
        
        if self.current_page_data.empty:
            return
        
        for idx, row in self.current_page_data.iterrows():
            # Prepare values for each column
            values = []
            row_id = str(idx)
            
            for col_id, _, _ in self.columns:
                if col_id == "select":
                    values.append("☑" if row_id in self.selected_rows else "☐")
                elif col_id == "thumbnail":
                    values.append("🖼")  # Placeholder for thumbnail
                elif col_id == "Master":
                    values.append("★" if row.get('IsMaster', False) else "")
                elif col_id == "Size" and col_id in row:
                    # Convert size to KB
                    size_bytes = row.get('Size', 0) or 0
                    if isinstance(size_bytes, (int, float)) and size_bytes > 0:
                        values.append(f"{int(size_bytes / 1024)}")
                    else:
                        values.append("")
                elif col_id in row:
                    value = row[col_id]
                    if pd.isna(value):
                        values.append("")
                    else:
                        values.append(str(value)[:50])  # Truncate long values
                else:
                    values.append("")
            
            # Insert row
            item = self.tree_view.insert("", "end", iid=row_id, values=values)
            
            # Apply styling for masters
            if self.highlight_masters and row.get('IsMaster', False):
                self.tree_view.set(item, "Master", "★ MASTER")
    
    def update_pagination_controls(self, total_pages: int):
        """Update pagination control states."""
        # Update page info
        current_page_display = self.current_page + 1
        self.page_label.configure(text=f"of {total_pages}")
        
        if hasattr(self, 'page_entry'):
            self.page_entry.delete(0, tk.END)
            self.page_entry.insert(0, str(current_page_display))
        
        # Update button states
        self.first_page_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.prev_page_btn.configure(state="normal" if self.current_page > 0 else "disabled")
        self.next_page_btn.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")
        self.last_page_btn.configure(state="normal" if self.current_page < total_pages - 1 else "disabled")
    
    def update_statistics(self):
        """Update the statistics display."""
        try:
            # Calculate statistics
            total_groups = len(self.filtered_data['GroupID'].unique()) if not self.filtered_data.empty else 0
            total_records = len(self.filtered_data)
            selected_records = len(self.selected_rows)
            
            # Selected groups and masters
            selected_groups = 0
            selected_masters = 0
            selected_non_masters = 0
            
            if selected_records > 0 and not self.filtered_data.empty:
                selected_data = self.filtered_data[self.filtered_data.index.isin([int(r) for r in self.selected_rows if r.isdigit()])]
                if not selected_data.empty:
                    selected_groups = len(selected_data['GroupID'].unique())
                    selected_masters = len(selected_data[selected_data['IsMaster'] == True])
                    selected_non_masters = selected_records - selected_masters
            
            # Update labels
            self.stats_labels['total_groups'].configure(text=str(total_groups))
            self.stats_labels['total_records'].configure(text=str(total_records))
            self.stats_labels['selected_records'].configure(text=str(selected_records))
            self.stats_labels['selected_groups'].configure(text=str(selected_groups))
            self.stats_labels['selected_masters'].configure(text=str(selected_masters))
            self.stats_labels['selected_non_masters'].configure(text=str(selected_non_masters))
            
            # Warning if all images in a group are selected
            if selected_masters > 0:
                self.stats_labels['selected_masters'].configure(text_color="orange")
            else:
                self.stats_labels['selected_masters'].configure(text_color="white")
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}", exc_info=True)
    
    def update_action_buttons(self):
        """Update the state of action buttons."""
        has_selection = len(self.selected_rows) > 0
        self.move_btn.configure(state="normal" if has_selection else "disabled")
        self.delete_btn.configure(state="normal" if has_selection else "disabled")
    
    # Event handlers
    def on_page_size_changed(self, value):
        """Handle page size change."""
        try:
            self.page_size = int(value)
            self.current_page = 0  # Reset to first page
            self.update_display()
            logger.debug(f"Page size changed to {self.page_size}")
        except ValueError:
            logger.warning(f"Invalid page size value: {value}")
    
    def on_filter_changed(self):
        """Handle filter toggle changes."""
        self.show_only_groups_with_multiple = self.multi_groups_var.get()
        logger.debug(f"Multi-group filter changed to {self.show_only_groups_with_multiple}")
        self.refresh_data()
    
    def on_highlight_changed(self):
        """Handle highlight toggle change."""
        self.highlight_masters = self.highlight_masters_var.get()
        logger.debug(f"Master highlighting changed to {self.highlight_masters}")
        self.update_display()
    
    def on_search_changed(self, event=None):
        """Handle search changes."""
        self.refresh_data()
    
    def clear_filters(self):
        """Clear all filters and search."""
        self.search_entry.delete(0, tk.END)
        self.search_column_var.set("all")
        self.search_type_var.set("contains")
        self.multi_groups_var.set(False)
        self.show_only_groups_with_multiple = False
        self.selected_rows.clear()  # Preserve selection as specified in TODO
        self.refresh_data()
        logger.info("Filters cleared")
    
    def sort_by_column(self, column: str):
        """Sort the data by the specified column."""
        if column in ["select", "thumbnail"]:
            return  # Can't sort by these columns
        
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        
        if not self.filtered_data.empty and column in self.filtered_data.columns:
            self.filtered_data = self.filtered_data.sort_values(
                by=column,
                ascending=self.sort_ascending,
                na_position='last'
            )
            
            # Update column header to show sort direction
            for col_id, col_name, _ in self.columns:
                if col_id == column:
                    arrow = " ↑" if self.sort_ascending else " ↓"
                    self.tree_view.heading(col_id, text=col_name + arrow)
                else:
                    self.tree_view.heading(col_id, text=[c[1] for c in self.columns if c[0] == col_id][0])
            
            self.update_display()
            logger.debug(f"Sorted by {column}, ascending={self.sort_ascending}")
    
    def on_tree_click(self, event):
        """Handle tree click events."""
        region = self.tree_view.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree_view.identify_row(event.y)
            column = self.tree_view.identify_column(event.x)
            
            # Check if clicking on select column
            if column == "#1":  # Select column
                self.toggle_row_selection(item)
    
    def on_tree_double_click(self, event):
        """Handle tree double-click events."""
        item = self.tree_view.identify_row(event.y)
        column = self.tree_view.identify_column(event.x)
        
        # Check if clicking on thumbnail column
        if column == "#2":  # Thumbnail column
            self.open_image_viewer(item)
    
    def toggle_row_selection(self, item: str):
        """Toggle selection state of a row."""
        if item in self.selected_rows:
            self.selected_rows.remove(item)
            self.tree_view.set(item, "select", "☐")
        else:
            self.selected_rows.add(item)
            self.tree_view.set(item, "select", "☑")
        
        self.update_statistics()
        self.update_action_buttons()
    
    def toggle_select_all(self):
        """Toggle selection of all visible rows."""
        select_all = self.select_all_var.get()
        
        for item in self.tree_view.get_children():
            if select_all:
                self.selected_rows.add(item)
                self.tree_view.set(item, "select", "☑")
            else:
                self.selected_rows.discard(item)
                self.tree_view.set(item, "select", "☐")
        
        self.update_statistics()
        self.update_action_buttons()
        logger.info(f"{'Selected' if select_all else 'Deselected'} all visible rows")
    
    def open_image_viewer(self, item: str):
        """Open image viewer for the selected item."""
        try:
            if item and not self.current_page_data.empty:
                row_idx = int(item)
                if row_idx in self.current_page_data.index:
                    row_data = self.current_page_data.loc[row_idx]
                    
                    # Create a temporary image widget for the viewer
                    # This would integrate with the existing ImageViewerWindow
                    logger.info(f"Opening image viewer for {row_data.get('Path', 'Unknown')}")
                    messagebox.showinfo("Image Viewer", f"Would open image viewer for:\n{row_data.get('Path', 'Unknown')}")
        
        except Exception as e:
            logger.error(f"Error opening image viewer: {e}", exc_info=True)
    
    # Navigation methods
    def go_to_first_page(self):
        """Go to the first page."""
        self.current_page = 0
        self.update_display()
    
    def go_to_previous_page(self):
        """Go to the previous page."""
        if self.current_page > 0:
            self.current_page -= 1
            self.update_display()
    
    def go_to_next_page(self):
        """Go to the next page."""
        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_display()
    
    def go_to_last_page(self):
        """Go to the last page."""
        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        self.current_page = total_pages - 1
        self.update_display()
    
    def go_to_page(self, event=None):
        """Go to a specific page number."""
        try:
            page_num = int(self.page_entry.get()) - 1
            total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
            
            if 0 <= page_num < total_pages:
                self.current_page = page_num
                self.update_display()
            else:
                messagebox.showwarning("Invalid Page", f"Please enter a page number between 1 and {total_pages}")
                
        except ValueError:
            messagebox.showwarning("Invalid Input", "Please enter a valid page number")
    
    # Action methods
    def move_selected(self):
        """Move selected images."""
        if not self.selected_rows:
            return
        
        # This would integrate with the main app's move functionality
        selected_count = len(self.selected_rows)
        logger.info(f"Moving {selected_count} selected images")
        messagebox.showinfo("Move Selected", f"Would move {selected_count} selected images")
    
    def delete_selected(self):
        """Delete selected images."""
        if not self.selected_rows:
            return
        
        selected_count = len(self.selected_rows)
        result = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete {selected_count} selected image(s)?\n\n"
            f"This action cannot be undone."
        )
        
        if result:
            logger.info(f"Deleting {selected_count} selected images")
            messagebox.showinfo("Delete Selected", f"Would delete {selected_count} selected images")
    
    def close(self):
        """Close the list screen."""
        if self.window:
            self.window.destroy()
            logger.info("List screen closed")