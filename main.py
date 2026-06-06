"""
main.py
───────
Punto de entrada de la aplicación.

Uso:
    python main.py
"""

from flask import Flask
from config.config import Config
from app.controller.controlador_peliculas import peliculas_bp


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

    # Registrar blueprint del controlador
    app.register_blueprint(peliculas_bp)

    return app


# ── Inicio ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = create_app()
    app.run(
        debug=Config.DEBUG,
        host="0.0.0.0",
        port=5000,
    )
