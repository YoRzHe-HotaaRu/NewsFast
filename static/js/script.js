// NewsFast Frontend JavaScript

document.addEventListener('DOMContentLoaded', function() {
    const urlForm = document.getElementById('urlForm');
    const articleUrl = document.getElementById('articleUrl');
    const summarizeBtn = document.getElementById('summarizeBtn');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const loadingState = document.getElementById('loadingState');
    const resultsSection = document.getElementById('resultsSection');
    const errorState = document.getElementById('errorState');
    const errorMessage = document.getElementById('errorMessage');

    // Form submission handler
    urlForm.addEventListener('submit', async function(e) {
        e.preventDefault();

        const url = articleUrl.value.trim();

        if (!url) {
            showError('Please enter a valid URL');
            return;
        }

        if (!isValidUrl(url)) {
            showError('Please enter a valid URL (e.g., https://example.com/article)');
            return;
        }

        // Show loading state
        showLoadingState();

        try {
            // Make API request
            const response = await fetch('/summarize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ url: url })
            });

            const data = await response.json();

            if (data.success) {
                // Display results
                displayResults(data);
            } else {
                // Show error
                showError(data.error || 'An error occurred during summarization');
            }

        } catch (error) {
            console.error('Error:', error);
            showError('Network error occurred. Please check your connection and try again.');
        } finally {
            // Hide loading state
            hideLoadingState();
        }
    });

    function isValidUrl(string) {
        try {
            const url = new URL(string);
            return url.protocol === 'http:' || url.protocol === 'https:';
        } catch (_) {
            return false;
        }
    }

    function showLoadingState() {
        // Update button
        summarizeBtn.disabled = true;
        loadingSpinner.classList.remove('d-none');
        summarizeBtn.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Processing...';

        // Show loading card
        loadingState.classList.remove('d-none');

        // Hide other states
        resultsSection.classList.add('d-none');
        errorState.classList.add('d-none');
    }

    function hideLoadingState() {
        // Reset button
        summarizeBtn.disabled = false;
        loadingSpinner.classList.add('d-none');
        summarizeBtn.innerHTML = '<span class="spinner-border spinner-border-sm d-none" id="loadingSpinner"></span> Summarize Article';

        // Hide loading card
        loadingState.classList.add('d-none');
    }

    function showError(message) {
        errorMessage.textContent = message;
        errorState.classList.remove('d-none');
        resultsSection.classList.add('d-none');
        loadingState.classList.add('d-none');

        // Also hide loading state
        hideLoadingState();
    }

    function displayResults(data) {
        // Hide error state
        errorState.classList.add('d-none');

        // Display article info
        displayArticleInfo(data.article);

        // Display extractive summary
        displayExtractiveSummary(data.extractive_summary);

        // Display keywords
        displayKeywords(data.keywords);

        // Display AI summary
        displayAISummary(data.ai_summary);

        // Show results section with fade-in animation
        resultsSection.classList.remove('d-none');
        resultsSection.classList.add('fade-in');

        // Scroll to results
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function displayArticleInfo(article) {
        // Title
        const titleElement = document.getElementById('articleTitle');
        titleElement.textContent = article.title || 'Unknown Title';

        // Meta information
        const metaElement = document.getElementById('articleMeta');
        const metaParts = [];

        if (article.authors && article.authors.length > 0) {
            metaParts.push('By: ' + article.authors.join(', '));
        }

        if (article.publish_date) {
            metaParts.push('Published: ' + new Date(article.publish_date).toLocaleDateString());
        }

        metaParts.push('Word count: ' + (article.word_count || 0));
        metaElement.textContent = metaParts.join(' | ');

        // Link
        const linkElement = document.getElementById('articleLink');
        linkElement.href = article.url;
    }

    function displayExtractiveSummary(summaryData) {
        const container = document.getElementById('extractiveSummary');

        if (!summaryData.summary) {
            container.innerHTML = '<p class="text-muted">No extractive summary available.</p>';
            return;
        }

        // Split into sentences and highlight key sentences
        const sentences = summaryData.summary.split(/[.!?]+/).filter(s => s.trim().length > 0);

        let html = '';
        sentences.forEach((sentence, index) => {
            const trimmedSentence = sentence.trim();
            if (trimmedSentence) {
                // Highlight alternating sentences or sentences with important words
                const isImportant = trimmedSentence.length > 100 ||
                                  trimmedSentence.includes('said') ||
                                  trimmedSentence.includes('announced') ||
                                  trimmedSentence.includes('according');

                if (isImportant) {
                    html += `<div class="highlight-sentence">${trimmedSentence}.</div>`;
                } else {
                    html += `<p>${trimmedSentence}.</p>`;
                }
            }
        });

        container.innerHTML = html || '<p class="text-muted">No extractive summary available.</p>';
    }

    function displayKeywords(keywordsData) {
        const container = document.getElementById('keywords');

        if (!keywordsData.keywords || !Array.isArray(keywordsData.keywords)) {
            container.innerHTML = '<p class="text-muted">No keywords available.</p>';
            return;
        }

        let html = '';
        keywordsData.keywords.forEach(([keyword, score]) => {
            const sizeClass = score > 0.05 ? 'keyword-badge' : 'keyword-badge';
            html += `<span class="${sizeClass}">${keyword}</span>`;
        });

        container.innerHTML = html || '<p class="text-muted">No keywords available.</p>';
    }

    function displayAISummary(aiData) {
        const container = document.getElementById('abstractiveSummary');

        if (!aiData.summary) {
            container.innerHTML = '<p class="text-muted">No AI summary available.</p>';
            return;
        }

        // Format AI summary with better styling
        let summary = aiData.summary;

        // Add some basic formatting if the AI didn't provide it
        if (!summary.includes('\n')) {
            // Split long summary into paragraphs
            const words = summary.split(' ');
            if (words.length > 50) {
                const midPoint = Math.floor(words.length / 2);
                summary = words.slice(0, midPoint).join(' ') + '\n\n' + words.slice(midPoint).join(' ');
            }
        }

        container.innerHTML = `<div class="ai-summary">${summary.replace(/\n/g, '</div><div class="ai-summary">')}</div>`;
    }

    // Reset form function (called from HTML)
    window.resetForm = function() {
        urlForm.reset();
        resultsSection.classList.add('d-none');
        errorState.classList.add('d-none');
        loadingState.classList.add('d-none');

        // Focus on URL input
        articleUrl.focus();
    };

    // Auto-resize textarea if needed
    function autoResizeTextarea() {
        const textarea = document.querySelector('textarea');
        if (textarea) {
            textarea.style.height = 'auto';
            textarea.style.height = textarea.scrollHeight + 'px';
        }
    }

    // Initialize tooltips if Bootstrap is available
    if (typeof bootstrap !== 'undefined') {
        var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K to focus URL input
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            articleUrl.focus();
        }

        // Escape to reset form
        if (e.key === 'Escape' && resultsSection.classList.contains('d-none') === false) {
            resetForm();
        }
    });

    // Auto-focus URL input on page load
    articleUrl.focus();
});

// Utility functions
function formatDate(dateString) {
    if (!dateString) return '';

    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (e) {
        return dateString;
    }
}

function truncateText(text, maxLength = 100) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substr(0, maxLength) + '...';
}

// Progress indicator for long-running operations
function showProgress(message = 'Processing...') {
    // This could be enhanced to show detailed progress
    console.log('Progress:', message);
}