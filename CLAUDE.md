# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

"lineup" is a cross-platform desktop application for managing and organizing photo collections by identifying and handling duplicate or similar images. The application reads CSV data containing grouped similar photos and provides a GUI for users to review and take actions (delete/move) on duplicate images.

## Development Commands

```bash
# Run the application
uv run main.py

# Install dependencies
uv sync

# The project uses Python 3.13+ as specified in pyproject.toml
# Always use uv for running and testing the application
```

## Architecture

This is an early-stage Python project that will be developed into a cross-platform GUI application. Current structure:

- `main.py` - Entry point with basic "Hello World" functionality
- `pyproject.toml` - Python project configuration requiring Python 3.13+
- `requirements/requirements.md` - Detailed project requirements and specifications

## Key Requirements from requirements.md

The application must:
1. Read CSV files with fields: GroupID, Master, File, Path, MatchReasons
2. Display images grouped by GroupID with Master image highlighted
3. Allow users to select and perform actions (delete/move) on images
4. Be cross-platform (Windows, Linux, macOS)
5. Handle missing/inaccessible files gracefully
6. Provide responsive performance with large image collections
7. Include features like undo, search, filtering, dark mode, and keyboard shortcuts

## Development Approach

Per requirements.md, the development process should follow:
1. Review mockup.png for interface reference
2. Propose appropriate technologies
3. Create implementation plan
4. Step-by-step implementation with feedback
5. Testing on all three platforms
6. Final deliverable as complete source code with documentation

The project emphasizes modern, intuitive UI/UX, robust error handling, maintainability, and extensibility for future enhancements.