"""
app/model/modelo_series.py
──────────────────────────
Capa de Modelo (M en MVC) para Series.

Responsabilidades:
  - Conectarse a la API de TMDB.
  - Realizar las peticiones HTTP para series.
  - Devolver los datos limpios al controlador.
"""

import requests
from config.config import Config


class SerieModel:
    """
    Modelo que representa y obtiene datos de series desde TMDB.
    """

    def __init__(self):
        self.api_key = Config.TMDB_API_KEY
        self.base_url = Config.TMDB_BASE_URL
        self.img_url = Config.TMDB_IMAGE_BASE_URL
        self.language = Config.TMDB_LANGUAGE

    # ── Método privado: petición genérica ──────────────────────────────────

    def _get(self, endpoint: str, params: dict = {}) -> dict:
        """
        Realiza una petición GET a TMDB.

        Args:
            endpoint : Ruta relativa, ej: '/tv/popular'
            params   : Parámetros extra de query string

        Returns:
            dict con la respuesta JSON de TMDB

        Raises:
            Exception si la petición falla
        """
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
        """Devuelve la URL completa de un póster o backdrop."""
        if not path:
            return None
        return f"{self.img_url}{path}"

    # ── Métodos públicos (usados por el controlador) ───────────────────────

    def obtener_populares(self, pagina: int = 1) -> dict:
        """
        Obtiene el listado de series populares.

        Args:
            pagina: Número de página (default 1)

        Returns:
            dict con 'series' (lista) y 'total_paginas'
        """
        data = self._get("/tv/popular", {"page": pagina})

        series = [
            {
                "id": s["id"],
                "titulo": s.get("name", "Sin título"),
                "descripcion": s.get("overview", "Sin descripción disponible."),
                "puntuacion": s.get("vote_average", 0),
                "poster": self.construir_url_imagen(s.get("poster_path")),
                "fecha": s.get("first_air_date", ""),
            }
            for s in data.get("results", [])
        ]

        return {
            "series": series,
            "total_paginas": data.get("total_pages", 1),
            "pagina_actual": pagina,
        }

    def obtener_credits(self, serie_id: int) -> dict:
        """
        Obtiene los creadores y elenco principal de una serie.

        Args:
            serie_id: ID numérico de la serie en TMDB

        Returns:
            dict con 'creadores' (lista de dicts) y 'cast' (lista de dicts)
        """
        data = self._get(f"/tv/{serie_id}/aggregate_credits")

        # Creadores: toma los primeros 3 creadores
        creadores = [
            {
                "nombre": p.get("name", ""),
                "foto": (
                    self.construir_url_imagen(p.get("profile_path"))
                    if p.get("profile_path")
                    else None
                ),
            }
            for p in data.get("crew", [])[:3]
        ]

        # Cast: toma los primeros 10 actores ordenados por order
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

        return {"creadores": creadores, "cast": cast}

    def obtener_keywords(self, serie_id: int) -> list:
        """
        Obtiene las keywords de una serie.

        Args:
            serie_id: ID numérico de la serie en TMDB

        Returns:
            Lista de strings con las keywords (máximo 15)
        """
        data = self._get(f"/tv/{serie_id}/keywords")

        return [k["name"] for k in data.get("results", [])]

    def obtener_providers(self, serie_id: int) -> dict:
        """
        Obtiene los proveedores de streaming para Argentina.

        Returns:
            dict con 'flatrate', 'rent' y 'buy' (listas de dicts con nombre y logo)
            Cualquiera de las listas puede ser vacía si no hay datos.
        """
        data = self._get(f"/tv/{serie_id}/watch/providers")

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
            "flatrate": parsear(ar_data.get("flatrate", [])),  # Streaming incluido
            "rent": parsear(ar_data.get("rent", [])),  # Alquiler
            "buy": parsear(ar_data.get("buy", [])),  # Compra
        }

    def _obtener_nombres_paises(self) -> dict:
        """Devuelve un dict {codigo: nombre_en_español} desde la API de TMDB."""
        data = self._get("/configuration/countries", {"language": "es-AR"})
        return {p["iso_3166_1"]: p["native_name"] for p in data}

    def obtener_clasificacion(self, serie_id: int) -> str:
        """
        Obtiene la clasificación de edad para Argentina (AR).

        Returns:
            String con la clasificación (ej: '13+') o vacío si no hay datos.
        """
        data = self._get(f"/tv/{serie_id}/content_ratings")
        resultados = data.get("results", [])

        def extraer_cert(iso: str) -> str:
            region = next((r for r in resultados if r["iso_3166_1"] == iso), None)
            if not region:
                return ""
            return region.get("rating", "")

        return extraer_cert("AR") or extraer_cert("US") or ""

    def obtener_detalle(self, serie_id: int) -> dict:
        """
        Obtiene el detalle completo de una serie.

        Args:
            serie_id: ID numérico de la serie en TMDB

        Returns:
            dict con los datos de la serie
        """
        data = self._get(f"/tv/{serie_id}")
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

        # Temporadas y episodios
        num_temporadas = data.get("number_of_seasons", 0)
        num_episodios = data.get("number_of_episodes", 0)

        return {
            "id": data["id"],
            "titulo": data.get("name", "Sin título"),
            "titulo_original": data.get("original_name", "Sin título original"),
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
            "fecha": data.get("first_air_date", "-"),
            "duracion": f"{num_temporadas} Temporada{'s' if num_temporadas != 1 else ''} - {num_episodios} Episodios",
            "generos": [g["name"] for g in data.get("genres", [])],
            "productora": [p["name"] for p in data.get("production_companies", [])],
            "tagline": data.get("tagline", ""),
            "web": data.get("homepage", ""),
        }

    def buscar(self, query: str, pagina: int = 1) -> dict:
        """
        Busca series por título.

        Args:
            query : Texto a buscar
            pagina: Número de página (default 1)

        Returns:
            dict con 'series' (lista) y 'total_paginas'
        """
        data = self._get("/search/tv", {"query": query, "page": pagina})

        series = [
            {
                "id": s["id"],
                "titulo": s.get("name", "Sin título"),
                "descripcion": s.get("overview", "Sin descripción disponible."),
                "puntuacion": s.get("vote_average", 0),
                "poster": self.construir_url_imagen(s.get("poster_path")),
                "fecha": s.get("first_air_date", ""),
            }
            for s in data.get("results", [])
        ]

        return {
            "series": series,
            "total_paginas": data.get("total_pages", 1),
            "pagina_actual": pagina,
            "query": query,
        }
