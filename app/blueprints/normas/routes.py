# Rotas de Normas — verificação ABNT/APA + IMETRO 2014 (local + IA)
import os
import uuid
from flask import render_template, request, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from app.blueprints.normas import normas_bp
from core.auth_helpers import requer_verificador


@normas_bp.route('/verificar', methods=['GET', 'POST'])
@requer_verificador
def verificar():
    resultado = None
    if request.method == 'POST':
        ficheiro = request.files.get('ficheiro')
        if not ficheiro or not ficheiro.filename:
            flash('Seleccione um ficheiro.', 'erro')
            return redirect(url_for('normas.verificar'))

        ext = ficheiro.filename.rsplit('.', 1)[1].lower() if '.' in ficheiro.filename else ''
        if ext not in ('pdf', 'docx', 'txt'):
            flash('Formato não suportado.', 'erro')
            return redirect(url_for('normas.verificar'))

        nome_seg = f'{uuid.uuid4().hex[:16]}.{ext}'
        caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_seg)
        ficheiro.save(caminho)

        try:
            from core.ingestor import extrair
            from core.abnt_checker import verificar_abnt, verificar_apa
            texto = extrair(caminho)
            
            resultado_abnt = verificar_abnt(texto)
            resultado_apa = verificar_apa(texto)
            
            resultado = {
                'nome_ficheiro': ficheiro.filename,
                'abnt': resultado_abnt,
                'apa': resultado_apa
            }
        except Exception as e:
            flash(f'Erro na verificação: {e}', 'erro')

    return render_template('normas/verificar.html', resultado=resultado)


@normas_bp.route('/verificar-imetro', methods=['GET', 'POST'])
@requer_verificador
def verificar_imetro():
    """Verificação de normas IMETRO 2014 — local (regex) + IA (opcional)."""
    resultado = None

    if request.method == 'POST':
        ficheiro = request.files.get('ficheiro')
        if not ficheiro or not ficheiro.filename:
            flash('Seleccione um ficheiro TFC para análise.', 'erro')
            return redirect(url_for('normas.verificar_imetro'))

        ext = ficheiro.filename.rsplit('.', 1)[1].lower() if '.' in ficheiro.filename else ''
        if ext not in ('pdf', 'docx', 'txt'):
            flash('Formato não suportado. Envie PDF, DOCX ou TXT.', 'erro')
            return redirect(url_for('normas.verificar_imetro'))

        nome_seg = f'{uuid.uuid4().hex[:16]}.{ext}'
        caminho = os.path.join(current_app.config['UPLOAD_FOLDER'], nome_seg)
        ficheiro.save(caminho)

        # Metadados do formulário
        titulo = request.form.get('titulo', 'Não informado').strip()
        autores = request.form.get('autores', 'Não informado').strip()
        curso = request.form.get('curso', 'Não informado').strip()
        orientador = request.form.get('orientador', 'Não informado').strip()
        ano = request.form.get('ano', 'Não informado').strip()
        usar_ia = request.form.get('usar_ia') == '1'

        try:
            from core.ingestor import extrair
            from core.abnt_checker import verificar_imetro as verificar_imetro_local
            
            texto = extrair(caminho)
            num_paginas = max(1, len(texto) // 2500)

            # ── Verificação LOCAL (sempre disponível) ──
            resultado_local = verificar_imetro_local(texto)
            resultado_local['nome_ficheiro'] = ficheiro.filename

            resultado = {
                'nome_ficheiro': ficheiro.filename,
                'local': resultado_local,
                'ia': None,
                'titulo': titulo,
                'autores': autores,
                'curso': curso,
                'num_paginas': num_paginas,
            }

            # ── Verificação via IA (opcional) ──
            if usar_ia:
                try:
                    from core.normas_imetro_checker import verificar_normas_imetro, get_llm_config
                    config_db = get_llm_config(current_app.config['DB_PATH'])
                    
                    resultado_ia = verificar_normas_imetro(
                        texto_extraido=texto,
                        titulo=titulo,
                        autores=autores,
                        curso=curso,
                        orientador=orientador,
                        ano=ano,
                        num_paginas=num_paginas,
                        formato_ficheiro=ext.upper(),
                        config_db=config_db,
                    )
                    resultado['ia'] = resultado_ia

                    if resultado_ia.get('erro'):
                        flash(f'IA: {resultado_ia["erro"]}', 'aviso')
                except Exception as e:
                    flash(f'Erro na análise por IA: {e}', 'aviso')

        except Exception as e:
            flash(f'Erro na verificação IMETRO: {e}', 'erro')

    return render_template('normas/verificar_imetro.html', resultado=resultado)


@normas_bp.route('/referencia')
@requer_verificador
def referencia():
    return render_template('normas/referencia.html')
