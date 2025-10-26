/**
 * ═══════════════════════════════════════════════════════════
 * GODEYE OSINT PLATFORM - SEARCH PAGE MODULE
 * ═══════════════════════════════════════════════════════════
 * 
 * Purpose: Handles search form submission, API communication,
 *          data validation, and navigation to results page
 * 
 * File: dashboard/static/js/app.js
 * Author: BinaryShield
 * Version: 2.0.0
 * 
 * Features:
 * - Async API communication with timeout handling
 * - Form validation and sanitization
 * - localStorage data persistence
 * - Loading states and user feedback
 * - Image upload support
 * - Comprehensive error handling
 * - Debug logging for troubleshooting
 * 
 * Dependencies: None (Vanilla JavaScript)
 * Browser Support: Modern browsers (ES6+)
 */

(function(window, document) {
    'use strict';

    // ═══════════════════════════════════════════════════════════
    // MODULE CONFIGURATION
    // ═══════════════════════════════════════════════════════════
    
    const CONFIG = {
        // API Configuration
        API: {
            BASE_URL: window.location.origin || 'http://localhost:5000',
            ENDPOINTS: {
                SEARCH: '/api/search',
                ANALYZE: '/api/analyze',
                HEALTH: '/health'
            },
            TIMEOUT: 60000, // 60 seconds
            RETRY_ATTEMPTS: 3,
            RETRY_DELAY: 1000 // 1 second
        },

        // Storage Configuration
        STORAGE: {
            RESULTS_KEY: 'godeyeResults',
            QUERY_KEY: 'lastQuery',
            TYPE_KEY: 'lastQueryType',
            TIMESTAMP_KEY: 'lastSearchTimestamp'
        },

        // UI Configuration
        UI: {
            LOADING_MIN_DURATION: 500, // Minimum loading display time
            REDIRECT_DELAY: 800,
            NOTIFICATION_DURATION: 3000,
            NOTIFICATION_POSITION: 'top-right' // top-right, top-left, bottom-right, bottom-left
        },

        // Validation Patterns
        PATTERNS: {
            DOMAIN: /^(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]$/i,
            IP: /^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$/,
            EMAIL: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
            URL: /^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$/
        },

        // File Upload Limits
        UPLOAD: {
            MAX_SIZE: 10 * 1024 * 1024, // 10MB
            ALLOWED_TYPES: ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp'],
            ALLOWED_EXTENSIONS: ['.png', '.jpg', '.jpeg', '.gif', '.webp']
        },

        // Debug Mode
        DEBUG: true // Set to false in production
    };

    // ═══════════════════════════════════════════════════════════
    // LOGGING UTILITIES
    // ═══════════════════════════════════════════════════════════
    
    const Logger = {
        log: function(message, data = null) {
            if (CONFIG.DEBUG) {
                console.log(`[GodEye] ${message}`, data || '');
            }
        },
        
        info: function(message, data = null) {
            if (CONFIG.DEBUG) {
                console.info(`[GodEye] ℹ️ ${message}`, data || '');
            }
        },
        
        success: function(message, data = null) {
            if (CONFIG.DEBUG) {
                console.log(`[GodEye] ✅ ${message}`, data || '');
            }
        },
        
        warn: function(message, data = null) {
            console.warn(`[GodEye] ⚠️ ${message}`, data || '');
        },
        
        error: function(message, error = null) {
            console.error(`[GodEye] ❌ ${message}`, error || '');
        }
    };

    // ═══════════════════════════════════════════════════════════
    // STORAGE MANAGER
    // ═══════════════════════════════════════════════════════════
    
    const StorageManager = {
        /**
         * Set item in localStorage with error handling
         */
        set: function(key, value) {
            try {
                const serialized = JSON.stringify(value);
                localStorage.setItem(key, serialized);
                Logger.success(`Stored: ${key}`);
                return true;
            } catch (error) {
                Logger.error(`Storage set failed for ${key}:`, error);
                return false;
            }
        },

        /**
         * Get item from localStorage with error handling
         */
        get: function(key, defaultValue = null) {
            try {
                const item = localStorage.getItem(key);
                return item ? JSON.parse(item) : defaultValue;
            } catch (error) {
                Logger.error(`Storage get failed for ${key}:`, error);
                return defaultValue;
            }
        },

        /**
         * Remove item from localStorage
         */
        remove: function(key) {
            try {
                localStorage.removeItem(key);
                Logger.info(`Removed: ${key}`);
                return true;
            } catch (error) {
                Logger.error(`Storage remove failed for ${key}:`, error);
                return false;
            }
        },

        /**
         * Clear all GodEye related storage
         */
        clearAll: function() {
            try {
                Object.values(CONFIG.STORAGE).forEach(key => {
                    localStorage.removeItem(key);
                });
                Logger.info('Cleared all storage');
                return true;
            } catch (error) {
                Logger.error('Storage clear failed:', error);
                return false;
            }
        }
    };

    // ═══════════════════════════════════════════════════════════
    // VALIDATION UTILITIES
    // ═══════════════════════════════════════════════════════════
    
    const Validator = {
        /**
         * Validate query based on type
         */
        validateQuery: function(query, type) {
            if (!query || typeof query !== 'string') {
                return { valid: false, error: 'Query must be a non-empty string' };
            }

            const trimmedQuery = query.trim();
            
            if (trimmedQuery.length === 0) {
                return { valid: false, error: 'Query cannot be empty' };
            }

            if (trimmedQuery.length > 500) {
                return { valid: false, error: 'Query is too long (max 500 characters)' };
            }

            // If type is auto, no pattern validation needed
            if (type === 'auto') {
                return { valid: true, query: trimmedQuery };
            }

            // Validate against pattern
            const pattern = CONFIG.PATTERNS[type.toUpperCase()];
            if (pattern && !pattern.test(trimmedQuery)) {
                return { valid: false, error: `Invalid ${type} format` };
            }

            return { valid: true, query: trimmedQuery };
        },

        /**
         * Auto-detect query type
         */
        detectQueryType: function(query) {
            if (CONFIG.PATTERNS.IP.test(query)) return 'ip';
            if (CONFIG.PATTERNS.EMAIL.test(query)) return 'email';
            if (CONFIG.PATTERNS.DOMAIN.test(query)) return 'domain';
            if (CONFIG.PATTERNS.URL.test(query)) return 'url';
            return 'unknown';
        },

        /**
         * Validate file upload
         */
        validateFile: function(file) {
            if (!file) {
                return { valid: false, error: 'No file provided' };
            }

            // Check file size
            if (file.size > CONFIG.UPLOAD.MAX_SIZE) {
                const maxSizeMB = CONFIG.UPLOAD.MAX_SIZE / (1024 * 1024);
                return { valid: false, error: `File size exceeds ${maxSizeMB}MB limit` };
            }

            // Check file type
            if (!CONFIG.UPLOAD.ALLOWED_TYPES.includes(file.type)) {
                return { valid: false, error: 'Invalid file type. Only images are allowed.' };
            }

            return { valid: true };
        }
    };

    // ═══════════════════════════════════════════════════════════
    // API CLIENT
    // ═══════════════════════════════════════════════════════════
    
    const APIClient = {
        /**
         * Make API request with timeout and retry logic
         */
        request: async function(endpoint, options = {}) {
            const url = `${CONFIG.API.BASE_URL}${endpoint}`;
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), CONFIG.API.TIMEOUT);

            const defaultOptions = {
                method: 'GET',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                signal: controller.signal
            };

            const requestOptions = { ...defaultOptions, ...options };

            try {
                Logger.info(`API Request: ${options.method || 'GET'} ${url}`);
                
                const response = await fetch(url, requestOptions);
                clearTimeout(timeoutId);

                Logger.info(`API Response: ${response.status} ${response.statusText}`);

                if (!response.ok) {
                    const errorText = await response.text();
                    let errorData;
                    
                    try {
                        errorData = JSON.parse(errorText);
                    } catch {
                        errorData = { message: errorText || response.statusText };
                    }

                    throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
                }

                const data = await response.json();
                Logger.success('API request successful', data);
                
                return data;

            } catch (error) {
                clearTimeout(timeoutId);

                if (error.name === 'AbortError') {
                    Logger.error('Request timeout');
                    throw new Error('Request timeout. Please try again.');
                }

                Logger.error('API request failed:', error);
                throw error;
            }
        },

        /**
         * Search analysis endpoint
         */
        search: async function(query, type = 'auto') {
            return await this.request(CONFIG.API.ENDPOINTS.SEARCH, {
                method: 'POST',
                body: JSON.stringify({ query, type })
            });
        },

        /**
         * Health check endpoint
         */
        healthCheck: async function() {
            try {
                return await this.request(CONFIG.API.ENDPOINTS.HEALTH);
            } catch (error) {
                Logger.error('Health check failed:', error);
                return { status: 'unhealthy' };
            }
        }
    };

    // ═══════════════════════════════════════════════════════════
    // UI MANAGER
    // ═══════════════════════════════════════════════════════════
    
    const UIManager = {
        /**
         * Show loading overlay
         */
        showLoading: function() {
            const overlay = document.getElementById('loadingOverlay') || 
                          document.getElementById('loaderOverlay');
            
            if (overlay) {
                overlay.classList.add('active');
                overlay.style.display = 'flex';
                Logger.info('Loading overlay shown');
            }
        },

        /**
         * Hide loading overlay
         */
        hideLoading: function() {
            const overlay = document.getElementById('loadingOverlay') || 
                          document.getElementById('loaderOverlay');
            
            if (overlay) {
                overlay.classList.remove('active');
                overlay.style.display = 'none';
                Logger.info('Loading overlay hidden');
            }
        },

        /**
         * Show notification toast
         */
        showNotification: function(message, type = 'info', duration = CONFIG.UI.NOTIFICATION_DURATION) {
            Logger.info(`Notification [${type}]: ${message}`);

            const colors = {
                success: '#00ff88',
                error: '#ff3366',
                warning: '#ffaa00',
                info: '#00aaff'
            };

            const icons = {
                success: '✓',
                error: '✕',
                warning: '⚠',
                info: 'ℹ'
            };

            const toast = document.createElement('div');
            toast.className = `godeye-toast godeye-toast-${type}`;
            toast.innerHTML = `
                <span class="toast-icon">${icons[type]}</span>
                <span class="toast-message">${this.escapeHtml(message)}</span>
            `;

            toast.style.cssText = `
                display: flex;
                align-items: center;
                gap: 0.75rem;
                min-width: 300px;
                max-width: 500px;
                padding: 1rem 1.5rem;
                background: #1a1a1a;
                border-left: 4px solid ${colors[type]};
                border-radius: 8px;
                color: #fff;
                box-shadow: 0 10px 30px rgba(0,0,0,0.6);
                font-size: 0.95rem;
                animation: slideInRight 0.3s ease;
                margin-bottom: 0.5rem;
                cursor: pointer;
                transition: transform 0.2s;
            `;

            // Get or create toast container
            let container = document.getElementById('godeye-toast-container');
            if (!container) {
                container = document.createElement('div');
                container.id = 'godeye-toast-container';
                
                const positions = {
                    'top-right': 'top: 20px; right: 20px;',
                    'top-left': 'top: 20px; left: 20px;',
                    'bottom-right': 'bottom: 20px; right: 20px;',
                    'bottom-left': 'bottom: 20px; left: 20px;'
                };

                container.style.cssText = `
                    position: fixed;
                    ${positions[CONFIG.UI.NOTIFICATION_POSITION]}
                    z-index: 10000;
                    display: flex;
                    flex-direction: column;
                `;
                
                document.body.appendChild(container);
            }

            container.appendChild(toast);

            // Click to dismiss
            toast.addEventListener('click', () => {
                this.removeToast(toast);
            });

            // Hover effect
            toast.addEventListener('mouseenter', () => {
                toast.style.transform = 'translateX(-5px)';
            });

            toast.addEventListener('mouseleave', () => {
                toast.style.transform = 'translateX(0)';
            });

            // Auto remove
            setTimeout(() => {
                this.removeToast(toast);
            }, duration);
        },

        /**
         * Remove toast notification
         */
        removeToast: function(toast) {
            toast.style.opacity = '0';
            toast.style.transform = 'translateX(100%)';
            toast.style.transition = 'all 0.3s ease';
            
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
            }, 300);
        },

        /**
         * Disable form elements
         */
        disableForm: function(formId) {
            const form = document.getElementById(formId);
            if (form) {
                const inputs = form.querySelectorAll('input, button, select, textarea');
                inputs.forEach(input => input.disabled = true);
                Logger.info('Form disabled');
            }
        },

        /**
         * Enable form elements
         */
        enableForm: function(formId) {
            const form = document.getElementById(formId);
            if (form) {
                const inputs = form.querySelectorAll('input, button, select, textarea');
                inputs.forEach(input => input.disabled = false);
                Logger.info('Form enabled');
            }
        },

        /**
         * Escape HTML to prevent XSS
         */
        escapeHtml: function(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
    };

    // ═══════════════════════════════════════════════════════════
    // SEARCH HANDLER
    // ═══════════════════════════════════════════════════════════
    
    const SearchHandler = {
        /**
         * Handle form submission
         */
        handleSubmit: async function(event) {
            event.preventDefault();
            Logger.log('=== Search Form Submitted ===');

            const searchInput = document.getElementById('q');
            const typeSelector = document.getElementById('typeSelector');

            if (!searchInput) {
                Logger.error('Search input not found');
                UIManager.showNotification('Form error: Search input not found', 'error');
                return;
            }

            const query = searchInput.value.trim();
            const type = typeSelector ? typeSelector.value : 'auto';

            Logger.info('Search Parameters', { query, type });

            // Validate query
            const validation = Validator.validateQuery(query, type);
            if (!validation.valid) {
                Logger.warn('Validation failed:', validation.error);
                UIManager.showNotification(validation.error, 'error');
                return;
            }

            // Store search parameters
            StorageManager.set(CONFIG.STORAGE.QUERY_KEY, validation.query);
            StorageManager.set(CONFIG.STORAGE.TYPE_KEY, type);
            StorageManager.set(CONFIG.STORAGE.TIMESTAMP_KEY, new Date().toISOString());

            // Disable form
            UIManager.disableForm('searchForm');
            UIManager.showLoading();

            const startTime = Date.now();

            try {
                // Make API request
                Logger.info('Sending API request...');
                const results = await APIClient.search(validation.query, type);

                // Ensure minimum loading time for better UX
                const elapsed = Date.now() - startTime;
                if (elapsed < CONFIG.UI.LOADING_MIN_DURATION) {
                    await new Promise(resolve => 
                        setTimeout(resolve, CONFIG.UI.LOADING_MIN_DURATION - elapsed)
                    );
                }

                Logger.success('Analysis complete', results);

                // Validate response structure
                if (!results || typeof results !== 'object') {
                    throw new Error('Invalid response format from server');
                }

                if (results.status !== 'success') {
                    throw new Error(results.message || 'Analysis failed');
                }

                // Store results
                const stored = StorageManager.set(CONFIG.STORAGE.RESULTS_KEY, results);
                
                if (!stored) {
                    throw new Error('Failed to store results. Check browser storage.');
                }

                // Show success notification
                UIManager.showNotification('Analysis complete! Redirecting...', 'success');

                // Redirect to results page
                Logger.info('Redirecting to results page...');
                setTimeout(() => {
                    window.location.href = 'results.html';
                }, CONFIG.UI.REDIRECT_DELAY);

            } catch (error) {
                Logger.error('Search failed:', error);
                
                UIManager.hideLoading();
                UIManager.enableForm('searchForm');
                
                const errorMessage = error.message || 'Analysis failed. Please try again.';
                UIManager.showNotification(errorMessage, 'error');
            }
        },

        /**
         * Initialize search form
         */
        initialize: function() {
            Logger.log('=== Initializing Search Module ===');

            const searchForm = document.getElementById('searchForm');
            const searchInput = document.getElementById('q');
            const searchBtn = document.getElementById('searchBtn');

            if (!searchForm) {
                Logger.error('Search form not found');
                return false;
            }

            Logger.success('Search form found');

            // Attach submit handler
            searchForm.addEventListener('submit', this.handleSubmit.bind(this));

            // Real-time validation
            if (searchInput && searchBtn) {
                searchInput.addEventListener('input', function() {
                    const hasValue = searchInput.value.trim().length > 0;
                    searchBtn.disabled = !hasValue;
                    
                    if (hasValue) {
                        searchBtn.classList.remove('disabled');
                    } else {
                        searchBtn.classList.add('disabled');
                    }
                });

                // Initial state
                searchBtn.disabled = searchInput.value.trim().length === 0;
            }

            // Initialize type selector
            if (document.getElementById('typeSelector')) {
                this.initializeTypeSelector();
            }

            Logger.success('Search module initialized');
            return true;
        },

        /**
         * Initialize type selector with auto-detection
         */
        initializeTypeSelector: function() {
            const searchInput = document.getElementById('q');
            const typeSelector = document.getElementById('typeSelector');

            if (!searchInput || !typeSelector) return;

            searchInput.addEventListener('input', function() {
                if (typeSelector.value === 'auto') {
                    const query = searchInput.value.trim();
                    if (query) {
                        const detectedType = Validator.detectQueryType(query);
                        Logger.info(`Auto-detected type: ${detectedType}`);
                    }
                }
            });
        }
    };

    // ═══════════════════════════════════════════════════════════
    // IMAGE UPLOAD HANDLER (Optional Feature)
    // ═══════════════════════════════════════════════════════════
    
    const ImageUploadHandler = {
        selectedFile: null,

        /**
         * Initialize image upload functionality
         */
        initialize: function() {
            const imgToggle = document.getElementById('imgToggle');
            const imageArea = document.getElementById('imageArea');
            const imgInput = document.getElementById('imgInput');
            const dropZone = document.getElementById('dropZone');
            const preview = document.getElementById('preview');

            if (!imgToggle || !imageArea) {
                Logger.info('Image upload not available on this page');
                return;
            }

            Logger.info('Initializing image upload...');

            // Toggle image search area
            imgToggle.addEventListener('click', () => {
                const isVisible = imageArea.style.display === 'flex';
                imageArea.style.display = isVisible ? 'none' : 'flex';
                imgToggle.setAttribute('aria-pressed', (!isVisible).toString());
                Logger.info(`Image area ${isVisible ? 'hidden' : 'shown'}`);
            });

            // Click to upload
            if (dropZone) {
                dropZone.addEventListener('click', () => imgInput.click());
            }

            // File input change
            if (imgInput) {
                imgInput.addEventListener('change', (e) => {
                    if (e.target.files.length > 0) {
                        this.handleFileSelect(e.target.files[0], preview);
                    }
                });
            }

            // Drag and drop
            if (dropZone) {
                dropZone.addEventListener('dragover', (e) => {
                    e.preventDefault();
                    dropZone.classList.add('drag-over');
                });

                dropZone.addEventListener('dragleave', () => {
                    dropZone.classList.remove('drag-over');
                });

                dropZone.addEventListener('drop', (e) => {
                    e.preventDefault();
                    dropZone.classList.remove('drag-over');
                    
                    if (e.dataTransfer.files.length > 0) {
                        this.handleFileSelect(e.dataTransfer.files[0], preview);
                    }
                });
            }

            Logger.success('Image upload initialized');
        },

        /**
         * Handle file selection
         */
        handleFileSelect: function(file, previewElement) {
            Logger.info('File selected', { name: file.name, size: file.size, type: file.type });

            // Validate file
            const validation = Validator.validateFile(file);
            if (!validation.valid) {
                UIManager.showNotification(validation.error, 'error');
                return;
            }

            this.selectedFile = file;

            // Show preview
            if (previewElement) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    previewElement.innerHTML = `
                        <img src="${e.target.result}" 
                             alt="preview" 
                             style="max-width:100%; max-height:250px; border-radius:6px; object-fit:contain;">
                    `;
                    Logger.success('Preview loaded');
                };
                reader.readAsDataURL(file);
            }

            UIManager.showNotification('Image loaded successfully', 'success');
        }
    };

    // ═══════════════════════════════════════════════════════════
    // APPLICATION INITIALIZATION
    // ═══════════════════════════════════════════════════════════
    
    function initialize() {
        Logger.log('╔══════════════════════════════════════════════════════════╗');
        Logger.log('║         GODEYE OSINT PLATFORM - SEARCH MODULE           ║');
        Logger.log('║                    Version 2.0.0                         ║');
        Logger.log('╚══════════════════════════════════════════════════════════╝');

        // Check localStorage availability
        try {
            localStorage.setItem('test', 'test');
            localStorage.removeItem('test');
            Logger.success('localStorage available');
        } catch (error) {
            Logger.error('localStorage not available:', error);
            UIManager.showNotification('Browser storage is not available. Some features may not work.', 'warning');
        }

        // Check API health
        APIClient.healthCheck().then(health => {
            if (health.status === 'healthy') {
                Logger.success('API server is healthy');
            } else {
                Logger.warn('API server health check failed');
            }
        });

        // Initialize modules
        const searchInitialized = SearchHandler.initialize();
        
        if (searchInitialized) {
            ImageUploadHandler.initialize();
        }

        Logger.success('Application initialized successfully');
    }

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }

    // ═══════════════════════════════════════════════════════════
    // PUBLIC API (for debugging and testing)
    // ═══════════════════════════════════════════════════════════
    
    window.GodEyeSearch = {
        // Expose modules for testing
        CONFIG,
        Logger,
        StorageManager,
        Validator,
        APIClient,
        UIManager,
        SearchHandler,
        
        // Utility functions
        version: '2.0.0',
        debugMode: CONFIG.DEBUG,
        
        // Manual controls
        clearStorage: () => StorageManager.clearAll(),
        testAPI: () => APIClient.healthCheck(),
        
        // Get current state
        getState: function() {
            return {
                lastQuery: StorageManager.get(CONFIG.STORAGE.QUERY_KEY),
                lastType: StorageManager.get(CONFIG.STORAGE.TYPE_KEY),
                hasResults: !!StorageManager.get(CONFIG.STORAGE.RESULTS_KEY)
            };
        }
    };

    // Log initialization complete
    if (CONFIG.DEBUG) {
        console.log('%c GodEye Search Module Loaded ', 
                   'background: #ff0000; color: #fff; padding: 5px 10px; border-radius: 3px;');
        console.log('Access via: window.GodEyeSearch');
    }

})(window, document);