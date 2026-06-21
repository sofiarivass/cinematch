// @ts-nocheck

// PLATAFORMAS
document.addEventListener("DOMContentLoaded", function() {
    const input = document.getElementById("input-otra-plataforma");
    if (!input) return;

    const lista = document.getElementById("sugerencias-lista");
    const tagsContainer = document.getElementById("tags-container");
    const hidden = document.getElementById("plataformas-otras-hidden");

    // 1. INICIALIZAR LEYENDO LO QUE JINJA DEJÓ EN EL INPUT OCULTO
    let seleccionados = [];
    if (hidden && hidden.value) {
        const idsGuardados = hidden.value.split(",");
        // Buscamos los objetos completos en todosProviders basándonos en los IDs guardados
        seleccionados = todosProviders.filter(p => idsGuardados.includes(String(p.id)));
    }

    // ── Actualizar el input hidden con los seleccionados ──
    function actualizarHidden() {
        hidden.value = seleccionados.map(p => p.id).join(",");
    }

    // 2. DARLE VIDA A LOS TAGS PRE-RENDERIZADOS POR JINJA
    tagsContainer.querySelectorAll(".encuesta-tag").forEach(tag => {
        const idTag = tag.getAttribute("data-id");
        const botonEliminar = tag.querySelector(".encuesta-tag-remove");
        
        if (botonEliminar && idTag) {
            botonEliminar.addEventListener("click", function() {
                // Filtramos convirtiendo a String para evitar errores de tipo (int vs string)
                seleccionados = seleccionados.filter(p => String(p.id) !== String(idTag));
                actualizarHidden();
                tag.remove();
            });
        }
    });

    // ── Crear badge (para las nuevas que agregue el usuario) ──
    function agregarTag(provider) {
        if (seleccionados.find(p => p.id === provider.id)) return;
        seleccionados.push(provider);
        actualizarHidden();

        const tag = document.createElement("span");
        tag.className = "encuesta-tag";
        tag.dataset.id = provider.id;
        tag.innerHTML = `${provider.nombre} <button type="button" class="encuesta-tag-remove">×</button>`;

        tag.querySelector(".encuesta-tag-remove").addEventListener("click", function() {
            seleccionados = seleccionados.filter(p => p.id !== provider.id);
            actualizarHidden();
            tag.remove();
        });

        tagsContainer.appendChild(tag);
        input.value = "";
        lista.innerHTML = "";
        lista.style.display = "none";
    }

    // ── Mostrar sugerencias ──
    input.addEventListener("input", function() {
        const query = input.value.trim().toLowerCase();
        lista.innerHTML = "";

        if (query.length < 2) {
            lista.style.display = "none";
            return;
        }

        const filtrados = todosProviders.filter(p =>
            p.nombre.toLowerCase().includes(query) &&
            !seleccionados.find(s => s.id === p.id)
        ).slice(0, 6);

        if (filtrados.length === 0) {
            lista.style.display = "none";
            return;
        }

        filtrados.forEach(function(provider) {
            const li = document.createElement("li");
            li.className = "encuesta-sugerencia-item";
            li.textContent = provider.nombre;
            li.addEventListener("click", function() {
                agregarTag(provider);
            });
            lista.appendChild(li);
        });

        lista.style.display = "block";
    });

    // ── Cerrar sugerencias al hacer click afuera ──
    document.addEventListener("click", function(e) {
        if (!input.contains(e.target) && !lista.contains(e.target)) {
            lista.style.display = "none";
        }
    });
});

