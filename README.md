# Interactive Story Game

A web-based gamebook reader that converts EPUB "Choose Your Own Adventure" style books into interactive stories using the inkjs library.

## Features

- **EPUB Import**: Upload and process gamebook EPUB files
- **Interactive Story Engine**: Uses inkjs for narrative flow and choice management
- **Progress Tracking**: Save and resume your adventures
- **Clean UI**: Responsive design with dark/light theme support
- **Python Backend**: Robust EPUB processing with Flask REST API

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Modern web browser

### Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd interactive-story-game
   ```

2. **Start the backend server**:
   ```bash
   python start_backend.py
   ```
   This will automatically install dependencies and start the Flask server on `http://localhost:5000`

3. **Open the frontend**:
   - Open `index.html` in your web browser
   - Or serve it using any local web server:
   ```bash
   # Using Python
   python -m http.server 8000
   # Then visit http://localhost:8000
   ```

### Usage

1. **Upload an EPUB**: Drag and drop or select a gamebook EPUB file
2. **Start Playing**: Click on the imported book to begin your adventure
3. **Make Choices**: Follow the narrative and make decisions
4. **Auto-save**: Your progress is automatically saved

## Project Structure

```
interactive-story-game/
├── README.md                 # This file
├── index.html               # Main frontend page
├── start_backend.py         # Backend startup script
├── package.json             # Frontend dependencies
│
├── src/                     # Frontend source code
│   ├── js/
│   │   ├── main.js          # Main application controller
│   │   ├── ApiClient.js     # Backend communication
│   │   ├── GameEngine.js    # inkjs integration
│   │   └── UIManager.js     # UI state management
│   ├── css/
│   │   └── styles.css       # Application styling
│   └── assets/              # Static assets
│
├── backend/                 # Python backend
│   ├── app.py              # Main Flask application
│   ├── requirements.txt    # Python dependencies
│   ├── src/                # Backend modules
│   │   ├── epub_parser.py  # EPUB processing logic
│   │   ├── ink_converter.py # Gamebook to ink conversion
│   │   ├── book_manager.py # Book data management
│   │   ├── config.py       # Configuration management
│   │   └── utils.py        # Utility functions
│   ├── data/               # Application data
│   │   ├── books.json      # Book metadata
│   │   ├── ink_scripts/    # Generated ink scripts
│   │   └── saves/          # Game save files
│   └── uploads/            # Uploaded EPUB files
│
├── docs/                   # Documentation
│   ├── PRD_Interactive_Story_Game.md  # Product requirements
│   ├── CLAUDE.md          # Development notes
│   ├── README_BACKEND.md  # Backend documentation
│   └── references/        # Reference documentation
│
└── examples/              # Example files
    └── book/              # Sample EPUB files
```

## Architecture

### Backend (Python/Flask)
- **EPUB Processing**: Uses `ebooklib` for reliable EPUB parsing
- **Content Extraction**: Extracts paragraphs, choices, and combat stats
- **Ink Conversion**: Converts gamebook structure to ink script format
- **REST API**: Clean API endpoints for all operations

### Frontend (HTML/CSS/JavaScript)
- **Game Engine**: inkjs integration for story management
- **UI Management**: Clean, responsive interface
- **API Communication**: Handles backend communication with error handling
- **State Management**: Local storage and backend persistence

## API Endpoints

- `GET /api/health` - Server health check
- `GET /api/books` - List all imported books
- `POST /api/upload` - Upload EPUB file
- `GET /api/books/{id}` - Get book details
- `GET /api/books/{id}/ink` - Get ink script for book
- `POST /api/saves/{id}` - Save game state
- `GET /api/saves/{id}` - Load game state

## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
python app.py
```

### Frontend Development
The frontend is vanilla HTML/CSS/JavaScript. Simply modify files and refresh the browser.

### Scripts
- `npm run dev` - Start local development server
- `python start_backend.py` - Start backend with auto-install

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript (ES6+), inkjs
- **Backend**: Python 3.8+, Flask, ebooklib, BeautifulSoup4
- **Storage**: JSON files, local filesystem
- **Architecture**: REST API with static frontend

## Troubleshooting

### Backend Issues
- **Module not found**: Run `pip install -r backend/requirements.txt`
- **Port in use**: Change `PORT` in `backend/src/config.py`
- **EPUB parsing errors**: Check that the EPUB file is a valid gamebook format

### Frontend Issues
- **Backend unavailable**: Ensure the Python server is running on port 5000
- **CORS errors**: The backend includes CORS support; check browser console for details

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source under the MIT License. See LICENSE file for details.