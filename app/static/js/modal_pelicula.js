document.addEventListener("DOMContentLoaded", function () {
    const modalEl = document.getElementById("modal-info-pelicula");
    const modalContenido = document.getElementById("modal-contenido");

    if (!modalEl || !modalContenido) return;

    modalEl.addEventListener("show.bs.modal", function (e) {
        const trigger = e.relatedTarget;
        if (!trigger) return;

        const id = trigger.dataset.id;
        const tipo = trigger.dataset.tipo || "pelicula"; 

        if (!id) {
            modalContenido.innerHTML =
                "<p class='text-center p-4 text-muted'>No se encontró el ID del contenido.</p>";
            return;
        }

        // spinner de carga mientras se obtiene la información
        modalContenido.innerHTML = `
            <div class="d-flex flex-column justify-content-center align-items-center p-5" style="min-height: 250px;">
                <div class="spinner-border text-light" role="status"></div>
                <span class="mt-4 text-light opacity-50">Cargando...</span>
            </div>`;
            

        // Enrutamiento dinámico según el tipo de contenido
        const url = tipo === "serie"
            ? `/explorar/modal/${id}?tipo=serie`
            : `/pelicula/${id}/modal`;

        fetch(url, { cache: "no-store" })
            .then(r => r.text())
            .then(html => {
                modalContenido.innerHTML = html;

                if (modalEl.dataset.footer === "false") {
                    const footerWrapper = modalContenido.querySelector(".modal-footer-wrapper");
                    if (footerWrapper) footerWrapper.remove();
                }
            })
            .catch(() => {
                modalContenido.innerHTML =
                    "<p class='text-center p-4 text-muted'>Error al cargar la información.</p>";
            });
    });

    // Delegación de eventos para los botones internos del modal
    modalEl.addEventListener("click", function (e) {
        const btn = e.target.closest(".btn-toggle-lista");
        if (!btn) return;

        const lista = btn.dataset.lista;
        const peliculaId = btn.dataset.id;
        const tipo = btn.dataset.tipo;
        const icono = btn.querySelector("i");

        // Soporte completo para todas tus listas mapeadas
        const iconos = {
            matchlist: ["bi-bookmark", "bi-bookmark-fill"],
            favoritos: ["bi-heart", "bi-heart-fill"],
            peliculas_vistas: ["bi-eye", "bi-eye-fill"],
            series_vistas: ["bi-eye", "bi-eye-fill"],
        };

        const generoIds = (btn.dataset.generos || "")
            .split(",")
            .filter(g => g !== "")
            .map(g => parseInt(g));

        fetch("/perfil/lista/toggle", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                lista: lista,
                id: parseInt(peliculaId),
                tipo: tipo,
                titulo: btn.dataset.titulo || "",
                poster: btn.dataset.poster || "",
                puntuacion: parseFloat(btn.dataset.puntuacion) || 0,
                fecha: btn.dataset.fecha || "",
                genero_ids: generoIds,
            }),
        })
        .then(r => r.json())
        .then(data => {
            // Control seguro para evitar crasheos si la lista no está en el mapa
            if (icono && iconos[lista]) {
                const [vacio, lleno] = iconos[lista];
                const agregado = data.accion === "agregado";
                icono.classList.toggle(vacio, !agregado);
                icono.classList.toggle(lleno, agregado);
            }
        })
        .catch(() => alert("Error al actualizar la lista"));
    });
});
