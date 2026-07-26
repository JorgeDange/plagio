# IMETRO TFC v3 — Modelo de Utilizador (MySQL)

from flask_login import UserMixin
from flask_bcrypt import check_password_hash
from app.database.db import get_db


class Utilizador(UserMixin):
    PAPEIS_VALIDOS = ('administrador', 'carregador', 'verificador', 'aprovador')

    def __init__(self, id, nome, email, password_hash, papel, ativo=1,
                 criado_em=None, ultimo_login=None):
        self.id = id
        self.nome = nome
        self.email = email
        self.password_hash = password_hash
        self.papel = papel
        self.ativo = ativo
        self.criado_em = criado_em
        self.ultimo_login = ultimo_login

    @property
    def is_active(self):
        return self.ativo == 1

    @property
    def is_admin(self):
        return self.papel == 'administrador'

    @property
    def is_carregador(self):
        return self.papel == 'carregador'

    @property
    def is_verificador(self):
        return self.papel == 'verificador'

    @property
    def is_aprovador(self):
        return self.papel == 'aprovador'

    @classmethod
    def carregar_por_id(cls, user_id):
        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT * FROM utilizadores WHERE id = %s', (user_id,))
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()
        cur.close()
        if row:
            return cls._from_row(dict(zip(cols, row)))
        return None

    @classmethod
    def carregar_por_email(cls, email):
        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT * FROM utilizadores WHERE email = %s', (email,))
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()
        cur.close()
        if row:
            return cls._from_row(dict(zip(cols, row)))
        return None

    @classmethod
    def _from_row(cls, row):
        return cls(
            id=row['id'],
            nome=row['nome'],
            email=row['email'],
            password_hash=row['password_hash'],
            papel=row['papel'],
            ativo=row['ativo'],
            criado_em=row.get('criado_em'),
            ultimo_login=row.get('ultimo_login')
        )

    def verificar_password(self, password):
        try:
            return check_password_hash(self.password_hash, password)
        except (ValueError, TypeError):
            return False

    def __repr__(self):
        return f'<Utilizador {self.email} ({self.papel})>'
