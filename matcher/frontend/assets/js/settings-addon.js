
// Add enableApiKeyEdit function at the end of settings.js
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
