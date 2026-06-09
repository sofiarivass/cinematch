document.addEventListener("DOMContentLoaded", function () {
    const input = document.getElementById("input-otra-plataforma");
    if (!input) return;

    const lista = document.getElementById("sugerencias-lista");
    const tagsContainer = document.getElementById("tags-container");
    const hidden = document.getElementById("plataformas-otras-hidden");

    let seleccionados = [];

    // ── Actualizar el input hidden con los seleccionados ──
    function actualizarHidden() {
        hidden.value = seleccionados.map(p => p.id).join(",");
    }

    // ── Crear badge ──
    function agregarTag(provider) {
        if (seleccionados.find(p => p.id === provider.id)) return;
        seleccionados.push(provider);
        actualizarHidden();

        const tag = document.createElement("span");
        tag.className = "encuesta-tag";
        tag.dataset.id = provider.id;
        tag.innerHTML = `${provider.nombre} <button type="button" class="encuesta-tag-remove">×</button>`;

        tag.querySelector(".encuesta-tag-remove").addEventListener("click", function () {
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
    input.addEventListener("input", function () {
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

        filtrados.forEach(function (provider) {
            const li = document.createElement("li");
            li.className = "encuesta-sugerencia-item";
            li.textContent = provider.nombre;
            li.addEventListener("click", function () {
                agregarTag(provider);
            });
            lista.appendChild(li);
        });

        lista.style.display = "block";
    });

    // ── Cerrar sugerencias al hacer click afuera ──
    document.addEventListener("click", function (e) {
        if (!input.contains(e.target) && !lista.contains(e.target)) {
            lista.style.display = "none";
        }
    });
});