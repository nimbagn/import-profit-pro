// search.js
// Gestion de la recherche globale

let searchTimeout;
let suggestionTimeout;
let currentPage = 0;
const resultsPerPage = 20;

document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('searchInput');
    const searchClear = document.getElementById('searchClear');
    const searchResults = document.getElementById('searchResults');
    const searchSuggestions = document.getElementById('searchSuggestions');
    const moduleFilters = document.getElementById('moduleFilters');
    const typeFilters = document.getElementById('typeFilters');
    
    if (!searchInput) return;
    
    // Recherche avec debounce
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        if (query.length > 0) {
            searchClear.classList.add('visible');
            
            // Afficher les suggestions si la requête fait au moins 2 caractères
            if (query.length >= 2) {
                clearTimeout(suggestionTimeout);
                suggestionTimeout = setTimeout(() => {
                    loadSuggestions(query);
                }, 200);
            } else {
                hideSuggestions();
            }
        } else {
            searchClear.classList.remove('visible');
            hideSuggestions();
            showEmptyState();
            return;
        }
        
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            performSearch(query, 0);
            hideSuggestions();
        }, 500);
    });
    
    // Masquer les suggestions quand on clique ailleurs
    document.addEventListener('click', function(e) {
        if (searchSuggestions && !searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
            hideSuggestions();
        }
    });
    
    // Recherche avec Enter
    searchInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            clearTimeout(searchTimeout);
            performSearch(this.value.trim(), 0);
        }
    });
    
    // Bouton clear
    searchClear.addEventListener('click', function() {
        searchInput.value = '';
        searchClear.classList.remove('visible');
        showEmptyState();
    });
    
    // Filtres
    [moduleFilters, typeFilters].forEach(container => {
        if (container) {
            container.addEventListener('change', function() {
                const query = searchInput.value.trim();
                if (query.length > 0) {
                    performSearch(query, 0);
                }
            });
        }
    });
});

function getActiveFilters() {
    const modules = Array.from(document.querySelectorAll('#moduleFilters input[type="checkbox"]:checked'))
        .map(cb => cb.value);
    const types = Array.from(document.querySelectorAll('#typeFilters input[type="checkbox"]:checked'))
        .map(cb => cb.value);
    
    return { modules, types };
}

