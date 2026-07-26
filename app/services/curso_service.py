# Sistema de Detecção de Plágio — Serviço de Cursos

from app.database import db

def listar_cursos_admin() -> list[dict]:
    """Retorna todos os cursos como dicionários."""
    rows = db.listar_cursos_admin()
    return [dict(row) for row in rows]

def buscar_curso(id: int) -> dict | None:
    row = db.buscar_curso(id)
    return dict(row) if row else None

def buscar_curso_por_nome(nome: str) -> dict | None:
    row = db.buscar_curso_por_nome(nome)
    return dict(row) if row else None

def criar_curso(nome: str, codigo: str = None, departamento: str = None, descricao: str = None, activo: int = 1) -> dict:
    # Verifica duplicado
    if buscar_curso_por_nome(nome):
        return {'sucesso': False, 'erro': 'Já existe um curso com este nome.'}
    
    try:
        curso_id = db.inserir_curso(nome, codigo, departamento, descricao, activo)
        return {'sucesso': True, 'id': curso_id}
    except Exception as e:
        return {'sucesso': False, 'erro': str(e)}

def editar_curso(id: int, nome: str, codigo: str = None, departamento: str = None, descricao: str = None, activo: int = 1) -> dict:
    # Verifica duplicado de outro curso
    existente = buscar_curso_por_nome(nome)
    if existente and existente['id'] != id:
        return {'sucesso': False, 'erro': 'Já existe um curso com este nome.'}
    
    try:
        db.editar_curso(id, nome, codigo, departamento, descricao, activo)
        return {'sucesso': True}
    except Exception as e:
        return {'sucesso': False, 'erro': str(e)}

def remover_curso(id: int) -> dict:
    try:
        sucesso = db.remover_curso(id)
        if sucesso:
            return {'sucesso': True}
        else:
            return {'sucesso': False, 'erro': 'Existem monografias associadas a este curso. Arquive-o em vez de remover.'}
    except Exception as e:
        return {'sucesso': False, 'erro': str(e)}
