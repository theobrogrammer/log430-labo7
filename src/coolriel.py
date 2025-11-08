"""
Coolriel: Event-Driven Email Sender
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""
import config
from consumers.user_event_history_consumer import UserEventHistoryConsumer
from logger import Logger
from consumers.user_event_consumer import UserEventConsumer
from handlers.handler_registry import HandlerRegistry
from handlers.user_created_handler import UserCreatedHandler
from handlers.user_deleted_handler import UserDeletedHandler

logger = Logger.get_instance("Coolriel")

def main():
    """Main entry point for the Coolriel service"""
    logger.info("🚀 Démarrage de Coolriel - Service d'emails event-driven")
    
    # Initialisation du registry avec les handlers
    registry = HandlerRegistry()
    registry.register(UserCreatedHandler(output_dir=config.OUTPUT_DIR))
    registry.register(UserDeletedHandler(output_dir=config.OUTPUT_DIR))
    
    # ÉTAPE 1: Consumer d'historique - Lit l'historique complet AVANT le service temps réel
    logger.info("📚 Phase 1: Lecture de l'historique des événements Kafka...")
    consumer_service_history = UserEventHistoryConsumer(
        bootstrap_servers=config.KAFKA_HOST,
        topic=config.KAFKA_TOPIC,
        group_id=f"{config.KAFKA_GROUP_ID}-history",  # Group ID distinct comme demandé
        registry=registry,
        output_file=f"{config.OUTPUT_DIR}/events_history.json"
    )
    
    # Démarrage du consumer d'historique (BLOQUANT jusqu'à completion)
    logger.info("🔍 Début de la lecture historique - cette phase est bloquante...")
    consumer_service_history.start()
    logger.info("✅ Lecture historique terminée! Passage au service temps réel...")
    
    # ÉTAPE 2: Consumer temps réel - Service principal qui écoute les nouveaux événements
    logger.info("⚡ Phase 2: Démarrage du service temps réel...")
    # NOTE: le consommateur peut écouter 1 ou plusieurs topics (str or array)
    consumer_service = UserEventConsumer(
        bootstrap_servers=config.KAFKA_HOST,
        topic=config.KAFKA_TOPIC,
        group_id=config.KAFKA_GROUP_ID,  # Group ID principal (coolriel-group)
        registry=registry,
    )
    
    # Démarrage du consumer principal (BLOQUANT - service infini)
    logger.info("🎧 Service temps réel en écoute permanente des nouveaux événements...")
    consumer_service.start()

if __name__ == "__main__":
    main()
