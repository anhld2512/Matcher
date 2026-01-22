/**
 * AI Settings Management
 * Handles the AI configuration modal, provider selection, and model management.
 */

// Check if variables are already declared to avoid SyntaxError on double load
if (typeof availableProviders === 'undefined') {
    var availableProviders = [];
    var currentConfig = null;
}

// Main Initialization Function
function initAiSettings() {
    // Prevent duplicate injection
    if (document.getElementById('aiSettingsModal')) {
        console.log('AI Settings Modal already exists');
        return;
    }

    const modalHtml = `
    <div id="aiSettingsModal" class="modal">
        <div class="modal-content" style="max-width: 600px;">
            <div class="modal-header">
                <h3 class="modal-title">
                    <i class="bi bi-robot"></i>
                    Cấu hình AI
                </h3>
                <button class="modal-close" id="aiModalCloseX">
                    <i class="bi bi-x"></i>
                </button>
            </div>
            <div class="modal-body">
                <!-- Status Alert -->
                <div id="aiConnectionStatus" class="mb-4 hidden"></div>

                <!-- Provider Selection -->
                <div class="form-group">
                    <label class="form-label">Nhà cung cấp AI (AI Provider)</label>
                    <select id="aiProviderSelect" class="form-control" onchange="handleProviderChange()">
                        <option value="">Đang tải...</option>
                    </select>
                    <p id="aiProviderDesc" class="text-sm text-gray-500 mt-1"></p>
                </div>

                <!-- Settings Form -->
                <div id="aiConfigForm">
                    <!-- Dynamic fields will be injected here -->
                </div>

                <!-- Test & Save Buttons -->
                <div class="flex items-center gap-2 mt-6 pt-4 border-t border-gray-200">
                    <button id="testConnectionBtn" class="btn btn-outline" onclick="testAiConnection()">
                        <i class="bi bi-lightning-charge"></i>
                        Kiểm tra kết nối
                    </button>
                    <div style="flex: 1;"></div>
                    <button class="btn btn-outline" id="aiModalCloseBtn">Hủy</button>
                    <button id="saveAiSettingsBtn" class="btn btn-primary" onclick="saveAiSettings()">
                        <i class="bi bi-save"></i>
                        Lưu cấu hình
                    </button>
                </div>
            </div>
        </div>
    </div>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    
    // Add event listeners (Robust Fix)
    const modal = document.getElementById('aiSettingsModal');
    const closeX = document.getElementById('aiModalCloseX');
    const closeBtn = document.getElementById('aiModalCloseBtn');

    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'aiSettingsModal') closeAiSettingsModal();
        });
    }

    if (closeX) {
        closeX.addEventListener('click', (e) => {
            e.preventDefault(); 
            closeAiSettingsModal();
        });
    }

    if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            closeAiSettingsModal();
        });
    }

    console.log('AI Settings Modal Initialized');
    
    // Initialize data
    loadAiProviders();
}

async function loadAiProviders() {
    try {
        const [providersRes, settingsRes] = await Promise.all([
            fetch('/ai-providers'),
            fetch('/ai-settings')
        ]);
        
        const providersData = await providersRes.json();
        availableProviders = providersData.providers;
        
        currentConfig = await settingsRes.json();
        
        // Store actual API key for testing (when input is disabled/masked)
        if (currentConfig.api_key) {
            window.currentAiApiKey = currentConfig.api_key;
        }
        
        const select = document.getElementById('aiProviderSelect');
        if (select) {
            select.innerHTML = availableProviders.map(p => 
                `<option value="${p.id}">${p.name}</option>`
            ).join('');
            
            // Select current provider
            if (currentConfig.configured) {
                select.value = currentConfig.provider;
            } else {
                select.value = 'gemini'; // Default to Gemini (cloud-based, fast)
            }
            
            handleProviderChange();
        }
        
    } catch (e) {
        console.error('Failed to load AI settings:', e);
    }
}

async function handleProviderChange() {
    const select = document.getElementById('aiProviderSelect');
    if (!select) return;
    
    const providerId = select.value;
    const provider = availableProviders.find(p => p.id === providerId);
    
    // Update description
    document.getElementById('aiProviderDesc').textContent = provider.description;
    
    // Build form
    const container = document.getElementById('aiConfigForm');
    let html = '';
    
    // API Key (All cloud providers)
    if (provider.requires_api_key) {
        const hasKey = currentConfig.api_key_set && currentConfig.provider === providerId;
        html += `
            <div class="form-group">
                <label class="form-label">API Key</label>
                ${hasKey ? `
                    <div class="flex items-center gap-2">
                        <input type="password" id="aiApiKey" class="form-control" value="••••••••••••••••••••••••••" disabled>
                        <button type="button" class="btn btn-outline" onclick="enableApiKeyEdit()">
                            <i class="bi bi-pencil"></i> Đổi
                        </button>
                    </div>
                    <small class="text-gray-500 text-xs">API key đã được lưu</small>
                ` : `
                    <input type="password" id="aiApiKey" class="form-control" placeholder="Nhập API key...">
                    <small class="text-gray-500 text-xs">Lấy API key từ trang chủ của provider</small>
                `}
            </div>
        `;
    }
    
    // Model Selection
    html += `
        <div class="form-group">
            <label class="form-label">Model</label>
            <select id="aiModel" class="form-control" onchange="handleModelChange()">
                <option value="">Đang tải...</option>
            </select>
        </div>
    `;
    
    container.innerHTML = html;
    
    // Load models for this provider
    loadModels(providerId);
}

async function loadModels(providerId) {
    try {
        const res = await fetch(`/ai-models/${providerId}`);
        const data = await res.json();
        
        const modelSelect = document.getElementById('aiModel');
        if (!modelSelect) return;
        
        if (data.models && data.models.length > 0) {
            modelSelect.innerHTML = data.models.map(m => 
                `<option value="${m}">${m}</option>`
            ).join('');
            
            // Select current model if matches
            if (currentConfig.provider === providerId && currentConfig.model_name) {
                modelSelect.value = currentConfig.model_name;
            } else {
                modelSelect.value = data.models[0];
            }
        } else {
            modelSelect.innerHTML = '<option value="">Không có model</option>';
        }
        
    } catch (e) {
        console.error('Failed to load models:', e);
        const modelSelect = document.getElementById('aiModel');
        if (modelSelect) {
            modelSelect.innerHTML = '<option value="">Lỗi tải models</option>';
        }
    }
}

function handleModelChange() {
    // Optional: Add any model-specific logic here
    // For now, just a placeholder
}

function togglePullModel() {
    document.getElementById('pullModelSection').classList.toggle('hidden');
}

async function pullOllamaModel() {
    const modelName = document.getElementById('pullModelName').value.trim();
    if (!modelName) return;
    
    const statusDiv = document.getElementById('pullStatus');
    const btn = document.getElementById('startPullBtn');
    
    statusDiv.classList.remove('hidden');
    btn.disabled = true;
    
    try {
        const host = document.getElementById('aiHost').value;
        const port = document.getElementById('aiPort').value;
        
        const res = await fetch(`/ai-models/pull?provider=ollama&model_name=${modelName}&host=${host}&port=${port}`, {
            method: 'POST'
        });
        
        if (!res.ok) throw new Error(await res.text());
        
        alert('Đã thêm model vào hàng đợi tải xuống! Bạn có thể đóng cửa sổ này, quá trình sẽ chạy ngầm.');
        document.getElementById('pullModelName').value = '';
        
        // Refresh models after delay
        setTimeout(() => loadModels('ollama'), 5000);
        
    } catch (e) {
        alert('Lỗi: ' + e.message);
    } finally {
        statusDiv.classList.add('hidden');
        btn.disabled = false;
    }
}

async function saveAiSettings() {
    const provider = document.getElementById('aiProviderSelect').value;
    const modelSelect = document.getElementById('aiModel');
    const model = modelSelect ? modelSelect.value : '';
    
    if (!model) {
        alert('Vui lòng chọn Model');
        return;
    }
    
    const apiKeyInput = document.getElementById('aiApiKey');
    const payload = {
        provider: provider,
        model_name: model,
        api_key: (apiKeyInput && !apiKeyInput.disabled) ? apiKeyInput.value : ""
    };
    
    try {
        const res = await fetch('/ai-settings', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        if (!res.ok) throw new Error(await res.text());
        
        const data = await res.json();
        currentConfig = {...currentConfig, ...payload, configured: true};
        
        alert('Đã lưu cấu hình thành công!');
        closeAiSettingsModal();
        
    } catch (e) {
        alert('Lỗi lưu cấu hình: ' + e.message);
    }
}

async function testAiConnection() {
    const statusDiv = document.getElementById('aiConnectionStatus');
    statusDiv.className = 'mb-4 p-3 rounded bg-blue-50 text-blue-700 flex items-center gap-2';
    statusDiv.innerHTML = '<i class="bi bi-hourglass-split"></i> Đang kiểm tra kết nối...';
    statusDiv.classList.remove('hidden');
    
    try {
        // Get current form values
        const provider = document.getElementById('aiProviderSelect').value;
        const modelSelect = document.getElementById('aiModel');
        const model = modelSelect ? modelSelect.value : '';
        const apiKeyInput = document.getElementById('aiApiKey');
        
        // If input is disabled (showing masked key), use saved key from global variable
        // Otherwise use the value from input (user is entering new key)
        let apiKey = '';
        if (apiKeyInput.disabled && window.currentAiApiKey) {
            apiKey = window.currentAiApiKey;
        } else if (!apiKeyInput.disabled) {
            apiKey = apiKeyInput.value;
        }
        
        if (!model) {
            throw new Error('Vui lòng chọn model trước');
        }
        
        if (!apiKey) {
            throw new Error('Vui lòng nhập API key trước');
        }
        
        // Test with current values
        const res = await fetch('/test-ai', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                provider: provider,
                config: {
                    api_key: apiKey,
                    model: model
                }
            })
        });
        
        const data = await res.json();
        
        if (data.connected) {
            statusDiv.className = 'mb-4 p-3 rounded bg-green-50 text-green-700 flex items-center gap-2';
            statusDiv.innerHTML = '<i class="bi bi-check-circle-fill"></i> Kết nối thành công!';
        } else {
            throw new Error(data.message || 'Không thể kết nối');
        }
        
    } catch (e) {
        statusDiv.className = 'mb-4 p-3 rounded bg-red-50 text-red-700 flex items-center gap-2';
        statusDiv.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> Lỗi: ${e.message}`;
    }
}

function openAiSettingsModal() {
    const modal = document.getElementById('aiSettingsModal');
    if (modal) modal.classList.add('active');
}

function closeAiSettingsModal() {
    const modal = document.getElementById('aiSettingsModal');
    if (modal) modal.classList.remove('active');
}

// Expose functions to global scope
window.openAiSettingsModal = openAiSettingsModal;
window.closeAiSettingsModal = closeAiSettingsModal;
window.saveAiSettings = saveAiSettings;
window.testAiConnection = testAiConnection;
window.loadModels = loadModels;
window.handleProviderChange = handleProviderChange;
window.togglePullModel = togglePullModel;
window.pullOllamaModel = pullOllamaModel;

// Enable API Key editing
function enableApiKeyEdit() {
    const input = document.getElementById('aiApiKey');
    if (input) {
        input.disabled = false;
        input.value = '';
        input.placeholder = 'Nhập API key mới...';
        input.focus();
        
        // Hide the Change button
        const btn = event.target.closest('button');
        if (btn) btn.style.display = 'none';
    }
}
window.enableApiKeyEdit = enableApiKeyEdit;

// Robust Start Logic
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAiSettings);
} else {
    initAiSettings(); // DOM already ready, run now
}
