// Utility functions

// Global API base URL
const API_BASE = window.location.origin;

/**
 * Format timestamp to readable string
 */
function formatTime(date = new Date()) {
    return date.toLocaleTimeString('ko-KR', {
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Escape HTML to prevent XSS
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Auto-resize textarea
 */
function autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 150) + 'px';
}

/**
 * Scroll to bottom of element
 */
function scrollToBottom(element, smooth = true) {
    element.scrollTo({
        top: element.scrollHeight,
        behavior: smooth ? 'smooth' : 'auto'
    });
}

/**
 * Show notification (simple toast)
 */
function showNotification(message, type = 'info') {
    // Simple console log for now
    // Can be enhanced with a proper toast notification system
    console.log(`[${type.toUpperCase()}] ${message}`);
}

/**
 * Parse markdown-like text to HTML (very basic)
 */
function parseMarkdown(text) {
    // Very basic markdown parsing
    // Code blocks
    text = text.replace(/```(\w+)?\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>');

    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Bold
    text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // Italic
    text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // Line breaks
    text = text.replace(/\n/g, '<br>');

    return text;
}

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
