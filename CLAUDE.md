# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"lineup" is a fully-featured cross-platform desktop application for managing and organizing photo collections by identifying and handling duplicate or similar images. The application provides an intuitive GUI for reviewing CSV data containing grouped similar photos and performing batch operations (delete/move) on duplicate images.

## Development Commands

```bash
# Run the application
uv run main.py

# Install dependencies
uv sync

# View application logs
tail -f logs/lineup_info.log
tail -f logs/lineup_debug.log

# The project uses Python 3.13+ as specified in pyproject.toml
# Always use uv for running and testing the application
```

## Current Architecture

The application is a mature, production-ready GUI application with the following structure:

### **Core Modules**
- `main.py` - Main application with comprehensive UI, state management, and logging
- `data_manager.py` - CSV loading, validation, and data processing with file existence checking
- `image_manager.py` - Image handling, thumbnail caching, and full-size viewer with navigation

### **Feature Implementation Status** ✅

#### **Data Management**
- ✅ CSV file loading with comprehensive validation
- ✅ CSV file reload functionality with state preservation
- ✅ GroupID-based organization with master image detection
- ✅ File existence validation and missing file handling
- ✅ Real-time data refresh after operations

#### **User Interface**  
- ✅ Modern customtkinter-based GUI with dark mode support
- ✅ Comprehensive toolbar with Load CSV, Reload, and configuration controls
- ✅ Dynamic thumbnail sizing (200-400px) based on screen space
- ✅ Visual group selection with color-coded navigation
- ✅ Responsive grid layout that adapts to window size
- ✅ Real-time status messages and operation feedback
- ✅ Auto-select duplicates and hide single groups toggles

#### **Image Viewing & Navigation**
- ✅ Full-size image viewer with modal windows
- ✅ Cross-group navigation (Previous/Next group buttons)
- ✅ Keyboard shortcuts (←/→ for images, Esc to close, D=Delete, M=Move, N=Next Group, P=Previous Group)
- ✅ Smart image scaling maintaining aspect ratios
- ✅ Double-click thumbnails to open viewer
- ✅ Auto-advance to next group after operations for efficient workflow

#### **Batch Operations**
- ✅ Visual selection with color-coded borders
- ✅ Global "Move To" directory with state sharing across viewers
- ✅ Delete operations with confirmation dialogs and batch processing
- ✅ Move operations with conflict resolution and automatic renaming
- ✅ Automatic screen refresh and data validation after operations
- ✅ Smart selection logic (master selection clears others, auto-select non-masters)

#### **Advanced Features**
- ✅ Comprehensive multi-level logging system with file rotation
- ✅ File-based thumbnail caching with metadata and optimal sizing
- ✅ Master image highlighting with ★ indicators and protection logic
- ✅ Missing file detection with ❌ indicators and graceful handling
- ✅ Operation status display with auto-clear timers and color coding
- ✅ CSV reload with intelligent state restoration and error handling
- ✅ Image viewer state synchronization across multiple windows
- ✅ Filter controls for hiding single-image groups and auto-selection

## Development Guidelines

### **Code Organization**
- Follow existing patterns for UI layout and state management
- Use the established logger pattern: `logger = logging.getLogger('lineup.module_name')`
- Maintain separation of concerns between data, UI, and image handling
- Add comprehensive logging for user actions and errors

### **UI Development**
- Use customtkinter components consistently
- Follow the color scheme: green=unselected, blue=selected, gold=master, red=action
- Implement proper state management with refresh methods
- Add visual feedback for all user interactions

### **Testing**
- Test with the included `sample_data.csv` file
- Verify cross-platform compatibility (Windows, Linux, macOS)
- Check all keyboard shortcuts and navigation flows
- Validate file operations with missing/inaccessible files

### **Performance Considerations**
- Use asynchronous thumbnail loading for responsiveness
- Implement proper caching strategies for large collections
- Optimize grid layout calculations for smooth resizing
- Monitor memory usage with large image collections

## Logging System

The application uses structured logging with multiple levels:
- `logs/lineup_debug.log` - Complete debug information with function names
- `logs/lineup_info.log` - User actions and important events
- Console output - Warnings and errors only

Log format: `timestamp - module - level - function:line - message`

## Key Implementation Patterns

### **State Management**
- Global state tracked in main application instance
- UI refresh methods for data synchronization
- Event-driven updates between components

### **Error Handling**
- Comprehensive exception handling with user-friendly messages
- Graceful degradation for missing files
- Detailed logging for debugging issues

### **Visual Feedback**
- Immediate status messages for operations
- Color-coded UI elements for different states
- Auto-clearing temporary messages

The project is feature-complete and ready for production use, with extensible architecture for future enhancements.