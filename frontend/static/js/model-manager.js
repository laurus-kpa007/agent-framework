// Model Manager JavaScript

// DOM Elements
const modelSelectBtn = document.getElementById('model-select-btn');
const currentModelName = document.getElementById('current-model-name');
const modelDropdown = document.getElementById('model-dropdown');
const modelList = document.getElementById('model-list');
const refreshModelsBtn = document.getElementById('refresh-models-btn');

let currentModel = null;
let availableModels = [];

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupModelManager();
    loadModels();
});

// Setup event listeners
function setupModelManager() {
    // Toggle dropdown
    modelSelectBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        modelDropdown.classList.toggle('hidden');
        modelSelectBtn.classList.toggle('open');
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!modelDropdown.contains(e.target) && e.target !== modelSelectBtn) {
            modelDropdown.classList.add('hidden');
            modelSelectBtn.classList.remove('open');
        }
    });

    // Refresh models
    refreshModelsBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        loadModels();
    });
}

// Load available models
async function loadModels() {
    try {
        modelList.innerHTML = '<div class="loading">Loading models...</div>';

        const response = await fetch(`${API_BASE}/api/chat/models`);
        const data = await response.json();

        availableModels = data.models;
        currentModel = data.current_model;

        // Update UI
        if (currentModel) {
            currentModelName.textContent = formatModelName(currentModel);
        } else {
            currentModelName.textContent = 'Select Model';
        }

        renderModelList();

    } catch (error) {
        console.error('Failed to load models:', error);
        modelList.innerHTML = '<div class="loading" style="color: var(--error-color);">Failed to load models</div>';
    }
}

// Render model list
function renderModelList() {
    if (availableModels.length === 0) {
        modelList.innerHTML = '<div class="loading">No models available. Please pull models using: ollama pull &lt;model-name&gt;</div>';
        return;
    }

    modelList.innerHTML = '';

    availableModels.forEach(model => {
        const modelItem = createModelItem(model);
        modelList.appendChild(modelItem);
    });
}

// Create model item element
function createModelItem(model) {
    const item = document.createElement('div');
    item.className = 'model-item';

    const isCurrent = model.name === currentModel;
    if (isCurrent) {
        item.classList.add('current');
    }

    // Model name
    const nameDiv = document.createElement('div');
    nameDiv.className = 'model-item-name';
    nameDiv.innerHTML = `
        <span>${formatModelName(model.name)}</span>
        ${isCurrent ? '<span class="badge">LOADED</span>' : ''}
    `;

    // Model info
    const infoDiv = document.createElement('div');
    infoDiv.className = 'model-item-info';
    infoDiv.textContent = `Size: ${formatSize(model.size)}`;

    item.appendChild(nameDiv);
    item.appendChild(infoDiv);

    // Load button
    if (!isCurrent) {
        const loadBtn = document.createElement('button');
        loadBtn.className = 'model-load-btn';
        loadBtn.textContent = 'Load Model';
        loadBtn.onclick = (e) => {
            e.stopPropagation();
            loadModel(model.name, loadBtn);
        };
        item.appendChild(loadBtn);
    }

    return item;
}

// Load a specific model
async function loadModel(modelName, buttonElement) {
    try {
        // Disable button and show loading
        buttonElement.disabled = true;
        buttonElement.innerHTML = '<span class="model-loading"></span> Loading...';

        const response = await fetch(`${API_BASE}/api/chat/models/load`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                model_name: modelName
            })
        });

        const data = await response.json();

        if (data.success) {
            // Update current model
            currentModel = modelName;
            currentModelName.textContent = formatModelName(modelName);

            // Close dropdown
            modelDropdown.classList.add('hidden');
            modelSelectBtn.classList.remove('open');

            // Reload model list
            await loadModels();

            // Show success message
            showNotification(`Model '${formatModelName(modelName)}' loaded successfully!`, 'success');

            // Refresh health status
            if (typeof checkHealth === 'function') {
                checkHealth();
            }

        } else {
            showNotification(`Failed to load model: ${data.message}`, 'error');
            buttonElement.disabled = false;
            buttonElement.textContent = 'Load Model';
        }

    } catch (error) {
        console.error('Error loading model:', error);
        showNotification('Error loading model. Please try again.', 'error');
        buttonElement.disabled = false;
        buttonElement.textContent = 'Load Model';
    }
}

// Format model name (remove version tags for display)
function formatModelName(name) {
    if (!name) return 'Unknown';
    // Keep first part before : if it exists
    return name.split(':')[0];
}

// Format size in bytes to human-readable
function formatSize(bytes) {
    if (!bytes) return 'Unknown';

    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';

    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

// Show notification (enhanced version)
function showNotification(message, type = 'info') {
    console.log(`[${type.toUpperCase()}] ${message}`);

    // You can enhance this with a toast notification library
    // For now, use console and alert for important messages
    if (type === 'error') {
        alert(message);
    }
}

// Export for use in other scripts
window.modelManager = {
    loadModels,
    getCurrentModel: () => currentModel,
    isModelLoaded: () => currentModel !== null
};
