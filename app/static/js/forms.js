document.addEventListener('DOMContentLoaded', function() {
    
    // Comportamento 1: Contador de caracteres
    const textareas = document.querySelectorAll('textarea[maxlength]');
    textareas.forEach(ta => {
        const counterId = ta.id + '-counter';
        const counter = document.getElementById(counterId);
        if (counter) {
            const max = parseInt(ta.getAttribute('maxlength'));
            
            const updateCounter = () => {
                const len = ta.value.length;
                counter.textContent = `${len} / ${max}`;
                
                if (len >= max) {
                    counter.classList.add('over-limit');
                    counter.style.color = '#e53e3e'; // vermelho
                } else if (len >= max * 0.9) {
                    counter.classList.remove('over-limit');
                    counter.style.color = '#f59e0b'; // ambar
                } else {
                    counter.classList.remove('over-limit');
                    counter.style.color = 'var(--text-muted, #9ca3af)';
                }
            };
            
            ta.addEventListener('input', updateCounter);
            updateCounter(); // init
        }
    });

    // Comportamento 2: Drag and drop na área de upload
    const uploadAreas = document.querySelectorAll('.form-upload-area');
    uploadAreas.forEach(area => {
        area.addEventListener('dragover', e => {
            e.preventDefault();
            area.classList.add('dragover');
        });
        area.addEventListener('dragleave', e => {
            e.preventDefault();
            area.classList.remove('dragover');
        });
        area.addEventListener('drop', e => {
            e.preventDefault();
            area.classList.remove('dragover');
            
            const fileInputId = area.getAttribute('for');
            const fileInput = document.getElementById(fileInputId);
            const spanNome = document.getElementById(fileInputId + '-nome');
            
            if (fileInput && e.dataTransfer.files.length > 0) {
                fileInput.files = e.dataTransfer.files;
                if (spanNome) {
                    spanNome.textContent = fileInput.files[0].name;
                }
            }
        });
    });

    // Comportamento 3: Mostrar nome do ficheiro apos seleccao
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', e => {
            const spanNome = document.getElementById(input.id + '-nome');
            if (spanNome && input.files.length > 0) {
                spanNome.textContent = input.files[0].name;
            }
        });
    });

    // Comportamento 4: Validação visual em tempo real
    const requiredInputs = document.querySelectorAll('.form-control[required]');
    requiredInputs.forEach(input => {
        input.addEventListener('blur', () => {
            if (!input.value.trim()) {
                input.classList.add('is-invalid');
                input.classList.remove('is-valid');
            } else {
                input.classList.remove('is-invalid');
                input.classList.add('is-valid');
            }
        });
    });

    // Comportamento 5: Desactivar botao submit enquanto envia
    const asyncForms = document.querySelectorAll('form.form-async');
    asyncForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Nao fazemos evt.preventDefault(), apenas desativamos o botao
            const btn = form.querySelector('button[type="submit"]');
            if (btn) {
                // Pequeno atraso para garantir que o envio acontece
                setTimeout(() => {
                    btn.disabled = true;
                    const origHtml = btn.innerHTML;
                    btn.dataset.originalText = origHtml;
                    btn.innerHTML = "<i class='ti ti-loader-2' style='animation: spin 1s linear infinite;'></i> A processar...";
                }, 10);
            }
        });
    });

    // Comportamento 6: Toggle switch (se for construído manualmente)
    // Opcional: na estrutura .form-toggle o css + label for já faz o trabalho, mas podemos
    // adicionar feedback caso precise
});
