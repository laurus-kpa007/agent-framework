// Chat Application JavaScript

let isStreaming = false;

// DOM Elements
const chatForm = document.getElementById('chat-form');
const messageInput = document.getElementById('message-input');
const sendBtn = document.getElementById('send-btn');
const chatMessages = document.getElementById('chat-messages');
const statusIndicator = document.querySelector('.status-dot');
const statusText = document.querySelector('.status-text');
const toolsList = document.getElementById('tools-list');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkHealth();
    loadActiveTools();
    setupEventListeners();
});

// Event Listeners
function setupEventListeners() {
    chatForm.addEventListener('submit', handleSubmit);

    messageInput.addEventListener('input', () => {
        autoResizeTextarea(messageInput);
    });

    messageInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            if (e.ctrlKey) {
                // Ctrl+Enter: Insert new line
                return;
            } else {
                // Enter: Send message
                e.preventDefault();
                chatForm.requestSubmit();
            }
        }
    });
}

// Check server health
async function checkHealth() {
    try {
        const response = await fetch(`${API_BASE}/api/chat/health`);
        const data = await response.json();

        if (data.ollama_connected) {
            statusIndicator.classList.add('connected');
            if (data.model_loaded && data.ollama_model) {
                statusText.textContent = `Connected (${data.ollama_model})`;
            } else {
                statusText.textContent = 'Connected - No Model';
            }
        } else {
            statusIndicator.classList.remove('connected');
            statusText.textContent = 'Ollama Disconnected';
        }
    } catch (error) {
        statusIndicator.classList.remove('connected');
        statusText.textContent = 'Server Error';
        console.error('Health check failed:', error);
    }
}

// Load active tools
async function loadActiveTools() {
    try {
        const response = await fetch(`${API_BASE}/api/chat/health`);
        const data = await response.json();

        if (data.active_tools_count > 0) {
            toolsList.textContent = `${data.active_tools_count} tools available`;
        } else {
            toolsList.textContent = 'No tools loaded';
        }
    } catch (error) {
        toolsList.textContent = 'Error loading tools';
        console.error('Failed to load tools:', error);
    }
}

// Handle form submission
async function handleSubmit(e) {
    e.preventDefault();

    const message = messageInput.value.trim();
    if (!message || isStreaming) return;

    // Check if model is loaded
    if (window.modelManager && !window.modelManager.isModelLoaded()) {
        alert('Please select and load a model first from the dropdown!');
        return;
    }

    // Add user message to UI
    addMessage(message, 'user');

    // Clear input
    messageInput.value = '';
    autoResizeTextarea(messageInput);

    // Disable input during streaming
    setInputState(false);

    // Send message and stream response
    await streamMessage(message);
}

// Stream message to API (TTFT Optimized)
async function streamMessage(message) {
    isStreaming = true;

    // Create assistant message container
    const messageDiv = createMessageElement('', 'assistant');
    const contentDiv = messageDiv.querySelector('.message-content');

    // Track timing for TTFT measurement
    const startTime = performance.now();
    let firstTokenTime = null;

    try {
        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                stream: true
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let fullText = '';
        let isFirstChunk = true;

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop(); // Keep incomplete line in buffer

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        // Handle processing status (immediate feedback)
                        if (data.status === 'processing') {
                            contentDiv.innerHTML = '<p><span class="typing-indicator">Thinking</span></p>';
                            continue;
                        }

                        if (data.error) {
                            contentDiv.innerHTML = `<p style="color: var(--error-color);">Error: ${escapeHtml(data.error)}</p>`;
                            break;
                        }

                        if (data.text) {
                            // Measure TTFT
                            if (isFirstChunk) {
                                firstTokenTime = performance.now();
                                const ttft = Math.round(firstTokenTime - startTime);
                                console.log(`⚡ TTFT: ${ttft}ms`);
                                isFirstChunk = false;
                            }

                            fullText += data.text;
                            contentDiv.innerHTML = `<div>${parseMarkdown(fullText)}</div>`;

                            // Optimize scrolling - only scroll if near bottom
                            const isNearBottom = chatMessages.scrollHeight - chatMessages.scrollTop - chatMessages.clientHeight < 100;
                            if (isNearBottom) {
                                scrollToBottom(chatMessages, false); // Use non-smooth scroll for performance
                            }
                        }

                        if (data.done) {
                            // Log final stats
                            const totalTime = Math.round(performance.now() - startTime);
                            console.log(`✓ Total time: ${totalTime}ms, Chunks: ${data.chunks || 0}`);

                            // Optionally show tools used
                            if (data.tools_used && data.tools_used.length > 0) {
                                const toolsDiv = document.createElement('div');
                                toolsDiv.className = 'tool-indicator';
                                toolsDiv.textContent = `🔧 Tools: ${data.tools_used.join(', ')}`;
                                messageDiv.appendChild(toolsDiv);
                            }
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }

    } catch (error) {
        console.error('Streaming error:', error);
        contentDiv.innerHTML = `<p style="color: var(--error-color);">Error: Failed to get response. Is Ollama running?</p>`;
    } finally {
        isStreaming = false;
        setInputState(true);
        messageInput.focus();
    }
}

// Add message to chat
function addMessage(text, type) {
    const messageDiv = createMessageElement(text, type);
    scrollToBottom(chatMessages);
}

// Create message element
function createMessageElement(text, type) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;

    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';

    if (text) {
        const div = document.createElement('div');
        div.innerHTML = parseMarkdown(text);
        contentDiv.appendChild(div);
    } else {
        // Empty message for streaming
        const p = document.createElement('p');
        p.innerHTML = '<span class="typing-indicator">Thinking</span>';
        contentDiv.appendChild(p);
    }

    messageDiv.appendChild(contentDiv);
    chatMessages.appendChild(messageDiv);

    return messageDiv;
}

// Set input state
function setInputState(enabled) {
    messageInput.disabled = !enabled;
    sendBtn.disabled = !enabled;

    if (enabled) {
        messageInput.focus();
    }
}

// Refresh health periodically
setInterval(checkHealth, 30000); // Every 30 seconds
