/**
 * UIManager - Handles UI interactions, animations, and responsive behavior
 */

export class UIManager {
    constructor() {
        this.isInitialized = false;
        this.currentTheme = 'modern'; // Changed default to modern
        this.animations = {
            fadeIn: 'fadeIn 0.3s ease-in',
            slideIn: 'slideIn 0.3s ease-out',
            bounce: 'bounce 0.5s ease-out'
        };
    }

    /**
     * Initialize UI Manager
     */
    init() {
        if (this.isInitialized) return;

        console.log('Initializing UI Manager...');
        
        this.setupTheme();
        this.setupAnimations();
        this.setupResponsive();
        this.setupAccessibility();
        
        this.isInitialized = true;
        console.log('UI Manager initialized');
    }

    /**
     * Setup theme handling
     */
    setupTheme() {
        // Load saved theme
        const savedTheme = localStorage.getItem('theme') || 'modern';
        this.setTheme(savedTheme);

        // Setup theme switcher
        this.setupThemeSwitcher();

        // Listen for system theme changes
        if (window.matchMedia) {
            const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
            
            mediaQuery.addEventListener('change', (e) => {
                if (!localStorage.getItem('theme')) {
                    this.setTheme(e.matches ? 'modern' : 'terminal');
                }
            });
        }
    }

    /**
     * Setup theme switcher buttons
     */
    setupThemeSwitcher() {
        const themeButtons = document.querySelectorAll('.theme-btn');
        
        themeButtons.forEach(button => {
            button.addEventListener('click', () => {
                const theme = button.getAttribute('data-theme');
                this.setTheme(theme);
                this.updateThemeSwitcher(theme);
            });
        });
        
        this.updateThemeSwitcher(this.currentTheme);
    }

    /**
     * Update theme switcher button states
     */
    updateThemeSwitcher(activeTheme) {
        const themeButtons = document.querySelectorAll('.theme-btn');
        
        themeButtons.forEach(button => {
            const theme = button.getAttribute('data-theme');
            if (theme === activeTheme) {
                button.classList.add('active');
            } else {
                button.classList.remove('active');
            }
        });
    }

    /**
     * Set theme
     * @param {string} theme - Theme name ('terminal', 'modern', 'light', 'dark')
     */
    setTheme(theme) {
        this.currentTheme = theme;
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update theme switcher
        this.updateThemeSwitcher(theme);
        
        // Update theme toggle buttons (for backward compatibility)
        this.updateThemeButtons();
    }

    /**
     * Toggle between terminal and modern themes
     */
    toggleTheme() {
        const newTheme = this.currentTheme === 'terminal' ? 'modern' : 'terminal';
        this.setTheme(newTheme);
    }

    /**
     * Update theme toggle button states
     */
    updateThemeButtons() {
        const themeButtons = document.querySelectorAll('.theme-toggle');
        const icon = this.currentTheme === 'terminal' ? '✨' : '🖥️';
        
        themeButtons.forEach(button => {
            button.textContent = icon;
            button.setAttribute('aria-label', 
                `Switch to ${this.currentTheme === 'terminal' ? 'modern' : 'terminal'} mode`
            );
        });
    }

