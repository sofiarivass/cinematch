"""
main.py
───────
Punto de entrada de la aplicación.

Uso:
    python main.py
"""

from flask import Flask
from config.config import Config

from app.controller.controlador import cinematch_bp
from app.controller.controlador_peliculas import peliculas_bp
from app.controller.controlador_series import series_bp
from app.controller.controlador_rec import recomendaciones_bp
from app.controller.controlador_usuarios import usuarios_bp

from app.services.google_oauth import init_oauth

def create_app() -> Flask:
    """
    Crea y configura la instancia de Flask.

    Returns:
        Flask: Aplicación lista para correr.
    """
    app = Flask(
        __name__,
        template_folder="app/templates",  # Jinja2 buscará los templates aquí
        static_folder="app/static",       # Archivos estáticos (CSS, JS, img)
    )

    # Cargar configuración desde config/config.py
    app.config.from_object(Config)

    init_oauth(app)

    # Registrar blueprints del controlador
    app.register_blueprint(cinematch_bp)
    app.register_blueprint(peliculas_bp)
    app.register_blueprint(series_bp)
    app.register_blueprint(recomendaciones_bp)
    app.register_blueprint(usuarios_bp)

    return app


# ── Inicio ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(
        debug=Config.DEBUG,
        host="0.0.0.0",
        port=5000,
    )
