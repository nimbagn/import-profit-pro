// Fichier: static/js/forecast_mobile_table_to_cards.js

document.addEventListener('DOMContentLoaded', () => {
    const applyTableToCards = () => {
        // Appliquer la transformation uniquement sur les écrans mobiles
        if (window.innerWidth <= 768) {
            // Traiter les tableaux .table-hl
            document.querySelectorAll('.table-hl table, .editable-table').forEach(table => {
                // Vérifier si la table a déjà été traitée
                if (table.dataset.mobileTransformed === 'true') {
                    return;
                }

                const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());

                table.querySelectorAll('tbody tr').forEach(row => {
                    Array.from(row.querySelectorAll('td')).forEach((td, index) => {
                        if (headers[index]) {
                            td.setAttribute('data-label', headers[index]);
                        }
                    });
                });
                table.dataset.mobileTransformed = 'true';
            });
        } else {
            // Réinitialiser si l'écran est plus grand
            document.querySelectorAll('.table-hl table, .editable-table').forEach(table => {
                if (table.dataset.mobileTransformed === 'true') {
                    table.querySelectorAll('tbody td').forEach(td => {
                        td.removeAttribute('data-label');
                    });
                    table.dataset.mobileTransformed = 'false';
                }
            });
        }
    };

    // Appliquer au chargement initial
    applyTableToCards();

    // Observer les changements dans le DOM pour les tableaux chargés dynamiquement
    const observer = new MutationObserver(mutations => {
        mutations.forEach(mutation => {
            if (mutation.addedNodes.length) {
                mutation.addedNodes.forEach(node => {
                    if (node.nodeType === 1) {
                        // Vérifier si le nœud ou ses enfants contiennent des tableaux
                        if (node.querySelector && (node.querySelector('.table-hl table') || node.querySelector('.editable-table'))) {
                            applyTableToCards();
                        }
                    }
                });
            }
        });
    });

    // Commencer l'observation du corps du document
    observer.observe(document.body, { childList: true, subtree: true });

    // Réappliquer lors du redimensionnement de la fenêtre
    let resizeTimer;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(applyTableToCards, 200);
    });
});