    /**
     * Setup CSS animations
     */
    setupAnimations() {
        // Add animation keyframes if not already present
        if (!document.getElementById('ui-animations')) {
            const style = document.createElement('style');
            style.id = 'ui-animations';
            style.textContent = `
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                
                @keyframes slideIn {
                    from { transform: translateY(20px); opacity: 0; }
                    to { transform: translateY(0); opacity: 1; }
                }
                
                @keyframes bounce {
                    0%, 60%, 75%, 90%, 100% {
                        transform: translateY(0);
                    }
                    25% {
                        transform: translateY(-5px);
                    }
                    50% {
                        transform: translateY(-3px);
                    }
                    80% {
                        transform: translateY(-1px);
                    }
                }

                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
                }

                .animate-fade-in {
                    animation: fadeIn 0.3s ease-in;
                }

                .animate-slide-in {
                    animation: slideIn 0.3s ease-out;
                }

                .animate-bounce {
                    animation: bounce 0.5s ease-out;
                }

                .animate-pulse {
                    animation: pulse 2s infinite;
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Setup responsive behavior
     */
    setupResponsive() {
        // Handle window resize
        let resizeTimeout;
        window.addEventListener('resize', () => {
            clearTimeout(resizeTimeout);
            resizeTimeout = setTimeout(() => {
                this.handleResize();
            }, 250);
        });

        // Handle orientation change
        window.addEventListener('orientationchange', () => {
            setTimeout(() => {
                this.handleResize();
            }, 100);
        });

        this.handleResize();
    }

    /**
     * Handle window resize
     */
    handleResize() {
        const width = window.innerWidth;
        const height = window.innerHeight;
        
        // Update viewport info
        document.documentElement.style.setProperty('--viewport-width', width + 'px');
        document.documentElement.style.setProperty('--viewport-height', height + 'px');

        // Adjust layout for mobile
        if (width <= 768) {
            document.body.classList.add('mobile-layout');
        } else {
            document.body.classList.remove('mobile-layout');
        }

        // Handle very small screens
        if (width <= 480 || height <= 480) {
            document.body.classList.add('compact-layout');
        } else {
            document.body.classList.remove('compact-layout');
        }
    }

    /**
     * Setup accessibility features
     */
    setupAccessibility() {
        // Add focus indicators
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });

        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });

        // Ensure proper ARIA labels and roles
        this.updateAriaLabels();

        // Handle reduced motion preference
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            document.body.classList.add('reduced-motion');
        }
    }

    /**
     * Update ARIA labels and accessibility attributes
     */
    updateAriaLabels() {
        // Update theme toggle
        const themeButtons = document.querySelectorAll('.theme-toggle');
        themeButtons.forEach(button => {
            if (!button.getAttribute('aria-label')) {
                button.setAttribute('aria-label', 'Toggle dark mode');
            }
        });

        // Update file input
        const fileInput = document.getElementById('file-input');
        if (fileInput && !fileInput.getAttribute('aria-label')) {
            fileInput.setAttribute('aria-label', 'Select EPUB file');
        }

        // Update buttons without labels
        const buttons = document.querySelectorAll('button:not([aria-label]):not([aria-labelledby])');
        buttons.forEach(button => {
            if (!button.textContent.trim()) {
                const icon = button.innerHTML;
                if (icon.includes('💾')) {
                    button.setAttribute('aria-label', 'Save game');
                } else if (icon.includes('←')) {
                    button.setAttribute('aria-label', 'Go back');
                } else if (icon.includes('×')) {
                    button.setAttribute('aria-label', 'Close');
                }
            }
        });
    }

    /**
     * Show notification/toast message
     * @param {string} message - Message to display
     * @param {string} type - Type ('success', 'error', 'info')
     * @param {number} duration - Duration in milliseconds
     */
    showNotification(message, type = 'info', duration = 3000) {
        // Remove existing notifications
        const existing = document.querySelectorAll('.notification');
        existing.forEach(el => el.remove());

        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type} animate-slide-in`;
        notification.textContent = message;
        notification.setAttribute('role', 'alert');
        notification.setAttribute('aria-live', 'polite');

        // Style the notification
        Object.assign(notification.style, {
            position: 'fixed',
            top: '20px',
            right: '20px',
            backgroundColor: type === 'error' ? '#dc3545' : 
                           type === 'success' ? '#28a745' : '#007bff',
            color: 'white',
            padding: '12px 20px',
            borderRadius: '8px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            zIndex: '10000',
            maxWidth: '300px',
            fontSize: '14px',
            lineHeight: '1.4'
        });

        document.body.appendChild(notification);

        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.style.animation = 'fadeOut 0.3s ease-out forwards';
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }

        return notification;
    }

