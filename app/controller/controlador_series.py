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
from app.model.modelo_usuarios import PerfilModel

# Blueprint principal — todas las rutas de series quedan agrupadas aquí
series_bp = Blueprint("series", __name__)

# Instancias del modelo y la vista de series
modelo = SerieModel()
modelo_usuario = UsuarioModel()
modelo_perfil = PerfilModel()
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

        nombre_usuario = session.get("nombre_usuario")
        print("NOMBRE USUARIO:", nombre_usuario)
        print("SERIE ID:", serie_id, type(serie_id))

        estados = {"matchlist": False, "favoritos": False, "series_vistas": False}
        if nombre_usuario:
            for lista in estados:
                resultado = modelo_perfil.esta_en_lista(
                    nombre_usuario, lista, serie_id, "tv"
                )
                estados[lista] = resultado
        print("ESTADOS FINALES:", estados)
        return vista.render_modal_serie(
            serie=serie,
            credits=credits,
            keywords=keywords,
            providers=providers,
            clasificacion=clasificacion,
            estados=estados,
            trailer=trailer,
        )
    except Exception as e:
        return str(e), 500
