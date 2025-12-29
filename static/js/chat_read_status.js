// chat_read_status.js
// Gestion des marqueurs de lecture en temps réel

class ChatReadStatus {
    constructor(roomId, currentUserId) {
        this.roomId = roomId;
        this.currentUserId = currentUserId;
        this.updateInterval = null;
    }
    
    start() {
        // Mettre à jour les statuts de lecture toutes les 5 secondes
        this.updateInterval = setInterval(() => {
            this.updateReadStatuses();
        }, 5000);
        
        // Mettre à jour immédiatement
        this.updateReadStatuses();
    }
    
    stop() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    async updateReadStatuses() {
        try {
            // Récupérer les messages de l'utilisateur actuel dans cette room
            const myMessages = document.querySelectorAll(
                `.chat-message.own[data-message-id]`
            );
            
            if (myMessages.length === 0) return;
            
            const messageIds = Array.from(myMessages).map(msg => 
                parseInt(msg.getAttribute('data-message-id'))
            );
            
            const response = await fetch(`/chat/api/rooms/${this.roomId}/read-status`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message_ids: messageIds })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateUI(data.read_statuses);
            }
        } catch (error) {
            console.error('Erreur lors de la mise à jour des statuts de lecture:', error);
        }
    }
    
    updateUI(readStatuses) {
        for (const [messageId, status] of Object.entries(readStatuses)) {
            const statusElement = document.getElementById(`read-status-${messageId}`);
            if (!statusElement) continue;
            
            const readCount = status.read_count || 0;
            const totalMembers = status.total_members || 1;
            
            // Mettre à jour l'icône
            if (readCount >= totalMembers - 1) {
                // Lu par tous (sauf l'expéditeur)
                statusElement.innerHTML = '<i class="fas fa-check-double" style="color: #10b981;" title="Lu par tous"></i>';
            } else if (readCount > 0) {
                // Lu par certains
                statusElement.innerHTML = `<i class="fas fa-check" style="color: #7a8a9a;" title="Lu par ${readCount} personne(s)"></i>`;
            } else {
                // Non lu
                statusElement.innerHTML = '<i class="far fa-check" style="color: #d1d5db;" title="Non lu"></i>';
            }
        }
    }
}

