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
        this.navigationHistory = [];
        this.debugPanelVisible = true;
        
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
        // Navigation
        document.getElementById('back-btn')?.addEventListener('click', () => this.showHomeScreen());

        // Game controls
        // Save button removed - auto-save is enabled
        document.getElementById('reset-btn')?.addEventListener('click', () => this.resetGame());
        
        // Debug controls
        document.getElementById('toggle-debug')?.addEventListener('click', () => this.toggleDebugPanel());
        
        // Note: Index EPUBs functionality removed - use CLI: python app.py --index

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
        
        const welcomeSection = document.querySelector('.welcome-section');
        if (!welcomeSection) return;

        const offlineMessage = document.createElement('div');
        offlineMessage.id = 'offline-message';
        offlineMessage.innerHTML = `
            <div style="background: rgba(255, 0, 0, 0.1); border: 1px solid var(--terminal-green-dim); padding: 15px; margin-bottom: 20px; font-family: var(--font-mono);">
                <strong style="color: var(--terminal-green);">[CONNECTION ERROR]</strong><br>
                <span style="color: var(--terminal-text);">TERMINAL SERVER OFFLINE. EXECUTE:</span>
                <code style="background: var(--terminal-bg); color: var(--terminal-green); padding: 4px 8px; border: 1px solid var(--terminal-green-dim); display: inline-block; margin-top: 8px;">
                    python start_backend.py
                </code>
            </div>
        `;
        
        welcomeSection.insertBefore(offlineMessage, welcomeSection.firstChild);
    }

    removeOfflineMessage() {
        const message = document.getElementById('offline-message');
        message?.remove();
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

    // Note: indexEPUBs method removed - use CLI: python app.py --index

    displayBookLibrary(books) {
        const bookList = document.getElementById('book-list');
        const librarySection = document.getElementById('library-section');

        if (!bookList) return;

        // Always show library section
        librarySection.style.display = 'block';
        
        if (books.length === 0) {
            bookList.innerHTML = `
                <div style="text-align: center; padding: 2rem; color: var(--terminal-text-dim); font-family: var(--font-mono);">
                    <p style="color: var(--terminal-green); text-transform: uppercase; margin-bottom: 1rem;">[NO MODULES FOUND]</p>
                    <p style="font-size: 0.9rem;">PLACE .EPUB FILES IN backend/data/epubs/</p>
                    <p style="font-size: 0.9rem;">RESTART TERMINAL TO RELOAD DATABASE</p>
                </div>
            `;
            return;
        }
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
            ? `LAST: ${book.last_section}` 
            : 'STATUS: NEW';

        bookDiv.innerHTML = `
            <div class="book-title">${this.escapeHtml(book.title)}</div>
            <div class="book-author">by ${this.escapeHtml(book.author)}</div>
            <div class="book-progress">${progressText}</div>
            <div class="book-stats">${book.total_sections}</div>
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
            
            // Initialize debug info
            this.navigationHistory = [];
            const startingSection = this.gameEngine.currentSection;
            this.addToNavigationHistory(null, startingSection, null, 'Game started');
            
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
            this.updateDebugInfo();
        } catch (error) {
            console.error('Game display update failed:', error);
            console.error('Error details:', error.stack);
            this.showErrorModal('Game Error', `Failed to update game display: ${error.message}`);
        }
    }

    displayStoryText(text) {
        const storyTextElement = document.getElementById('story-text');
        if (!storyTextElement) return;

        // Handle empty text explicitly
        if (text === null || text === undefined) {
            storyTextElement.innerHTML = '<p><em>Aucun texte disponible</em></p>';
            return;
        }

        // If text is empty string, show placeholder
        if (text.length === 0) {
            storyTextElement.innerHTML = '<p><em>Section sans texte - passez directement au choix</em></p>';
            return;
        }

        const formattedText = text
            .split('\n\n')
            .filter(p => p.trim().length > 0)
            .map(p => {
                // Preserve single line breaks within paragraphs
                const paragraphContent = this.escapeHtml(p.trim())
                    .replace(/\n/g, '<br>');
                return `<p>${paragraphContent}</p>`;
            })
            .join('');

        // If after formatting there's no content, show placeholder
        if (formattedText.length === 0) {
            storyTextElement.innerHTML = '<p><em>Section sans texte - passez directement au choix</em></p>';
        } else {
            storyTextElement.innerHTML = formattedText;
        }
    }

    displayChoices(choices) {
        const choicesContainer = document.getElementById('choices-container');
        if (!choicesContainer) return;

        choicesContainer.innerHTML = '';

        if (!choices || choices.length === 0) {
            choicesContainer.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; color: var(--terminal-green); font-style: italic;">Fin de l\'aventure</div>';
            return;
        }

        choices.forEach((choice, index) => {
            // Create choice item container
            const choiceItem = document.createElement('div');
            choiceItem.className = 'choice-item';
            
            // Check if choice destination is available
            const isAvailable = choice.isAvailable !== false; // Default to true for backward compatibility
            
            if (!isAvailable) {
                choiceItem.className += ' choice-unavailable';
            }
            
            // Create choice text element
            const choiceText = document.createElement('div');
            choiceText.className = 'choice-text';
            
            // Improve malformed choice text before displaying
            const improvedText = this.improveChoiceText(choice.text, choice.destination);
            choiceText.textContent = improvedText;
            
            if (!isAvailable) {
                choiceText.textContent += ' [SECTION CORROMPUE]';
            }
            
            if (isAvailable) {
                // Add click handler to the entire item for better UX
                choiceItem.addEventListener('click', () => this.makeChoice(index));
                choiceItem.style.cursor = 'pointer';
            }
            
            choiceItem.appendChild(choiceText);
            choicesContainer.appendChild(choiceItem);
        });
    }

    /**
     * Improve malformed choice text by detecting and fixing common parsing issues
     * @param {string} text - Original choice text
     * @param {number} destination - Choice destination section
     * @returns {string} Improved choice text
     */
    improveChoiceText(text, destination) {
        if (!text || typeof text !== 'string') {
            console.log(`[improveChoiceText] Empty text, returning default for destination ${destination}`);
            return `Continuer → ${destination}`;
        }

        console.log(`[improveChoiceText] Processing: "${text}" → ${destination}`);

        // Pattern 1: Fragment like "s au 191. s'il est supérieur,"
        // This indicates a dice roll condition that was fragmented
        if (/^s au \d+\. s'il est (supérieur|inférieur|égal)/i.test(text)) {
            const improved = `Continuer si votre jet de dé est ${text.includes('supérieur') ? 'supérieur' : text.includes('inférieur') ? 'inférieur' : 'égal'} → ${destination}`;
            console.log(`[improveChoiceText] Pattern 1 matched! Improved to: "${improved}"`);
            return improved;
        }

        // Pattern 2: Fragment starting with conditional words
        if (/^(si |s'il |si vous |si votre)/i.test(text)) {
            const improved = `Continuer ${text} → ${destination}`;
            console.log(`[improveChoiceText] Pattern 2 matched! Improved to: "${improved}"`);
            return improved;
        }

        // Pattern 3: Fragment ending with incomplete sentence (but not dice rolls)
        if ((text.endsWith(',') || text.endsWith('.')) && text.length < 20 && !/s au \d+\./i.test(text)) {
            const improved = `${text.replace(/[,.]$/, '')} → ${destination}`;
            console.log(`[improveChoiceText] Pattern 3 matched! Improved to: "${improved}"`);
            return improved;
        }

        // Pattern 4: Very short fragments (less than 10 characters)
        if (text.trim().length < 10) {
            const improved = `Continuer → ${destination}`;
            console.log(`[improveChoiceText] Pattern 4 matched! Improved to: "${improved}"`);
            return improved;
        }

        // Pattern 5: Fragment with incomplete dice reference
        if (/\d+\.\s*$/.test(text)) {
            const improved = `${text.replace(/\d+\.\s*$/, '')} → ${destination}`;
            console.log(`[improveChoiceText] Pattern 5 matched! Improved to: "${improved}"`);
            return improved;
        }

        // Return original text if no patterns match
        console.log(`[improveChoiceText] No patterns matched, returning original: "${text}"`);
        return text;
    }

    async makeChoice(choiceIndex) {
        try {
            // Get current state before making choice
            const currentSection = this.gameEngine.currentSection;
            const storyData = this.gameEngine.continue();
            const choice = storyData.choices[choiceIndex];
            
            // Make the choice
            this.gameEngine.makeChoice(choiceIndex);
            
            // Track navigation
            this.addToNavigationHistory(
                currentSection, 
                choice.destination, 
                choiceIndex, 
                choice.text.substring(0, 50) + (choice.text.length > 50 ? '...' : '')
            );
            
            this.updateGameDisplay();
            
            // Auto-save
            await this.saveGame();
            
        } catch (error) {
            console.error('Choice handling failed:', error);
            console.error('Error details:', error.stack);
            this.showErrorModal('Game Error', `Failed to process choice: ${error.message}`);
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

    async resetGame() {
        if (!this.currentBook || !this.gameEngine.hasStory()) {
            return;
        }

        try {
            // Confirm reset with user
            if (!confirm('Are you sure you want to restart the adventure from the beginning? All progress will be lost.')) {
                return;
            }

            // Reset the game engine to starting section
            this.gameEngine.reset();
            
            console.log('🔄 Game reset to beginning');
            this.ui.showNotification('Adventure restarted', 'success', 2000);
            
            // Update the display to show the starting section
            this.updateGameDisplay();
            
        } catch (error) {
            console.error('Reset failed:', error);
            this.ui.showNotification('Reset failed', 'error', 3000);
        }
    }

    toggleDebugPanel() {
        const debugPanel = document.getElementById('debug-panel');
        const toggleButton = document.getElementById('toggle-debug');
        
        if (!debugPanel || !toggleButton) return;
        
        this.debugPanelVisible = !this.debugPanelVisible;
        
        if (this.debugPanelVisible) {
            debugPanel.classList.remove('hidden');
            toggleButton.textContent = 'HIDE';
            this.updateDebugInfo();
        } else {
            debugPanel.classList.add('hidden');
            toggleButton.textContent = 'SHOW';
        }
    }

    updateDebugInfo() {
        if (!this.debugPanelVisible || !this.gameEngine.hasStory()) return;

        try {
            // Current section info
            const currentSection = this.gameEngine.currentSection;
            const storyData = this.gameEngine.continue();
            
            document.getElementById('debug-current-section').innerHTML = 
                `Section: <strong>${currentSection}</strong><br>` +
                `Text length: ${storyData.text.length} chars<br>` +
                `Choices: ${storyData.choices.length}`;

            // Available choices
            const choicesHtml = storyData.choices.map((choice, index) => 
                `<div class="debug-choice">` +
                `[${index}] "${choice.text}" → ${choice.destination} ` +
                `${choice.isAvailable ? '✓' : '✗ (missing)'}` +
                `</div>`
            ).join('');
            document.getElementById('debug-choices').innerHTML = choicesHtml || 'No choices available';

            // Navigation history (last 10 items)
            const historyHtml = this.navigationHistory.slice(-10).map((item, index) => 
                `<div class="debug-path-item">` +
                `${item.timestamp} - Section ${item.from} → ${item.to} ` +
                `(Choice: "${item.choiceText}")` +
                `</div>`
            ).join('');
            document.getElementById('debug-history').innerHTML = historyHtml || 'No navigation history';

        } catch (error) {
            console.error('Debug update failed:', error);
        }
    }

    addToNavigationHistory(fromSection, toSection, choiceIndex, choiceText) {
        const timestamp = new Date().toLocaleTimeString();
        this.navigationHistory.push({
            timestamp,
            from: fromSection,
            to: toSection,
            choiceIndex,
            choiceText
        });
        
        // Keep only last 50 items
        if (this.navigationHistory.length > 50) {
            this.navigationHistory = this.navigationHistory.slice(-50);
        }
        
        this.updateDebugInfo();
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