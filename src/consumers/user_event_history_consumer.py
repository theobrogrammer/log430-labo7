"""
Kafka Historical User Event Consumer (Event Sourcing)
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import json
from logger import Logger
from typing import Optional
from kafka import KafkaConsumer
from handlers.handler_registry import HandlerRegistry

class UserEventHistoryConsumer:
    """
    Consumer Kafka pour lire l'historique complet des événements (Event Sourcing)
    
    Ce consumer diffère du UserEventConsumer principal car :
    - Il utilise un group_id DISTINCT pour éviter la répartition des partitions
    - Il lit depuis le DÉBUT (earliest) au lieu de la fin (latest)
    - Il sauvegarde tous les événements dans un fichier JSON pour l'audit
    """
    
    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        group_id: str,
        registry: HandlerRegistry,
        output_file: str = "events_history.json"
    ):
        # Configuration des paramètres Kafka pour l'Event Sourcing
        self.bootstrap_servers = bootstrap_servers
        self.topic = topic
        
        # GROUP_ID DISTINCT: Essentiel pour éviter que ce consumer partage 
        # les partitions avec le consumer principal (UserEventConsumer)
        # Si même group_id -> Kafka répartit 50/50 -> on rate des messages!
        self.group_id = group_id  # Doit être différent de "coolriel-group"
        
        self.registry = registry
        self.output_file = output_file  # Fichier JSON pour sauvegarder l'historique
        
        # AUTO_OFFSET_RESET = EARLIEST: 
        # - "earliest" = lit depuis le DÉBUT du topic (tous les anciens messages)
        # - "latest" = lit seulement les NOUVEAUX messages (défaut du consumer principal)
        self.auto_offset_reset = "earliest"
        
        self.consumer: Optional[KafkaConsumer] = None
        self.logger = Logger.get_instance("UserEventHistoryConsumer")
        
        # Liste pour accumuler tous les événements lus
        self.events_history = []
    
    def start(self) -> None:
        """
        Démarre la lecture de l'historique complet depuis Kafka
        
        Différences avec le consumer principal :
        1. auto_offset_reset="earliest" -> lit TOUT l'historique
        2. group_id différent -> pas de conflit de partitions
        3. Sauvegarde JSON -> persistence pour audit/analyse
        """
        self.logger.info(f"🔍 Démarrage du consumer d'historique avec group_id: {self.group_id}")
        self.logger.info(f"📖 Lecture depuis le DÉBUT (earliest) du topic: {self.topic}")
        
        # Création du consumer Kafka configuré pour l'Event Sourcing
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.bootstrap_servers,
            
            # GROUP_ID DISTINCT : Évite la répartition avec le consumer principal
            # Si on utilisait "coolriel-group" -> Kafka partagerait les partitions!
            group_id=self.group_id,
            
            # EARLIEST : Lit depuis le début du topic (tous les anciens événements)
            # Contrairement au consumer principal qui utilise "latest"
            auto_offset_reset=self.auto_offset_reset,
            
            # Désérialisation JSON : Convertit les bytes Kafka en objets Python
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            
            # Auto-commit pour marquer les messages comme lus
            enable_auto_commit=True,
            
            # Timeout pour éviter d'attendre indéfiniment s'il n'y a plus de messages
            consumer_timeout_ms=10000  # 10 secondes max sans nouveau message
        )
        
        try:
            self.logger.info("📚 Lecture de l'historique des événements...")
            message_count = 0
            
            # Boucle de lecture des messages historiques
            for message in self.consumer:
                event_data = message.value
                message_count += 1
                
                # Log de progression pour voir l'avancement
                if message_count % 10 == 0:
                    self.logger.info(f"📋 Lu {message_count} événements...")
                
                # Traitement de chaque événement (comme le consumer principal)
                self._process_historical_event(event_data)
                
                # Ajout à l'historique pour la sauvegarde JSON
                self.events_history.append({
                    "timestamp": message.timestamp,
                    "partition": message.partition,
                    "offset": message.offset,
                    "event_data": event_data
                })
            
            self.logger.info(f"✅ Lecture terminée! Total: {message_count} événements traités")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de la lecture historique: {e}", exc_info=True)
        finally:
            # SAUVEGARDE JSON : Persistence de l'historique pour audit
            self._save_history_to_json()
            self.stop()

    def _process_historical_event(self, event_data: dict) -> None:
        """
        Traite un événement historique (similaire au consumer principal)
        
        Cette méthode peut :
        1. Appliquer les handlers pour régénérer des emails
        2. Faire de l'analyse statistique
        3. Valider la cohérence des données
        """
        event_type = event_data.get('event')
        user_id = event_data.get('id')
        
        if not event_type:
            self.logger.warning(f"⚠️ Événement historique sans type: {event_data}")
            return
        
        # Log détaillé pour l'audit
        self.logger.debug(f"📜 Événement historique: {event_type} pour utilisateur {user_id}")
        
        # OPTIONNEL: Appliquer les handlers pour régénérer les emails
        # Utile pour reconstruire l'état après une panne
        handler = self.registry.get_handler(event_type)
        if handler:
            try:
                # Note: Ceci régénérerait les emails (peut être désactivé selon le besoin)
                # handler.handle(event_data)
                self.logger.debug(f"✅ Handler trouvé pour {event_type}")
            except Exception as e:
                self.logger.error(f"❌ Erreur handler historique {event_type}: {e}")
        else:
            self.logger.debug(f"ℹ️ Pas de handler pour le type historique: {event_type}")
    
    def _save_history_to_json(self) -> None:
        """
        Sauvegarde l'historique complet dans un fichier JSON
        
        Le fichier contient :
        - Métadonnées Kafka (timestamp, partition, offset)
        - Données complètes de chaque événement
        - Format structuré pour analyse ultérieure
        """
        if not self.events_history:
            self.logger.warning("📂 Aucun événement à sauvegarder")
            return
        
        try:
            # Préparation du fichier JSON avec métadonnées
            history_data = {
                "metadata": {
                    "topic": self.topic,
                    "group_id": self.group_id,
                    "total_events": len(self.events_history),
                    "export_timestamp": json.dumps(None, default=str),  # Timestamp actuel
                    "consumer_type": "UserEventHistoryConsumer"
                },
                "events": self.events_history
            }
            
            # SAUVEGARDE JSON : Utilisation de json.dumps pour la sérialisation
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # json.dumps avec indentation pour lisibilité
                json.dump(history_data, f, indent=2, ensure_ascii=False, default=str)
            
            self.logger.info(f"💾 Historique sauvegardé: {self.output_file} ({len(self.events_history)} événements)")
            
        except Exception as e:
            self.logger.error(f"❌ Erreur sauvegarde JSON: {e}", exc_info=True)
    
    def stop(self) -> None:
        """Arrête le consumer proprement"""
        if self.consumer:
            self.consumer.close()
            self.logger.info("🛑 Consumer d'historique arrêté!")