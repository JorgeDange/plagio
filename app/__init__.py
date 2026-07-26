# IMETRO TFC v3 — Application Factory (MySQL)
import os
import sys
import json
from flask import Flask
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from dotenv import load_dotenv

login_manager = LoginManager()
bcrypt = Bcrypt()


def create_app() -> Flask:
    app = Flask(__name__, instance_relative_config=True,
                static_folder='static', template_folder='templates')

    basedir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    instance_dir = os.path.join(basedir, 'instance')

    dotenv_path = os.path.join(basedir, '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path)
    elif os.path.exists(os.path.join(basedir, '.env.example')):
        load_dotenv(os.path.join(basedir, '.env.example'))

    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'chave-dev-insegura')
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
    app.config['UPLOAD_FOLDER'] = os.path.join(basedir, 'uploads')
    app.config['RELATORIOS_FOLDER'] = os.path.join(basedir, 'relatorios')

    app.config['LIMIAR_PLAGIO'] = float(os.environ.get('LIMIAR_PLAGIO', '0.85'))
    app.config['CHUNK_SIZE'] = int(os.environ.get('CHUNK_SIZE', '200'))
    app.config['CHUNK_OVERLAP'] = int(os.environ.get('CHUNK_OVERLAP', '50'))

    config_json = os.path.join(instance_dir, 'config.json')
    if os.path.exists(config_json):
        try:
            with open(config_json, 'r', encoding='utf-8') as f:
                app.config.update(json.load(f))
        except (json.JSONDecodeError, IOError):
            pass

    for p in [app.config['UPLOAD_FOLDER'], app.config['RELATORIOS_FOLDER'], instance_dir]:
        os.makedirs(p, exist_ok=True)

    core_dir = os.path.join(basedir, 'core')
    if core_dir not in sys.path:
        sys.path.insert(0, core_dir)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para continuar.'
    login_manager.login_message_category = 'erro'

    @login_manager.user_loader
    def load_user(user_id):
        from core.models.utilizador import Utilizador
        return Utilizador.carregar_por_id(int(user_id))

    bcrypt.init_app(app)

    @app.context_processor
    def inject_user():
        from flask_login import current_user
        return dict(current_user=current_user)

    from app.database.db import init_db, get_db
    init_db()

    _load_llm_config(app)

    app.config['MODELO'] = None
    print('[Flask] Embeddings via OpenRouter API (qwen3-embedding-8b).')

    from app.blueprints.main import main_bp
    from app.blueprints.cursos import cursos_bp
    from app.blueprints.orientadores import orientadores_bp
    from app.blueprints.tcc_validos import tcc_validos_bp
    from app.blueprints.tcc_suspeitos import tcc_suspeitos_bp
    from app.blueprints.verificacoes import verificacoes_bp
    from app.blueprints.normas import normas_bp
    from app.blueprints.api import api_bp
    from app.blueprints.configuracoes import config_bp
    from app.blueprints.analise_ia import analise_ia_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(cursos_bp)
    app.register_blueprint(orientadores_bp)
    app.register_blueprint(tcc_validos_bp)
    app.register_blueprint(tcc_suspeitos_bp)
    app.register_blueprint(verificacoes_bp, url_prefix='/verificacoes')
    app.register_blueprint(normas_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(config_bp)
    app.register_blueprint(analise_ia_bp)

    from app.blueprints.auth import auth_bp
    from app.blueprints.utilizadores import utilizadores_bp
    from app.blueprints.aprovacoes import aprovacoes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(utilizadores_bp)
    app.register_blueprint(aprovacoes_bp)

    from app.blueprints.pesquisa_individual import pesquisa_individual_bp
    app.register_blueprint(pesquisa_individual_bp)

    from app.database.db import close_db
    app.teardown_appcontext(close_db)

    if not os.path.exists(config_json):
        try:
            with open(config_json, 'w', encoding='utf-8') as f:
                json.dump({
                    'LIMIAR_PLAGIO': app.config['LIMIAR_PLAGIO'],
                    'CHUNK_SIZE': app.config['CHUNK_SIZE'],
                    'CHUNK_OVERLAP': app.config['CHUNK_OVERLAP']
                }, f, indent=2, ensure_ascii=False)
        except IOError:
            pass

    print('[Flask] IMETRO TFC v3 pronto em http://0.0.0.0:5000')
    return app


def _load_llm_config(app: Flask) -> None:
    try:
        with app.app_context():
            from app.database.db import get_db
            db = get_db()
            cur = db.cursor()
            cur.execute("SELECT chave, valor FROM configuracoes WHERE chave LIKE 'LLM_%%' OR chave = 'OLLAMA_URL'")
            for r in cur.fetchall():
                app.config[r[0]] = r[1]
            cur.execute("SELECT COUNT(*) FROM configuracoes WHERE chave LIKE 'LLM_%%' OR chave = 'OLLAMA_URL'")
            count = cur.fetchone()[0]
            if count:
                print(f'[Flask] Configuracoes IA carregadas: {count} chave(s)')
    except Exception as e:
        print(f'[Flask] Aviso ao carregar config IA: {e}')
