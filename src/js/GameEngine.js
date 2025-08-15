/**
 * GameEngine - Handles simple JSON story management and game state
 */

export class GameEngine {
    constructor() {
        this.storyData = null;
        this.currentSection = null;
        this.gameVariables = {
            current_section: 1,
            player_health: 20,
            player_skill: 10,
            player_luck: 10
        };
    }

    /**
     * Load story from JSON data
     * @param {string} storyJson - JSON story data
     */
    async loadStory(storyJson) {
        try {
            // Parse the JSON story data
            this.storyData = JSON.parse(storyJson);
            
            // Validate story structure
            if (!this.storyData.sections || this.storyData.startingSection === undefined || this.storyData.startingSection === null) {
                throw new Error('Invalid story format: missing sections or startingSection');
            }
            
            // Initialize to starting section
            this.currentSection = String(this.storyData.startingSection);
            this.gameVariables.current_section = this.storyData.startingSection;
            
            console.log('Story loaded successfully');
            console.log('Title:', this.storyData.title);
            console.log('Author:', this.storyData.author);
            console.log('Sections:', Object.keys(this.storyData.sections).length);
            
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
            const section = this.storyData.sections[this.currentSection];
            
            if (!section) {
                throw new Error(`Section ${this.currentSection} not found`);
            }

            // Get current section text
            const text = section.text || '';

            // Get available choices, mapped to our format, only include available destinations
            const allChoices = (section.choices || []).map((choice, index) => ({
                text: choice.text,
                index: index,
                destination: choice.destination,
                isAvailable: !!this.storyData.sections[String(choice.destination)]
            }));
            
            // Include all choices (available and unavailable) for display
            const choices = allChoices;

            return {
                text: text.trim(),
                choices: choices,
                canContinue: false, // We don't use continuous text like ink
                variables: this.getCurrentVariables(),
                currentTags: [],
                isEnd: section.isEnd || choices.length === 0
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

        const section = this.storyData.sections[this.currentSection];
        if (!section || !section.choices || choiceIndex >= section.choices.length) {
            throw new Error('Invalid choice index');
        }

        try {
            const choice = section.choices[choiceIndex];
            const destinationSection = String(choice.destination);
            
            // Check if destination section exists
            if (!this.storyData.sections[destinationSection]) {
                throw new Error(`Destination section ${destinationSection} not found (corrupted or missing file)`);
            }
            
            // Move to the new section
            this.currentSection = destinationSection;
            this.gameVariables.current_section = choice.destination;
            
            console.log(`Made choice ${choiceIndex}: ${choice.text}`);
            console.log(`Moving to section: ${destinationSection}`);
            
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

        return { ...this.gameVariables };
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
            this.gameVariables[name] = value;
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
                currentSection: this.currentSection,
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

        if (!saveData || !saveData.currentSection) {
            console.warn('No valid save data to load');
            return;
        }

        try {
            this.currentSection = String(saveData.currentSection);
            if (saveData.variables) {
                this.gameVariables = { ...this.gameVariables, ...saveData.variables };
            }
            console.log('Story state loaded successfully');
            console.log('Current section:', this.currentSection);
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
                this.currentSection = String(this.storyData.startingSection);
                this.gameVariables = {
                    current_section: this.storyData.startingSection,
                    player_health: 20,
                    player_skill: 10,
                    player_luck: 10
                };
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
        return this.storyData !== null && this.currentSection !== null;
    }

    /**
     * Check if story has ended
     * @returns {boolean} True if story has ended
     */
    hasEnded() {
        if (!this.hasStory()) {
            return true;
        }
        
        const section = this.storyData.sections[this.currentSection];
        return !section || section.isEnd || (section.choices && section.choices.length === 0);
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
        const section = this.storyData.sections[this.currentSection];
        
        return {
            currentSection: this.currentSection,
            playerHealth: variables.player_health || 0,
            playerSkill: variables.player_skill || 0,
            playerLuck: variables.player_luck || 0,
            hasEnded: this.hasEnded(),
            canContinue: false, // We don't use continuous text
            choicesAvailable: section ? (section.choices || []).length : 0,
            totalSections: Object.keys(this.storyData.sections).length
        };
    }

    /**
     * Validate story JSON before loading
     * @param {string} storyJson - Story JSON to validate
     * @returns {Object} Validation result
     */
    static validateStoryJson(storyJson) {
        const errors = [];
        const warnings = [];

        // Basic validation
        if (!storyJson || typeof storyJson !== 'string') {
            errors.push('Invalid story data: must be a non-empty string');
            return { isValid: false, errors, warnings };
        }

        try {
            const storyData = JSON.parse(storyJson);
            
            // Check required fields
            if (!storyData.sections) {
                errors.push('Missing sections object');
            }
            if (storyData.startingSection === undefined || storyData.startingSection === null) {
                errors.push('Missing startingSection');
            }
            if (!storyData.title) {
                warnings.push('Missing title');
            }
            
            // Check sections structure
            if (storyData.sections) {
                const sectionCount = Object.keys(storyData.sections).length;
                if (sectionCount === 0) {
                    errors.push('No sections found');
                }
                
                const startingSection = String(storyData.startingSection);
                if (!storyData.sections[startingSection]) {
                    errors.push('Starting section not found in sections');
                }
            }

        } catch (parseError) {
            errors.push(`Invalid JSON format: ${parseError.message}`);
        }

        return {
            isValid: errors.length === 0,
            errors: errors,
            warnings: warnings
        };
    }
}