// IDIOMAS
document.addEventListener("DOMContentLoaded", () => {

    const inputOtro = document.getElementById("input-otro-idioma");
    const listaSugerencias = document.getElementById("sugerencias-idiomas");
    const contenedorTags = document.getElementById("tags-idiomas-contenedor");
    const formulario = document.getElementById("form-encuesta-idiomas");

    if (!inputOtro || !TODOS_LOS_IDIOMAS) return;

    let idiomasSeleccionados = new Set();

    // Registrar tags pre-renderizados desde session
    contenedorTags.querySelectorAll(".encuesta-tag").forEach(tag => {
        const iso = tag.getAttribute("data-iso");
        if (iso) idiomasSeleccionados.add(iso);

        const botonEliminar = tag.querySelector(".encuesta-tag-remove");
        if (botonEliminar) {
            botonEliminar.addEventListener("click", () => {
                tag.remove();
                const hiddenIdioma = document.getElementById(`hidden-idioma-${iso}`);
                if (hiddenIdioma) hiddenIdioma.remove();
                idiomasSeleccionados.delete(iso);
            });
        }
    });

    const checkboxAny = formulario.querySelector('input[name="idiomas"][value="any"]');
    const otrosCheckboxes = formulario.querySelectorAll('input[name="idiomas"]:not([value="any"])');

    function aplicarEstadoIndistinto() {
        if (checkboxAny.checked) {
            otrosCheckboxes.forEach(cb => cb.checked = false);
            contenedorTags.innerHTML = "";
            idiomasSeleccionados.clear();
            formulario.querySelectorAll('input[id^="hidden-idioma-"]').forEach(h => h.remove());
            inputOtro.disabled = true;
            inputOtro.placeholder = "Desmarcá 'Indistinto' para buscar";
            listaSugerencias.style.display = "none";
        } else {
            inputOtro.disabled = false;
            inputOtro.placeholder = "Ej: Deutsch, polski...";
        }
    }

    checkboxAny.addEventListener("change", aplicarEstadoIndistinto);

    otrosCheckboxes.forEach(cb => {
        cb.addEventListener("change", () => {
            if (cb.checked) {
                checkboxAny.checked = false;
                aplicarEstadoIndistinto();
            }
        });
    });

    // Aplicar estado inicial al cargar
    aplicarEstadoIndistinto();

    inputOtro.addEventListener("input", (e) => {
        if (checkboxAny.checked) return;

        const query = e.target.value.toLowerCase().trim();
        listaSugerencias.innerHTML = "";

        if (query.length < 2) {
            listaSugerencias.style.display = "none";
            return;
        }

        const fijos = ['es', 'en', 'pt', 'fr', 'ko', 'ja', 'it', 'any'];
        const filtrados = TODOS_LOS_IDIOMAS.filter(idioma =>
            idioma.nombre.toLowerCase().includes(query) &&
            !idiomasSeleccionados.has(idioma.iso) &&
            !fijos.includes(idioma.iso)
        ).slice(0, 5);

        if (filtrados.length > 0) {
            filtrados.forEach(idioma => {
                const li = document.createElement("li");
                li.className = "encuesta-sugerencia-item";
                li.textContent = idioma.nombre;
                li.addEventListener("click", () => {
                    agregarIdiomaTag(idioma.iso, idioma.nombre);
                    inputOtro.value = "";
                    listaSugerencias.style.display = "none";
                });
                listaSugerencias.appendChild(li);
            });
            listaSugerencias.style.display = "block";
        } else {
            listaSugerencias.style.display = "none";
        }
    });

    document.addEventListener("click", (e) => {
        if (!inputOtro.contains(e.target) && !listaSugerencias.contains(e.target)) {
            listaSugerencias.style.display = "none";
        }
    });

    function agregarIdiomaTag(iso, nombre) {
        if (idiomasSeleccionados.has(iso)) return;
        idiomasSeleccionados.add(iso);

        const tag = document.createElement("div");
        tag.className = "encuesta-tag";
        tag.setAttribute("data-iso", iso);
        tag.innerHTML = `<span>${nombre}</span><button type="button" class="encuesta-tag-remove">&times;</button>`;

        const hiddenInput = document.createElement("input");
        hiddenInput.type = "hidden";
        hiddenInput.name = "idiomas";
        hiddenInput.value = iso;
        hiddenInput.id = `hidden-idioma-${iso}`;
        formulario.appendChild(hiddenInput);

        tag.querySelector(".encuesta-tag-remove").addEventListener("click", () => {
            tag.remove();
            const hiddenIdioma = document.getElementById(`hidden-idioma-${iso}`);
            if (hiddenIdioma) hiddenIdioma.remove();
            idiomasSeleccionados.delete(iso);
        });

        contenedorTags.appendChild(tag);
    }
});