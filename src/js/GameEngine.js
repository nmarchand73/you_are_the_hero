/**
 * GameEngine - Handles inkjs story management and game state
 */

export class GameEngine {
    constructor() {
        this.story = null;
        this.inkjs = null;
    }

    /**
     * Load inkjs library dynamically
     * @returns {Promise<Object>} inkjs library
     */
    async loadInkJS() {
        if (this.inkjs) {
            return this.inkjs;
        }

        // Try to load from window (if already loaded)
        if (window.inkjs) {
            this.inkjs = window.inkjs;
            return this.inkjs;
        }

        // Load from CDN
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/inkjs@2.2.3/dist/ink.min.js';
        
        return new Promise((resolve, reject) => {
            script.onload = () => {
                if (window.inkjs) {
                    this.inkjs = window.inkjs;
                    resolve(this.inkjs);
                } else {
                    reject(new Error('Failed to load inkjs library'));
                }
            };
            script.onerror = () => reject(new Error('Failed to load inkjs library'));
            document.head.appendChild(script);
        });
    }

    /**
     * Load story from ink script
     * @param {string} inkScript - Compiled ink script
     */
    async loadStory(inkScript) {
        try {
            // Load inkjs if not already loaded
            const inkjs = await this.loadInkJS();

            // Create story instance
            this.story = new inkjs.Story(inkScript);
            
            console.log('Story loaded successfully');
            console.log('Global variables:', this.story.variablesState._globalVariables);
            
        } catch (error) {
            console.error('Error loading story:', error);
            throw new Error(`Failed to load story: ${error.message}`);
        }
    }

    /**
     * Continue the story and get current content
     * @returns {Object} Current story state
     */
    continue() {
        if (!this.hasStory()) {
            throw new Error('No story loaded');
        }

        try {
            let text = '';
            
            // Continue reading until we hit choices or the end
            while (this.story.canContinue) {
                const line = this.story.Continue();
                if (line && line.trim()) {
                    text += line;
                }
            }

            // Get available choices
            const choices = this.story.currentChoices.map(choice => ({
                text: choice.text,
                index: choice.index
            }));

            // Get current variables/state
            const variables = this.getCurrentVariables();

            return {
                text: text.trim(),
                choices: choices,
                canContinue: this.story.canContinue,
                variables: variables,
                currentTags: this.story.currentTags || []
            };

        } catch (error) {
            console.error('Error continuing story:', error);
            throw new Error(`Story error: ${error.message}`);
        }
    }

    /**
     * Make a choice and continue
     * @param {number} choiceIndex - Index of the selected choice
     */
    makeChoice(choiceIndex) {
        if (!this.hasStory()) {
            throw new Error('No story loaded');
        }

        if (!this.story.currentChoices || choiceIndex >= this.story.currentChoices.length) {
            throw new Error('Invalid choice index');
        }

        try {
            this.story.ChooseChoiceIndex(choiceIndex);
            console.log(`Made choice ${choiceIndex}: ${this.story.currentChoices[choiceIndex]?.text}`);
            
        } catch (error) {
            console.error('Error making choice:', error);
            throw new Error(`Choice error: ${error.message}`);
        }
    }

    /**
     * Get current story variables
     * @returns {Object} Current variables
     */
    getCurrentVariables() {
        if (!this.hasStory()) {
            return {};
        }

        try {
            const variables = {};
            
            // Common game variables we want to track
            const commonVars = [
                'current_section',
                'player_health', 
                'player_skill',
                'player_luck'
            ];

            for (const varName of commonVars) {
                try {
                    const value = this.story.variablesState[varName];
                    if (value !== undefined) {
                        variables[varName] = value;
                    }
                } catch (e) {
                    // Variable doesn't exist - that's ok
                }
            }

            return variables;
        } catch (error) {
            console.warn('Error getting variables:', error);
            return {};
        }
    }

    /**
     * Set a story variable
     * @param {string} name - Variable name
     * @param {*} value - Variable value
     */
    setVariable(name, value) {
        if (!this.hasStory()) {
            throw new Error('No story loaded');
        }

        try {
            this.story.variablesState[name] = value;
            console.log(`Set variable ${name} = ${value}`);
        } catch (error) {
            console.error(`Error setting variable ${name}:`, error);
        }
    }

    /**
     * Get story state for saving
     * @returns {Object} Serializable story state
     */
    getState() {
        if (!this.hasStory()) {
            return null;
        }

        try {
            const state = {
                storyState: this.story.state.toJson(),
                variables: this.getCurrentVariables(),
                timestamp: new Date().toISOString()
            };

            return state;
        } catch (error) {
            console.error('Error getting story state:', error);
            return null;
        }
    }

    /**
     * Load story state from save data
     * @param {Object} saveData - Previously saved state
     */
    loadState(saveData) {
        if (!this.hasStory()) {
            throw new Error('No story loaded');
        }

        if (!saveData || !saveData.storyState) {
            console.warn('No valid save data to load');
            return;
        }

        try {
            this.story.state.LoadJson(saveData.storyState);
            console.log('Story state loaded successfully');
            console.log('Loaded variables:', saveData.variables);
            
        } catch (error) {
            console.error('Error loading story state:', error);
            throw new Error(`Failed to load save: ${error.message}`);
        }
    }

    /**
     * Reset the story to beginning
     */
    reset() {
        if (this.hasStory()) {
            try {
                this.story.ResetState();
                console.log('Story reset to beginning');
            } catch (error) {
                console.error('Error resetting story:', error);
            }
        }
    }

    /**
     * Check if story is loaded
     * @returns {boolean} True if story is loaded
     */
    hasStory() {
        return this.story !== null;
    }

    /**
     * Check if story has ended
     * @returns {boolean} True if story has ended
     */
    hasEnded() {
        if (!this.hasStory()) {
            return true;
        }
        
        return !this.story.canContinue && 
               (!this.story.currentChoices || this.story.currentChoices.length === 0);
    }

    /**
     * Get story statistics
     * @returns {Object} Story stats
     */
    getStats() {
        if (!this.hasStory()) {
            return null;
        }

        const variables = this.getCurrentVariables();
        
        return {
            currentSection: variables.current_section || 'unknown',
            playerHealth: variables.player_health || 0,
            playerSkill: variables.player_skill || 0,
            playerLuck: variables.player_luck || 0,
            hasEnded: this.hasEnded(),
            canContinue: this.story.canContinue,
            choicesAvailable: this.story.currentChoices ? this.story.currentChoices.length : 0
        };
    }

    /**
     * Validate ink script before loading
     * @param {string} inkScript - Ink script to validate
     * @returns {Object} Validation result
     */
    static validateInkScript(inkScript) {
        const errors = [];
        const warnings = [];

        // Basic validation
        if (!inkScript || typeof inkScript !== 'string') {
            errors.push('Invalid ink script: must be a non-empty string');
            return { isValid: false, errors, warnings };
        }

        // Check for required elements
        if (!inkScript.includes('-> section_1')) {
            warnings.push('No starting section found (expected "-> section_1")');
        }

        // Check for basic ink syntax
        const hasKnots = /=== \w+ ===/.test(inkScript);
        if (!hasKnots) {
            errors.push('No knots found - invalid ink script structure');
        }

        return {
            isValid: errors.length === 0,
            errors: errors,
            warnings: warnings
        };
    }
}