/**
 * ═══════════════════════════════════════════════════════════
 * GODEYE OSINT PLATFORM - RESULTS PAGE MODULE
 * ═══════════════════════════════════════════════════════════
 * 
 * Purpose: Handles results display, data visualization,
 *          analytics rendering, and report export
 * 
 * File: dashboard/static/js/results.js
 * Author: BinaryShield
 * Version: 2.0.0
 * 
 * Features:
 * - Dynamic data rendering from localStorage
 * - Animated statistics and counters
 * - Interactive data tables with sorting
 * - Export to JSON/CSV
 * - Chart visualization support
 * - Comprehensive error handling
 * - Responsive design support
 * 
 * Dependencies: Chart.js (optional, for graphs)
 * Browser Support: Modern browsers (ES6+)
 */

(function(window, document) {
    'use strict';

    // ═══════════════════════════════════════════════════════════
    // MODULE CONFIGURATION
    // ═══════════════════════════════════════════════════════════
    
    const CONFIG = {
        // Storage Configuration
        STORAGE: {
            RESULTS_KEY: 'godeyeResults',
            QUERY_KEY: 'lastQuery',
            TYPE_KEY: 'lastQueryType',
            TIMESTAMP_KEY: 'lastSearchTimestamp'
        },

        // UI Configuration
        UI: {
            ANIMATION_DURATION: 300,
            COUNTER_DURATION: 1000,
            FADE_IN_DELAY: 150,
            TABLE_PAGE_SIZE: 50,
            NOTIFICATION_DURATION: 3000
        },

        // Chart Configuration
        CHART: {
            ENABLED: typeof Chart !== 'undefined',
            TYPE: 'doughnut',
            COLORS: {
                HIGH: '#ff00009e',
                MEDIUM: '#ffaa00',
                LOW: '#33ff3d9c'
            }
        },

        // Export Configuration
        EXPORT: {
            FILENAME_PREFIX: 'godeye-report',
            CSV_FILENAME_PREFIX: 'godeye-indicators',
            DATE_FORMAT: 'YYYY-MM-DD_HH-mm-ss'
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
                console.log(`[GodEye Results] ${message}`, data || '');
            }
        },
        
        info: function(message, data = null) {
            if (CONFIG.DEBUG) {
                console.info(`[GodEye Results] ℹ️ ${message}`, data || '');
            }
        },
        
        success: function(message, data = null) {
            if (CONFIG.DEBUG) {
                console.log(`[GodEye Results] ✅ ${message}`, data || '');
            }
        },
        
        warn: function(message, data = null) {
            console.warn(`[GodEye Results] ⚠️ ${message}`, data || '');
        },
        
        error: function(message, error = null) {
            console.error(`[GodEye Results] ❌ ${message}`, error || '');
        }
    };

    // ═══════════════════════════════════════════════════════════
    // STORAGE MANAGER
    // ═══════════════════════════════════════════════════════════
    
    const StorageManager = {
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
         * Check if results exist
         */
        hasResults: function() {
            return !!localStorage.getItem(CONFIG.STORAGE.RESULTS_KEY);
        }
    };

    // ═══════════════════════════════════════════════════════════
    // UI UTILITIES
    // ═══════════════════════════════════════════════════════════
    
    const UIUtils = {
        /**
         * Escape HTML to prevent XSS
         */
        escapeHtml: function(text) {
            if (!text) return '';
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        /**
         * Format date to readable string
         */
        formatDate: function(dateString) {
            try {
                const date = new Date(dateString);
                return date.toLocaleString('en-US', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
            } catch (error) {
                Logger.error('Date formatting failed:', error);
                return dateString;
            }
        },

        /**
         * Animate counter from start to end
         */
        animateCounter: function(element, start, end, duration, suffix = '') {
            if (!element) return;

            const range = end - start;
            const increment = range / (duration / 16); // 60fps
            let current = start;

            const timer = setInterval(() => {
                current += increment;
                
                if ((increment > 0 && current >= end) || (increment < 0 && current <= end)) {
                    current = end;
                    clearInterval(timer);
                }

                element.textContent = Math.round(current) + suffix;
            }, 16);
        },

        /**
         * Apply fade-in animation
         */
        fadeIn: function(elements, delay = CONFIG.UI.FADE_IN_DELAY) {
            elements.forEach((elem, index) => {
                if (!elem) return;
                
                elem.style.opacity = '0';
                elem.style.transform = 'translateY(20px)';
                
                setTimeout(() => {
                    elem.style.transition = `all ${CONFIG.UI.ANIMATION_DURATION}ms ease`;
                    elem.style.opacity = '1';
                    elem.style.transform = 'translateY(0)';
                }, index * delay);
            });
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

            const toast = document.createElement('div');
            toast.className = `godeye-toast godeye-toast-${type}`;
            toast.textContent = message;
            
            toast.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                min-width: 300px;
                padding: 1rem 1.5rem;
                background: #1a1a1a;
                border-left: 4px solid ${colors[type]};
                border-radius: 8px;
                color: #fff;
                box-shadow: 0 10px 30px rgba(0,0,0,0.6);
                z-index: 10000;
                animation: slideInRight 0.3s ease;
                cursor: pointer;
            `;

            document.body.appendChild(toast);

            toast.addEventListener('click', () => {
                this.removeToast(toast);
            });

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
         * Get confidence class based on value
         */
        getConfidenceClass: function(confidence) {
            const value = typeof confidence === 'number' ? confidence : parseFloat(confidence) || 0;
            
            if (value >= 0.8) return 'high';
            if (value >= 0.5) return 'medium';
            return 'low';
        },

        /**
         * Format confidence as percentage
         */
        formatConfidence: function(confidence) {
            const value = typeof confidence === 'number' ? confidence : parseFloat(confidence) || 0;
            return Math.round(value * 100) + '%';
        }
    };

    // ═══════════════════════════════════════════════════════════
    // DATA MANAGER
    // ═══════════════════════════════════════════════════════════
    
    const DataManager = {
        /**
         * Load results from storage
         */
        loadResults: function() {
            Logger.info('Loading results from storage...');
            
            const results = StorageManager.get(CONFIG.STORAGE.RESULTS_KEY);
            
            if (!results) {
                Logger.error('No results found in storage');
                return null;
            }

            Logger.success('Results loaded successfully', results);
            return results;
        },

        /**
         * Validate results structure
         */
        validateResults: function(results) {
            if (!results || typeof results !== 'object') {
                return { valid: false, error: 'Invalid results format' };
            }

            if (results.status !== 'success') {
                return { valid: false, error: results.message || 'Analysis failed' };
            }

            if (!results.analytics || !results.results) {
                return { valid: false, error: 'Incomplete results data' };
            }

            return { valid: true };
        },

        /**
         * Get query information
         */
        getQueryInfo: function(results) {
            return {
                query: StorageManager.get(CONFIG.STORAGE.QUERY_KEY) || 
                       results.query_info?.query || 'Unknown',
                type: StorageManager.get(CONFIG.STORAGE.TYPE_KEY) || 
                      results.query_info?.type || 'auto',
                timestamp: results.timestamp || 
                          StorageManager.get(CONFIG.STORAGE.TIMESTAMP_KEY) || 
                          new Date().toISOString()
            };
        }
    };

    // ═══════════════════════════════════════════════════════════
    // RENDERER MODULE
    // ═══════════════════════════════════════════════════════════
    
    const Renderer = {
        /**
         * Render complete results page
         */
        renderAll: function(results) {
            Logger.log('=== Starting Results Rendering ===');

            try {
                this.renderHeader(results);
                this.renderAnalytics(results.analytics);
                this.renderSummary(results.summary, results.analytics);
                this.renderTable(results.results);
                this.renderChart(results.analytics);

                Logger.success('All components rendered successfully');
                
                // Apply fade-in animations
                this.applyAnimations();

            } catch (error) {
                Logger.error('Rendering failed:', error);
                throw error;
            }
        },

        /**
         * Render page header with query info
         */
        renderHeader: function(results) {
            Logger.info('Rendering header...');

            const queryInfo = DataManager.getQueryInfo(results);
            
            const queryElem = document.getElementById('queryInfo');
            const timestampElem = document.getElementById('timestamp');

            if (queryElem) {
                queryElem.textContent = `Query: ${queryInfo.query}`;
            }

            if (timestampElem) {
                timestampElem.textContent = UIUtils.formatDate(queryInfo.timestamp);
            }

            Logger.success('Header rendered');
        },

        /**
         * Render analytics metrics
         */
        renderAnalytics: function(analytics) {
            Logger.info('Rendering analytics...', analytics);

            if (!analytics) {
                Logger.warn('No analytics data provided');
                return;
            }

            // Total Entities
            const totalElem = document.getElementById('totalEntities');
            if (totalElem) {
                UIUtils.animateCounter(totalElem, 0, analytics.total_entities || 0, CONFIG.UI.COUNTER_DURATION);
            }

            // Average Confidence
            const confElem = document.getElementById('avgConfidence');
            if (confElem) {
                const percentage = Math.round((analytics.avg_confidence || 0) * 100);
                UIUtils.animateCounter(confElem, 0, percentage, CONFIG.UI.COUNTER_DURATION, '%');
            }

            // Source Count
            const sourceElem = document.getElementById('sourceCount');
            if (sourceElem) {
                UIUtils.animateCounter(sourceElem, 0, analytics.source_count || 0, CONFIG.UI.COUNTER_DURATION);
            }

            // Risk Level
            const riskElem = document.getElementById('riskLevel');
            if (riskElem) {
                const confidence = analytics.avg_confidence || 0;
                let riskLevel, riskClass;

                if (confidence >= 0.8) {
                    riskLevel = 'High';
                    riskClass = 'risk-high';
                } else if (confidence >= 0.5) {
                    riskLevel = 'Medium';
                    riskClass = 'risk-medium';
                } else {
                    riskLevel = 'Low';
                    riskClass = 'risk-low';
                }

                riskElem.textContent = riskLevel;
                riskElem.className = `stat-value ${riskClass}`;
            }

            Logger.success('Analytics rendered');
        },

        /**
         * Render AI summary
         */
        renderSummary: function(summary, analytics) {
            Logger.info('Rendering summary...');

            const summaryElem = document.getElementById('aiSummary') || 
                               document.getElementById('summaryText');

            if (!summaryElem) {
                Logger.warn('Summary element not found');
                return;
            }

            if (!summary) {
                summary = 'No summary available for this analysis.';
            }

            // Create formatted summary HTML
            summaryElem.innerHTML = `
                <div class="summary-content">
                    <p>${UIUtils.escapeHtml(summary)}</p>
                </div>
            `;

            Logger.success('Summary rendered');
        },

        /**
         * Render results table
         */
        renderTable: function(results) {
            Logger.info(`Rendering table with ${results?.length || 0} items...`);

            const tableBody = document.getElementById('tableBody');
            if (!tableBody) {
                Logger.error('Table body element not found');
                return;
            }

            // Clear existing content
            tableBody.innerHTML = '';

            // Update indicator count
            const indicatorCount = document.getElementById('indicatorCount');
            if (indicatorCount) {
                indicatorCount.textContent = `${results?.length || 0} indicator${results?.length !== 1 ? 's' : ''}`;
            }

            // Handle empty results
            if (!results || results.length === 0) {
                tableBody.innerHTML = `
                    <tr>
                        <td colspan="5" style="text-align:center; padding:2rem; color:#666;">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <line x1="12" y1="8" x2="12" y2="12"/>
                                <line x1="12" y1="16" x2="12.01" y2="16"/>
                            </svg>
                            <p style="margin-top:1rem;">No indicators found</p>
                        </td>
                    </tr>
                `;
                Logger.warn('No results to display');
                return;
            }

            // Render each result row
            results.forEach((item, index) => {
                const row = this.createTableRow(item, index);
                tableBody.appendChild(row);
            });

            Logger.success(`Table rendered with ${results.length} rows`);
        },

        /**
         * Create individual table row
         */
        createTableRow: function(item, index) {
            const row = document.createElement('tr');
            row.style.opacity = '0';
            row.style.transform = 'translateY(10px)';

            // Animate row appearance
            setTimeout(() => {
                row.style.transition = `all ${CONFIG.UI.ANIMATION_DURATION}ms ease`;
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
            }, index * 50);

            // Indicator cell
            const indicatorCell = document.createElement('td');
            indicatorCell.className = 'indicator-cell';
            indicatorCell.textContent = item.indicator || 'unknown';
            indicatorCell.title = item.indicator || 'unknown';
            row.appendChild(indicatorCell);

            // Type cell
            const typeCell = document.createElement('td');
            const typeBadge = document.createElement('span');
            typeBadge.className = `type-badge type-${(item.type || 'unknown').toLowerCase()}`;
            typeBadge.textContent = UIUtils.escapeHtml(item.type || 'unknown');
            typeCell.appendChild(typeBadge);
            row.appendChild(typeCell);

            // Confidence cell
            const confidenceCell = document.createElement('td');
            const confidence = Math.round((item.confidence || 0) * 100);
            const confClass = UIUtils.getConfidenceClass(item.confidence || 0);
            
            confidenceCell.innerHTML = `
                <div class="confidence-bar">
                    <div class="confidence-progress">
                        <div class="confidence-fill ${confClass}" style="width: ${confidence}%"></div>
                    </div>
                    <span class="confidence-value ${confClass}">${confidence}%</span>
                </div>
            `;
            row.appendChild(confidenceCell);

            // Connections cell
            const connectionsCell = document.createElement('td');
            connectionsCell.textContent = item.connections || 0;
            connectionsCell.className = 'connections-cell';
            row.appendChild(connectionsCell);

            // Source cell
            const sourceCell = document.createElement('td');
            sourceCell.className = 'source-cell';
            sourceCell.textContent = item.source || 'unknown';
            sourceCell.title = item.source || 'unknown';
            row.appendChild(sourceCell);

            return row;
        },

        /**
         * Render confidence distribution chart
         */
        renderChart: function(analytics) {
            if (!CONFIG.CHART.ENABLED) {
                Logger.info('Chart.js not available, skipping chart');
                return;
            }

            Logger.info('Rendering chart...');

            const canvas = document.getElementById('confidenceChart');
            if (!canvas) {
                Logger.warn('Chart canvas not found');
                return;
            }

            try {
                const confidence = analytics.avg_confidence || 0;
                
                // Calculate distribution (simplified)
                const high = confidence >= 0.8 ? analytics.total_entities * 0.6 : 0;
                const medium = confidence >= 0.5 ? analytics.total_entities * 0.3 : 0;
                const low = analytics.total_entities - high - medium;

                new Chart(canvas, {
                    type: CONFIG.CHART.TYPE,
                    data: {
                        labels: ['High Confidence', 'Medium Confidence', 'Low Confidence'],
                        datasets: [{
                            data: [high, medium, low],
                            backgroundColor: [
                                CONFIG.CHART.COLORS.HIGH,
                                CONFIG.CHART.COLORS.MEDIUM,
                                CONFIG.CHART.COLORS.LOW
                            ],
                            borderWidth: 0
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                position: 'bottom',
                                labels: {
                                    color: '#fff',
                                    padding: 15
                                }
                            }
                        }
                    }
                });

                Logger.success('Chart rendered');
            } catch (error) {
                Logger.error('Chart rendering failed:', error);
            }
        },

        /**
         * Apply animations to page elements
         */
        applyAnimations: function() {
            const animatedElements = document.querySelectorAll('.left-panel, .right-panel, .summary-card, .table-card');
            UIUtils.fadeIn(Array.from(animatedElements));
        }
    };

    // ═══════════════════════════════════════════════════════════
    // EXPORT MANAGER
    // ═══════════════════════════════════════════════════════════
    
    const ExportManager = {
        /**
         * Download results as JSON
         */
        downloadJSON: function(data) {
            try {
                Logger.info('Exporting JSON...');

                const jsonString = JSON.stringify(data, null, 2);
                const blob = new Blob([jsonString], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                
                const filename = `${CONFIG.EXPORT.FILENAME_PREFIX}-${Date.now()}.json`;
                
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                URL.revokeObjectURL(url);

                Logger.success('JSON downloaded');
                UIUtils.showNotification('Report downloaded successfully', 'success');

            } catch (error) {
                Logger.error('JSON export failed:', error);
                UIUtils.showNotification('Failed to download report', 'error');
            }
        },

        /**
         * Export table to CSV
         */
        downloadCSV: function(results) {
            try {
                Logger.info('Exporting CSV...');

                if (!results || results.length === 0) {
                    UIUtils.showNotification('No data to export', 'warning');
                    return;
                }

                const headers = ['Indicator', 'Type', 'Confidence', 'Connections', 'Source'];
                const rows = results.map(item => [
                    item.indicator || 'unknown',
                    item.type || 'unknown',
                    Math.round((item.confidence || 0) * 100) + '%',
                    item.connections || 0,
                    item.source || 'unknown'
                ]);

                const csv = [headers, ...rows]
                    .map(row => row.map(cell => `"${cell}"`).join(','))
                    .join('\n');

                const blob = new Blob([csv], { type: 'text/csv' });
                const url = URL.createObjectURL(blob);
                
                const filename = `${CONFIG.EXPORT.CSV_FILENAME_PREFIX}-${Date.now()}.csv`;
                
                const a = document.createElement('a');
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                
                URL.revokeObjectURL(url);

                Logger.success('CSV downloaded');
                UIUtils.showNotification('Table exported to CSV', 'success');

            } catch (error) {
                Logger.error('CSV export failed:', error);
                UIUtils.showNotification('Failed to export table', 'error');
            }
        }
    };

    // ═══════════════════════════════════════════════════════════
    // BUTTON HANDLERS
    // ═══════════════════════════════════════════════════════════
    
    const ButtonHandlers = {
        /**
         * Initialize all button handlers
         */
        initialize: function(results) {
            Logger.info('Initializing button handlers...');

            // Download JSON button
            const downloadBtn = document.getElementById('downloadBtn');
            if (downloadBtn) {
                downloadBtn.addEventListener('click', () => {
                    ExportManager.downloadJSON(results);
                });
            }

            // Export CSV button
            const exportBtn = document.getElementById('exportTableBtn');
            if (exportBtn) {
                exportBtn.addEventListener('click', () => {
                    ExportManager.downloadCSV(results.results);
                });
            }

            // Back to search button
            const backBtn = document.getElementById('backBtn');
            if (backBtn) {
                backBtn.addEventListener('click', () => {
                    Logger.info('Returning to search page');
                    window.location.href = '/';
                });
            }

            // New search button (alternative)
            const newSearchBtn = document.getElementById('newSearchBtn');
            if (newSearchBtn) {
                newSearchBtn.addEventListener('click', () => {
                    Logger.info('Starting new search');
                    window.location.href = '/';
                });
            }

            Logger.success('Button handlers initialized');
        }
    };

    // ═══════════════════════════════════════════════════════════
    // ERROR HANDLER
    // ═══════════════════════════════════════════════════════════
    
    const ErrorHandler = {
        /**
         * Display error state
         */
        showErrorState: function(message, autoRedirect = true) {
            Logger.error('Showing error state:', message);

            const container = document.querySelector('.container') || 
                            document.querySelector('.results-container') || 
                            document.querySelector('main') ||
                            document.body;

            container.innerHTML = `
                <div class="error-state" style="
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    justify-content: center;
                    min-height: 50vh;
                    text-align: center;
                    padding: 2rem;
                ">
                    <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="#ff3366" stroke-width="2">
                        <circle cx="12" cy="12" r="10"/>
                        <line x1="12" y1="8" x2="12" y2="12"/>
                        <line x1="12" y1="16" x2="12.01" y2="16"/>
                    </svg>
                    <h2 style="margin-top: 1.5rem; color: #fff; font-size: 1.5rem;">
                        ${UIUtils.escapeHtml(message)}
                    </h2>
                    ${autoRedirect ? `
                        <p style="color: #666; margin-top: 0.5rem;">
                            Redirecting to home page in <span id="countdown">3</span> seconds...
                        </p>
                    ` : ''}
                    <button onclick="window.location.href='dashboard/index.html'" 
                            style="
                                margin-top: 2rem;
                                padding: 0.75rem 2rem;
                                background: #ff0000;
                                color: #fff;
                                border: none;
                                border-radius: 8px;
                                cursor: pointer;
                                font-size: 1rem;
                            ">
                        Go to Search Page
                    </button>
                </div>
            `;

            if (autoRedirect) {
                this.startCountdown();
            }
        },

        /**
         * Start countdown for redirect
         */
        startCountdown: function() {
            let seconds = 3;
            const countdownElem = document.getElementById('countdown');

            const timer = setInterval(() => {
                seconds--;
                
                if (countdownElem) {
                    countdownElem.textContent = seconds;
                }

                if (seconds <= 0) {
                    clearInterval(timer);
                    window.location.href = 'index.html';
                }
            }, 1000);
        }
    };

    // ═══════════════════════════════════════════════════════════
    // APPLICATION INITIALIZATION
    // ═══════════════════════════════════════════════════════════
    
    function initialize() {
        Logger.log('╔══════════════════════════════════════════════════════════╗');
        Logger.log('║        GODEYE OSINT PLATFORM - RESULTS MODULE            ║');
        Logger.log('║                    Version 1.3.0                         ║');
        Logger.log('╚══════════════════════════════════════════════════════════╝');

        try {
            // Check if results exist
            if (!StorageManager.hasResults()) {
                Logger.error('No results found in storage');
                ErrorHandler.showErrorState('No analysis data found. Please run a new search.');
                return;
            }

            // Load results
            const results = DataManager.loadResults();
            if (!results) {
                ErrorHandler.showErrorState('Failed to load results. Please try again.');
                return;
            }

            // Validate results
            const validation = DataManager.validateResults(results);
            if (!validation.valid) {
                Logger.error('Invalid results:', validation.error);
                ErrorHandler.showErrorState(validation.error);
                return;
            }

            Logger.success('Results validated successfully');

            // Render results
            setTimeout(() => {
                Renderer.renderAll(results);
                ButtonHandlers.initialize(results);
            }, 100);

            Logger.success('Application initialized successfully');

        } catch (error) {
            Logger.error('Initialization failed:', error);
            ErrorHandler.showErrorState('An error occurred while loading results.');
        }
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
    
    window.GodEyeResults = {
        // Expose modules for testing
        CONFIG,
        Logger,
        StorageManager,
        DataManager,
        Renderer,
        ExportManager,
        
        // Utility functions
        version: '2.0.0',
        debugMode: CONFIG.DEBUG,
        
        // Manual controls
        reloadResults: initialize,
        clearResults: () => StorageManager.remove(CONFIG.STORAGE.RESULTS_KEY),
        
        // Get current state
        getState: function() {
            return {
                hasResults: StorageManager.hasResults(),
                results: DataManager.loadResults()
            };
        }
    };

    // Log initialization complete
    if (CONFIG.DEBUG) {
        console.log('%c GodEye Results Module Loaded ', 
                   'background: #ff0000; color: #fff; padding: 5px 10px; border-radius: 3px;');
        console.log('Access via: window.GodEyeResults');
    }

})(window, document);