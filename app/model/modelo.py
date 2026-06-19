"""
app/model/modelo.py
───────────────────
Modelo especificamente utilizado para la página Explorar.
Orquesta búsquedas y filtros sobre películas Y series (TMDB).
No duplica lógica: hereda el _get de PeliculaModel y añade lo específico.
"""

import requests
from config.config import Config


class Model:
    """
    Consultas unificadas para el catálogo explorable (películas + series).
    """

    GENEROS_MOVIE = {}   # Se pueblan lazy en _cargar_generos()
    GENEROS_TV    = {}

    ORDEN_MAP = {
        "popularidad": "popularity.desc",
        "puntaje":     "vote_average.desc",
        "fecha_desc":  "primary_release_date.desc",   # para TV: first_air_date.desc
        "fecha_asc":   "primary_release_date.asc",
        "titulo":      "title.asc",                   # para TV: name.asc
    }

    DURACION_MAP = {
        # (with_runtime.gte, with_runtime.lte)  — None = sin límite
        "corta": (None, 89),
        "media": (90,  120),
        "larga": (121, None),
    }

    def __init__(self):
        self.api_key  = Config.TMDB_API_KEY
        self.base_url = Config.TMDB_BASE_URL
        self.img_url  = Config.TMDB_IMAGE_BASE_URL
        self.language = Config.TMDB_LANGUAGE

    # ── Utilidades internas ────────────────────────────────────────────────

    def _get(self, endpoint: str, params: dict = {}) -> dict:
        url = f"{self.base_url}{endpoint}"
        params_completos = {
            "api_key":  self.api_key,
            "language": self.language,
            **params,
        }
        try:
            r = requests.get(url, params=params_completos, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.exceptions.ConnectionError:
            raise Exception("No se pudo conectar con TMDB.")
        except requests.exceptions.Timeout:
            raise Exception("La solicitud a TMDB tardó demasiado.")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"Error de TMDB: {e}")

    def _img(self, path: str | None, size: str = "w300") -> str | None:
        if not path:
            return None
        return f"{self.img_url}{path}"

    def _normalizar_movie(self, p: dict) -> dict:
        """Convierte un resultado de TMDB /movie a nuestro esquema común."""
        return {
            "id":          p["id"],
            "tipo":        "pelicula",
            "titulo":      p.get("title", "Sin título"),
            "descripcion": p.get("overview", ""),
            "puntuacion":  round(p.get("vote_average", 0), 1),
            "votos":       p.get("vote_count", 0),
            "poster":      p.get("poster_path"),   # ruta relativa, la template arma la URL
            "fecha":       p.get("release_date", ""),
            "genero_ids":  p.get("genre_ids", []),
            "popularidad": p.get("popularity", 0),
        }

    def _normalizar_tv(self, s: dict) -> dict:
        """Convierte un resultado de TMDB /tv a nuestro esquema común."""
        return {
            "id":          s["id"],
            "tipo":        "serie",
            "titulo":      s.get("name", "Sin título"),
            "descripcion": s.get("overview", ""),
            "puntuacion":  round(s.get("vote_average", 0), 1),
            "votos":       s.get("vote_count", 0),
            "poster":      s.get("poster_path"),
            "fecha":       s.get("first_air_date", ""),
            "genero_ids":  s.get("genre_ids", []),
            "popularidad": s.get("popularity", 0),
        }

    # ── Géneros ────────────────────────────────────────────────────────────

    def obtener_generos(self) -> list[dict]:
        """
        Devuelve géneros únicos combinando los de películas y series.
        Útil para poblar el <select> de filtros.
        """
        movies = self._get("/genre/movie/list").get("genres", [])
        series = self._get("/genre/tv/list").get("genres", [])

        # Unión por id, sin duplicados
        vistos = set()
        resultado = []
        for g in movies + series:
            if g["id"] not in vistos:
                vistos.add(g["id"])
                resultado.append({"id": g["id"], "nombre": g["name"]})

        resultado.sort(key=lambda x: x["nombre"])
        return resultado

    # ── Años disponibles ───────────────────────────────────────────────────

    def obtener_anios(self, desde: int = 1950) -> list[int]:
        """Rango de años para el filtro, del más reciente al más antiguo."""
        from datetime import date
        return list(range(date.today().year, desde - 1, -1))

    # ── Búsqueda por texto ─────────────────────────────────────────────────

    def buscar(self, query: str, pagina: int = 1, tipo: str = "todo") -> dict:
        """
        Busca en /search/multi y filtra por tipo si es necesario.
        tipo: 'todo' | 'pelicula' | 'serie'
        """
        data = self._get("/search/multi", {
            "query": query,
            "page":  pagina,
        })

        resultados = []
        for item in data.get("results", []):
            media = item.get("media_type")
            if media == "movie" and tipo in ("todo", "pelicula"):
                resultados.append(self._normalizar_movie(item))
            elif media == "tv" and tipo in ("todo", "serie"):
                resultados.append(self._normalizar_tv(item))
            # media_type == "person" se descarta silenciosamente

        return {
            "resultados":    resultados,
            "total_paginas": data.get("total_pages", 1),
            "pagina_actual": pagina,
            "query":         query,
            "total":         data.get("total_results", 0),
        }

    # ── Discover con filtros ───────────────────────────────────────────────

    def _params_discover(self, filtros: dict, es_tv: bool = False) -> dict:
        """
        Construye el dict de params para /discover/movie o /discover/tv
        a partir del dict de filtros normalizados.

        filtros admitidos:
            genero      → int id
            anio        → int año
            plataforma  → int provider_id
            puntaje     → float mínimo
            duracion    → 'corta' | 'media' | 'larga'
            orden       → clave de ORDEN_MAP
        """
        orden_key = filtros.get("orden", "popularidad")

        if es_tv:
            sort_map = {
                "popularidad": "popularity.desc",
                "puntaje":     "vote_average.desc",
                "fecha_desc":  "first_air_date.desc",
                "fecha_asc":   "first_air_date.asc",
                "titulo":      "name.asc",
            }
            sort = sort_map.get(orden_key, "popularity.desc")
        else:
            sort = self.ORDEN_MAP.get(orden_key, "popularity.desc")

        params = {
            "sort_by":      sort,
            "page":         filtros.get("pagina", 1),
            "watch_region": "AR",
            # Filtramos votos mínimos para evitar resultados basura
            "vote_count.gte": 50,
        }

        if filtros.get("genero"):
            params["with_genres"] = filtros["genero"]

        if filtros.get("anio"):
            if es_tv:
                params["first_air_date_year"] = filtros["anio"]
            else:
                params["primary_release_year"] = filtros["anio"]

        if filtros.get("plataforma"):
            params["with_watch_providers"] = filtros["plataforma"]

        if filtros.get("puntaje"):
            params["vote_average.gte"] = filtros["puntaje"]

        if filtros.get("duracion"):
            gte, lte = self.DURACION_MAP.get(filtros["duracion"], (None, None))
            # Duración solo aplica a películas (TMDB no tiene runtime en /discover/tv)
            if not es_tv:
                if gte:
                    params["with_runtime.gte"] = gte
                if lte:
                    params["with_runtime.lte"] = lte

        return params

    def descubrir(self, filtros: dict, tipo: str = "todo") -> dict:
        """
        Llama a /discover según el tipo y devuelve resultados normalizados.
        tipo: 'todo' | 'pelicula' | 'serie'

        Cuando tipo='todo' hace dos llamadas en paralelo (movie + tv) y
        mezcla los resultados ordenados por el criterio elegido.
        """
        pagina = int(filtros.get("pagina", 1))

        if tipo == "pelicula":
            data = self._get("/discover/movie", self._params_discover(filtros, es_tv=False))
            resultados = [self._normalizar_movie(p) for p in data.get("results", [])]
            total_paginas = min(data.get("total_pages", 1), 500)
            total = data.get("total_results", 0)

        elif tipo == "serie":
            data = self._get("/discover/tv", self._params_discover(filtros, es_tv=True))
            resultados = [self._normalizar_tv(s) for s in data.get("results", [])]
            total_paginas = min(data.get("total_pages", 1), 500)
            total = data.get("total_results", 0)

        else:  # "todo" → merge movie + tv
            data_m = self._get("/discover/movie", self._params_discover(filtros, es_tv=False))
            data_t = self._get("/discover/tv",    self._params_discover(filtros, es_tv=True))

            movies = [self._normalizar_movie(p) for p in data_m.get("results", [])]
            series = [self._normalizar_tv(s)    for s in data_t.get("results", [])]

            orden_key = filtros.get("orden", "popularidad")
            resultados = self._merge(movies, series, orden_key)

            # Para paginación usamos el máximo de ambos (aproximado)
            total_paginas = min(
                max(data_m.get("total_pages", 1), data_t.get("total_pages", 1)),
                500
            )
            total = data_m.get("total_results", 0) + data_t.get("total_results", 0)

        return {
            "resultados":    resultados,
            "total_paginas": total_paginas,
            "pagina_actual": pagina,
            "total":         total,
        }

    def _merge(self, movies: list, series: list, orden: str) -> list:
        """
        Intercala películas y series para que el resultado no sea
        primero todas las películas y luego todas las series.
        El criterio de sort es el mismo que se pidió en los filtros.
        """
        combinados = movies + series

        if orden == "puntaje":
            combinados.sort(key=lambda x: x["puntuacion"], reverse=True)
        elif orden in ("fecha_desc", "fecha_asc"):
            reverse = orden == "fecha_desc"
            combinados.sort(key=lambda x: x["fecha"] or "", reverse=reverse)
        elif orden == "titulo":
            combinados.sort(key=lambda x: x["titulo"].lower())
        else:  # popularidad (default)
            combinados.sort(key=lambda x: x["popularidad"], reverse=True)

        return combinados

    # ── Entry point principal ──────────────────────────────────────────────

    def explorar(self, filtros: dict) -> dict:
        """
        Método que llama el controlador. Decide internamente si usar
        búsqueda por texto o discover por filtros.

        filtros admitidos (todos opcionales):
            q           → str  búsqueda libre
            tipo        → 'todo' | 'pelicula' | 'serie'
            genero      → int
            anio        → int
            plataforma  → int
            puntaje     → float
            duracion    → 'corta' | 'media' | 'larga'
            orden       → str
            pagina      → int
        """
        query = (filtros.get("q") or "").strip()
        tipo  = filtros.get("tipo", "todo")

        if query:
            return self.buscar(query, pagina=int(filtros.get("pagina", 1)), tipo=tipo)
        else:
            return self.descubrir(filtros, tipo=tipo)
