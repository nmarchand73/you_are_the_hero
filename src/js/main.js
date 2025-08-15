/**
 * Interactive Story Game - Main Application Controller
 * 
 * Coordinates the frontend application, manages API communication,
 * and handles the game flow between screens.
 */

import { ApiClient } from './ApiClient.js';
import { GameEngine } from './GameEngine.js';
import { UIManager } from './UIManager.js';

class InteractiveStoryApp {
    constructor() {
        this.api = new ApiClient();
        this.gameEngine = new GameEngine();
        this.ui = new UIManager();
        
        this.currentBook = null;
        this.isLoading = false;
        this.isBackendAvailable = false;
        
        this.initialize();
    }

    async initialize() {
        console.log('🎮 Initializing Interactive Story Game...');
        
        try {
            this.setupEventListeners();
            this.ui.init();
            
            await this.checkBackendStatus();
            await this.loadBookLibrary();
            
            console.log('✅ Application initialized successfully');
        } catch (error) {
            console.error('❌ Initialization failed:', error);
            this.ui.showNotification('Failed to initialize application', 'error');
        }
    }

    // ====================================================================
    // EVENT LISTENERS
    // ====================================================================

    setupEventListeners() {
        // File upload
        const fileInput = document.getElementById('file-input');
        const selectFileBtn = document.getElementById('select-file-btn');
        const dropZone = document.getElementById('drop-zone');

        selectFileBtn?.addEventListener('click', () => fileInput?.click());
        fileInput?.addEventListener('change', (e) => this.handleFileSelect(e));

        // Drag and drop
        dropZone?.addEventListener('dragover', this.handleDragOver.bind(this));
        dropZone?.addEventListener('dragleave', this.handleDragLeave.bind(this));
        dropZone?.addEventListener('drop', this.handleDrop.bind(this));

        // Navigation
        document.getElementById('back-btn')?.addEventListener('click', () => this.showHomeScreen());

        // Theme toggles
        document.getElementById('theme-toggle')?.addEventListener('click', () => this.ui.toggleTheme());
        document.getElementById('game-theme-toggle')?.addEventListener('click', () => this.ui.toggleTheme());

        // Game controls
        document.getElementById('save-btn')?.addEventListener('click', () => this.saveGame());

        // Modal controls
        document.getElementById('close-error-modal')?.addEventListener('click', () => this.hideErrorModal());
    }

    // ====================================================================
    // BACKEND COMMUNICATION
    // ====================================================================

    async checkBackendStatus() {
        try {
            this.isBackendAvailable = await this.api.isBackendAvailable();
            
            if (this.isBackendAvailable) {
                console.log('✅ Backend is online');
                this.removeOfflineMessage();
            } else {
                console.warn('⚠️ Backend is offline');
                this.showOfflineMessage();
            }
        } catch (error) {
            console.error('Backend status check failed:', error);
            this.isBackendAvailable = false;
            this.showOfflineMessage();
        }
    }

    showOfflineMessage() {
        // Remove existing message
        this.removeOfflineMessage();
        
        const uploadSection = document.querySelector('.upload-section');
        if (!uploadSection) return;

        const offlineMessage = document.createElement('div');
        offlineMessage.id = 'offline-message';
        offlineMessage.innerHTML = `
            <div style="background: #ffeaa7; border: 1px solid #fdcb6e; border-radius: 8px; padding: 15px; margin-bottom: 20px;">
                <strong>⚠️ Backend Unavailable</strong><br>
                The Python server is not accessible. To upload EPUB files, start the backend:
                <code style="background: #2d3436; color: #ddd; padding: 4px 8px; border-radius: 4px; display: inline-block; margin-top: 8px;">
                    python start_backend.py
                </code>
            </div>
        `;
        
        uploadSection.insertBefore(offlineMessage, uploadSection.firstChild);
    }

    removeOfflineMessage() {
        const message = document.getElementById('offline-message');
        message?.remove();
    }

