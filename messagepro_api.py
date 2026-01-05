#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Module d'intégration API Message Pro
Service pour envoyer des SMS, WhatsApp, OTP via l'API Message Pro
"""

import requests
import os
from typing import Dict, Optional, List, Any
from flask import current_app


class MessageProAPI:
    """Client API pour Message Pro"""
    
    BASE_URL = "https://messagepro-gn.com/api"
    
    def __init__(self, api_secret: Optional[str] = None):
        """
        Initialise le client API Message Pro
        
        Args:
            api_secret: Clé secrète API (si None, lit depuis la DB puis MESSAGEPRO_API_SECRET)
        """
        if api_secret:
            self.api_secret = api_secret
        else:
            # Essayer de récupérer depuis la base de données
            try:
                from models import ApiConfig
                self.api_secret = ApiConfig.get_api_secret('messagepro')
            except Exception:
                self.api_secret = None
            
            # Si pas trouvé dans la DB, utiliser la variable d'environnement
            if not self.api_secret:
                self.api_secret = os.getenv('MESSAGEPRO_API_SECRET')
        
        if not self.api_secret:
            raise ValueError("MESSAGEPRO_API_SECRET doit être défini dans la base de données ou les variables d'environnement")
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                     data: Optional[Dict] = None, files: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Effectue une requête HTTP vers l'API Message Pro
        
        Args:
            method: Méthode HTTP (GET, POST)
            endpoint: Endpoint de l'API
            params: Paramètres de requête
            data: Données POST
            files: Fichiers à envoyer (multipart/form-data)
        
        Returns:
            Réponse JSON de l'API
        """
        url = f"{self.BASE_URL}/{endpoint}"
        
        # Ajouter le secret aux paramètres ou données
        if params is None:
            params = {}
        if data is None:
            data = {}
        
        if method == 'GET':
            params['secret'] = self.api_secret
        else:
            if files:
                data['secret'] = self.api_secret
            else:
                data['secret'] = self.api_secret
        
        try:
            if method == 'GET':
                response = requests.get(url, params=params, timeout=30)
            elif method == 'POST':
                if files:
                    response = requests.post(url, data=data, files=files, timeout=30)
                else:
                    response = requests.post(url, data=data, timeout=30)
            else:
                raise ValueError(f"Méthode HTTP non supportée: {method}")
            
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                'status': 500,
                'message': f'Erreur lors de la requête API: {str(e)}',
                'data': None
            }
    
    # =========================================================
    # ACCOUNT APIs
    # =========================================================
    
    def get_credits(self) -> Dict[str, Any]:
        """Récupère les crédits restants"""
        return self._make_request('GET', 'get/credits')
    
    def get_subscription(self) -> Dict[str, Any]:
        """Récupère les informations d'abonnement"""
        return self._make_request('GET', 'get/subscription')
    
    def get_earnings(self) -> Dict[str, Any]:
        """Récupère les gains du partenaire"""
        return self._make_request('GET', 'get/earnings')
    
    # =========================================================
    # CONTACTS APIs
    # =========================================================
    
    def create_contact(self, phone: str, name: str, groups: str) -> Dict[str, Any]:
        """
        Crée un nouveau contact
        
        Args:
            phone: Numéro de téléphone (E.164 ou format local)
            name: Nom du contact
            groups: Liste d'IDs de groupes séparés par des virgules
        """
        data = {
            'phone': phone,
            'name': name,
            'groups': groups
        }
        return self._make_request('POST', 'create/contact', data=data)
    
    def create_group(self, name: str) -> Dict[str, Any]:
        """Crée un nouveau groupe de contacts"""
        data = {'name': name}
        return self._make_request('POST', 'create/group', data=data)
    
    def get_contacts(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère la liste des contacts"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/contacts', params=params)
    
    def get_groups(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère la liste des groupes"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/groups', params=params)
    
    def delete_contact(self, contact_id: int) -> Dict[str, Any]:
        """Supprime un contact"""
        params = {'id': contact_id}
        return self._make_request('GET', 'delete/contact', params=params)
    
    def delete_group(self, group_id: int) -> Dict[str, Any]:
        """Supprime un groupe"""
        params = {'id': group_id}
        return self._make_request('GET', 'delete/group', params=params)
    
    # =========================================================
    # OTP APIs
    # =========================================================
    
    def send_otp(self, phone: str, message: str, message_type: str = 'sms',
                  expire: int = 300, priority: int = 2, account: Optional[str] = None,
                  mode: Optional[str] = None, device: Optional[str] = None,
                  gateway: Optional[str] = None, sim: Optional[int] = None) -> Dict[str, Any]:
        """
        Envoie un code OTP
        
        Args:
            phone: Numéro de téléphone (E.164)
            message: Message avec {{otp}} pour le code
            message_type: 'sms' ou 'whatsapp'
            expire: Temps d'expiration en secondes (défaut: 300)
            priority: Priorité (1=immédiat, 2=normal) - WhatsApp uniquement
            account: ID compte WhatsApp - WhatsApp uniquement
            mode: 'devices' ou 'credits' - SMS uniquement
            device: ID appareil - SMS mode 'devices'
            gateway: ID gateway - SMS mode 'credits'
            sim: Slot SIM (1 ou 2) - SMS mode 'devices'
        """
        data = {
            'type': message_type,
            'phone': phone,
            'message': message,
            'expire': expire,
            'priority': priority
        }
        
        if account:
            data['account'] = account
        if mode:
            data['mode'] = mode
        if device:
            data['device'] = device
        if gateway:
            data['gateway'] = gateway
        if sim:
            data['sim'] = sim
        
        return self._make_request('POST', 'send/otp', data=data)
    
    def verify_otp(self, otp: str) -> Dict[str, Any]:
        """Vérifie un code OTP"""
        params = {'otp': otp}
        return self._make_request('GET', 'get/otp', params=params)
    
    # =========================================================
    # SMS APIs
    # =========================================================
    
    def send_sms(self, phone: str, message: str, mode: str = 'devices',
                device: Optional[str] = None, gateway: Optional[str] = None,
                sim: Optional[int] = None, priority: int = 0,
                shortener: Optional[int] = None) -> Dict[str, Any]:
        """
        Envoie un SMS unique
        
        Args:
            phone: Numéro de téléphone (E.164 ou format local)
            message: Message à envoyer
            mode: 'devices' ou 'credits'
            device: ID appareil (requis pour mode 'devices')
            gateway: ID gateway (requis pour mode 'credits')
            sim: Slot SIM (1 ou 2) - mode 'devices' uniquement
            priority: Priorité (0 ou 1=immédiat, 2=normal) - mode 'devices' uniquement
            shortener: ID raccourcisseur d'URL
        """
        data = {
            'mode': mode,
            'phone': phone,
            'message': message,
            'priority': priority
        }
        
        if device:
            data['device'] = device
        if gateway:
            data['gateway'] = gateway
        if sim:
            data['sim'] = sim
        if shortener:
            data['shortener'] = shortener
        
        return self._make_request('POST', 'send/sms', data=data)
    
    def send_bulk_sms(self, campaign: str, message: str, mode: str = 'devices',
                     numbers: Optional[str] = None, groups: Optional[str] = None,
                     device: Optional[str] = None, gateway: Optional[str] = None,
                     sim: Optional[int] = None, priority: int = 0,
                     shortener: Optional[int] = None) -> Dict[str, Any]:
        """
        Envoie des SMS en masse
        
        Args:
            campaign: Nom de la campagne
            message: Message à envoyer
            mode: 'devices' ou 'credits'
            numbers: Liste de numéros séparés par des virgules
            groups: Liste d'IDs de groupes séparés par des virgules
            device: ID appareil (requis pour mode 'devices')
            gateway: ID gateway (requis pour mode 'credits')
            sim: Slot SIM (1 ou 2) - mode 'devices' uniquement
            priority: Priorité (0 ou 1=immédiat, 2=normal) - mode 'devices' uniquement
            shortener: ID raccourcisseur d'URL
        """
        data = {
            'mode': mode,
            'campaign': campaign,
            'message': message,
            'priority': priority
        }
        
        if numbers:
            data['numbers'] = numbers
        if groups:
            data['groups'] = groups
        if device:
            data['device'] = device
        if gateway:
            data['gateway'] = gateway
        if sim:
            data['sim'] = sim
        if shortener:
            data['shortener'] = shortener
        
        return self._make_request('POST', 'send/sms.bulk', data=data)
    
    def get_sent_messages(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère les SMS envoyés"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/sms.sent', params=params)
    
    def get_received_messages(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère les SMS reçus"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/sms.received', params=params)
    
    def get_pending_messages(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère les SMS en attente"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/sms.pending', params=params)
    
    def get_sms_campaigns(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère les campagnes SMS"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/sms.campaigns', params=params)
    
    # =========================================================
    # WHATSAPP APIs
    # =========================================================
    
    def send_whatsapp(self, account: str, recipient: str, message: str,
                     message_type: str = 'text', priority: int = 2,
                     media_file: Optional[Any] = None, media_url: Optional[str] = None,
                     media_type: Optional[str] = None,
                     document_file: Optional[Any] = None, document_url: Optional[str] = None,
                     document_name: Optional[str] = None, document_type: Optional[str] = None,
                     shortener: Optional[int] = None) -> Dict[str, Any]:
        """
        Envoie un message WhatsApp unique
        
        Args:
            account: ID compte WhatsApp
            recipient: Numéro ou adresse groupe WhatsApp
            message: Message ou légende
            message_type: 'text', 'media', 'document'
            priority: Priorité (1=immédiat, 2=normal)
            media_file: Fichier média (pour type 'media')
            media_url: URL média (pour type 'media')
            media_type: Type média ('image', 'audio', 'video')
            document_file: Fichier document (pour type 'document')
            document_url: URL document (pour type 'document')
            document_name: Nom du document
            document_type: Type document ('pdf', 'xml', 'xls', etc.)
            shortener: ID raccourcisseur d'URL
        """
        data = {
            'account': account,
            'recipient': recipient,
            'type': message_type,
            'message': message,
            'priority': priority
        }
        
        files = {}
        if media_file:
            files['media_file'] = media_file
        if document_file:
            files['document_file'] = document_file
        
        if media_url:
            data['media_url'] = media_url
        if media_type:
            data['media_type'] = media_type
        if document_url:
            data['document_url'] = document_url
        if document_name:
            data['document_name'] = document_name
        if document_type:
            data['document_type'] = document_type
        if shortener:
            data['shortener'] = shortener
        
        return self._make_request('POST', 'send/whatsapp', data=data, files=files if files else None)
    
    def send_bulk_whatsapp(self, account: str, campaign: str, message: str,
                          recipients: Optional[str] = None, groups: Optional[str] = None,
                          message_type: str = 'text',
                          media_file: Optional[Any] = None, media_url: Optional[str] = None,
                          media_type: Optional[str] = None,
                          document_file: Optional[Any] = None, document_url: Optional[str] = None,
                          document_name: Optional[str] = None, document_type: Optional[str] = None,
                          shortener: Optional[int] = None) -> Dict[str, Any]:
        """
        Envoie des messages WhatsApp en masse
        
        Args:
            account: ID compte WhatsApp
            campaign: Nom de la campagne
            message: Message ou légende
            recipients: Liste de numéros séparés par des virgules
            groups: Liste d'IDs de groupes séparés par des virgules
            message_type: 'text', 'media', 'document'
            media_file: Fichier média (pour type 'media')
            media_url: URL média (pour type 'media')
            media_type: Type média ('image', 'audio', 'video')
            document_file: Fichier document (pour type 'document')
            document_url: URL document (pour type 'document')
            document_name: Nom du document
            document_type: Type document ('pdf', 'xml', 'xls', etc.)
            shortener: ID raccourcisseur d'URL
        """
        data = {
            'account': account,
            'campaign': campaign,
            'type': message_type,
            'message': message
        }
        
        files = {}
        if media_file:
            files['media_file'] = media_file
        if document_file:
            files['document_file'] = document_file
        
        if recipients:
            data['recipients'] = recipients
        if groups:
            data['groups'] = groups
        if media_url:
            data['media_url'] = media_url
        if media_type:
            data['media_type'] = media_type
        if document_url:
            data['document_url'] = document_url
        if document_name:
            data['document_name'] = document_name
        if document_type:
            data['document_type'] = document_type
        if shortener:
            data['shortener'] = shortener
        
        return self._make_request('POST', 'send/whatsapp.bulk', data=data, files=files if files else None)
    
    def get_whatsapp_accounts(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère les comptes WhatsApp"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/wa.accounts', params=params)
    
    def get_sent_chats(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère les messages WhatsApp envoyés"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/wa.sent', params=params)
    
    def get_received_chats(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère les messages WhatsApp reçus"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/wa.received', params=params)
    
    def get_whatsapp_campaigns(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère les campagnes WhatsApp"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/wa.campaigns', params=params)
    
    # =========================================================
    # GATEWAYS APIs
    # =========================================================
    
    def get_rates(self) -> Dict[str, Any]:
        """Récupère les tarifs des gateways"""
        return self._make_request('GET', 'get/rates')
    
    def get_devices(self, limit: int = 10, page: int = 1) -> Dict[str, Any]:
        """Récupère les appareils Android liés"""
        params = {'limit': limit, 'page': page}
        return self._make_request('GET', 'get/devices', params=params)
    
    def get_shorteners(self) -> Dict[str, Any]:
        """Récupère la liste des raccourcisseurs d'URL disponibles"""
        return self._make_request('GET', 'get/shorteners')

