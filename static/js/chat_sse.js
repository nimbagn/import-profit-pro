// chat_sse.js
// Client JavaScript pour Server-Sent Events du chat

class ChatSSE {
    constructor(roomId, onMessage, onError) {
        this.roomId = roomId;
        this.onMessage = onMessage;
        this.onError = onError;
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 1000; // 1 seconde
    }
    
    connect() {
        if (this.eventSource) {
            this.disconnect();
        }
        
        const url = `/chat/api/stream/${this.roomId}`;
        this.eventSource = new EventSource(url);
        
        this.eventSource.onopen = () => {
            console.log('✅ Connexion SSE établie');
            this.reconnectAttempts = 0;
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'connected') {
                    console.log('✅ Connecté au stream SSE');
                } else if (data.type === 'new_message') {
                    // Vérifier si le message n'existe pas déjà avant de l'afficher
                    // On affiche tous les messages, même ceux de l'utilisateur actuel
                    // car ils peuvent être envoyés depuis un autre onglet/navigateur
                    console.log('📨 Nouveau message reçu:', data);
                    
                    // Notification si le message n'est pas de l'utilisateur actuel
                    if (data.sender_id !== parseInt(window.currentUserId || 0)) {
                        showChatNotification(
                            data.sender_name || 'Nouveau message',
                            data.content ? (data.content.length > 50 ? data.content.substring(0, 50) + '...' : data.content) : 'Nouveau message',
                            null
                        );
                    }
                    
                    this.onMessage(data);
                } else if (data.type === 'heartbeat') {
                    // Heartbeat pour maintenir la connexion
                    console.log('💓 Heartbeat SSE');
                } else if (data.type === 'error') {
                    console.error('❌ Erreur SSE:', data.message);
                    if (this.onError) {
                        this.onError(data);
                    }
                }
            } catch (e) {
                console.error('Erreur parsing SSE:', e);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('❌ Erreur SSE:', error);
            
            if (this.eventSource.readyState === EventSource.CLOSED) {
                // Tentative de reconnexion
                this.reconnect();
            }
        };
    }
    
    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ Nombre maximum de tentatives de reconnexion atteint');
            if (this.onError) {
                this.onError({ message: 'Impossible de se reconnecter au serveur' });
            }
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`🔄 Tentative de reconnexion ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay * this.reconnectAttempts);
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

class ChatRoomsSSE {
    constructor(onRoomUpdate, onError) {
        this.onRoomUpdate = onRoomUpdate;
        this.onError = onError;
        this.eventSource = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 10;
        this.reconnectDelay = 2000; // 2 secondes
    }
    
    connect() {
        if (this.eventSource) {
            this.disconnect();
        }
        
        const url = `/chat/api/stream/rooms`;
        this.eventSource = new EventSource(url);
        
        this.eventSource.onopen = () => {
            console.log('✅ Connexion SSE rooms établie');
            this.reconnectAttempts = 0;
        };
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'connected') {
                    console.log('✅ Connecté au stream SSE rooms');
                } else if (data.type === 'room_update') {
                    this.onRoomUpdate(data);
                } else if (data.type === 'heartbeat') {
                    // Heartbeat silencieux
                } else if (data.type === 'error') {
                    console.error('❌ Erreur SSE rooms:', data.message);
                    if (this.onError) {
                        this.onError(data);
                    }
                }
            } catch (e) {
                console.error('Erreur parsing SSE rooms:', e);
            }
        };
        
        this.eventSource.onerror = (error) => {
            console.error('❌ Erreur SSE rooms:', error);
            
            if (this.eventSource.readyState === EventSource.CLOSED) {
                this.reconnect();
            }
        };
    }
    
    reconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('❌ Nombre maximum de tentatives de reconnexion atteint');
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`🔄 Tentative de reconnexion rooms ${this.reconnectAttempts}/${this.maxReconnectAttempts}...`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectDelay * this.reconnectAttempts);
    }
    
    disconnect() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
        }
    }
}

