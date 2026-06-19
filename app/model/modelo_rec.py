"""
app/model/modelo_rec.py
───────────────────
Capa de Modelo (M en MVC).
"""

import requests
from config.config import Config


class RecomendacionesModel:
    """
    Modelo para obtener recomendaciones de películas.
    """

    def __init__(self):
        self.api_key = Config.TMDB_API_KEY
        self.base_url = Config.TMDB_BASE_URL
        self.img_url = Config.TMDB_IMAGE_BASE_URL
        self.language = Config.TMDB_LANGUAGE

    def _get(self, endpoint: str, params: dict = {}) -> dict:
        url = f"{self.base_url}{endpoint}"
        params_completos = {
            "api_key": self.api_key,
            "language": self.language,
            **params,
        }

        try:
            respuesta = requests.get(url, params=params_completos, timeout=10)
            respuesta.raise_for_status()
            return respuesta.json()
        except requests.exceptions.ConnectionError:
            raise Exception(
                "No se pudo conectar con TMDB. Verificá tu conexión a internet."
            )
        except requests.exceptions.Timeout:
            raise Exception("La solicitud a TMDB tardó demasiado. Intentá de nuevo.")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Error de TMDB: {e}")

    # Mapeo emociones → géneros TMDB (movie / tv)
    GENEROS_EMOCIONES = {
        "pelicula": {
            "tension": [53, 27, 80],  # Suspenso, Terror, Crimen
            "emocionarme": [18, 10749, 36],  # Drama, Romance, Historia
            "reirme": [35, 16],  # Comedia, Animación
            "sorprenderme": [9648, 14, 878],  # Misterio, Fantasía, Ciencia ficción
            "adrenalina": [28, 12, 10752],  # Acción, Aventura, Bélica
            "familia": [10751, 16],  # Familia, Animación
            "aprender": [99, 36],  # Documental, Historia
            "nostalgia": [37, 36, 10402],  # Western, Historia, Música
            "inspiracion": [10402, 36, 18],  # Música, Historia, Drama
        },
        "serie": {
            "tension": [80, 9648, 18],  # Crimen, Misterio, Drama
            "emocionarme": [18, 10749],  # Drama, Romance
            "reirme": [35, 16, 10764],  # Comedia, Animación, Reality
            "sorprenderme": [10765, 9648, 16],  # Sci-Fi & Fantasy, Misterio, Animación
            "adrenalina": [
                10759,
                10768,
                37,
            ],  # Action & Adventure, War & Politics, Western
            "familia": [10751, 10762, 35],  # Familia, Kids, Comedia
            "aprender": [99, 10767],  # Documental, Talk
            "nostalgia": [10764, 10767],  # Reality, Talk
            "inspiracion": [10767, 99, 18],  # Talk, Documental, Drama
        },
    }

    # Mapeo época → rango de fechas
    EPOCAS = {
        "estrenos": ("2022-01-01", None),
        "modernas": ("2000-01-01", "2021-12-31"),
        "clasicos": (None, "1999-12-31"),
        "todo": (None, None),
    }

    # Mapeo tiempo → minutos (películas)
    DURACION_PELICULA = {
        "menos de 90 minutos": (None, 90),
        "90-120 minutos": (90, 120),
        "más de 2 horas": (120, None),
    }

    # Mapeo tiempo → episodios máximos (series)
    EPISODIOS_SERIE = {
        "miniserie": (None, 15),
        "media": (15, 40),
        "larga": (40, None),
    }

    # IDs de proveedores de TMDB (Región AR / Latam)
    PLATAFORMAS_TMDB = {
        "netflix": 8,
        "prime": 119,
        "disney": 337,
        "max": 1899,
        "apple": 2,
    }

    def _obtener_detalle_completo(self, item_id: int, tipo: str) -> dict:
        """
        Consulta el detalle profundo de un item (movie o tv) incluyendo
        créditos y proveedores de streaming en una sola petición.
        """
        endpoint = f"/movie/{item_id}" if tipo == "movie" else f"/tv/{item_id}"
        # append_to_response nos ahorra hacer 3 peticiones separadas por película
        params = {"append_to_response": "credits,watch/providers"}
        try:
            return self._get(endpoint, params)
        except Exception:
            return {}

    def obtener_recomendaciones(self, preferencias: dict, pagina: int = 1) -> list:
        """
        Obtiene recomendaciones desde TMDB /discover según las preferencias de la encuesta.
        """
        formato = preferencias.get("formato", "pelicula")
        emociones = preferencias.get("emociones", [])
        epoca = preferencias.get("epoca", "todo")
        tiempo = preferencias.get("tiempo", "")
        clasificacion = preferencias.get("clasificacion", "")

        endpoint = "/discover/movie" if formato == "pelicula" else "/discover/tv"
        tipo_item = "movie" if formato == "pelicula" else "serie"

        mapa = self.GENEROS_EMOCIONES.get(formato, {})
        ids_generos = set()
        for emocion in emociones:
            ids_generos.update(mapa.get(emocion, []))

        # ── Parámetros base ───────────────────────────────────────────────────
        params = {
            "page": pagina,
            "sort_by": "popularity.desc",
            "vote_count.gte": 100,
            "with_genres": (
                "|".join(str(g) for g in ids_generos) if ids_generos else None
            ),
        }

        # ── Filtro de Proveedores Dinámico (Viene directo de la BD) ───────────
        proveedores = preferencias.get("proveedores", [])
        if proveedores:
            ids_validos = [str(p) for p in proveedores if str(p).isdigit()]
            if ids_validos:
                params["with_watch_providers"] = "|".join(ids_validos)
                params["watch_region"] = "AR"

        # ── Época ─────────────────────────────────────────────────────────────
        fecha_desde, fecha_hasta = self.EPOCAS.get(epoca, (None, None))
        campo_fecha = (
            "primary_release_date" if formato == "pelicula" else "first_air_date"
        )
        if fecha_desde:
            params[f"{campo_fecha}.gte"] = fecha_desde
        if fecha_hasta:
            params[f"{campo_fecha}.lte"] = fecha_hasta

        # ── Filtro de Duración Nativo (Solo películas) ────────────────────────
        if formato == "pelicula":
            min_min, max_min = self.DURACION_PELICULA.get(tiempo, (None, None))
            if min_min:
                params["with_runtime.gte"] = min_min
            if max_min:
                params["with_runtime.lte"] = max_min

        # ── Filtro de Clasificación (Edades) ──────────────────────────────────
        mapa_certificaciones = {"atp": "PG", "+13": "PG-13", "+16": "R"}
        if clasificacion in mapa_certificaciones and clasificacion != "+18":
            params["certification_country"] = "US"
            params["certification.lte"] = mapa_certificaciones[clasificacion]

        # Limpiar params vacíos
        params = {k: v for k, v in params.items() if v is not None}

        # 1. Petición inicial a Discover (Traemos 20 o 30 por si descartamos series)
        data = self._get(endpoint, params)
        resultados_base = data.get("results", [])[:30]
        lista_enriquecida = []

        # 2. Iteramos los resultados para buscar detalles y filtrar en código
        for r in resultados_base:
            if len(lista_enriquecida) >= 10:
                break

            item_id = r["id"]
            detalles = self._obtener_detalle_completo(item_id, tipo_item)
            if not detalles:
                detalles = r

            # 🔥 FILTRO MANUAL ESTRICTO PARA PELÍCULAS
            if tipo_item == "movie" and tiempo:
                runtime = detalles.get("runtime", 0)

                if runtime == 0:
                    continue

                min_min, max_min = self.DURACION_PELICULA.get(tiempo, (None, None))
                if min_min is not None and runtime <= min_min:
                    continue
                if max_min is not None and runtime > max_min:
                    continue

            # 🔥 FILTRO MANUAL BASADO EN TU LÓGICA DE EPISODIOS PARA SERIES
            if tipo_item == "serie":
                total_episodios = detalles.get("number_of_episodes", 0)

                if tiempo and total_episodios == 0:
                    continue

                min_ep, max_ep = self.EPISODIOS_SERIE.get(tiempo, (None, None))
                if min_ep is not None and total_episodios <= min_ep:
                    continue
                if max_ep is not None and total_episodios > max_ep:
                    continue

            # ── Procesamiento normal si superó los filtros ────────────────────
            generos_nombres = [g["name"] for g in detalles.get("genres", [])]

            if tipo_item == "movie":
                runtime = detalles.get("runtime")
                duracion_str = f"{runtime} min" if runtime else "N/D"
            else:
                seasons = detalles.get("number_of_seasons")
                duracion_str = (
                    f"{total_episodios} Eps. ({seasons} Temp.)"
                    if total_episodios
                    else "N/D"
                )

            credits_raw = detalles.get("credits", {})
            cast_list = [
                {"nombre": actor.get("name", "")}
                for actor in credits_raw.get("cast", [])[:5]
            ]

            directores_list = []
            if tipo_item == "movie":
                for crew_item in credits_raw.get("crew", []):
                    if crew_item.get("job") == "Director":
                        directores_list.append(
                            {"nombre": crew_item.get("name", "").split()}
                        )
            else:
                for creator in detalles.get("created_by", []):
                    directores_list.append({"nombre": creator.get("name", "").split()})

            providers_dict = {"flatrate": []}
            wp_results = detalles.get("watch/providers", {}).get("results", {})
            region_data = wp_results.get("AR", {})
            if not region_data:
                for r_code, r_val in wp_results.items():
                    if "flatrate" in r_val:
                        region_data = r_val
                        break

            if region_data and "flatrate" in region_data:
                for p in region_data["flatrate"]:
                    providers_dict["flatrate"].append(
                        {
                            "nombre": p.get("provider_name", ""),
                            "logo": (
                                f"https://image.tmdb.org/t/p/w154{p.get('logo_path')}"
                                if p.get("logo_path")
                                else ""
                            ),
                        }
                    )

            campo_titulo = "title" if formato == "pelicula" else "name"
            campo_fecha_r = (
                "release_date" if formato == "pelicula" else "first_air_date"
            )

            backdrop_path = detalles.get("backdrop_path")
            backdrop_url = (
                f"https://image.tmdb.org/t/p/w780{backdrop_path}"
                if backdrop_path
                else ""
            )

            lista_enriquecida.append(
                {
                    "id": item_id,
                    "titulo": detalles.get(
                        "title" if formato == "pelicula" else "name", "Sin título"
                    ),
                    "poster": r.get("poster_path", ""),
                    "backdrop": backdrop_url,
                    "puntuacion": round(
                        detalles.get("vote_average", r.get("vote_average", 0)), 1
                    ),
                    "fecha": detalles.get(campo_fecha_r, r.get(campo_fecha_r, "")),
                    "descripcion": detalles.get("overview", "Sin sinopsis disponible."),
                    "duracion": duracion_str,
                    "generos": generos_nombres,
                    "tipo": tipo_item,
                    "credits": {"cast": cast_list, "directores": directores_list},
                    "providers": providers_dict,
                }
            )

        return lista_enriquecida
