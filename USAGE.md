# Lineup Usage Guide

This guide covers all the features and workflows in Lineup for efficient photo duplicate management.

## 🚀 Getting Started

### Basic Workflow
1. **Launch**: Run `uv run main.py`
2. **Load Data**: Click "Load CSV File" to import your photo groups
3. **Set Move Directory**: (Optional) Click "Browse..." to pre-select destination
4. **Review & Act**: Navigate groups, select duplicates, and take actions

## 📁 Data Requirements

### CSV File Format
Your CSV must contain these exact column headers:
- `GroupID` - Groups similar photos together (any string/number)
- `Master` - `True` for recommended keeper, `False` for duplicates  
- `File` - Image filename (e.g., "IMG_001.jpg")
- `Path` - Full file path (e.g., "/Users/name/Photos/IMG_001.jpg")
- `MatchReasons` - Why images are similar (e.g., "Exact duplicate")

### Sample CSV
```csv
GroupID,Master,File,Path,MatchReasons
1,True,IMG_001.jpg,/path/to/IMG_001.jpg,Exact duplicate
1,False,IMG_001_copy.jpg,/path/to/IMG_001_copy.jpg,Exact duplicate
2,True,vacation.jpg,/path/to/vacation.jpg,Near duplicate
2,False,vacation_edit.jpg,/path/to/vacation_edit.jpg,95% similarity
```

## 🎨 Visual Interface Guide

### Color-Coded Elements

#### **Group Navigation (Left Panel)**
- **Blue Button**: Currently selected group
- **Gray Buttons**: Unselected groups
- **Text Format**: "Group X - Y/Z images" (Y=existing, Z=total)

#### **Image Thumbnails**
- **Green Border**: Unselected image
- **Red Border**: Selected image
- **★ MASTER**: Text indicator for recommended keeper image

#### **Status Indicators**
- **★ MASTER**: Recommended image to keep
- **❌ Missing**: File not found at specified path
- **Green Status**: Successful move operations
- **Red Status**: Delete operations

## 🖱️ Navigation & Controls

### Mouse Actions
- **Single Click**: Select/deselect image
- **Double Click**: Open full-size image viewer
- **Group Button Click**: Switch to different group

### Keyboard Shortcuts
- **← →**: Navigate between images in viewer
- **Esc**: Close image viewer
- **Enter**: Close image viewer

## 🔍 Image Viewer Features

### Opening the Viewer
- Double-click any thumbnail to open full-size view
- Window opens as modal overlay
- Shows current image scaled to fit window

### Navigation Controls
- **◀ Previous / Next ▶**: Navigate within current group
- **◀ Prev Group / Next Group ▶**: Jump between groups
- **Image Counter**: "Image X of Y" shows position
- **Group Info**: Shows group details and match reasons

### Image Actions
- **Delete Image**: Remove current image with confirmation
- **Move Image**: Move to pre-selected or chosen directory
- **Auto-refresh**: Display updates after operations

## 📂 File Operations

### Setting Up Move Directory
1. Click "Browse..." next to "Move To:" in main toolbar
2. Select destination folder
3. Directory shows in green when set
4. All move operations use this directory until changed

### Moving Images
#### From Main Screen:
1. Select images (click for red borders)
2. Click "Move Selected" or "Move to Pre-selected"
3. If no directory set, you'll be prompted to choose one
4. Files moved with automatic conflict resolution

#### From Image Viewer:
1. Click "Move Image" button
2. Uses pre-selected directory or prompts for one
3. Automatically advances to next image

### Deleting Images
#### From Main Screen:
1. Select images for deletion
2. Click "Delete Selected"
3. Confirm in dialog box
4. Files permanently deleted

#### From Image Viewer:
1. Click "Delete Image" button
2. Confirm deletion
3. Automatically advances to next image

## ⚡ Advanced Features

### Dynamic Thumbnails
- Automatically sizes thumbnails (200-400px) based on window size
- More columns = smaller thumbnails
- Fewer columns = larger thumbnails
- Responsive grid adapts to window resizing

### Global Directory State
- "Move To" directory shared between main app and image viewer
- Set once, use everywhere
- Updates from either location sync immediately
- Button text changes to "Move to Pre-selected" when set

### Auto-Refresh System
- Screen updates automatically after file operations
- Group counts refresh to show current state
- Missing files display with ❌ indicators
- No manual refresh needed

### Smart Conflict Resolution
- Duplicate filenames automatically get numbered suffixes
- Example: `image.jpg` → `image_1.jpg` → `image_2.jpg`
- Prevents accidental overwrites

## 📊 Status & Feedback

### Operation Status Messages
- Appear in main toolbar after operations
- **Green**: "Moved X file(s)" for successful moves
- **Red**: "Deleted X file(s)" for deletions
- Auto-clear after 3 seconds

### Progress Tracking
- Group navigation shows "X/Y images" counts
- Image viewer shows "Image X of Y" position
- Real-time updates after operations

## 🐛 Troubleshooting

### Missing Files
- Shows ❌ indicator on thumbnails
- Can still be selected and processed
- Check logs for detailed file paths

### Performance with Large Collections
- Thumbnails cache automatically for speed
- Use `.image_cache/` directory for storage
- Clear cache by deleting `.image_cache/` folder

### Logging & Debugging
- Check `logs/lineup_info.log` for user actions
- Check `logs/lineup_debug.log` for detailed debugging
- Logs show file operations and errors

## 💡 Best Practices

### Efficient Workflow
1. **Pre-select move directory** for batch operations
2. **Use image viewer** for quick review and navigation
3. **Process groups systematically** using group navigation
4. **Check operation status** messages for confirmation

### Data Management
- **Backup important photos** before processing
- **Verify CSV paths** point to correct locations
- **Test with small batches** before large operations
- **Review master selections** before deleting duplicates

### Performance Tips
- **Close image viewer** when not needed to save memory
- **Process large collections** in smaller batches
- **Use keyboard shortcuts** for faster navigation
- **Monitor logs** for performance issues

## 🔧 Technical Notes

### File Path Requirements
- Use full absolute paths in CSV files
- Forward slashes work on all platforms
- Spaces in paths are handled automatically

### Supported Image Formats
- JPEG, PNG, TIFF, BMP, GIF
- Most common image formats supported by Pillow
- PDF files also supported for document scanning

### Cross-Platform Compatibility
- Windows: Use standard Windows paths
- macOS: Use standard Unix paths  
- Linux: Use standard Unix paths
- GUI adapts to system theme automatically