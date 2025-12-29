// themes.js
// Gestion dynamique des thèmes personnalisables

let currentTheme = 'hapag-lloyd';
let currentMode = 'light';
let customColors = {};

/**
 * Détermine le mode automatique selon l'heure
 */
function getAutoMode() {
    const hour = new Date().getHours();
    // Mode sombre entre 20h et 7h
    return (hour >= 20 || hour < 7) ? 'dark' : 'light';
}

/**
 * Détecte le mode préféré du système
 */
function getSystemMode() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}

/**
 * Historique des thèmes utilisés
 */
let themeHistory = [];

/**
 * Ajoute un thème à l'historique
 */
function addToHistory(themeName, colorMode) {
    const entry = {
        theme: themeName,
        mode: colorMode,
        timestamp: new Date().toISOString()
    };
    
    // Éviter les doublons consécutifs
    const lastEntry = themeHistory[themeHistory.length - 1];
    if (!lastEntry || lastEntry.theme !== themeName || lastEntry.mode !== colorMode) {
        themeHistory.push(entry);
        // Garder seulement les 10 derniers
        if (themeHistory.length > 10) {
            themeHistory.shift();
        }
        localStorage.setItem('theme_history', JSON.stringify(themeHistory));
    }
}

/**
 * Charge l'historique depuis le localStorage
 */
function loadHistory() {
    const saved = localStorage.getItem('theme_history');
    if (saved) {
        try {
            themeHistory = JSON.parse(saved);
        } catch (e) {
            console.error('Erreur lors du chargement de l\'historique:', e);
        }
    }
}

/**
 * Exporte les préférences de thème
 */
