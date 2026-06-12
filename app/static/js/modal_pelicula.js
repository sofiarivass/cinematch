document.addEventListener("DOMContentLoaded", function () {
    const modalEl = document.getElementById("modal-info-pelicula");
    const modalContenido = document.getElementById("modal-contenido");

    // Si la página no tiene el modal, no hacemos nada
    if (!modalEl || !modalContenido) return;

    modalEl.addEventListener("show.bs.modal", function (e) {
        const trigger = e.relatedTarget;

        if (!trigger) return;

        const peliculaId = trigger.dataset.peliculaId;

        if (!peliculaId) {
            modalContenido.innerHTML =
                "<p class='text-center p-4 text-muted'>No se encontró el ID de la película.</p>";
            return;
        }

        modalContenido.innerHTML = `
            <div class="d-flex justify-content-center p-5">
                <div class="spinner-border text-light" role="status"></div>
            </div>`;

        fetch(`/pelicula/${peliculaId}/modal`)
            .then(r => r.text())
            .then(html => {
                modalContenido.innerHTML = html;

                if (modalEl.dataset.footer === "true") {
                    modalContenido.insertAdjacentHTML(
                        "beforeend",
                        `
            <div class="modal-footer justify-content-center">
                <a role="button" data-bs-toggle="modal" data-bs-target="#modal-info-pelicula" data-pelicula-id="{{ pelicula.id }}" class="btn-modal-footer d-flex align-items-center justify-content-center">
                    <i class="bi bi-bookmark icono-modal-footer"></i>
                </a>
                <a role="button" data-bs-toggle="modal" data-bs-target="#modal-info-pelicula" data-pelicula-id="{{ pelicula.id }}" class="btn-modal-footer d-flex align-items-center justify-content-center">
                    <i class="bi bi-heart icono-modal-footer"></i>
                </a>
                <a role="button" data-bs-toggle="modal" data-bs-target="#modal-info-pelicula" data-pelicula-id="{{ pelicula.id }}" class="btn-modal-footer d-flex align-items-center justify-content-center">
                    <i class="bi bi-eye icono-modal-footer"></i>
                </a>
            </div>
            `
                    );
                }
            })
            .catch(() => {
                modalContenido.innerHTML =
                    "<p class='text-center p-4 text-muted'>Error al cargar la información.</p>";
            });
    });
});