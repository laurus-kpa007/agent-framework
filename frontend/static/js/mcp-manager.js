// MCP Settings Manager JavaScript

// DOM Elements
const serversList = document.getElementById('servers-list');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadMCPServers();
});

// Load MCP servers
async function loadMCPServers() {
    try {
        const response = await fetch(`${API_BASE}/api/mcp/servers`);
        const servers = await response.json();

        if (servers.length === 0) {
            serversList.innerHTML = `
                <div class="loading">
                    No MCP servers configured.
                    Edit config/mcp_servers.yaml to add servers.
                </div>
            `;
            return;
        }

        serversList.innerHTML = '';
        servers.forEach(server => {
            const serverCard = createServerCard(server);
            serversList.appendChild(serverCard);
        });

    } catch (error) {
        console.error('Failed to load MCP servers:', error);
        serversList.innerHTML = `
            <div class="loading" style="color: var(--error-color);">
                Failed to load MCP servers. Please check the server.
            </div>
        `;
    }
}

// Create server card
function createServerCard(server) {
    const card = document.createElement('div');
    card.className = 'server-card';

    const statusBadge = server.enabled
        ? '<span class="status-badge enabled">✓ Enabled</span>'
        : '<span class="status-badge disabled">✗ Disabled</span>';

    const toggleButton = server.enabled
        ? '<button class="toggle-btn disable" onclick="toggleServer(\'' + server.name + '\')">Disable</button>'
        : '<button class="toggle-btn enable" onclick="toggleServer(\'' + server.name + '\')">Enable</button>';

    card.innerHTML = `
        <div class="server-header">
            <div class="server-info">
                <h3>${escapeHtml(server.name)}</h3>
                <span class="server-type">${escapeHtml(server.type)}</span>
            </div>
            <div class="server-status">
                ${statusBadge}
                ${toggleButton}
            </div>
        </div>

        ${server.description ? `<p class="server-description">${escapeHtml(server.description)}</p>` : ''}

        <div class="server-details">
            <h4>Configuration:</h4>
            <div class="detail-row">
                <span class="detail-label">Command:</span>
                <span class="detail-value">${escapeHtml(server.config.command)}</span>
            </div>
            ${server.config.args && server.config.args.length > 0 ? `
            <div class="detail-row">
                <span class="detail-label">Arguments:</span>
                <span class="detail-value">${escapeHtml(server.config.args.join(' '))}</span>
            </div>
            ` : ''}
            ${Object.keys(server.env || {}).length > 0 ? `
            <div class="detail-row">
                <span class="detail-label">Env Vars:</span>
                <span class="detail-value">${Object.keys(server.env).join(', ')}</span>
            </div>
            ` : ''}
        </div>
    `;

    return card;
}

// Toggle server (placeholder - requires server restart)
async function toggleServer(serverName) {
    try {
        const response = await fetch(`${API_BASE}/api/mcp/servers/${serverName}/toggle`, {
            method: 'POST'
        });
        const result = await response.json();

        alert(`${result.message}\n\nNote: Server restart required for changes to take effect.`);

        // Reload servers list
        loadMCPServers();

    } catch (error) {
        console.error('Failed to toggle server:', error);
        alert('This feature will be fully implemented in Phase 2.\n\nFor now, please edit config/mcp_servers.yaml manually and restart the server.');
    }
}

// Test server connection (placeholder)
async function testServer(serverName) {
    try {
        const response = await fetch(`${API_BASE}/api/mcp/test/${serverName}`, {
            method: 'POST'
        });
        const result = await response.json();

        alert(`Server Test:\n${result.message}`);

    } catch (error) {
        console.error('Failed to test server:', error);
        alert('Failed to test server connection.');
    }
}
