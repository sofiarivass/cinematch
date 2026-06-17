"""
app/controller/controlador_rec.py
──────────────────────────────
Capa de Controlador (C en MVC).

Responsabilidades:
  - Definir las rutas (URLs) de la aplicación.
  - Recibir los requests del usuario.
  - Llamar al Modelo para obtener los datos.
  - Pasar los datos a la Vista para renderizar.
"""

from flask import Blueprint, request, redirect, url_for, session, flash
from app.model.modelo_rec import RecomendacionesModel
from app.views.vista_rec import RecomendacionesView
from app.model.modelo_peliculas import PeliculaModel
from app.views.vista_peliculas import PeliculaView
from app.model.modelo_usuarios import UsuarioModel

# Blueprint principal — todas las rutas quedan agrupadas aquí
recomendaciones_bp = Blueprint("recomendaciones", __name__)

# Instancias del modelo y la vista
modelo = RecomendacionesModel()
modelo_pelicula = PeliculaModel()
vista_pelicula = PeliculaView()
modelo_usuario = UsuarioModel()
vista = RecomendacionesView()


# SESIÓN DE USUARIO Y RUTA DE ENCUESTA
@recomendaciones_bp.route("/encuesta-recomendaciones", methods=["GET", "POST"])
def encuesta_recomendaciones():
    if request.method == "POST":
        paso = int(request.form.get("paso", 0))
        error = False  # 🟢 Bandera para controlar si hay error

        # Guardar respuesta del paso actual en session
        if paso == 1:
            formato = request.form.get("formato")
            if not formato:
                error = True
            else:
                session["formato"] = formato

        elif paso == 2:
            tiempo = request.form.get("tiempo")
            if not tiempo:
                error = True
            else:
                session["tiempo"] = tiempo

        elif paso == 3:
            emociones = request.form.getlist("emociones")
            if not emociones:
                error = True
            else:
                session["emociones"] = emociones

        elif paso == 4:
            epoca = request.form.get("epoca")
            if not epoca:
                error = True
            else:
                session["epoca"] = epoca

        elif paso == 5:
            clasificacion = request.form.get("clasificacion")
            if not clasificacion:
                error = True
            else:
                session["clasificacion"] = clasificacion

                # 🟢 ENCUESTA FINALIZADA: Armamos el objeto JSON estructurado
                preferencias_finales = {
                    "formato": session.get("formato", ""),
                    "tiempo": session.get("tiempo", ""),
                    "emociones": session.get("emociones", []),
                    "epoca": session.get("epoca", ""),
                    "clasificacion": session.get("clasificacion", ""),
                }

                # Acá iría la lógica para guardar en la BD si hace falta
                return redirect(url_for("cinematch.index"))

        # 🟢 Evaluamos si avanzamos o nos quedamos mostrando el error
        if error:
            flash("Por favor, seleccioná al menos una opción para continuar.", "danger")
            siguiente_paso = paso
        else:
            siguiente_paso = paso + 1

    else:
        siguiente_paso = request.args.get("paso", 0, type=int)

    return vista.render_encuesta_rec(
        paso=siguiente_paso,
    )


# RUTA RECOMENDACIONES PELICULA
@recomendaciones_bp.route("/rec-pelicula/<int:pelicula_id>")
def recomendacion(pelicula_id: int):
    try:
        pelicula = modelo_pelicula.obtener_detalle(pelicula_id)
        credits = modelo_pelicula.obtener_credits(pelicula_id)
        keywords = modelo_pelicula.obtener_keywords(pelicula_id)
        providers = modelo_pelicula.obtener_providers(pelicula_id)
        clasificacion = modelo_pelicula.obtener_clasificacion(pelicula_id)

        return vista.render_recomendaciones(
            pelicula, credits, keywords, providers, clasificacion
        )

    except Exception as e:
        return vista.render_error(str(e))