function exportTheme() {
    const exportData = {
        theme_name: currentTheme,
        color_mode: currentMode,
        custom_colors: customColors,
        timestamp: new Date().toISOString(),
        version: '1.0'
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `theme-${currentTheme}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showNotification('Thème exporté avec succès!', 'success');
}

/**
 * Importe un thème depuis un fichier
 */
function importTheme(file) {
    const reader = new FileReader();
    reader.onload = function(e) {
        try {
            const data = JSON.parse(e.target.result);
            
            if (data.theme_name && data.color_mode) {
                currentTheme = data.theme_name;
                currentMode = data.color_mode;
                
                if (data.custom_colors) {
                    customColors = data.custom_colors;
                    localStorage.setItem('custom_colors', JSON.stringify(customColors));
                }
                
                applyTheme(currentTheme, currentMode, true);
                selectThemeOption(currentTheme);
                selectModeOption(currentMode);
                
                showNotification('Thème importé avec succès!', 'success');
            } else {
                showNotification('Format de fichier invalide', 'error');
            }
        } catch (error) {
            console.error('Erreur lors de l\'import:', error);
            showNotification('Erreur lors de l\'import du thème', 'error');
        }
    };
    reader.readAsText(file);
}

/**
 * Applique des paramètres avancés (police, espacement, etc.)
 */
function applyAdvancedSettings(settings) {
    const root = document.documentElement;
    
    if (settings.fontSize) {
        root.style.setProperty('--base-font-size', settings.fontSize + 'px');
    }
    
    if (settings.spacing) {
        root.style.setProperty('--base-spacing', settings.spacing + 'px');
    }
    
    if (settings.borderRadius) {
        root.style.setProperty('--base-radius', settings.borderRadius + 'px');
    }
    
    if (settings.fontFamily) {
        root.style.setProperty('--font-family', settings.fontFamily);
    }
    
    localStorage.setItem('advanced_settings', JSON.stringify(settings));
}

/**
 * Applique un thème et un mode de couleur au document
 */
function applyTheme(themeName, colorMode, animate = true) {
    const root = document.documentElement;
    const body = document.body;
    
    // Gérer le mode automatique
    if (colorMode === 'auto') {
        colorMode = getAutoMode();
    }
    
    // Animation de transition
    if (animate) {
        body.classList.add('theme-changing');
        setTimeout(() => {
            body.classList.remove('theme-changing');
        }, 400);
    }
    
    // Appliquer le thème
    root.setAttribute('data-theme', themeName);
    root.setAttribute('data-color-mode', colorMode);
    
    // Appliquer les couleurs personnalisées si le thème est "custom"
    if (themeName === 'custom' && Object.keys(customColors).length > 0) {
        Object.entries(customColors).forEach(([key, value]) => {
            root.style.setProperty(`--${key}`, value);
        });
    }
    
    // Mettre à jour les variables globales
    currentTheme = themeName;
    currentMode = colorMode;
    
    // Stocker dans le localStorage pour persistance
    localStorage.setItem('theme_name', themeName);
    localStorage.setItem('color_mode', colorMode);
    if (themeName === 'custom') {
        localStorage.setItem('custom_colors', JSON.stringify(customColors));
    }
}

/**
 * Charge les préférences depuis le serveur
 */
async function loadPreferences() {
    try {
        const response = await fetch('/themes/api/preferences');
        if (response.ok) {
            const data = await response.json();
            applyTheme(data.theme_name, data.color_mode);
            return data;
        }
    } catch (error) {
        console.error('Erreur lors du chargement des préférences:', error);
    }
    return null;
}

/**
 * Sauvegarde les préférences sur le serveur
 */
async function savePreferences(themeName, colorMode) {
    try {
        const response = await fetch('/themes/api/preferences', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                theme_name: themeName,
                color_mode: colorMode
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            showNotification('Préférences enregistrées avec succès!', 'success');
            return data;
        } else {
            const error = await response.json();
            showNotification('Erreur lors de l\'enregistrement: ' + error.error, 'error');
            return null;
        }
    } catch (error) {
        console.error('Erreur lors de la sauvegarde:', error);
        showNotification('Erreur de connexion lors de la sauvegarde', 'error');
        return null;
    }
}

/**
 * Applique un thème temporairement (sans sauvegarder)
 */
async function applyTemporaryTheme(themeName, colorMode) {
    try {
        const response = await fetch('/themes/api/apply', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                theme_name: themeName,
                color_mode: colorMode
            })
        });
        
        if (response.ok) {
            applyTheme(themeName, colorMode, true);
        }
    } catch (error) {
        console.error('Erreur lors de l\'application temporaire:', error);
        // Fallback : appliquer localement
        applyTheme(themeName, colorMode, true);
    }
}

/**
 * Définit une couleur personnalisée pour le thème custom
 */
function setCustomColor(colorName, colorValue) {
    customColors[colorName] = colorValue;
    if (currentTheme === 'custom') {
        document.documentElement.style.setProperty(`--${colorName}`, colorValue);
        localStorage.setItem('custom_colors', JSON.stringify(customColors));
    }
}

/**
 * Charge les couleurs personnalisées
 */
function loadCustomColors() {
    const saved = localStorage.getItem('custom_colors');
    if (saved) {
        try {
            customColors = JSON.parse(saved);
            if (currentTheme === 'custom') {
                Object.entries(customColors).forEach(([key, value]) => {
                    document.documentElement.style.setProperty(`--${key}`, value);
                });
            }
        } catch (e) {
            console.error('Erreur lors du chargement des couleurs personnalisées:', e);
        }
    }
}

/**
 * Sélectionne une option de thème visuellement
 */
function selectThemeOption(themeName) {
    // Retirer la sélection de tous les thèmes
    document.querySelectorAll('.theme-preview').forEach(preview => {
        preview.classList.remove('selected');
    });
    
    // Ajouter la sélection au thème choisi
    const selectedPreview = document.querySelector(`.theme-preview[data-theme="${themeName}"]`);
    if (selectedPreview) {
        selectedPreview.classList.add('selected');
    }
}

/**
 * Sélectionne une option de mode visuellement
 */
function selectModeOption(mode) {
    // Retirer la sélection de tous les modes
    document.querySelectorAll('.mode-option').forEach(option => {
        option.classList.remove('selected');
    });
    
    // Ajouter la sélection au mode choisi
    const selectedMode = document.querySelector(`.mode-option[data-mode="${mode}"]`);
    if (selectedMode) {
        selectedMode.classList.add('selected');
    }
}

/**
 * Affiche une notification
 */
function showNotification(message, type = 'info') {
    // Créer l'élément de notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 1rem 1.5rem;
        background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#3b82f6'};
        color: white;
        border-radius: 8px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
        z-index: 10000;
        animation: slideIn 0.3s ease;
    `;
    notification.textContent = message;
    
    // Ajouter au DOM
    document.body.appendChild(notification);
    
    // Retirer après 3 secondes
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Initialisation au chargement de la page
document.addEventListener('DOMContentLoaded', function() {
    // Charger les couleurs personnalisées si elles existent
    const savedCustomColors = localStorage.getItem('custom_colors');
    if (savedCustomColors) {
        try {
            customColors = JSON.parse(savedCustomColors);
        } catch (e) {
            console.error('Erreur lors du chargement des couleurs personnalisées:', e);
        }
    }
    
    // Charger les préférences depuis le serveur
    loadPreferences().then(data => {
        if (data) {
            currentTheme = data.theme_name;
            currentMode = data.color_mode;
            selectThemeOption(currentTheme);
            selectModeOption(currentMode);
        } else {
            // Utiliser les valeurs du localStorage en fallback
            const savedTheme = localStorage.getItem('theme_name') || 'hapag-lloyd';
            const savedMode = localStorage.getItem('color_mode') || 'light';
            applyTheme(savedTheme, savedMode, false);
            selectThemeOption(savedTheme);
            selectModeOption(savedMode);
        }
    });
    
    // Charger l'historique
    loadHistory();
    
    // Vérifier le mode automatique toutes les minutes
    if (currentMode === 'auto') {
        setInterval(() => {
            const autoMode = getAutoMode();
            const root = document.documentElement;
            const currentAppliedMode = root.getAttribute('data-color-mode');
            if (currentAppliedMode !== autoMode) {
                applyTheme(currentTheme, 'auto', false);
            }
        }, 60000); // Vérifier toutes les minutes
    }
    
    // Vérifier le mode système
    if (currentMode === 'system') {
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        mediaQuery.addEventListener('change', (e) => {
            applyTheme(currentTheme, 'system', false);
        });
    }
    
    // Ajouter au changement de thème
    const originalApplyTheme = applyTheme;
    applyTheme = function(themeName, colorMode, animate) {
        originalApplyTheme(themeName, colorMode, animate);
        addToHistory(themeName, colorMode);
    };
    
    // Gestionnaires d'événements pour les sélecteurs de thème
    document.querySelectorAll('.theme-preview').forEach(preview => {
        preview.addEventListener('click', function() {
            const themeName = this.getAttribute('data-theme');
            currentTheme = themeName;
            applyTemporaryTheme(themeName, currentMode);
            selectThemeOption(themeName);
        });
    });
    
    // Gestionnaires d'événements pour les sélecteurs de mode
    document.querySelectorAll('.mode-option').forEach(option => {
        option.addEventListener('click', function() {
            const mode = this.getAttribute('data-mode');
            currentMode = mode;
            applyTemporaryTheme(currentTheme, mode);
            selectModeOption(mode);
        });
    });
    
    // Bouton de sauvegarde
    const saveBtn = document.getElementById('save-theme-btn');
    if (saveBtn) {
        saveBtn.addEventListener('click', async function() {
            this.disabled = true;
            this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enregistrement...';
            
            const result = await savePreferences(currentTheme, currentMode);
            
            this.disabled = false;
            this.innerHTML = '<i class="fas fa-save"></i> Enregistrer les Préférences';
        });
    }
    
    // Bouton de réinitialisation
    const resetBtn = document.getElementById('reset-theme-btn');
    if (resetBtn) {
        resetBtn.addEventListener('click', function() {
            currentTheme = 'hapag-lloyd';
            currentMode = 'light';
            applyTemporaryTheme(currentTheme, currentMode);
            selectThemeOption(currentTheme);
            selectModeOption(currentMode);
        });
    }
});

// Ajouter les animations CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Raccourcis clavier globaux
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + Shift + T : Ouvrir les paramètres de thème
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
        e.preventDefault();
        if (window.location.pathname !== '/themes/settings') {
            window.location.href = '/themes/settings';
        }
    }
    
    // Ctrl/Cmd + Shift + L : Basculer entre clair et sombre
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'L') {
        e.preventDefault();
        const newMode = currentMode === 'light' ? 'dark' : (currentMode === 'dark' ? 'light' : 'light');
        currentMode = newMode;
        applyTemporaryTheme(currentTheme, newMode);
        if (typeof selectModeOption === 'function') {
            selectModeOption(newMode);
        }
    }
    
    // Ctrl/Cmd + Shift + A : Activer le mode automatique
    if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'A') {
        e.preventDefault();
        currentMode = 'auto';
        applyTemporaryTheme(currentTheme, 'auto');
        if (typeof selectModeOption === 'function') {
            selectModeOption('auto');
        }
    }
});

