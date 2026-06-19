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

from flask import Blueprint, request, redirect, url_for, session, flash, jsonify
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
        error = False

        # Si inicia la encuesta (Paso 0), limpiamos respuestas anteriores para que se sobreescriban
        if paso == 0:
            claves_a_limpiar = [
                "formato",
                "tiempo",
                "emociones",
                "epoca",
                "clasificacion",
                "rec_resultados",
                "rec_matches",
                "rec_ids_vistos",
                "rec_pagina_actual",
            ]
            for clave in claves_a_limpiar:
                session.pop(clave, None)

        elif paso == 1:
            formato = request.form.get("formato")
            if not formato:
                error = True
            else:
                session["formato"] = formato  # Sin el 'rec_' para coincidir con tu HTML

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
                return redirect(url_for("recomendaciones.ver_recomendaciones"))

        if error:
            flash("Por favor, seleccioná al menos una opción para continuar.", "danger")
            siguiente_paso = paso
        else:
            siguiente_paso = paso + 1

    else:
        siguiente_paso = request.args.get("paso", 0, type=int)

    return vista.render_encuesta_rec(paso=siguiente_paso)


@recomendaciones_bp.route("/recomendaciones")
def ver_recomendaciones():
    """Muestra 10 recomendaciones fusionando preferencias de sesión y BD."""
    pagina = request.args.get("pagina", 1, type=int)
    session["rec_pagina_actual"] = pagina

    # 1. Obtenemos las preferencias de la sesión (Encuesta rápida temporal)
    prefs_sesion = {
        "formato": session.get("formato"),
        "tiempo": session.get("tiempo"),
        "emociones": session.get("emociones"),
        "epoca": session.get("epoca"),
        "clasificacion": session.get("clasificacion"),
    }

    # 2. Obtenemos las preferencias de la base de datos (Perfil del usuario)
    prefs_db = {}
    nombre_usuario = session.get("nombre_usuario")

    if nombre_usuario:
        # Extraemos el usuario de la BD usando UsuarioModel
        usuario_db = modelo_usuario.usuarios.find_one(
            {"nombre_usuario": nombre_usuario}
        )
        if usuario_db:
            prefs_db = usuario_db.get("preferencias", {})

    # 3. Fusionamos: Prioridad a la sesión actual -> luego a la BD -> luego valores por defecto
    preferencias = {
        "formato": prefs_sesion.get("formato") or prefs_db.get("formato") or "pelicula",
        "tiempo": prefs_sesion.get("tiempo") or prefs_db.get("tiempo") or "",
        "emociones": prefs_sesion.get("emociones") or prefs_db.get("emociones") or [],
        "epoca": prefs_sesion.get("epoca") or prefs_db.get("epoca") or "todo",
        "clasificacion": prefs_sesion.get("clasificacion")
        or prefs_db.get("clasificacion")
        or "",
        "proveedores": prefs_db.get("plataformas", []),
    }

    # 4. Llamamos al modelo con las preferencias finales construidas
    recomendaciones = modelo.obtener_recomendaciones(preferencias, pagina=pagina)

    # ── Filtrar IDs ya vistos en esta sesión de descubrimiento ──
    ids_vistos = set(session.get("rec_ids_vistos", []))
    recomendaciones_nuevas = [r for r in recomendaciones if r["id"] not in ids_vistos]

    # Si no hay suficientes nuevas (menos de 1), consideramos que se acabó el catálogo filtrado
    if len(recomendaciones_nuevas) < 1:
        flash(
            "Ya viste todo el contenido disponible que coincide con tus filtros. "
            "Probá completar la encuesta de nuevo con otras preferencias.",
            "info",
        )
        return redirect(url_for("recomendaciones.mis_matches_redirect"))

    # Registrar los IDs nuevos que se están mostrando ahora
    ids_vistos.update(r["id"] for r in recomendaciones_nuevas)
    session["rec_ids_vistos"] = list(ids_vistos)

    # Guardamos los objetos completos en la sesión para la ruta /mis-matches
    session["rec_resultados"] = recomendaciones

    return vista.render_recomendaciones(
        recomendaciones=recomendaciones,
        pagina=pagina,
    )


