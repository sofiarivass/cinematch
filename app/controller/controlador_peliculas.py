"""
app/controller/controlador_peliculas.py
──────────────────────────────
Capa de Controlador (C en MVC).

Responsabilidades:
  - Definir las rutas (URLs) de la aplicación.
  - Recibir los requests del usuario.
  - Llamar al Modelo para obtener los datos.
  - Pasar los datos a la Vista para renderizar.
"""

from flask import Blueprint, jsonify, request, redirect, url_for, session
from app.model.modelo_peliculas import PeliculaModel
from app.views.vista_peliculas import PeliculaView
from app.model.modelo_usuarios import UsuarioModel
from app.model.modelo_usuarios import PerfilModel

# Blueprint principal — todas las rutas quedan agrupadas aquí
peliculas_bp = Blueprint("peliculas", __name__)

# Instancias del modelo y la vista
modelo = PeliculaModel()
modelo_usuario = UsuarioModel()
modelo_perfil = PerfilModel()
vista = PeliculaView()


# RUTA CONTENIDO MODAL DETALLE PELIS
@peliculas_bp.route("/pelicula/<int:pelicula_id>/modal")
def modal_pelicula(pelicula_id: int):
    try:
        pelicula = modelo.obtener_detalle(pelicula_id)
        credits = modelo.obtener_credits(pelicula_id)
        keywords = modelo.obtener_keywords(pelicula_id)
        providers = modelo.obtener_providers(pelicula_id)
        clasificacion = modelo.obtener_clasificacion(pelicula_id)
        trailer = modelo.obtener_trailer(pelicula_id)

        nombre_usuario = session.get("nombre_usuario")
        print("NOMBRE USUARIO:", nombre_usuario)
        print("PELICULA ID:", pelicula_id, type(pelicula_id))

        estados = {"matchlist": False, "favoritos": False, "peliculas_vistas": False}
        if nombre_usuario:
            for lista in estados:
                resultado = modelo_perfil.esta_en_lista(
                    nombre_usuario, lista, pelicula_id, "movie"
                )
                estados[lista] = resultado
        print("ESTADOS FINALES:", estados)
        return vista.render_modal_pelicula(
            pelicula=pelicula,
            credits=credits,
            keywords=keywords,
            providers=providers,
            clasificacion=clasificacion,
            estados=estados,
            trailer=trailer,
        )
    except Exception as e:
        return str(e), 500
