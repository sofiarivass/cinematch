from flask import Flask, app
from config.config import Config
from app.extensions import cache
from app.controller.controlador import cinematch_bp
from app.controller.controlador_peliculas import peliculas_bp
from app.controller.controlador_series import series_bp
from app.controller.controlador_rec import recomendaciones_bp
from app.controller.controlador_matchlist import matchlist_bp
from app.controller.controlador_usuarios import usuarios_bp, perfil_bp

from app.services.google_oauth import init_oauth


def create_app() -> Flask:

    app = Flask(
        __name__,
        template_folder="app/templates",
        static_folder="app/static",
    )

    # Cargar configuración
    app.config.from_object(Config)

    cache.init_app(app)

    # Inicializar OAuth
    init_oauth(app)

    # Registrar blueprints
    app.register_blueprint(cinematch_bp)
    app.register_blueprint(peliculas_bp)
    app.register_blueprint(series_bp)
    app.register_blueprint(recomendaciones_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(perfil_bp)
    app.register_blueprint(matchlist_bp)

    return app


# ← ESTO ES LO NUEVO
app = create_app()


if __name__ == "__main__":
    app.run(
        debug=Config.DEBUG,
        host="0.0.0.0",
        port=5000,
    )
