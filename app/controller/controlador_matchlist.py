from flask import Blueprint, redirect, url_for
# Importás las dependencias de tu perfil/modelo existente
from .controlador_usuarios import _usuario_requerido, modelo_perfil
# Importás tu nueva clase Vista
from app.views.vista_matchlist import MatchlistView

matchlist_bp = Blueprint("matchlist", __name__)

# Instanciamos la vista que acabamos de crear
vista_matchlist = MatchlistView()

@matchlist_bp.route("/mi-matchlist")
def ver_matchlist_completa():
    print("=== ENTRANDO A /MI-MATCHLIST (USANDO CAPA VIEW) ===")
    
    # 1. Validación de usuario mediante el controlador/sesión
    nombre_usuario = _usuario_requerido()
    if not nombre_usuario:
        return redirect(url_for("usuarios.login"))

    usuario = modelo_perfil.usuario_model.obtener_por_nombre(nombre_usuario)
    if not usuario:
        return redirect(url_for("usuarios.login"))

    # 2. El controlador le pide los datos al Modelo
    listas = modelo_perfil.obtener_listas(nombre_usuario)
    matchlist_completa = listas.get("matchlist", [])

    # Lógica mínima del controlador: separar datos para los contadores de la interfaz
    peliculas_match = [item for item in matchlist_completa if item.get("tipo") == "movie"]
    series_match = [item for item in matchlist_completa if item.get("tipo") == "serie"]

    # 3. DELEGACIÓN A LA VISTA: El controlador NO renderiza, le pasa los datos a la View
    return vista_matchlist.render_matchlist_completa(
        usuario=usuario,
        matchlist=matchlist_completa,
        peliculas_match=peliculas_match,
        series_match=series_match
    )