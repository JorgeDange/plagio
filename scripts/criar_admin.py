#!/usr/bin/env python3
"""
IMETRO TFC v3 — Script para criar/actualizar o administrador.

Uso:
    python scripts/criar_admin.py

Lê email e password do terminal e insere/actualiza o administrador na base de dados.
"""
import os
import sys
import getpass

basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, basedir)

try:
    from flask_bcrypt import generate_password_hash
except ImportError:
    print('Erro: flask-bcrypt não instalado.')
    print('Execute: pip install flask-bcrypt')
    sys.exit(1)


def main():
    from app.database.db import get_db

    print('╔══════════════════════════════════════════╗')
    print('║   IMETRO TFC v3 — Criar Administrador   ║')
    print('╚══════════════════════════════════════════╝')
    print()

    nome = input('Nome completo [Administrador]: ').strip() or 'Administrador'
    email = input('Email [admin@imetro.ao]: ').strip() or 'admin@imetro.ao'

    while True:
        password = getpass.getpass('Password (mín. 8 caracteres): ')
        if len(password) < 8:
            print('Erro: Password deve ter pelo menos 8 caracteres.')
            continue
        password_confirm = getpass.getpass('Confirmar password: ')
        if password != password_confirm:
            print('Erro: As passwords não coincidem.')
            continue
        break

    password_hash = generate_password_hash(password).decode('utf-8')

    conn = get_db()
    c = conn.cursor()

    c.execute('SELECT id FROM utilizadores WHERE email = %s', (email,))
    existente = c.fetchone()

    if existente:
        c.execute(
            'UPDATE utilizadores SET nome = %s, password_hash = %s, papel = %s, ativo = 1 WHERE email = %s',
            (nome, password_hash, 'administrador', email)
        )
        print(f'\nAdministrador actualizado com sucesso!')
    else:
        c.execute(
            'INSERT INTO utilizadores (nome, email, password_hash, papel) VALUES (%s, %s, %s, %s)',
            (nome, email, password_hash, 'administrador')
        )
        print(f'\nAdministrador criado com sucesso!')

    conn.commit()
    c.close()

    print(f'   Email: {email}')
    print(f'   Papel: administrador')
    print()


if __name__ == '__main__':
    main()
