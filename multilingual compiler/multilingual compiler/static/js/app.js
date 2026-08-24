/* Global Application Utilities */

function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.position = 'fixed';
        container.style.bottom = '20px';
        container.style.right = '20px';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `glass-card toast toast-${type}`;
    toast.style.padding = '0.75rem 1.25rem';
    toast.style.marginTop = '0.5rem';
    toast.style.minWidth = '250px';
    toast.style.borderLeft = type === 'success' ? '4px solid #10b981' : type === 'danger' ? '4px solid #f43f5e' : '4px solid #6366f1';

    toast.innerHTML = `<strong>${type.toUpperCase()}</strong>: ${message}`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Modal open/close utilities
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.add('active');
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.classList.remove('active');
    }
}

// Programmatic tab switching utility
function switchTab(tabId) {
    const btn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
    if (btn) {
        const parentNav = btn.closest('.tabs-nav') || btn.parentElement;
        parentNav.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        const parentContainer = btn.closest('.output-panel') || document;
        parentContainer.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        const targetContent = document.getElementById(tabId);
        if (targetContent) targetContent.classList.add('active');
    }
}

// Close modals when clicking overlay outside card
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        e.target.classList.remove('active');
    }
});

// Tab Switching Event Listener
document.addEventListener('DOMContentLoaded', () => {
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const parentNav = btn.closest('.tabs-nav') || btn.parentElement;
            parentNav.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const targetId = btn.getAttribute('data-tab');
            if (targetId) {
                const parentContainer = btn.closest('.output-panel') || document;
                parentContainer.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                const targetContent = document.getElementById(targetId);
                if (targetContent) targetContent.classList.add('active');
            }
        });
    });
});
