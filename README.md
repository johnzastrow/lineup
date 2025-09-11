# Lineup - Photo Duplicate Manager

A cross-platform desktop application for managing and organizing photo collections by identifying and handling duplicate or similar images.

## Features

- **CSV Data Import**: Load photo groupings from CSV files with GroupID, Master, File, Path, and MatchReasons columns
- **Visual Photo Review**: View thumbnails of grouped similar photos with master image highlighting
- **Batch Operations**: Select multiple images for deletion or moving to specified directories
- **Master Image Indication**: Clear visual indicators for recommended images to keep (★ MASTER)
- **Missing File Handling**: Graceful handling of missing or inaccessible image files
- **Dark Mode Support**: Toggle between light and dark themes
- **Responsive Layout**: Adaptive grid layout that works on different screen sizes
- **Comprehensive Logging**: Track all user actions and errors for debugging

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd lineup
```

2. Install dependencies using uv:
```bash
uv sync
```

## Usage

1. Run the application:
```bash
uv run main.py
```

2. Click "Load CSV File" to import your photo data
3. Select a group from the left panel to view images
4. Click on images to select them (red border indicates selection)
5. Use "Delete Selected" or "Move Selected" to manage duplicates

## CSV Format

Your CSV file should contain these columns:
- `GroupID`: Identifier grouping similar photos together
- `Master`: Boolean indicating the recommended image to keep
- `File`: Image filename
- `Path`: Full path to the image file
- `MatchReasons`: Description of why images are considered duplicates

Example CSV structure:
```csv
GroupID,Master,File,Path,MatchReasons
1,True,IMG_001.jpg,/path/to/IMG_001.jpg,Exact duplicate
1,False,IMG_001_copy.jpg,/path/to/IMG_001_copy.jpg,Exact duplicate
```

A sample CSV file (`sample_data.csv`) is included for testing.

## Requirements

- Python 3.13+
- customtkinter >= 5.2.0
- pillow >= 10.0.0  
- pandas >= 2.0.0

## Development

The application is built with:
- **customtkinter**: Modern GUI framework
- **Pillow**: Image processing and thumbnail generation
- **pandas**: CSV data handling and manipulation

Key components:
- `main.py`: Main application window and UI logic
- `data_manager.py`: CSV loading and data processing
- `image_manager.py`: Image loading, thumbnails, and caching

## License

See LICENSE file for details.
