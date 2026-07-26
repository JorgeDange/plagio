/**
 * Sistema de Detecção de Plágio — JavaScript Principal
 * Funções: filtro de tabela, progresso de jobs, confirmação de remoção, sidebar mobile.
 * Vanilla JS puro, sem dependências.
 */

/* ══════════════════════════════════════
   1. FILTRO DE TABELA EM TEMPO REAL
   ══════════════════════════════════════ */

/**
 * Filtra as linhas de uma tabela com base no texto digitado.
 * @param {string} inputId  — ID do campo de pesquisa
 * @param {string} tableId  — ID da tabela a filtrar
 */
function filtroTabela(inputId, tableId) {
    const input = document.getElementById(inputId);
    const tabela = document.getElementById(tableId);
    if (!input || !tabela) return;

    const filtro = input.value.toLowerCase().trim();
    const linhas = tabela.querySelectorAll('tbody tr');

    linhas.forEach(linha => {
        const texto = linha.textContent.toLowerCase();
        linha.style.display = texto.includes(filtro) ? '' : 'none';
    });
}


/* ══════════════════════════════════════
   2. POLLING DE PROGRESSO
   ══════════════════════════════════════ */

/**
 * Faz polling ao endpoint /api/progresso/<jobId> em intervalos regulares.
 * Actualiza a barra de progresso visualmente.
 * Pára quando status === 'concluido'.
 *
 * @param {string} jobId     — Identificador único do job
 * @param {string} barraId   — ID do elemento da barra de preenchimento
 * @param {number} intervalo — Milissegundos entre cada polling (padrão: 1500)
 */
function iniciarProgresso(jobId, barraId, intervalo) {
    intervalo = intervalo || 1500;

    const barra = document.getElementById(barraId);
    const textoEl = document.getElementById('progressTexto');
    const contagemEl = document.getElementById('progressContagem');
    const statusEl = document.getElementById('progressStatus');
    const resultadosEl = document.getElementById('progressResultados');

    if (!barra) return;

    const timer = setInterval(function () {
        fetch('/api/progresso/' + jobId)
            .then(function (res) { return res.json(); })
            .then(function (data) {
                // Actualizar barra
                var pct = 0;
                if (data.total && data.total > 0) {
                    pct = Math.round((data.progresso / data.total) * 100);
                }
                barra.style.width = pct + '%';

                // Actualizar texto
                if (contagemEl) {
                    contagemEl.textContent = data.progresso + ' / ' + data.total;
                }
                if (textoEl) {
                    textoEl.textContent = data.status === 'concluido'
                        ? 'Processamento concluído!'
                        : 'A processar ficheiro ' + (data.progresso + 1) + '...';
                }

                // Verificar conclusão
                if (data.status === 'concluido') {
                    clearInterval(timer);
                    barra.style.width = '100%';
                    barra.classList.remove('pct-bar-moderado');
                    barra.classList.add('pct-bar-baixo');

                    if (statusEl) {
                        statusEl.textContent = 'Concluído';
                        statusEl.className = 'badge badge-baixo';
                    }

                    // Mostrar resultados individuais
                    if (resultadosEl && data.resultados && data.resultados.length > 0) {
                        resultadosEl.style.display = 'block';
                        var html = '<div style="margin-top:0.5rem;">';
                        data.resultados.forEach(function (r) {
                            if (r.erro) {
                                html += '<div class="flash flash-erro" style="margin-bottom:0.35rem;">'
                                    + '<span class="flash-icon">✕</span>'
                                    + '<span>' + r.ficheiro + ': ' + r.erro + '</span></div>';
                            } else {
                                var badgeClass = r.nivel === 'Baixo' ? 'baixo' : (r.nivel === 'Moderado' ? 'moderado' : 'alto');
                                html += '<div class="flash flash-info" style="margin-bottom:0.35rem;">'
                                    + '<span>' + r.ficheiro + ': ' + r.pct + '% '
                                    + '<span class="badge badge-' + badgeClass + '">' + r.nivel + '</span></span>'
                                    + ' <a href="/verificar/resultado/' + r.id + '" class="btn btn-sm btn-ghost">Ver</a>'
                                    + '</div>';
                            }
                        });
                        html += '</div>';
                        resultadosEl.innerHTML = html;
                    }

                    // Redirigir se só há 1 resultado
                    if (data.resultados && data.resultados.length === 1 && data.ultimo_id) {
                        setTimeout(function () {
                            window.location.href = '/verificar/resultado/' + data.ultimo_id;
                        }, 2000);
                    }
                }
            })
            .catch(function (err) {
                console.error('Erro no polling:', err);
            });
    }, intervalo);
}


/* ══════════════════════════════════════
   3. CONFIRMAÇÃO DE REMOÇÃO
   ══════════════════════════════════════ */

/**
 * Exibe um diálogo de confirmação antes de submeter um formulário de remoção.
 * @param {string} mensagem — Texto a exibir no diálogo
 * @returns {boolean} — true se confirmado, false caso contrário
 */
function confirmarRemocao(mensagem) {
    if (typeof openModal === 'function') {
        return new Promise(function(resolve) {
            openModal('Confirmar', mensagem || 'Tem certeza que deseja remover este item?', 'Remover', 'btn-danger', function() {
                resolve(true);
            });
        });
    }
    return window.confirm(mensagem || 'Tem certeza que deseja remover este item?');
}


/* ══════════════════════════════════════
   4. SIDEBAR MOBILE TOGGLE
   ══════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', function () {
    var toggleBtn = document.getElementById('sidebarToggle');
    var sidebar = document.getElementById('sidebar');

    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener('click', function () {
            sidebar.classList.toggle('open');
        });

        // Fechar sidebar ao clicar fora
        document.addEventListener('click', function (e) {
            if (sidebar.classList.contains('open') &&
                !sidebar.contains(e.target) &&
                !toggleBtn.contains(e.target)) {
                sidebar.classList.remove('open');
            }
        });
    }

    // ── Verificar estado do sistema (indicador no sidebar) ──
    var statusDot = document.getElementById('statusDot');
    var statusTexto = document.getElementById('statusTexto');

    if (statusDot) {
        fetch('/api/status')
            .then(function (res) { return res.json(); })
            .then(function (data) {
                if (data.modelo_ok && data.chroma_ok) {
                    statusDot.classList.add('online');
                    statusTexto.textContent = 'Sistema operacional';
                } else {
                    statusDot.classList.add('offline');
                    statusTexto.textContent = 'Sistema com problemas';
                }
            })
            .catch(function () {
                statusDot.classList.add('offline');
                statusTexto.textContent = 'Sem ligação';
            });
    }

    // ── Auto-remover flash messages após 8 segundos ──
    var flashes = document.querySelectorAll('.flash');
    flashes.forEach(function (flash) {
        setTimeout(function () {
            flash.style.opacity = '0';
            flash.style.transform = 'translateY(-8px)';
            flash.style.transition = 'all 0.3s ease';
            setTimeout(function () { flash.remove(); }, 300);
        }, 8000);
    });
});