function performSearch(query, offset = 0) {
    if (!query || query.length < 2) {
        showEmptyState();
        return;
    }
    
    const { modules, types } = getActiveFilters();
    const resultsContainer = document.getElementById('searchResults');
    
    // Afficher le loading
    resultsContainer.innerHTML = `
        <div class="loading">
            <i class="fas fa-spinner"></i>
            <p>Recherche en cours...</p>
        </div>
    `;
    
    // Requête API
    fetch('/search/api/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            query: query,
            modules: modules,
            entity_types: types,
            limit: resultsPerPage,
            offset: offset
        })
    })
    .then(response => response.json())
    .then(data => {
        displayResults(data);
        currentPage = Math.floor(offset / resultsPerPage);
    })
    .catch(error => {
        console.error('Erreur de recherche:', error);
        resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-exclamation-triangle"></i>
                <p>Erreur lors de la recherche. Veuillez réessayer.</p>
                <p class="text-muted" style="margin-top: 0.5rem; font-size: 0.9rem;">${error.message || 'Erreur réseau'}</p>
            </div>
        `;
    });
}

function displayResults(data) {
    const resultsContainer = document.getElementById('searchResults');
    
    if (!data.results || data.results.length === 0) {
        resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-search"></i>
                <p>Aucun résultat trouvé pour "${escapeHtml(data.query)}"</p>
                <p class="text-muted mt-2">Essayez avec d'autres mots-clés ou modifiez les filtres</p>
            </div>
        `;
        return;
    }
    
    // Gérer les erreurs
    if (data.error) {
        resultsContainer.innerHTML = `
            <div class="no-results">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${escapeHtml(data.error)}</p>
            </div>
        `;
        return;
    }
    
    let html = `
        <div class="results-header">
            <div class="results-count">
                <strong>${data.total.toLocaleString('fr-FR')}</strong> résultat${data.total > 1 ? 's' : ''} trouvé${data.total > 1 ? 's' : ''} pour "${escapeHtml(data.query)}"
            </div>
            ${data.has_more ? '<div style="color: var(--color-text-secondary); font-size: 0.9rem;"><i class="fas fa-info-circle me-1"></i>Plus de résultats disponibles</div>' : ''}
        </div>
    `;
    
    data.results.forEach((result, index) => {
        const moduleBadge = getModuleBadge(result.module);
        const typeIcon = getTypeIcon(result.entity_type);
        const scoreBadge = result.score > 5 ? `<span style="background: var(--color-success); color: white; padding: 0.25rem 0.5rem; border-radius: 8px; font-size: 0.75rem; margin-left: 0.5rem;">Pertinent</span>` : '';
        
        html += `
            <div class="result-item" 
                 data-url="${escapeHtml(result.url || '#')}" 
                 data-index="${index}"
                 onclick="handleResultClick('${escapeHtml(result.url || '#')}')"
                 onmouseenter="highlightResult(${index})"
                 style="opacity: 0; transform: translateY(20px);">
                <div class="result-header">
                    <h3 class="result-title">
                        <i class="${typeIcon} me-2"></i>${highlightQuery(result.title, data.query)}${scoreBadge}
                    </h3>
                    <span class="result-badge">${moduleBadge}</span>
                </div>
                <div class="result-content">
                    ${highlightQuery(result.content || '', data.query)}
                </div>
                <div class="result-meta">
                    <div class="result-meta-item">
                        <i class="fas fa-folder"></i>
                        <span>${escapeHtml(result.module)}</span>
                    </div>
                    <div class="result-meta-item">
                        <i class="fas fa-tag"></i>
                        <span>${escapeHtml(result.entity_type)}</span>
                    </div>
                    ${result.created_at ? `
                    <div class="result-meta-item">
                        <i class="fas fa-calendar"></i>
                        <span>${formatDate(result.created_at)}</span>
                    </div>
                    ` : ''}
                    ${result.metadata && Object.keys(result.metadata).length > 0 ? `
                    <div class="result-meta-item">
                        <i class="fas fa-info-circle"></i>
                        <span>Détails disponibles</span>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    });
    
    // Pagination
    const totalPages = Math.ceil(data.total / resultsPerPage);
    if (totalPages > 1) {
        html += generatePagination(currentPage, totalPages, data.query);
    }
    
    resultsContainer.innerHTML = html;
    
    // Ajouter les animations avec délai
    animateResults();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function handleResultClick(url) {
    if (url && url !== '#') {
        // Ajouter un effet de transition
        event.target.closest('.result-item').style.transform = 'scale(0.98)';
        setTimeout(() => {
            window.location.href = url;
        }, 150);
    }
}

function highlightResult(index) {
    const item = document.querySelector(`.result-item[data-index="${index}"]`);
    if (item) {
        item.style.transition = 'all 0.2s ease';
    }
}

function highlightQuery(text, query) {
    if (!text || !query) return escapeHtml(text || '');
    // Échapper le HTML d'abord
    const escapedText = escapeHtml(text);
    // Échapper les caractères spéciaux pour la regex
    const escapedQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(${escapedQuery})`, 'gi');
    return escapedText.replace(regex, '<mark style="background: linear-gradient(135deg, var(--color-primary-light) 0%, var(--color-primary) 100%); color: white; padding: 0.15rem 0.3rem; border-radius: 4px; font-weight: 600;">$1</mark>');
}

function getModuleBadge(module) {
    const badges = {
        'articles': 'Articles',
        'simulations': 'Simulations',
        'forecast': 'Prévisions',
        'stocks': 'Stocks',
        'flotte': 'Flotte',
        'chat': 'Chat'
    };
    return badges[module] || module;
}

function getTypeIcon(entityType) {
    const icons = {
        'article': 'fas fa-box',
        'simulation': 'fas fa-calculator',
        'forecast': 'fas fa-chart-line',
        'stock_item': 'fas fa-warehouse',
        'stock_movement': 'fas fa-exchange-alt',
        'vehicle': 'fas fa-truck',
        'chat_message': 'fas fa-comment'
    };
    return icons[entityType] || 'fas fa-file';
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function generatePagination(currentPage, totalPages, query) {
    let html = '<div class="pagination">';
    
    // Bouton précédent
    html += `
        <button 
            onclick="performSearch('${query}', ${(currentPage - 1) * resultsPerPage})"
            ${currentPage === 0 ? 'disabled' : ''}
        >
            <i class="fas fa-chevron-left"></i> Précédent
        </button>
    `;
    
    // Numéros de page
    const startPage = Math.max(0, currentPage - 2);
    const endPage = Math.min(totalPages - 1, currentPage + 2);
    
    for (let i = startPage; i <= endPage; i++) {
        html += `
            <button 
                class="${i === currentPage ? 'active' : ''}"
                onclick="performSearch('${query}', ${i * resultsPerPage})"
            >
                ${i + 1}
            </button>
        `;
    }
    
    // Bouton suivant
    html += `
        <button 
            onclick="performSearch('${query}', ${(currentPage + 1) * resultsPerPage})"
            ${currentPage >= totalPages - 1 ? 'disabled' : ''}
        >
            Suivant <i class="fas fa-chevron-right"></i>
        </button>
    `;
    
    html += '</div>';
    return html;
}

function showEmptyState() {
    const resultsContainer = document.getElementById('searchResults');
    resultsContainer.innerHTML = `
        <div class="no-results">
            <i class="fas fa-search"></i>
            <p>Tapez votre recherche ci-dessus pour commencer</p>
        </div>
    `;
}

function animateResults() {
    const items = document.querySelectorAll('.result-item');
    items.forEach((item, index) => {
        setTimeout(() => {
            item.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';
            item.style.opacity = '1';
            item.style.transform = 'translateY(0)';
        }, index * 80);
    });
}

function loadSuggestions(query) {
    const suggestionsContainer = document.getElementById('searchSuggestions');
    if (!suggestionsContainer) return;
    
    fetch(`/search/api/quick?q=${encodeURIComponent(query)}&limit=5`)
        .then(response => response.json())
        .then(data => {
            if (data.suggestions && data.suggestions.length > 0) {
                displaySuggestions(data.suggestions);
            } else {
                hideSuggestions();
            }
        })
        .catch(error => {
            console.error('Erreur lors du chargement des suggestions:', error);
            hideSuggestions();
        });
}

function displaySuggestions(suggestions) {
    const suggestionsContainer = document.getElementById('searchSuggestions');
    if (!suggestionsContainer) return;
    
    if (!suggestions || suggestions.length === 0) {
        hideSuggestions();
        return;
    }
    
    const query = document.getElementById('searchInput').value;
    let html = '';
    suggestions.forEach((suggestion, index) => {
        const icon = suggestion.icon || getTypeIcon(suggestion.entity_type);
        const badge = getModuleBadge(suggestion.module);
        
        html += `
            <div class="suggestion-item" 
                 onclick="selectSuggestion('${suggestion.title.replace(/'/g, "\\'")}')"
                 style="opacity: 0; transform: translateX(-10px);"
                 data-index="${index}">
                <i class="${icon}"></i>
                <span>${highlightQuery(suggestion.title, query)}</span>
                <span class="suggestion-badge">${badge}</span>
            </div>
        `;
    });
    
    suggestionsContainer.innerHTML = html;
    suggestionsContainer.classList.add('visible');
    
    // Animer les suggestions
    setTimeout(() => {
        suggestions.forEach((_, index) => {
            const item = suggestionsContainer.querySelector(`[data-index="${index}"]`);
            if (item) {
                setTimeout(() => {
                    item.style.transition = 'all 0.3s ease';
                    item.style.opacity = '1';
                    item.style.transform = 'translateX(0)';
                }, index * 50);
            }
        });
    }, 10);
}

function selectSuggestion(text) {
    const searchInput = document.getElementById('searchInput');
    searchInput.value = text;
    searchInput.focus();
    hideSuggestions();
    performSearch(text, 0);
}

function hideSuggestions() {
    const suggestionsContainer = document.getElementById('searchSuggestions');
    if (suggestionsContainer) {
        suggestionsContainer.classList.remove('visible');
    }
}

