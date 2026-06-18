"""
app/controller/controlador_series.py
──────────────────────────────
Capa de Controlador (C en MVC).

Responsabilidades:
  - Definir las rutas (URLs) de la aplicación.
  - Recibir los requests del usuario.
  - Llamar al Modelo para obtener los datos.
  - Pasar los datos a la Vista para renderizar.
"""

from flask import Blueprint, request, redirect, url_for, session
from app.model.modelo_series import SerieModel
from app.views.vista_series import SerieView
from app.model.modelo_usuarios import UsuarioModel

# Blueprint principal — todas las rutas de series quedan agrupadas aquí
series_bp = Blueprint("series", __name__)

# Instancias del modelo y la vista de series
modelo = SerieModel()
modelo_usuario = UsuarioModel()
vista = SerieView()


# RUTA CONTENIDO MODAL DETALLE SERIES
@series_bp.route("/serie/<int:serie_id>/modal")
def modal_serie(serie_id: int):
    try:
        # Llama al modelo de series para recolectar la data necesaria
        serie = modelo.obtener_detalle(serie_id)
        credits = modelo.obtener_credits(serie_id)
        keywords = modelo.obtener_keywords(serie_id)
        providers = modelo.obtener_providers(serie_id)
        clasificacion = modelo.obtener_clasificacion(serie_id)
        trailer = modelo.obtener_trailer(serie_id)

        credits["creadores"] = serie.get("creadores_raw", [])
        
        # Renderiza usando la vista de series
        return vista.render_modal_serie(serie, credits, keywords, providers, clasificacion, trailer)
    except Exception as e:
        return str(e), 500