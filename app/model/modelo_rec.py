"""
app/model/modelo_rec.py
───────────────────
Capa de Modelo (M en MVC).
"""

import requests
from config.config import Config
from concurrent.futures import ThreadPoolExecutor


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

    GENEROS_EXCLUIR_INFANTIL = {
    "pelicula": {16, 10751},          # Animación, Familia
    "serie": {16, 10751, 10762},      # Animación, Familia, Kids
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

    TIPO_SERIE_TMDB = {
        "miniserie": 2,  # TMDB type: Miniseries
    }

    # Orden jerárquico de clasificaciones (AR) — de menor a mayor restricción
    ORDEN_CLASIFICACION = {
        # AR — Movies
        "ATP": 0,
        "+13": 1,
        "+16": 2,
        "+18": 3,
        "C": 3,
        # AR — TV
        "SAM 13": 1,
        "SAM 16": 2,
        "SAM 18": 3,
        # US — Movies (fallback)
        "G": 0,
        "PG": 0,
        "PG-13": 1,
        "R": 2,
        "NC-17": 3,
        # US — TV (fallback)
        "TV-Y": 0,
        "TV-Y7": 0,
        "TV-G": 0,
        "TV-PG": 0,
        "TV-14": 1,
        "TV-MA": 3,
    }

    # Mapeo del valor del form → clasificación AR equivalente y su nivel máximo permitido
    CLASIFICACION_NIVEL = {
        "atp": 0,
        "+13": 1,
        "+16": 2,
        "+18": 3,
    }

    def _extraer_clasificacion(self, detalles: dict, tipo: str) -> str:
        """
        Extrae la clasificación de edad desde el dict de detalles
        ya obtenido (sin hacer una llamada HTTP nueva).
        """
        if tipo == "movie":
            resultados = detalles.get("release_dates", {}).get("results", [])

            def extraer_cert(iso: str) -> str:
                region = next((r for r in resultados if r["iso_3166_1"] == iso), None)
                if not region:
                    return ""
                return next(
                    (
                        r["certification"]
                        for r in region.get("release_dates", [])
                        if r.get("certification")
                    ),
                    "",
                )

            return extraer_cert("AR") or extraer_cert("US") or ""
        else:
            resultados = detalles.get("content_ratings", {}).get("results", [])

            def extraer_cert(iso: str) -> str:
                region = next((r for r in resultados if r["iso_3166_1"] == iso), None)
                return region.get("rating", "") if region else ""

            return extraer_cert("AR") or extraer_cert("US") or ""

    def _obtener_detalle_completo(self, item_id: int, tipo: str) -> dict:
        """
        Consulta el detalle profundo de un item (movie o tv) en una sola petición.
        """
        endpoint = f"/movie/{item_id}" if tipo == "movie" else f"/tv/{item_id}"
        if tipo == "movie":
            params = {"append_to_response": "credits,watch/providers,release_dates"}
        else:
            params = {"append_to_response": "credits,watch/providers,content_ratings"}
        try:
            return self._get(endpoint, params)
        except Exception:
            return {}

    def obtener_recomendaciones(
        self, preferencias: dict, pagina: int = 1, ids_excluir: set = None
    ) -> list:
        ids_excluir = ids_excluir or set()

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

        params_base = {
            "sort_by": "popularity.desc",
            "vote_count.gte": 100,
            "with_genres": (
                "|".join(str(g) for g in ids_generos) if ids_generos else None
            ),
        }

        if "familia" not in emociones:
            generos_excluir = self.GENEROS_EXCLUIR_INFANTIL.get(formato, set())
            if generos_excluir:
                params_base["without_genres"] = "|".join(str(g) for g in generos_excluir)


        # ── Filtro de tipo de serie (excluir talk shows/videos/news siempre, miniserie si aplica) ──
        if tipo_item == "serie":
            if tiempo == "miniserie":
                params_base["with_type"] = 2
            else:
                params_base["with_type"] = "0|3|4"  # documentales + reality + scripted

        proveedores = preferencias.get("proveedores", [])
        if proveedores:
            ids_validos = [str(p) for p in proveedores if str(p).isdigit()]
            if ids_validos:
                params_base["with_watch_providers"] = "|".join(ids_validos)
                params_base["watch_region"] = "AR"

        fecha_desde, fecha_hasta = self.EPOCAS.get(epoca, (None, None))
        campo_fecha = (
            "primary_release_date" if formato == "pelicula" else "first_air_date"
        )
        if fecha_desde:
            params_base[f"{campo_fecha}.gte"] = fecha_desde
        if fecha_hasta:
            params_base[f"{campo_fecha}.lte"] = fecha_hasta

        params_base = {k: v for k, v in params_base.items() if v is not None}

        lista_enriquecida = []

        # ── Calculamos a partir de qué página de TMDB arrancar ──
        # Cada "página lógica" de nuestra app consume varias páginas reales de TMDB
        PAGINAS_TMDB_POR_TANDA = (
            5  # cuántas páginas de TMDB exploramos como máximo por tanda
        )
        pagina_tmdb_inicio = (pagina - 1) * PAGINAS_TMDB_POR_TANDA + 1
        LIMITE_POOL = 20  # candidatos a reunir antes de rankear

        for offset in range(PAGINAS_TMDB_POR_TANDA):
            if len(lista_enriquecida) >= LIMITE_POOL:
                break

            pagina_tmdb_actual = pagina_tmdb_inicio + offset
            params = {**params_base, "page": pagina_tmdb_actual}

            print(f"--- Pidiendo página TMDB #{pagina_tmdb_actual} ---")
            data = self._get(endpoint, params)
            resultados_base = data.get("results", [])

            if not resultados_base:
                print("Sin más resultados en TMDB, deteniendo búsqueda.")
                break

            # ── Filtramos por coincidencia ANTES de pedir detalle, y solo pedimos detalle para los que sobreviven ──
            candidatos_validos = []
            for r in resultados_base:
                if r["id"] in ids_excluir:
                    continue
                genero_ids_item = set(r.get("genre_ids", []))
                coincidencia = len(genero_ids_item & ids_generos) if ids_generos else 0
                if ids_generos and coincidencia == 0:
                    continue
                candidatos_validos.append((r, coincidencia))

            if not candidatos_validos:
                continue

            # ── Pedimos el detalle de todos los candidatos válidos de esta página EN PARALELO ──
            with ThreadPoolExecutor(max_workers=10) as executor:
                detalles_lista = list(executor.map(
                    lambda c: self._obtener_detalle_completo(c[0]["id"], tipo_item),
                    candidatos_validos
                ))

            for (r, coincidencia_generos), detalles in zip(candidatos_validos, detalles_lista):
                if len(lista_enriquecida) >= LIMITE_POOL:
                    break

                item_id = r["id"]
                if not detalles:
                    detalles = r

                # ── Filtro de duración/temporadas ──
                if tipo_item == "movie" and tiempo:
                    runtime = detalles.get("runtime", 0)
                    if runtime == 0:
                        continue
                    min_min, max_min = self.DURACION_PELICULA.get(tiempo, (None, None))
                    if min_min is not None and runtime <= min_min:
                        continue
                    if max_min is not None and runtime > max_min:
                        continue

                if tipo_item == "serie" and tiempo:
                    total_temporadas = detalles.get("number_of_seasons", 0)
                    if total_temporadas == 0:
                        continue
                    if tiempo == "media" and (
                        total_temporadas <= 2 or total_temporadas > 10
                    ):
                        continue
                    elif tiempo == "larga" and total_temporadas <= 10:
                        continue

                # ── Filtro de clasificación ──
                cert_item = ""
                nivel_item = None
                es_clasificacion_exacta = False

                if clasificacion in self.CLASIFICACION_NIVEL:
                    nivel_max_permitido = self.CLASIFICACION_NIVEL[clasificacion]
                    try:
                        cert_item = self._extraer_clasificacion(detalles, tipo_item)
                    except Exception:
                        cert_item = ""

                    nivel_item = self.ORDEN_CLASIFICACION.get(cert_item)

                    if nivel_item is None:
                        continue
                    if nivel_item > nivel_max_permitido:
                        continue

                    es_clasificacion_exacta = nivel_item == nivel_max_permitido

                # ── Procesamiento normal ──
                generos_nombres = [g["name"] for g in detalles.get("genres", [])]

                if tipo_item == "movie":
                    runtime = detalles.get("runtime")
                    duracion_str = f"{runtime} min" if runtime else "N/D"
                else:
                    total_episodios = detalles.get("number_of_episodes", 0)
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
                        directores_list.append(
                            {"nombre": creator.get("name", "").split()}
                        )

                providers_dict = {"flatrate": []}
                wp_results = detalles.get("watch/providers", {}).get("results", {})
                region_data = wp_results.get("AR", {})

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

                print(f"{r.get('title') or r.get('name')} → coincidencia: {coincidencia_generos}")
                lista_enriquecida.append(
                    {
                        "id": item_id,
                        "titulo": detalles.get(campo_titulo, "Sin título"),
                        "clasificacion": cert_item,
                        "poster": r.get("poster_path", ""),
                        "backdrop": backdrop_url,
                        "puntuacion": round(
                            detalles.get("vote_average", r.get("vote_average", 0)), 1
                        ),
                        "fecha": detalles.get(campo_fecha_r, r.get(campo_fecha_r, "")),
                        "descripcion": detalles.get(
                            "overview", "Sin sinopsis disponible."
                        ),
                        "duracion": duracion_str,
                        "generos": generos_nombres,
                        "tipo": tipo_item,
                        "credits": {"cast": cast_list, "directores": directores_list},
                        "providers": providers_dict,
                        "_es_clasificacion_exacta": es_clasificacion_exacta,
                        "_coincidencia_generos": coincidencia_generos,
                    }
                )

        lista_enriquecida.sort(
            key=lambda x: (
                -x.pop("_coincidencia_generos", 0),
                not x.pop("_es_clasificacion_exacta", False),
            )
        )

        return lista_enriquecida[:10]
