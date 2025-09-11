# Lineup - Photo Duplicate Manager

A cross-platform, intuitive, python-based desktop application with GUI for identifying and handling duplicate or similar images based on output from preprocessing a directory using [photochomper](https://github.com/johnzastrow/photochomper).


## ✨ Key Features

### **Smart Image Management**
- **CSV Data Import**: Load photo groupings from CSV files from [photochomper](https://github.com/johnzastrow/photochomper) 
- **Dynamic Thumbnails**: Adaptive thumbnail sizing that maximizes screen usage (200-400px)
- **Visual Group Navigation**: Color-coded group selection with live image counts
- **Master Image Highlighting**: Clear ★ MASTER (recommended image to keep) indicators 

### **Advanced Viewing & Navigation**
- **Full-Size Image Viewer**: Double-click thumbnails for detailed viewing
- **Cross-Group Navigation**: Previous/Next group buttons in image viewer
- **Keyboard Shortcuts**: Left/Right arrows for image navigation, Esc to close
- **Smart Image Scaling**: Maintains aspect ratio while fitting window size
- **Group Information Display**: Shows current position, match reasons, and statistics

### **Efficient Batch Operations**
- **Visual Selection**: Click to select images (red borders for feedback)
- **Global Move Directory**: Set once, use everywhere with visual confirmation
- **Smart File Operations**: Automatic conflict resolution with naming
- **Operation Status**: Real-time feedback with color-coded messages
- **Auto-Refresh**: Instant UI updates after move/delete operations

### **Professional Interface**
- **Dark Mode Support**: System-aware theme switching
- **Responsive Layout**: Adapts to different screen sizes and window configurations
- **Visual Feedback**: Color-coded borders (green=unselected, red=selected, blue=selected group)
- **Status Indicators**: Clear operation progress and results
- **Text Wrapping**: Full filename display without truncation

### **Comprehensive Logging**
- **Multi-Level Logging**: Debug, Info, and Error levels with separate files
- **Structured Format**: Includes timestamps, function names, and line numbers
- **Performance Tracking**: Monitor load times and operation efficiency
- **Audit Trail**: Complete record of user actions and file operations

## Requirements

- Python 3.13+ (recommended)
- customtkinter >= 5.2.0
- pillow >= 10.0.0  
- pandas >= 2.0.0
- uv (for dependency management, optional but recommended)
- (Optional) photochomper for generating CSV files
-  Windows, macOS, or Linux OS
  
  
## Installation and Quick Start

This app was built and tested using Python 3.13 and using the `uv` tool from Astral for dependency management.

**1. Clone the repository:**
```bash
git clone <repository-url>
cd lineup
```

**2. Install dependencies using uv:**
```bash
uv sync
```

**3. Launch the application:**
```bash
uv run main.py
```
**Once in the UI, follow these steps:**

1. **Load your data**: Click "Load CSV File" and select your photo groupings file

2. **Set up "Move to" directory** (optional): Click "Browse..." next to "Move To:" to pre-select a destination folder

3. **Navigate groups**: Click on any group in the left panel - selected groups show in blue

4. **Review images**: 
   - Thumbnails automatically size to use available screen space
   - Master images show with ★ MASTER 
   - Missing files display with ❌ indicators

5. **Select and manage duplicates**:
   - Single-click images to select (red/orange borders)
   - Use "Delete Selected" or "Move Selected" buttons
   - Status messages show operation results

6. **Use the image viewer**:
   - Double-click any thumbnail for full-size viewing
   - Navigate with arrow keys or Previous/Next buttons
   - Jump between groups without closing the viewer
   - Delete or move images directly from the viewer

## 🎯 Pro Tips

- **Batch workflow**: Set a "Move To" directory once, then quickly process multiple groups
- **Keyboard navigation**: Use ← → keys in the image viewer for efficient review
- **Visual indicators**: 
  - Green borders = unselected images
  - Red borders = selected images
  - Blue group buttons = currently selected
  - ★ MASTER text = recommended keeper images
- **Check logs**: View detailed activity in `logs/lineup_info.log`

## CSV Format

Your CSV file should contain these columns and you can generate it using the `--search` function in [photochomper](https://github.com/johnzastrow/photochomper) or create it manually:
- `GroupID`: Identifier grouping similar photos together
- `Master`: Boolean indicating the recommended image to keep
- `File`: Image filename
- `Path`: Full path to the image file
- `MatchReasons`: Description of why images are considered duplicates

Example CSV structure:
```csv
GroupID,Master,File,Path,MatchReasons
1,True,IMG_001.jpg,/path/to/IMG_001.jpg,Exact duplicate
1,False,IMG_001_copy.jpg,/path/to/IMG_001_copy.jpg,Visually similar, Same size, Same Date
```

A sample CSV file (`sample_data.csv`) is included for testing.



## 🛠️ Development

### **Architecture**

The application follows a clean, modular architecture:

- **`main.py`**: Main application with enhanced UI, logging, and global state management
- **`data_manager.py`**: CSV processing, validation, and group management
- **`image_manager.py`**: Image loading, caching, thumbnails, and full-size viewer

### **Technology Stack**

- **GUI Framework**: customtkinter (modern, themeable UI components)
- **Image Processing**: Pillow (thumbnail generation, format support)
- **Data Handling**: pandas (CSV parsing, data manipulation)
- **Caching**: File-based thumbnail cache with metadata
- **Logging**: Multi-level structured logging system

### **Key Features Implementation**

- **Dynamic Layout**: Responsive grid system with optimal thumbnail sizing
- **State Management**: Global directory sharing between main app and image viewer
- **Visual Feedback**: Real-time UI updates with color-coded status indicators
- **Performance**: Asynchronous thumbnail loading with progress callbacks
- **Error Handling**: Comprehensive exception handling with user-friendly messages

### **File Structure**
```
lineup/
├── main.py              # Main application and UI logic
├── data_manager.py      # CSV data processing
├── image_manager.py     # Image handling and viewer
├── logs/               # Application logs
│   ├── lineup_debug.log # Detailed debug information
│   └── lineup_info.log  # User actions and events
├── .image_cache/       # Thumbnail cache
├── sample_data.csv     # Sample data for testing
└── CLAUDE.md          # Development guidelines
```

### **Development Commands**

```bash
# Run the application
uv run main.py

# Install/update dependencies  
uv sync

# View logs
tail -f logs/lineup_info.log
```

## License

See LICENSE file for details.
