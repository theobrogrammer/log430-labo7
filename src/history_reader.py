#!/usr/bin/env python3
"""
Script pour lire l'historique complet des événements Kafka
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025

Ce script utilise le UserEventHistoryConsumer pour :
1. Lire TOUS les événements depuis le début du topic
2. Les traiter avec les handlers appropriés (optionnel)
3. Sauvegarder l'historique complet en JSON
"""

import config
from consumers.user_event_history_consumer import UserEventHistoryConsumer
from logger import Logger
from handlers.handler_registry import HandlerRegistry
from handlers.user_created_handler import UserCreatedHandler
from handlers.user_deleted_handler import UserDeletedHandler

def main():
    """
    Point d'entrée pour la lecture d'historique des événements
    
    Configuration importante :
    - group_id DISTINCT de celui du service principal (coolriel-group)
    - auto_offset_reset="earliest" pour lire depuis le début
    - Sauvegarde JSON de tous les événements
    """
    logger = Logger.get_instance("HistoryReader")
    logger.info("🔍 Démarrage de la lecture d'historique Kafka...")
    
    # Même registry que le service principal pour pouvoir traiter les événements
    registry = HandlerRegistry()
    registry.register(UserCreatedHandler(output_dir=config.OUTPUT_DIR))
    registry.register(UserDeletedHandler(output_dir=config.OUTPUT_DIR))
    
    # CONSUMER D'HISTORIQUE avec GROUP_ID DISTINCT
    # "coolriel-history-group" != "coolriel-group" (service principal)
    # Ceci évite la répartition des partitions entre les consumers
    history_consumer = UserEventHistoryConsumer(
        bootstrap_servers=config.KAFKA_HOST,
        topic=config.KAFKA_TOPIC,
        group_id="coolriel-history-group",  # GROUP_ID DISTINCT!
        registry=registry,
        output_file="output/events_history.json"  # Fichier JSON de sortie
    )
    
    logger.info("📚 Lecture de l'historique complet depuis le début du topic...")
    logger.info("💡 Utilisation du group_id: coolriel-history-group (distinct du service principal)")
    
    # Démarrage de la lecture historique
    history_consumer.start()
    
    logger.info("✅ Lecture d'historique terminée! Vérifiez le fichier output/events_history.json")

if __name__ == "__main__":
    main()