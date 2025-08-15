# Interactive Story Game - Backend Setup

## 🚀 Quick Start

### Option 1: Automatic Setup (Recommended)
```bash
python start_backend.py
```

### Option 2: Manual Setup
```bash
cd backend
pip install -r requirements.txt
python app.py
```

## 📋 Requirements

- **Python 3.8+** 
- **pip** (Python package manager)

## 🔧 Installation

1. **Install Python dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Start the Flask server:**
   ```bash
   python app.py
   ```

   The server will start on `http://localhost:5000`

## 🧪 Testing

### Backend API Test
Visit `http://localhost:8000/backend_test.html` to test the backend:

- ✅ Check backend health status
- 📚 Create test books
- 📤 Upload EPUB files
- 🔍 View processed books and ink scripts

### Main Application
Visit `http://localhost:8000` for the full application:

- Upload EPUB files through the web interface
- Play interactive stories
- Save game progress

## 📁 Backend Structure

```
backend/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── uploads/           # Temporary EPUB uploads
├── data/             # Persistent data storage
│   ├── books.json    # Books index
│   ├── book_*.json   # Individual book data
│   ├── ink_scripts/  # Generated ink scripts
│   └── saves/        # Game save files
└── src/
    ├── epub_parser.py    # EPUB processing
    ├── ink_converter.py  # EPUB → Ink conversion
    └── book_manager.py   # Data management
```

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/books` | GET | List all books |
| `/api/books/<id>` | GET | Get book details |
| `/api/books/<id>/ink` | GET | Get ink script |
| `/api/upload` | POST | Upload EPUB |
| `/api/saves/<id>` | GET/POST/DELETE | Game saves |
| `/api/test/simple-book` | POST | Create test book |

## 🔍 Troubleshooting

### Backend won't start
- Check Python version: `python --version`
- Install dependencies: `pip install -r backend/requirements.txt`
- Check port 5000 is available

### EPUB processing fails
- Ensure file is valid EPUB format
- Check file size (max 50MB)
- Look at console logs for detailed errors

### Frontend can't connect
- Verify backend is running on `http://localhost:5000`
- Check CORS settings
- Browser console may show connection errors

## 📊 Features

### EPUB Processing
- ✅ Validates EPUB format
- ✅ Extracts metadata (title, author, cover)
- ✅ Parses paragraph numbers and choices
- ✅ Detects combat encounters
- ✅ Converts to ink script format

### Data Management
- ✅ Persistent book storage
- ✅ Game save/load functionality
- ✅ Multiple books support
- ✅ JSON-based data format

### Error Handling
- ✅ File validation
- ✅ Graceful error responses
- ✅ Detailed error messages
- ✅ Fallback mechanisms

## 🎮 Usage Flow

1. **Start Backend**: `python start_backend.py`
2. **Open Frontend**: Visit `http://localhost:8000`
3. **Upload EPUB**: Drag & drop or select EPUB file
4. **Play Story**: Click on processed book to start
5. **Save Progress**: Game auto-saves at each choice

The backend handles all EPUB processing, leaving the frontend to focus on the game experience!