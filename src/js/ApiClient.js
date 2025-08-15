/**
 * API Client for Interactive Story Game Backend
 * 
 * Handles all HTTP communication with the Python Flask backend,
 * including file uploads with progress tracking and error handling.
 */

export class ApiClient {
    constructor(baseURL = 'http://localhost:5000/api') {
        this.baseURL = baseURL;
        this.timeout = 30000; // 30 second timeout
    }

    /**
     * Make HTTP request to API
     */
    async request(endpoint, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        
        const config = {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json',
            },
            timeout: this.timeout,
            ...options
        };

        try {
            const response = await this.fetchWithTimeout(url, config);
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.error || `HTTP ${response.status}: ${response.statusText}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`API Request failed [${config.method}] ${endpoint}:`, error.message);
            throw this.enhanceError(error, endpoint);
        }
    }

    /**
     * Fetch with timeout support
     */
    async fetchWithTimeout(url, options) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeout);
        
        try {
            const response = await fetch(url, {
                ...options,
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            return response;
        } catch (error) {
            clearTimeout(timeoutId);
            if (error.name === 'AbortError') {
                throw new Error(`Request timeout after ${this.timeout}ms`);
            }
            throw error;
        }
    }

    /**
     * Enhance error with context
     */
    enhanceError(error, endpoint) {
        if (error.message.includes('fetch')) {
            return new Error('Network error: Unable to connect to backend server');
        }
        if (error.message.includes('timeout')) {
            return new Error(`Request timeout: ${endpoint} took too long to respond`);
        }
        return error;
    }

    // ====================================================================
    // HEALTH & STATUS
    // ====================================================================

    async healthCheck() {
        return await this.request('/health');
    }

    async isBackendAvailable() {
        try {
            await this.healthCheck();
            return true;
        } catch (error) {
            console.warn('Backend unavailable:', error.message);
            return false;
        }
    }

    async getBackendStatus() {
        try {
            const health = await this.healthCheck();
            const books = await this.getBooks();
            
            return {
                available: true,
                health,
                bookCount: books.length,
                timestamp: new Date().toISOString()
            };
        } catch (error) {
            return {
                available: false,
                error: error.message,
                timestamp: new Date().toISOString()
            };
        }
    }

    // ====================================================================
    // BOOK MANAGEMENT
    // ====================================================================

    async getBooks() {
        const response = await this.request('/books');
        return response.books || [];
    }

    async getBook(bookId) {
        this.validateBookId(bookId);
        const response = await this.request(`/books/${bookId}`);
        return response.book;
    }

    async getInkScript(bookId) {
        this.validateBookId(bookId);
        const response = await this.request(`/books/${bookId}/ink`);
        return response.ink_script;
    }

    async deleteBook(bookId) {
        this.validateBookId(bookId);
        return await this.request(`/books/${bookId}`, {
            method: 'DELETE'
        });
    }

    // Note: EPUB discovery functionality removed - use CLI: python app.py --index

    // ====================================================================
    // SAVE MANAGEMENT
    // ====================================================================

    async getSaveData(bookId) {
        try {
            this.validateBookId(bookId);
            const response = await this.request(`/saves/${bookId}`);
            return response.save_data;
        } catch (error) {
            // Return null for 404 (no save data)
            if (error.message.includes('404') || error.message.includes('not found')) {
                return null;
            }
            throw error;
        }
    }

    async saveGameState(bookId, saveData) {
        this.validateBookId(bookId);
        // Temporarily disable validation to debug
        // this.validateSaveData(saveData);
        
        console.log('Saving game state:', saveData);
        
        return await this.request(`/saves/${bookId}`, {
            method: 'POST',
            body: JSON.stringify(saveData)
        });
    }

    async deleteSaveData(bookId) {
        this.validateBookId(bookId);
        return await this.request(`/saves/${bookId}`, {
            method: 'DELETE'
        });
    }

    // ====================================================================
    // DEVELOPMENT & TESTING
    // ====================================================================

    async createTestBook() {
        return await this.request('/test/simple-book', {
            method: 'POST'
        });
    }

    // ====================================================================
    // VALIDATION HELPERS
    // ====================================================================

    validateBookId(bookId) {
        if (!bookId || typeof bookId !== 'string') {
            throw new Error('Invalid book ID');
        }
        if (bookId.length < 8 || bookId.length > 32) {
            throw new Error('Book ID must be between 8 and 32 characters');
        }
    }


    validateSaveData(saveData) {
        if (!saveData || typeof saveData !== 'object') {
            throw new Error('Invalid save data');
        }
        if (!saveData.currentSection) {
            throw new Error('Save data missing current section');
        }
    }

    parseErrorResponse(responseText) {
        try {
            return JSON.parse(responseText);
        } catch (error) {
            return { error: 'Unknown error' };
        }
    }
}