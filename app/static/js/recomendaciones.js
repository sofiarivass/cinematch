document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll('.tinder-card');
    const formMatches = document.getElementById('form-matches');
    let currentIndex = 0;

    // 🔥 Cambiamos a un array de objetos para guardar TODA la info del match
    let matchesAceptados = [];

    const urlYaLaVi = formMatches ? formMatches.getAttribute('data-url-yalavi') : '/ya-la-vi';

    if (cards.length > 0) {
        mostrarCard(currentIndex);
    }

    function mostrarCard(index) {
        if (index >= cards.length) {
            // 🚨 Se terminaron: Creamos inputs ocultos para CADA campo de la peli/serie
            if (formMatches) {
                formMatches.innerHTML = '';

                matchesAceptados.forEach(item => {
                    agregarInputOculto('ids', item.id);
                    agregarInputOculto('tipos', item.tipo);
                    agregarInputOculto('titulos', item.titulo);
                    agregarInputOculto('posters', item.poster);
                    agregarInputOculto('puntuaciones', item.puntuacion);
                    agregarInputOculto('fechas', item.fecha);
                });

                formMatches.submit();
            }
            return;
        }

        const card = cards[index];
        card.style.opacity = '1';
        card.style.pointerEvents = 'auto';
        card.style.transform = 'translateX(0) translateY(0) rotate(0deg)';
    }

    // Función auxiliar para no repetir código creando inputs
    function agregarInputOculto(nombre, valor) {
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = nombre;
        input.value = valor || '';
        formMatches.appendChild(input);
    }

    function procesarDecision(esLike, cardIndex) {
        const currentCard = cards[cardIndex];

        currentCard.style.pointerEvents = 'none';

        if (esLike) {
            currentCard.style.transform = 'translateX(120%) rotate(15deg)';
            currentCard.style.opacity = '0';

            // 🔥 Guardamos el objeto completo extrayéndolo de los data-attributes de la tarjeta
            matchesAceptados.push({
                id: currentCard.getAttribute('data-id'),
                tipo: currentCard.getAttribute('data-tipo') || 'pelicula',
                titulo: currentCard.getAttribute('data-titulo') || '',
                poster: currentCard.getAttribute('data-poster') || '',
                puntuacion: currentCard.getAttribute('data-puntuacion') || '0',
                fecha: currentCard.getAttribute('data-fecha') || ''
            });
        } else {
            currentCard.style.transform = 'translateX(-120%) rotate(-15deg)';
            currentCard.style.opacity = '0';
        }

        siguienteCard();
    }

    function siguienteCard() {
        setTimeout(() => {
            currentIndex++;
            mostrarCard(currentIndex);
        }, 400);
    }

    // Eventos (Se quedan igual)
    cards.forEach((card, index) => {
        const btnSi = card.querySelector('.btn-redondo-si');
        const btnNo = card.querySelector('.btn-redondo-no');
        const btnVista = card.querySelector('.btn-vista');

        if (btnSi) btnSi.addEventListener('click', (e) => { e.preventDefault(); procesarDecision(true, index); });
        if (btnNo) btnNo.addEventListener('click', (e) => { e.preventDefault(); procesarDecision(false, index); });

        if (btnVista) {
            btnVista.addEventListener('click', (e) => {
                e.preventDefault();
                const datosItem = {
                    id: card.getAttribute('data-id'),
                    tipo: card.getAttribute('data-tipo'),
                    titulo: card.getAttribute('data-titulo'),
                    poster: card.getAttribute('data-poster'),
                    puntuacion: card.getAttribute('data-puntuacion'),
                    fecha: card.getAttribute('data-fecha')
                };
                card.style.pointerEvents = 'none';
                card.style.transform = 'translateY(-120%) rotate(0deg)';
                card.style.opacity = '0';

                fetch(urlYaLaVi, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(datosItem)
                }).catch(err => console.error(err));

                siguienteCard();
            });
        }
    });
});