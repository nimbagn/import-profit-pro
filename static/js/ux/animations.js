// animations.js
// Gestion des animations avancées et interactions UX

// =========================================================
// UTILITAIRES D'ANIMATION
// =========================================================

/**
 * Animer un élément avec fade in
 */
function fadeIn(element, duration = 300) {
    if (!element) return;
    element.style.opacity = '0';
    element.style.display = 'block';
    element.style.transition = `opacity ${duration}ms ease`;
    requestAnimationFrame(() => {
        element.style.opacity = '1';
    });
}

/**
 * Animer un élément avec fade out
 */
function fadeOut(element, duration = 300, callback) {
    if (!element) return;
    element.style.transition = `opacity ${duration}ms ease`;
    element.style.opacity = '0';
    setTimeout(() => {
        if (element.style.opacity === '0') {
            element.style.display = 'none';
        }
        if (callback) callback();
    }, duration);
}

/**
 * Animer un élément avec slide
 */
function slideIn(element, direction = 'up', duration = 400) {
    if (!element) return;
    const directions = {
        'up': 'translateY(30px)',
        'down': 'translateY(-30px)',
        'left': 'translateX(-30px)',
        'right': 'translateX(30px)'
    };
    
    element.style.opacity = '0';
    element.style.transform = directions[direction] || directions['up'];
    element.style.transition = `all ${duration}ms ease-out`;
    element.style.display = 'block';
    
    requestAnimationFrame(() => {
        element.style.opacity = '1';
        element.style.transform = 'translate(0, 0)';
    });
}

/**
 * Animer plusieurs éléments avec stagger
 */
function staggerAnimation(elements, animationClass, delay = 100) {
    if (!elements || elements.length === 0) return;
    
    elements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add(animationClass);
        }, index * delay);
    });
}

/**
 * Créer un effet de ripple sur un bouton
 */
function createRipple(event) {
    const button = event.currentTarget;
    const circle = document.createElement('span');
    const diameter = Math.max(button.clientWidth, button.clientHeight);
    const radius = diameter / 2;
    
    const rect = button.getBoundingClientRect();
    circle.style.width = circle.style.height = `${diameter}px`;
    circle.style.left = `${event.clientX - rect.left - radius}px`;
    circle.style.top = `${event.clientY - rect.top - radius}px`;
    circle.classList.add('ripple');
    
    const ripple = button.getElementsByClassName('ripple')[0];
    if (ripple) {
        ripple.remove();
    }
    
    button.appendChild(circle);
}

// =========================================================
// DRAG & DROP
// =========================================================

/**
 * Initialiser le drag & drop pour un élément
 */
function initDragDrop(dragElement, dropZone, onDrop) {
    if (!dragElement || !dropZone) return;
    
    dragElement.draggable = true;
    dragElement.classList.add('draggable');
    
    dragElement.addEventListener('dragstart', (e) => {
        dragElement.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', dragElement.outerHTML);
        e.dataTransfer.setData('text/plain', dragElement.id || '');
    });
    
    dragElement.addEventListener('dragend', () => {
        dragElement.classList.remove('dragging');
    });
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        if (onDrop) {
            onDrop(dragElement, dropZone, e);
        }
    });
}

/**
 * Initialiser une zone de drop pour fichiers
 */
function initFileDropZone(dropZone, inputElement, onFilesSelected) {
    if (!dropZone || !inputElement) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('dragover');
        }, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('dragover');
        }, false);
    });
    
    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            inputElement.files = files;
            if (onFilesSelected) {
                onFilesSelected(files);
            }
            // Déclencher l'événement change
            const event = new Event('change', { bubbles: true });
            inputElement.dispatchEvent(event);
        }
    }, false);
    
    dropZone.addEventListener('click', () => {
        inputElement.click();
    });
}

// =========================================================
// OBSERVATEUR D'INTERSECTION (Lazy loading)
// =========================================================

/**
 * Observer pour animer les éléments quand ils entrent dans le viewport
 */
function initIntersectionObserver(selector = '.animate-on-scroll', animationClass = 'animate-fade-in') {
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add(animationClass);
                observer.unobserve(entry.target);
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    document.querySelectorAll(selector).forEach(element => {
        observer.observe(element);
    });
}

// =========================================================
// NOTIFICATIONS ANIMÉES
// =========================================================

/**
 * Afficher une notification animée
 */
function showNotification(message, type = 'info', duration = 3000) {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${getNotificationIcon(type)}"></i>
            <span>${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    const container = document.getElementById('notification-container') || createNotificationContainer();
    container.appendChild(notification);
    
    // Animer l'entrée
    requestAnimationFrame(() => {
        notification.classList.add('animate-slide-right');
    });
    
    // Auto-suppression
    if (duration > 0) {
        setTimeout(() => {
            notification.classList.add('hiding');
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, duration);
    }
}

function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

function createNotificationContainer() {
    const container = document.createElement('div');
    container.id = 'notification-container';
    container.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        display: flex;
        flex-direction: column;
        gap: 10px;
    `;
    document.body.appendChild(container);
    return container;
}

// =========================================================
// INITIALISATION AU CHARGEMENT
// =========================================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialiser l'observer d'intersection
    initIntersectionObserver();
    
    // Ajouter les effets ripple aux boutons
    document.querySelectorAll('.btn-ripple').forEach(button => {
        button.addEventListener('click', createRipple);
    });
    
    // Initialiser les zones de drop pour fichiers
    document.querySelectorAll('.drag-drop-zone').forEach(zone => {
        const input = zone.querySelector('input[type="file"]');
        if (input) {
            initFileDropZone(zone, input, (files) => {
                showNotification(`${files.length} fichier(s) sélectionné(s)`, 'success');
            });
        }
    });
});

// Exporter les fonctions pour utilisation globale
window.fadeIn = fadeIn;
window.fadeOut = fadeOut;
window.slideIn = slideIn;
window.staggerAnimation = staggerAnimation;
window.initDragDrop = initDragDrop;
window.initFileDropZone = initFileDropZone;
window.showNotification = showNotification;

