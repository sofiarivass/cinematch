"""
app/model/modelo.py
───────────────────
Capa de Modelo (M en MVC).
"""

import requests
from config.config import Config


class PeliculaModel:
    """
    Modelo que representa y obtiene datos de películas desde TMDB.
    """

    # Constantes de la clase bien declaradas al inicio
    PROVIDERS_PRINCIPALES_AR = {8, 1899, 119, 337, 350, 531}
    # Netflix, HBO Max, Amazon Prime, Disney+, Apple TV+, Paramount+

    PROVIDERS_LOGOS_LOCALES = {
        8: "img/servicios/netflix.svg",
        1899: "img/servicios/hbo-max.svg",
        119: "img/servicios/prime-video.svg",
        337: "img/servicios/disney.svg",
        350: "img/servicios/apple-tv.svg",
        531: "img/servicios/paramount.svg",
    }

    def __init__(self):
        self.api_key = Config.TMDB_API_KEY
        self.base_url = Config.TMDB_BASE_URL
        self.img_url = Config.TMDB_IMAGE_BASE_URL
        self.language = Config.TMDB_LANGUAGE

    # ── Método privado: petición genérica ──────────────────────────────────

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

    # ── Método auxiliar: construir URL de imagen ───────────────────────────

    def construir_url_imagen(self, path: str) -> str | None:
        if not path:
            return None
        return f"{self.img_url}{path}"

    # ── Métodos públicos (usados por el controlador) ───────────────────────

    def obtener_populares(self, pagina: int = 1) -> dict:
        data = self._get("/movie/popular", {"page": pagina})

        peliculas = [
            {
                "id": p["id"],
                "titulo": p.get("title", "Sin título"),
                "descripcion": p.get("overview", "Sin descripción disponible."),
                "puntuacion": p.get("vote_average", 0),
                "poster": self.construir_url_imagen(p.get("poster_path")),
                "fecha": p.get("release_date", ""),
            }
            for p in data.get("results", [])
        ]

        return {
            "peliculas": peliculas,
            "total_paginas": data.get("total_pages", 1),
            "pagina_actual": pagina,
        }

    def obtener_providers(self, pelicula_id: int) -> dict:
        """
        Obtiene los proveedores de streaming específicos para una película en Argentina.
        """
        data = self._get(f"/movie/{pelicula_id}/watch/providers")
        ar_data = data.get("results", {}).get("AR", {})

        def parsear(lista: list) -> list:
            return [
                {
                    "nombre": p.get("provider_name", ""),
                    "logo": self.construir_url_imagen(p.get("logo_path")),
                }
                for p in lista
            ]

        return {
            "flatrate": parsear(ar_data.get("flatrate", [])),  # Streaming
            "rent": parsear(ar_data.get("rent", [])),  # Alquiler
            "buy": parsear(ar_data.get("buy", [])),  # Compra
        }

    def obtener_todos_providers_ar(self) -> list:
        data = self._get(
            "/watch/providers/movie",
            {
                "watch_region": "AR",
                "language": "es-AR",
            },
        )
        principales_ids = set(self.PROVIDERS_PRINCIPALES_AR)
        return [
            {
                "id": p.get("provider_id"),
                "nombre": p.get("provider_name", ""),
            }
            for p in data.get("results", [])
            if p.get("provider_id") not in principales_ids
        ]

    def obtener_providers_ar(self) -> list:
        data = self._get(
            "/watch/providers/movie",
            {
                "watch_region": "AR",
                "language": "es-AR",
            },
        )

        principales = [
            {
                "id": p.get("provider_id"),
                "nombre": p.get("provider_name", ""),
                "logo": self.PROVIDERS_LOGOS_LOCALES.get(p.get("provider_id")),
            }
            for p in data.get("results", [])
            if p.get("provider_id") in self.PROVIDERS_PRINCIPALES_AR
        ]

        orden = [8, 1899, 119, 337, 350, 531]
        principales.sort(key=lambda x: orden.index(x["id"]) if x["id"] in orden else 99)

        return principales

    def obtener_todos_idiomas(self) -> list:
        """Obtiene la lista completa de idiomas soportados por TMDB en español."""
        try:
            data = self._get("/configuration/languages")

            # Formateamos la lista para la vista
            idiomas = [
                {
                    "iso": i.get("iso_639_1"),
                    "nombre": (
                        i.get("english_name") if i.get("name") == "" else i.get("name")
                    ),
                }
                for i in data
            ]

            # Los ordenamos alfabéticamente por nombre
            idiomas.sort(key=lambda x: x["nombre"])
            return idiomas
        except Exception:
            return []

    def obtener_credits(self, pelicula_id: int) -> dict:
        data = self._get(f"/movie/{pelicula_id}/credits")

        directores = [
            {
                "nombre": p.get("name", "").split(" ", 1),
                "foto": (
                    self.construir_url_imagen(p.get("profile_path"))
                    if p.get("profile_path")
                    else None
                ),
            }
            for p in data.get("crew", [])
            if p.get("job") == "Director"
        ]

        cast = [
            {
                "nombre": p.get("name", ""),
                "personaje": p.get("character", ""),
                "foto": (
                    self.construir_url_imagen(p.get("profile_path"))
                    if p.get("profile_path")
                    else None
                ),
            }
            for p in sorted(data.get("cast", []), key=lambda x: x.get("order", 99))[:10]
        ]

        return {"directores": directores, "cast": cast}

    def obtener_keywords(self, pelicula_id: int) -> list:
        data = self._get(f"/movie/{pelicula_id}/keywords")
        return [k["name"] for k in data.get("keywords", [])]

    def _obtener_nombres_paises(self) -> dict:
        data = self._get("/configuration/countries", {"language": "es-AR"})
        return {p["iso_3166_1"]: p["native_name"] for p in data}

    def obtener_clasificacion(self, pelicula_id: int) -> str:
        data = self._get(f"/movie/{pelicula_id}/release_dates")
        resultados = data.get("results", [])

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

    def obtener_trailer(self, pelicula_id: int) -> str | None:
        """
        Obtiene el link de YouTube del trailer oficial.
        Prioriza español, si no encuentra trae inglés, si no hay ninguno devuelve None.
        """
        data = self._get(f"/movie/{pelicula_id}/videos", {"language": "es-AR"})
        videos = data.get("results", [])

        # Si no hay videos en español, buscar en inglés
        if not videos:
            data_en = self._get(f"/movie/{pelicula_id}/videos", {"language": "en-US"})
            videos = data_en.get("results", [])

        # Filtrar solo trailers de YouTube
        trailer = next(
            (
                v
                for v in videos
                if v.get("type") == "Trailer" and v.get("site") == "YouTube"
            ),
            None,
        )

        if not trailer:
            # Intentar con cualquier video de YouTube si no hay trailer
            trailer = next((v for v in videos if v.get("site") == "YouTube"), None)

        if trailer:
            return f"https://www.youtube.com/watch?v={trailer['key']}"
        return None

    def obtener_detalle(self, pelicula_id: int) -> dict:
        data = self._get(f"/movie/{pelicula_id}")
        paises = self._obtener_nombres_paises()
        idioma_code = data.get("original_language", "")
        idioma_original = next(
            (
                l["name"]
                for l in data.get("spoken_languages", [])
                if l["iso_639_1"] == idioma_code
            ),
            idioma_code,
        )
        # Web oficial: intenta en español, si no en inglés
        web = data.get("homepage", "")
        if not web:
            data_en = self._get(f"/movie/{pelicula_id}", {"language": "en-US"})
            web = data_en.get("homepage", "")

        return {
            "id": data["id"],
            "titulo": data.get("title", "Sin título"),
            "titulo_original": data.get("original_title", "Sin título original"),
            "pais": [paises.get(c, c) for c in data.get("origin_country", [])],
            "idioma_original": idioma_original,
            "descripcion": data.get("overview", "Sin descripción disponible."),
            "puntuacion": round(data.get("vote_average", 0), 2),
            "votos": (
                f"{data.get('vote_count', 0) / 1000:.1f}k"
                if data.get("vote_count", 0) >= 1000
                else str(data.get("vote_count", 0))
            ),
            "poster": self.construir_url_imagen(data.get("poster_path")),
            "backdrop": self.construir_url_imagen(data.get("backdrop_path")),
            "fecha": data.get("release_date", "-"),
            "duracion": f"{data.get('runtime', 0) // 60}h {data.get('runtime', 0) % 60}m",
            "generos": [g["name"] for g in data.get("genres", [])],
            "productora": [p["name"] for p in data.get("production_companies", [])],
            "tagline": data.get("tagline", ""),
            "web": web,
        }

    def buscar(self, query: str, pagina: int = 1) -> dict:
        data = self._get("/search/movie", {"query": query, "page": pagina})

        peliculas = [
            {
                "id": p["id"],
                "titulo": p.get("title", "Sin título"),
                "descripcion": p.get("overview", "Sin descripción disponible."),
                "puntuacion": p.get("vote_average", 0),
                "poster": self.construir_url_imagen(p.get("poster_path")),
                "fecha": p.get("release_date", ""),
            }
            for p in data.get("results", [])
        ]

        return {
            "peliculas": peliculas,
            "total_paginas": data.get("total_pages", 1),
            "pagina_actual": pagina,
            "query": query,
        }