@recomendaciones_bp.route("/mis-matches", methods=["POST"])
def mis_matches():
    """Recibe los objetos de los matches directos del cliente y los renderiza."""
    # Capturamos las listas enviadas por los inputs múltiples del JS
    ids = request.form.getlist("ids")
    tipos = request.form.getlist("tipos")
    titulos = request.form.getlist("titulos")
    posters = request.form.getlist("posters")
    puntuaciones = request.form.getlist("puntuaciones")
    fechas = request.form.getlist("fechas")

    # Reconstruimos la estructura exacta que tu 'mis_matches.html' necesita
    matches = []
    for i in range(len(ids)):
        matches.append(
            {
                "id": ids[i],
                "tipo": tipos[i] if i < len(tipos) else "pelicula",
                "titulo": titulos[i] if i < len(titulos) else "Sin título",
                "poster": posters[i] if i < len(posters) else "",
                "puntuacion": puntuaciones[i] if i < len(puntuaciones) else "0",
                "fecha": fechas[i] if i < len(fechas) else "",
            }
        )

    # Guardamos la lista en sesión
    session["rec_matches"] = matches

    pagina_actual = session.get("rec_pagina_actual", 1)
    pagina_siguiente = pagina_actual + 1

    # Se lo mandamos directo a tu vista/template original
    return vista.render_mis_matches(matches=matches, pagina_siguiente=pagina_siguiente)


@recomendaciones_bp.route("/mis-matches-redirect")
def mis_matches_redirect():
    """Muestra los matches guardados en session cuando se acabó el catálogo filtrado."""
    matches = session.get("rec_matches", [])
    pagina_actual = session.get("rec_pagina_actual", 1)
    return vista.render_mis_matches(matches=matches, pagina_siguiente=pagina_actual + 1)


@recomendaciones_bp.route("/guardar-matches", methods=["POST"])
def guardar_matches():
    """Guarda los matches en la matchlist del usuario y redirige."""
    from app.model.modelo_usuarios import PerfilModel
    from flask import session as sess

    nombre_usuario = session.get("nombre_usuario")
    destino = request.form.get("destino", "index")

    if nombre_usuario:
        modelo_perfil = PerfilModel()
        ids = request.form.getlist("ids")
        tipos = request.form.getlist("tipos")
        titulos = request.form.getlist("titulos")
        posters = request.form.getlist("posters")
        puntuaciones = request.form.getlist("puntuaciones")
        fechas = request.form.getlist("fechas")

        for i, id_ in enumerate(ids):
            item = {
                "id": int(id_),
                "tipo": tipos[i] if i < len(tipos) else "movie",
                "titulo": titulos[i] if i < len(titulos) else "",
                "poster": posters[i] if i < len(posters) else "",
                "puntuacion": float(puntuaciones[i]) if i < len(puntuaciones) else 0,
                "fecha": fechas[i] if i < len(fechas) else "",
                "genero_ids": [],
            }
            modelo_perfil.agregar_a_lista(nombre_usuario, "matchlist", item)

    if destino == "perfil":
        return redirect(url_for("perfil.perfil"))
    return redirect(url_for("cinematch.index"))


@recomendaciones_bp.route("/ya-la-vi", methods=["POST"])
def ya_la_vi():
    nombre_usuario = session.get("nombre_usuario")
    if not nombre_usuario:
        return jsonify({"error": "No logueado"}), 401

    data = request.json
    tipo = data.get("tipo", "pelicula")

    # Determinamos la lista destino
    lista_destino = (
        "peliculas_vistas" if tipo in ["pelicula", "movie"] else "series_vistas"
    )

    # Armamos el item como lo pide tu PerfilModel
    item = {
        "id": int(data.get("id")),
        "tipo": tipo,
        "titulo": data.get("titulo", ""),
        "poster": data.get("poster", ""),
        "puntuacion": float(data.get("puntuacion", 0)),
        "fecha": data.get("fecha", ""),
        "genero_ids": [],  # Opcional si querés pasarlos desde el JS
    }

    # Importamos acá para evitar referencias circulares si es necesario
    from app.model.modelo_usuarios import PerfilModel

    modelo_perfil = PerfilModel()

    agregado = modelo_perfil.agregar_a_lista(nombre_usuario, lista_destino, item)
    return jsonify({"success": True, "agregado": agregado})