    /**
     * Show loading overlay
     * @param {string} message - Loading message
     * @returns {HTMLElement} Loading overlay element
     */
    showLoadingOverlay(message = 'Chargement...') {
        // Remove existing overlay
        this.hideLoadingOverlay();

        const overlay = document.createElement('div');
        overlay.id = 'loading-overlay';
        overlay.className = 'loading-overlay animate-fade-in';
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner"></div>
                <div class="loading-message">${message}</div>
            </div>
        `;

        // Style the overlay
        Object.assign(overlay.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100%',
            height: '100%',
            backgroundColor: 'rgba(0, 0, 0, 0.7)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: '9999',
            color: 'white',
            fontSize: '16px'
        });

        document.body.appendChild(overlay);
        return overlay;
    }

    /**
     * Update loading overlay message
     * @param {string} message - New message
     */
    updateLoadingMessage(message) {
        const messageElement = document.querySelector('#loading-overlay .loading-message');
        if (messageElement) {
            messageElement.textContent = message;
        }
    }

    /**
     * Hide loading overlay
     */
    hideLoadingOverlay() {
        const overlay = document.getElementById('loading-overlay');
        if (overlay) {
            overlay.style.animation = 'fadeOut 0.3s ease-out forwards';
            setTimeout(() => overlay.remove(), 300);
        }
    }

    /**
     * Animate element entrance
     * @param {HTMLElement} element - Element to animate
     * @param {string} animation - Animation type
     */
    animateIn(element, animation = 'fadeIn') {
        if (!element) return;
        
        element.style.animation = `${animation} 0.3s ease-out forwards`;
    }

    /**
     * Animate element exit
     * @param {HTMLElement} element - Element to animate
     * @param {string} animation - Animation type
     * @returns {Promise} Promise that resolves when animation completes
     */
    animateOut(element, animation = 'fadeOut') {
        return new Promise((resolve) => {
            if (!element) {
                resolve();
                return;
            }

            element.style.animation = `${animation} 0.3s ease-out forwards`;
            setTimeout(() => {
                resolve();
            }, 300);
        });
    }

    /**
     * Smooth scroll to element
     * @param {HTMLElement|string} target - Element or selector
     * @param {Object} options - Scroll options
     */
    scrollTo(target, options = {}) {
        const element = typeof target === 'string' ? 
                       document.querySelector(target) : target;
        
        if (!element) return;

        const defaultOptions = {
            behavior: 'smooth',
            block: 'start',
            inline: 'nearest'
        };

        element.scrollIntoView({ ...defaultOptions, ...options });
    }

    /**
     * Add ripple effect to button
     * @param {HTMLElement} button - Button element
     * @param {Event} event - Click event
     */
    addRippleEffect(button, event) {
        const rect = button.getBoundingClientRect();
        const size = Math.max(rect.width, rect.height);
        const x = event.clientX - rect.left - size / 2;
        const y = event.clientY - rect.top - size / 2;

        const ripple = document.createElement('span');
        ripple.style.cssText = `
            position: absolute;
            width: ${size}px;
            height: ${size}px;
            left: ${x}px;
            top: ${y}px;
            background: rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            transform: scale(0);
            animation: ripple 0.6s linear;
            pointer-events: none;
        `;

        // Add ripple keyframes if not already present
        if (!document.getElementById('ripple-animation')) {
            const style = document.createElement('style');
            style.id = 'ripple-animation';
            style.textContent = `
                @keyframes ripple {
                    to {
                        transform: scale(4);
                        opacity: 0;
                    }
                }
            `;
            document.head.appendChild(style);
        }

        const buttonStyle = getComputedStyle(button);
        if (buttonStyle.position === 'static') {
            button.style.position = 'relative';
        }
        if (buttonStyle.overflow !== 'hidden') {
            button.style.overflow = 'hidden';
        }

        button.appendChild(ripple);

        setTimeout(() => {
            ripple.remove();
        }, 600);
    }

    /**
     * Handle button clicks with effects
     * @param {HTMLElement} button - Button element
     * @param {Function} callback - Click handler
     */
    setupButton(button, callback) {
        if (!button) return;

        button.addEventListener('click', (event) => {
            // Add ripple effect
            this.addRippleEffect(button, event);
            
            // Add bounce animation
            button.style.animation = 'bounce 0.3s ease-out';
            setTimeout(() => {
                button.style.animation = '';
            }, 300);

            // Execute callback
            if (callback) {
                callback(event);
            }
        });
    }

    /**
     * Get current viewport size category
     * @returns {string} Size category ('mobile', 'tablet', 'desktop')
     */
    getViewportSize() {
        const width = window.innerWidth;
        
        if (width <= 480) return 'mobile';
        if (width <= 768) return 'tablet';
        return 'desktop';
    }

    /**
     * Check if device supports touch
     * @returns {boolean} True if touch is supported
     */
    isTouchDevice() {
        return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    }

    /**
     * Get system theme preference
     * @returns {string} 'dark' or 'light'
     */
    getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return 'dark';
        }
        return 'light';
    }

    /**
     * Clean up UI Manager resources
     */
    destroy() {
        // Remove event listeners
        window.removeEventListener('resize', this.handleResize);
        window.removeEventListener('orientationchange', this.handleResize);
        
        // Remove custom styles
        const customStyles = document.querySelectorAll('#ui-animations, #ripple-animation');
        customStyles.forEach(style => style.remove());
        
        this.isInitialized = false;
    }
}