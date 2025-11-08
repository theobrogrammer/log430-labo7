"""
Handler: User Created
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025

Ce handler fait partie d'un système event-driven utilisant Apache Kafka :
- Il traite les messages reçus du topic Kafka 'user-events'
- Chaque message contient des données d'événement utilisateur
- Le consumer Kafka appelle automatiquement ce handler quand un événement
  de type "UserCreated" est détecté dans le flux de messages
"""

import os
from pathlib import Path
from handlers.base import EventHandler
from typing import Dict, Any


class UserCreatedHandler(EventHandler):
    """
    Handles UserCreated events reçus via Kafka
    
    Ce handler est enregistré dans le HandlerRegistry et sera automatiquement
    invoqué par le UserEventConsumer quand un message Kafka de type "UserCreated"
    est reçu sur le topic configuré (user-events).
    """
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        super().__init__()
    
    def get_event_type(self) -> str:
        """
        Return the event type this handler processes
        
        Cette méthode permet au système Kafka de router automatiquement
        les messages vers le bon handler. Quand un message arrive du topic
        Kafka avec un champ 'type' == "UserCreated", ce handler sera invoqué.
        """
        return "UserCreated"
    
    def _customize_message_by_user_type_id(self, html_content: str, user_type_id: int, name: str) -> str:
        """
        Personnalise le contenu HTML selon l'ID du type d'utilisateur
        
        Args:
            html_content: Contenu HTML du template
            user_type_id: ID du type d'utilisateur (1=Client, 2=Employee, 3=Manager)
            name: Nom de l'utilisateur
            
        Returns:
            Contenu HTML personnalisé
        """
        if user_type_id == 2:  # Employee
            # Message personnalisé pour un employé
            welcome_message = f"Salut et bienvenue dans l'équipe, {name}!"
            store_message = "Nous sommes ravis de t'accueillir parmi nos employés. Tu vas contribuer à faire de notre magasin un endroit encore meilleur pour nos clients."
            signature = "L'équipe de direction<br>Magasin du Coin"
        elif user_type_id == 3:  # Manager
            # Message personnalisé pour un manager
            welcome_message = f"Bienvenue dans l'équipe de direction, {name}!"
            store_message = "Nous sommes honorés de vous accueillir en tant que manager. Votre leadership sera essentiel pour guider notre équipe vers l'excellence."
            signature = "La direction générale<br>Magasin du Coin"
        else:  # Client (user_type_id == 1 ou défaut)
            # Message par défaut pour un client
            welcome_message = f"Bienvenue, {name}!"
            store_message = "Merci d'avoir visité notre magasin. Nous espérons que vous aurez une excellente expérience avec nous."
            signature = "Cordialement,<br>Magasin du Coin"
        
                # Remplacement des placeholders dédiés dans le template
        html_content = html_content.replace("{{welcome_message}}", welcome_message)
        html_content = html_content.replace("{{main_message}}", store_message)
        html_content = html_content.replace("{{signature}}", signature)

        return html_content
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """
        Create an HTML email based on user creation data
        
        Cette méthode est appelée automatiquement par le UserEventConsumer
        quand un message Kafka de type "UserCreated" est reçu.
        
        Args:
            event_data: Données désérialisées du message Kafka JSON contenant:
                       - id: identifiant unique de l'utilisateur
                       - name: nom de l'utilisateur
                       - email: adresse email de l'utilisateur  
                       - datetime: timestamp de création
        
        Le flux Kafka typique:
        1. Un service externe publie un événement UserCreated sur le topic 'user-events'
        2. Le UserEventConsumer lit ce message du topic Kafka
        3. Le message JSON est désérialisé en dictionnaire Python
        4. Cette méthode handle() est invoquée avec les données de l'événement
        5. Un email HTML de bienvenue est généré et sauvegardé
        """

        # Extraction des données reçues du message Kafka
        user_id = event_data.get('id')
        name = event_data.get('name')
        email = event_data.get('email')
        datetime = event_data.get('datetime')
        user_type_id = event_data.get('user_type_id', 1)  # Défaut: 1 (Client)

        current_file = Path(__file__)
        project_root = current_file.parent.parent   
        with open(project_root / "templates" / "welcome_client_template.html", 'r') as file:
            html_content = file.read()
            
            # Personnalisation selon l'ID du type d'utilisateur
            html_content = self._customize_message_by_user_type_id(html_content, user_type_id, name)
            
            # Remplacement des placeholders standards
            html_content = html_content.replace("{{user_id}}", str(user_id))
            html_content = html_content.replace("{{name}}", name)
            html_content = html_content.replace("{{email}}", email)
            html_content = html_content.replace("{{creation_date}}", datetime)

        # Génère le fichier HTML de bienvenue basé sur les données Kafka
        filename = os.path.join(self.output_dir, f"welcome_{user_id}.html")
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Log de confirmation que l'événement Kafka a été traité avec succès
        user_type_names = {1: "client", 2: "employé", 3: "manager"}
        user_type_name = user_type_names.get(user_type_id, "utilisateur")
        self.logger.debug(f"Événement Kafka UserCreated traité - Courriel HTML généré pour {user_type_name} {name} (ID: {user_id}), {filename}")