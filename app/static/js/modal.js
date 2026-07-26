document.addEventListener('DOMContentLoaded', () => {
    const overlay = document.getElementById('institu-modal-overlay');
    if (!overlay) return;

    const btnClose = overlay.querySelector('.modal-close');
    const btnCancel = overlay.querySelector('.modal-btn-cancel');
    const btnConfirm = overlay.querySelector('.modal-btn-confirm');
    const titleEl = document.getElementById('modal-title');
    const messageEl = document.getElementById('modal-message');

    let currentAction = null;

    function closeModal() {
        overlay.classList.remove('active');
        setTimeout(() => {
            overlay.style.display = 'none';
            currentAction = null;
        }, 200);
    }

    function resetModal() {
        btnCancel.style.display = '';
        btnConfirm.style.display = '';
    }

    function openModal(title, message, confirmText, confirmClass, actionCallback) {
        resetModal();
        titleEl.textContent = title || 'Confirmação';
        messageEl.innerHTML = message || 'Tem a certeza que deseja realizar esta ação?';
        
        btnConfirm.textContent = confirmText || 'Confirmar';
        btnConfirm.className = `btn modal-btn-confirm ${confirmClass || 'btn-primary'}`;
        
        currentAction = actionCallback;

        overlay.style.display = 'flex';
        // Force reflow
        void overlay.offsetWidth;
        overlay.classList.add('active');
    }

    function showAlert(message, title, type) {
        const typeMap = {
            success: { btnClass: 'btn-success', defaultTitle: 'Sucesso' },
            error:   { btnClass: 'btn-danger',  defaultTitle: 'Erro' },
            warning: { btnClass: 'btn-warning', defaultTitle: 'Aviso' },
            info:    { btnClass: 'btn-primary', defaultTitle: 'Informação' },
        };
        const cfg = typeMap[type] || typeMap.info;

        btnCancel.style.display = 'none';
        titleEl.textContent = title || cfg.defaultTitle;
        messageEl.textContent = message;
        btnConfirm.textContent = 'OK';
        btnConfirm.className = `btn modal-btn-confirm ${cfg.btnClass}`;
        currentAction = null;

        overlay.style.display = 'flex';
        void overlay.offsetWidth;
        overlay.classList.add('active');
    }

    window.closeModal = closeModal;
    window.openModal = openModal;
    window.showAlert = showAlert;

    btnClose.addEventListener('click', closeModal);
    btnCancel.addEventListener('click', closeModal);
    
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
    });

    btnConfirm.addEventListener('click', () => {
        if (typeof currentAction === 'function') {
            currentAction();
        } else if (currentAction instanceof HTMLFormElement) {
            currentAction.submit();
        } else if (typeof currentAction === 'string') {
            window.location.href = currentAction;
        }
        closeModal();
    });

    // Intercept clicks on data-modal attributes
    document.addEventListener('click', (e) => {
        const trigger = e.target.closest('[data-modal-confirm]');
        if (trigger) {
            e.preventDefault();
            const message = trigger.getAttribute('data-modal-message') || 'Tem a certeza que deseja prosseguir?';
            const title = trigger.getAttribute('data-modal-title') || 'Confirmar Ação';
            const type = trigger.getAttribute('data-modal-type') || 'btn-primary'; // e.g. btn-danger
            const confirmText = trigger.getAttribute('data-modal-btn-text') || 'Confirmar';

            let action;
            if (trigger.tagName === 'A') {
                action = trigger.href;
            } else if (trigger.tagName === 'BUTTON' && trigger.type === 'submit') {
                action = trigger.closest('form');
            }

            openModal(title, message, confirmText, type, action);
        }
    });
});
