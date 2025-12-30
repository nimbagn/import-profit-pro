/**
 * RESPONSIVE ENHANCEMENTS - IMPORT PROFIT PRO
 * Améliorations JavaScript pour le responsive design
 */

(function() {
    'use strict';

    // =========================================================
    // MENU HAMBURGER - TOGGLE SIDEBAR
    // =========================================================
    
    function initSidebarToggle() {
        const sidebar = document.getElementById('sidebar');
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        const menuToggle = document.querySelector('.mobile-menu-toggle');
        
        if (!sidebar || !menuToggle) return;
        
        // Fonction pour ouvrir/fermer le menu
        function toggleSidebar() {
            sidebar.classList.toggle('mobile-open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
            document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
        }
        
        // Bouton hamburger
        menuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            toggleSidebar();
        });
        
        // Overlay pour fermer
        if (sidebarOverlay) {
            sidebarOverlay.addEventListener('click', function() {
                sidebar.classList.remove('mobile-open');
                sidebarOverlay.classList.remove('active');
                document.body.style.overflow = '';
            });
        }
        
        // Fermer au clic sur un lien du menu
        const menuLinks = sidebar.querySelectorAll('.menu-item, .menu-subitem');
        menuLinks.forEach(function(link) {
            link.addEventListener('click', function() {
                if (window.innerWidth <= 1024) {
                    sidebar.classList.remove('mobile-open');
                    if (sidebarOverlay) {
                        sidebarOverlay.classList.remove('active');
                    }
                    document.body.style.overflow = '';
                }
            });
        });
        
        // Fermer avec la touche Escape
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Escape' && sidebar.classList.contains('mobile-open')) {
                sidebar.classList.remove('mobile-open');
                if (sidebarOverlay) {
                    sidebarOverlay.classList.remove('active');
                }
                document.body.style.overflow = '';
            }
        });
    }
    
    // =========================================================
    // TABLEAUX RESPONSIVE - TRANSFORMATION EN CARTES
    // =========================================================
    
    function initResponsiveTables() {
        const tables = document.querySelectorAll('.table-responsive table, .table-mobile-cards');
        
        tables.forEach(function(table) {
            if (window.innerWidth <= 768) {
                // Ajouter data-label aux cellules si pas déjà fait
                const headers = table.querySelectorAll('thead th');
                const rows = table.querySelectorAll('tbody tr');
                
                headers.forEach(function(header, index) {
                    const headerText = header.textContent.trim();
                    rows.forEach(function(row) {
                        const cell = row.querySelectorAll('td')[index];
                        if (cell && !cell.getAttribute('data-label')) {
                            cell.setAttribute('data-label', headerText);
                        }
                    });
                });
            }
        });
    }
    
    // =========================================================
    // FORMULAIRES RESPONSIVE - AMÉLIORATIONS
    // =========================================================
    
    function initResponsiveForms() {
        // Empêcher le zoom sur iOS pour les inputs
        const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="number"], input[type="tel"], input[type="date"], textarea, select');
        
        inputs.forEach(function(input) {
            // S'assurer que la taille de police est au moins 16px pour éviter le zoom
            const computedStyle = window.getComputedStyle(input);
            const fontSize = parseFloat(computedStyle.fontSize);
            
            if (fontSize < 16) {
                input.style.fontSize = '16px';
            }
        });
        
        // Améliorer les selects sur mobile
        const selects = document.querySelectorAll('select');
        selects.forEach(function(select) {
            select.addEventListener('focus', function() {
                if (window.innerWidth <= 768) {
                    this.style.fontSize = '16px';
                }
            });
        });
    }
    
    // =========================================================
    // TOUCH TARGETS - AMÉLIORATION POUR MOBILE
    // =========================================================
    
    function enhanceTouchTargets() {
        if (window.innerWidth <= 768) {
            const touchElements = document.querySelectorAll('a, button, .btn, .menu-item, .menu-subitem, input[type="submit"], input[type="button"]');
            
            touchElements.forEach(function(element) {
                const rect = element.getBoundingClientRect();
                const minSize = 44; // Taille minimale recommandée pour les touch targets
                
                if (rect.width < minSize || rect.height < minSize) {
                    element.style.minWidth = minSize + 'px';
                    element.style.minHeight = minSize + 'px';
                    element.style.padding = '0.75rem 1rem';
                }
            });
        }
    }
    
    // =========================================================
    // SCROLL SMOOTH - AMÉLIORATION UX
    // =========================================================
    
    function initSmoothScroll() {
        // Smooth scroll pour les ancres
        document.querySelectorAll('a[href^="#"]').forEach(function(anchor) {
            anchor.addEventListener('click', function(e) {
                const href = this.getAttribute('href');
                if (href !== '#' && href.length > 1) {
                    const target = document.querySelector(href);
                    if (target) {
                        e.preventDefault();
                        target.scrollIntoView({
                            behavior: 'smooth',
                            block: 'start'
                        });
                    }
                }
            });
        });
    }
    
    // =========================================================
    // ORIENTATION CHANGE - REINITIALISATION
    // =========================================================
    
    function handleOrientationChange() {
        window.addEventListener('orientationchange', function() {
            // Attendre que l'orientation change soit complète
            setTimeout(function() {
                initResponsiveTables();
                enhanceTouchTargets();
                
                // Fermer le menu si ouvert
                const sidebar = document.getElementById('sidebar');
                if (sidebar && sidebar.classList.contains('mobile-open')) {
                    sidebar.classList.remove('mobile-open');
                    const overlay = document.getElementById('sidebarOverlay');
                    if (overlay) {
                        overlay.classList.remove('active');
                    }
                    document.body.style.overflow = '';
                }
            }, 100);
        });
    }
    
    // =========================================================
    // RESIZE HANDLER - OPTIMISATION
    // =========================================================
    
    let resizeTimer;
    function handleResize() {
        window.addEventListener('resize', function() {
            clearTimeout(resizeTimer);
            resizeTimer = setTimeout(function() {
                initResponsiveTables();
                enhanceTouchTargets();
                
                // Fermer le menu sur desktop
                if (window.innerWidth > 1024) {
                    const sidebar = document.getElementById('sidebar');
                    if (sidebar) {
                        sidebar.classList.remove('mobile-open');
                    }
                    const overlay = document.getElementById('sidebarOverlay');
                    if (overlay) {
                        overlay.classList.remove('active');
                    }
                    document.body.style.overflow = '';
                }
            }, 250);
        });
    }
    
    // =========================================================
    // INITIALISATION
    // =========================================================
    
    function init() {
        // Attendre que le DOM soit chargé
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', function() {
                initSidebarToggle();
                initResponsiveTables();
                initResponsiveForms();
                enhanceTouchTargets();
                initSmoothScroll();
                handleOrientationChange();
                handleResize();
            });
        } else {
            // DOM déjà chargé
            initSidebarToggle();
            initResponsiveTables();
            initResponsiveForms();
            enhanceTouchTargets();
            initSmoothScroll();
            handleOrientationChange();
            handleResize();
        }
    }
    
    // Démarrer
    init();
    
    // Exposer la fonction toggleSidebar globalement si nécessaire
    window.toggleSidebar = function() {
        const sidebar = document.getElementById('sidebar');
        const sidebarOverlay = document.getElementById('sidebarOverlay');
        if (sidebar) {
            sidebar.classList.toggle('mobile-open');
            if (sidebarOverlay) {
                sidebarOverlay.classList.toggle('active');
            }
            document.body.style.overflow = sidebar.classList.contains('mobile-open') ? 'hidden' : '';
        }
    };
    
})();

