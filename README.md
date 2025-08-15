# You Are The Hero

A web-based gamebook reader that converts EPUB "Choose Your Own Adventure" style books into interactive stories.

## Features

- **Human-in-the-Loop Workflow**: EPUB → Markdown → Manual Review → Game
- **Manual Section Tagging**: Identify Introduction, Rules, Title sections
- **Auto-save**: Progress automatically saved
- **Clean Terminal UI**: Retro interface with debug panel
- **Database Separation**: Sensitive data isolated from working files

## Quick Start

### Prerequisites

- Python 3.8 or higher
- Modern web browser

### Installation & Setup

1. **Clone and setup**:
   ```bash
   git clone https://github.com/nmarchand73/you_are_the_hero.git
   cd you_are_the_hero
   cd backend && pip install -r requirements.txt
   ```

2. **Start the server**:
   ```bash
   python app.py
   # Server runs on http://localhost:5000
   ```

3. **Open the game**:
   - Open `index.html` in your web browser
   - Games auto-save, no manual save needed

### Adding Books

**3-Step Workflow:**

```bash
# 1. Convert EPUB to reviewable Markdown
python scripts/epub_to_md.py your_book.epub

# 2. Manual review: Edit backend/data/reviews/your_book_review.md
#    - Change "## Section inconnue (...)" to "## Introduction" 
#    - Change "## Section inconnue (...)" to "## Title" 
#    - Change "## Section inconnue (...)" to "## Rules"

# 3. Index to game database  
cd backend && python app.py --index
```

**Key manual edits needed:**
- Identify and tag Introduction section: `## Introduction`
- Identify and tag Title page: `## Title` 
- Identify and tag Rules section: `## Rules`
- Game always starts from Introduction section

### Playing Games

1. **Start Backend**: `cd backend && python app.py`
2. **Open Frontend**: Open `index.html` in your browser
3. **Select Book**: Choose from your imported books
4. **Play**: Make choices and enjoy your adventure!

## Project Structure

```
you_are_the_hero/
├── index.html               # Main frontend
├── scripts/
│   └── epub_to_md.py       # EPUB → Markdown converter
├── backend/
│   ├── app.py              # Flask server
│   ├── src/                # Backend modules
│   ├── data/               # Working files
│   │   ├── epubs/          # Source EPUB files
│   │   └── reviews/        # Generated markdown reviews
│   └── database/           # Game database (gitignored)
│       ├── books.json      # Book index
│       ├── book_*.json     # Individual book data
│       ├── ink_scripts/    # Generated ink scripts
│       └── saves/          # Player save files
└── src/                    # Frontend code
    ├── js/                 # Game engine
    └── css/                # Styling
```

## Technology Stack

- **Backend**: Python 3.8+, Flask, BeautifulSoup4, zipfile
- **Frontend**: Vanilla HTML/CSS/JavaScript (no frameworks)
- **Storage**: JSON files in dedicated database directory
- **Workflow**: Human-in-the-loop EPUB processing

## License

MIT License