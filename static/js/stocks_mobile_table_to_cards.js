/**
 * Script pour convertir automatiquement les tableaux en cartes sur mobile
 * Module Stocks - Optimisé pour les magasiniers
 */

(function() {
  'use strict';
  
  /**
   * Convertit un tableau en cartes mobiles
   */
  function convertTableToCards(table) {
    // Vérifier si déjà converti
    if (table.dataset.converted === 'true') {
      return;
    }
    
    // Vérifier si on est sur mobile
    if (window.innerWidth > 768) {
      return;
    }
    
    const tableId = table.id || 'table-' + Math.random().toString(36).substr(2, 9);
    const thead = table.querySelector('thead');
    const tbody = table.querySelector('tbody');
    
    if (!thead || !tbody) {
      return;
    }
    
    // Récupérer les en-têtes
    const headers = Array.from(thead.querySelectorAll('th')).map(th => ({
      text: th.textContent.trim(),
      className: th.className,
      dataAttr: th.getAttribute('data-mobile-label') || th.textContent.trim()
    }));
    
    // Créer le conteneur de cartes
    const cardsContainer = document.createElement('div');
    cardsContainer.className = 'mobile-cards-view';
    cardsContainer.id = 'cards-' + tableId;
    
    // Parcourir les lignes
    const rows = tbody.querySelectorAll('tr');
    rows.forEach((row, rowIndex) => {
      const cells = row.querySelectorAll('td');
      const card = document.createElement('div');
      card.className = 'mobile-card';
      
      // En-tête de la carte (première colonne généralement)
      const cardHeader = document.createElement('div');
      cardHeader.className = 'mobile-card-header';
      
      const cardTitle = document.createElement('div');
      cardTitle.className = 'mobile-card-title';
      
      // Utiliser la première colonne comme titre
      if (cells.length > 0) {
        const firstCell = cells[0];
        cardTitle.innerHTML = firstCell.innerHTML;
        
        // Chercher un badge dans la ligne (statut, etc.)
        const badge = row.querySelector('.badge-type, .status-badge, .badge-quantity');
        if (badge) {
          const cardBadge = badge.cloneNode(true);
          cardBadge.className = 'mobile-card-badge ' + badge.className;
          cardHeader.appendChild(cardBadge);
        }
      }
      
      cardHeader.appendChild(cardTitle);
      card.appendChild(cardHeader);
      
      // Corps de la carte
      const cardBody = document.createElement('div');
      cardBody.className = 'mobile-card-body';
      
      // Parcourir les autres colonnes
      cells.forEach((cell, cellIndex) => {
        if (cellIndex === 0) return; // Déjà utilisé comme titre
        
        const header = headers[cellIndex];
        if (!header) return;
        
        // Ignorer les colonnes d'actions pour l'instant
        if (cell.classList.contains('actions') || 
            cell.querySelector('a.btn-hl, button.btn-hl')) {
          return;
        }
        
        const cardRow = document.createElement('div');
        cardRow.className = 'mobile-card-row';
        
        const cardLabel = document.createElement('div');
        cardLabel.className = 'mobile-card-label';
        cardLabel.textContent = header.dataAttr;
        
        const cardValue = document.createElement('div');
        cardValue.className = 'mobile-card-value';
        cardValue.innerHTML = cell.innerHTML;
        
        cardRow.appendChild(cardLabel);
        cardRow.appendChild(cardValue);
        cardBody.appendChild(cardRow);
      });
      
      card.appendChild(cardBody);
      
      // Actions de la carte
      const actionsCell = Array.from(cells).find(cell => 
        cell.querySelector('a.btn-hl, button.btn-hl')
      );
      
      if (actionsCell) {
        const cardActions = document.createElement('div');
        cardActions.className = 'mobile-card-actions';
        
        const actionLinks = actionsCell.querySelectorAll('a.btn-hl, button.btn-hl');
        actionLinks.forEach(link => {
          const actionBtn = link.cloneNode(true);
          actionBtn.classList.add('btn-hl-outline');
          cardActions.appendChild(actionBtn);
        });
        
        if (cardActions.children.length > 0) {
          card.appendChild(cardActions);
        }
      }
      
      cardsContainer.appendChild(card);
    });
    
    // Masquer le tableau et afficher les cartes
    table.style.display = 'none';
    table.dataset.converted = 'true';
    
    // Insérer les cartes après le tableau
    table.parentNode.insertBefore(cardsContainer, table.nextSibling);
  }
  
  /**
   * Convertit tous les tableaux de la page
   */
  function convertAllTables() {
    const tables = document.querySelectorAll('.table-hl, .table-responsive-wrapper table, table.dataTable');
    
    tables.forEach(table => {
      if (table.dataset.converted !== 'true') {
        convertTableToCards(table);
      }
    });
  }
  
  /**
   * Gère le redimensionnement de la fenêtre
   */
  function handleResize() {
    const isMobile = window.innerWidth <= 768;
    const cardsViews = document.querySelectorAll('.mobile-cards-view');
    const tables = document.querySelectorAll('.table-hl, .table-responsive-wrapper table');
    
    if (isMobile) {
      // Sur mobile : afficher les cartes, masquer les tableaux
      tables.forEach(table => {
        if (table.dataset.converted !== 'true') {
          convertTableToCards(table);
        }
      });
      cardsViews.forEach(cards => cards.style.display = 'block');
    } else {
      // Sur desktop : afficher les tableaux, masquer les cartes
      tables.forEach(table => {
        table.style.display = '';
        table.dataset.converted = 'false';
      });
      cardsViews.forEach(cards => cards.style.display = 'none');
    }
  }
  
  /**
   * Initialisation
   */
  function init() {
    // Convertir les tableaux au chargement
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', convertAllTables);
    } else {
      convertAllTables();
    }
    
    // Gérer le redimensionnement
    let resizeTimeout;
    window.addEventListener('resize', function() {
      clearTimeout(resizeTimeout);
      resizeTimeout = setTimeout(handleResize, 250);
    });
    
    // Observer les changements DOM (pour les tableaux chargés dynamiquement)
    if (window.MutationObserver) {
      const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
          if (mutation.addedNodes.length > 0) {
            convertAllTables();
          }
        });
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true
      });
    }
  }
  
  // Démarrer
  init();
})();