    // ====================================================================
    // FILE HANDLING
    // ====================================================================

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (file) {
            this.processEPUBFile(file);
        }
        event.target.value = ''; // Reset for re-selection
    }

    handleDragOver(event) {
        event.preventDefault();
        event.currentTarget.classList.add('dragover');
    }

    handleDragLeave(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('dragover');
    }

    handleDrop(event) {
        event.preventDefault();
        event.currentTarget.classList.remove('dragover');
        
        const files = event.dataTransfer.files;
        if (files.length > 0) {
            this.processEPUBFile(files[0]);
        }
    }

    async processEPUBFile(file) {
        if (this.isLoading) return;
        
        if (!this.isBackendAvailable) {
            this.showErrorModal('Backend Unavailable', 'Please start the Python backend server to process EPUB files.');
            return;
        }

        this.isLoading = true;
        this.showLoadingState('Uploading EPUB file...');

        try {
            console.log('📤 Processing EPUB:', file.name);

            const result = await this.api.uploadEPUB(file, (progress) => {
                this.updateLoadingText(`Upload progress: ${progress}%`);
            });

            this.updateLoadingText('Processing complete, updating library...');
            
            console.log('✅ Book processed:', result.book.title);
            this.hideLoadingState();
            
            this.ui.showNotification(`Book "${result.book.title}" imported successfully!`, 'success');
            await this.loadBookLibrary();

        } catch (error) {
            console.error('❌ EPUB processing failed:', error);
            this.hideLoadingState();
            this.showErrorModal('Import Error', error.message);
        } finally {
            this.isLoading = false;
        }
    }

    // ====================================================================
    // BOOK LIBRARY MANAGEMENT
    // ====================================================================

    async loadBookLibrary() {
        try {
            if (!this.isBackendAvailable) {
                this.displayBookLibrary([]);
                return;
            }

            const books = await this.api.getBooks();
            this.displayBookLibrary(books);
            console.log(`📚 Loaded ${books.length} books`);
        } catch (error) {
            console.error('Failed to load library:', error);
            this.displayBookLibrary([]);
        }
    }

    displayBookLibrary(books) {
        const bookList = document.getElementById('book-list');
        const librarySection = document.getElementById('library-section');

        if (!bookList) return;

        if (books.length === 0) {
            librarySection.style.display = 'none';
            return;
        }

        librarySection.style.display = 'block';
        bookList.innerHTML = '';

        books.forEach(book => {
            const bookElement = this.createBookElement(book);
            bookList.appendChild(bookElement);
        });
    }

    createBookElement(book) {
        const bookDiv = document.createElement('div');
        bookDiv.className = 'book-item';
        bookDiv.addEventListener('click', () => this.loadBook(book.id));

        const progressText = book.last_section 
            ? `Last paragraph: ${book.last_section}` 
            : 'Not started';

        bookDiv.innerHTML = `
            <div class="book-title">${this.escapeHtml(book.title)}</div>
            <div class="book-author">by ${this.escapeHtml(book.author)}</div>
            <div class="book-progress">${progressText}</div>
            <div class="book-stats">${book.total_sections} paragraphs</div>
        `;

        return bookDiv;
    }

    // ====================================================================
    // GAME MANAGEMENT
    // ====================================================================

    async loadBook(bookId) {
        try {
            if (!this.isBackendAvailable) {
                this.showErrorModal('Backend Unavailable', 'Please start the Python backend server to load books.');
                return;
            }

            this.showLoadingState('Loading book...');
            
            // Fetch book data and ink script
            const [bookData, inkScript] = await Promise.all([
                this.api.getBook(bookId),
                this.api.getInkScript(bookId)
            ]);

            if (!bookData || !inkScript) {
                throw new Error('Book or ink script not found');
            }

            this.currentBook = { ...bookData, id: bookId };
            
            this.updateLoadingText('Initializing game engine...');
            await this.gameEngine.loadStory(inkScript);
            
            // Load saved game if exists
            const saveData = await this.api.getSaveData(bookId);
            if (saveData) {
                this.gameEngine.loadState(saveData);
                console.log('💾 Loaded saved game state');
            }

            this.hideLoadingState();
            this.showGameScreen();
            this.updateGameDisplay();

        } catch (error) {
            console.error('Failed to load book:', error);
            this.hideLoadingState();
            this.showErrorModal('Loading Error', error.message);
        }
    }

    showGameScreen() {
        document.getElementById('home-screen')?.classList.remove('active');
        document.getElementById('game-screen')?.classList.add('active');
        
        const bookTitleElement = document.getElementById('book-title');
        if (bookTitleElement && this.currentBook) {
            bookTitleElement.textContent = this.currentBook.title;
        }
    }

    showHomeScreen() {
        document.getElementById('game-screen')?.classList.remove('active');
        document.getElementById('home-screen')?.classList.add('active');
        
        this.currentBook = null;
        this.gameEngine.reset();
    }

    updateGameDisplay() {
        if (!this.gameEngine.hasStory()) return;

        try {
            const storyData = this.gameEngine.continue();
            
            this.displayStoryText(storyData.text);
            this.displayChoices(storyData.choices);
        } catch (error) {
            console.error('Game display update failed:', error);
            this.showErrorModal('Game Error', 'Failed to update game display');
        }
    }

    displayStoryText(text) {
        const storyTextElement = document.getElementById('story-text');
        if (!storyTextElement || !text) return;

        const formattedText = text
            .split('\n\n')
            .filter(p => p.trim().length > 0)
            .map(p => `<p>${this.escapeHtml(p.trim())}</p>`)
            .join('');

        storyTextElement.innerHTML = formattedText;
    }

    displayChoices(choices) {
        const choicesContainer = document.getElementById('choices-container');
        if (!choicesContainer) return;

        choicesContainer.innerHTML = '';

        if (!choices || choices.length === 0) {
            choicesContainer.innerHTML = '<p class="text-center">End of adventure</p>';
            return;
        }

        choices.forEach((choice, index) => {
            const choiceButton = document.createElement('button');
            choiceButton.className = 'choice-btn';
            choiceButton.textContent = choice.text;
            choiceButton.addEventListener('click', () => this.makeChoice(index));
            
            choicesContainer.appendChild(choiceButton);
        });
    }

    async makeChoice(choiceIndex) {
        try {
            this.gameEngine.makeChoice(choiceIndex);
            this.updateGameDisplay();
            
            // Auto-save
            await this.saveGame();
            
        } catch (error) {
            console.error('Choice handling failed:', error);
            this.showErrorModal('Game Error', 'Failed to process choice');
        }
    }

    async saveGame() {
        if (!this.currentBook || !this.gameEngine.hasStory() || !this.isBackendAvailable) {
            return;
        }

        try {
            const gameState = this.gameEngine.getState();
            await this.api.saveGameState(this.currentBook.id, gameState);
            
            console.log('💾 Game saved successfully');
            this.ui.showNotification('Game saved', 'success', 2000);
            
        } catch (error) {
            console.error('Save failed:', error);
            this.ui.showNotification('Save failed', 'error', 3000);
        }
    }

    // ====================================================================
    // UI HELPER METHODS
    // ====================================================================

    showLoadingState(message) {
        const loadingSection = document.getElementById('loading-section');
        const loadingText = document.getElementById('loading-text');
        
        loadingSection?.classList.remove('hidden');
        if (loadingText) loadingText.textContent = message;
    }

    updateLoadingText(message) {
        const loadingText = document.getElementById('loading-text');
        if (loadingText) loadingText.textContent = message;
    }

    hideLoadingState() {
        const loadingSection = document.getElementById('loading-section');
        loadingSection?.classList.add('hidden');
    }

    showErrorModal(title, message) {
        const modal = document.getElementById('error-modal');
        const titleElement = modal?.querySelector('h3');
        const messageElement = document.getElementById('error-message');

        if (titleElement) titleElement.textContent = title;
        if (messageElement) messageElement.textContent = message;
        modal?.classList.remove('hidden');
    }

    hideErrorModal() {
        const modal = document.getElementById('error-modal');
        modal?.classList.add('hidden');
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Load saved theme
    const savedTheme = localStorage.getItem('theme') || 'light';
    document.documentElement.setAttribute('data-theme', savedTheme);
    
    // Initialize application
    window.storyApp = new InteractiveStoryApp();
});

// Handle page unload to save current state
window.addEventListener('beforeunload', () => {
    if (window.storyApp?.currentBook) {
        window.storyApp.saveGame();
    }
});