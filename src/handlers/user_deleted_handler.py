"""
Handler: User Deleted
SPDX-License-Identifier: LGPL-3.0-or-later
Auteurs : Gabriel C. Ullmann, Fabio Petrillo, 2025
"""

import os
from datetime import datetime
from pathlib import Path
from handlers.base import EventHandler
from typing import Dict, Any

class UserDeletedHandler(EventHandler):
    """
    Handles UserDeleted events reçus via Kafka
    
    Ce handler est enregistré dans le HandlerRegistry et sera automatiquement
    invoqué par le UserEventConsumer quand un message Kafka de type "UserDeleted"
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
        Kafka avec un champ 'event' == "UserDeleted", ce handler sera invoqué.
        """
        return "UserDeleted"
    
    def _customize_goodbye_message_by_user_type_id(self, html_content: str, user_type_id: int, name: str) -> str:
        """
        Personnalise le contenu HTML d'au revoir selon l'ID du type d'utilisateur
        
        Args:
            html_content: Contenu HTML du template
            user_type_id: ID du type d'utilisateur (1=Client, 2=Employee, 3=Manager)
            name: Nom de l'utilisateur
            
        Returns:
            Contenu HTML personnalisé
        """
        if user_type_id == 2:  # Employee
            # Message personnalisé pour un employé qui quitte
            goodbye_message = f"👋 Au revoir, {name}!"
            main_message = "Nous supprimons ton compte employé à ta demande. Merci pour ton excellent travail et ta contribution à notre équipe. Si jamais tu souhaites revenir dans notre équipe, n'hésite pas à nous contacter."
            signature = "Toute l'équipe<br>Magasin du Coin"
        elif user_type_id == 3:  # Manager
            # Message personnalisé pour un manager qui quitte
            goodbye_message = f"👋 Au revoir, {name}!"
            main_message = "Nous supprimons votre compte manager à votre demande. Merci pour votre leadership exceptionnel et votre dévouement. Votre contribution à notre équipe restera dans nos mémoires."
            signature = "La direction générale<br>Magasin du Coin"
        else:  # Client (user_type_id == 1 ou défaut)
            # Message par défaut pour un client
            goodbye_message = f"👋 Au revoir, {name}!"
            main_message = "Nous supprimons votre compte à votre demande. Merci d'avoir été client de notre magasin. Si jamais vous voulez créer une nouvelle compte, n'hésitez pas à nous contacter."
            signature = "Cordialement,<br>Magasin du Coin"
        
        # Remplacement des placeholders dédiés dans le template
        html_content = html_content.replace("{{goodbye_message}}", goodbye_message)
        html_content = html_content.replace("{{main_message}}", main_message)
        html_content = html_content.replace("{{signature}}", signature)

        return html_content
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        """
        Create an HTML email based on user deletion data
        
        Cette méthode est appelée automatiquement par le UserEventConsumer
        quand un message Kafka de type "UserDeleted" est reçu.
        
        Args:
            event_data: Données désérialisées du message Kafka JSON contenant:
                       - id: identifiant unique de l'utilisateur
                       - name: nom de l'utilisateur
                       - email: adresse email de l'utilisateur  
                       - datetime: timestamp de suppression
        
        Le flux Kafka typique:
        1. Un service externe publie un événement UserDeleted sur le topic 'user-events'
        2. Le UserEventConsumer lit ce message du topic Kafka
        3. Le message JSON est désérialisé en dictionnaire Python
        4. Cette méthode handle() est invoquée avec les données de l'événement
        5. Un email HTML d'au revoir est généré et sauvegardé
        """
        
        # Extraction des données reçues du message Kafka
        user_id = event_data.get('id')
        name = event_data.get('name')
        email = event_data.get('email')
        datetime_str = event_data.get('datetime')
        user_type_id = event_data.get('user_type_id', 1)  # Défaut: 1 (Client)
        
        # Validation des données requises
        if not all([user_id, name, email, datetime_str]):
            self.logger.warning(f"Données manquantes dans l'événement UserDeleted: {event_data}")
            return
        
        # Chargement et personnalisation du template d'au revoir
        current_file = Path(__file__)
        project_root = current_file.parent.parent   
        template_path = project_root / "templates" / "goodbye_client_template.html"
        
        try:
            with open(template_path, 'r', encoding='utf-8') as file:
                html_content = file.read()
                
                # Personnalisation selon l'ID du type d'utilisateur
                html_content = self._customize_goodbye_message_by_user_type_id(html_content, user_type_id, name)
                
                # Remplacement des placeholders avec les données de l'événement Kafka
                html_content = html_content.replace("{{user_id}}", str(user_id))
                html_content = html_content.replace("{{name}}", name)
                html_content = html_content.replace("{{email}}", email)
                html_content = html_content.replace("{{deletion_date}}", datetime_str)
        
        except FileNotFoundError:
            self.logger.error(f"Template d'au revoir introuvable: {template_path}")
            return
        except Exception as e:
            self.logger.error(f"Erreur lors du chargement du template: {e}")
            return

        # Génère le fichier HTML d'au revoir basé sur les données Kafka
        filename = os.path.join(self.output_dir, f"goodbye_{user_id}.html")
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            # Log de confirmation que l'événement Kafka a été traité avec succès
            user_type_names = {1: "client", 2: "employé", 3: "manager"}
            user_type_name = user_type_names.get(user_type_id, "utilisateur")
            self.logger.debug(f"Événement Kafka UserDeleted traité - Courriel HTML d'au revoir généré pour {user_type_name} {name} (ID: {user_id}), {filename}")
            
        except Exception as e:
            self.logger.error(f"Erreur lors de la génération du fichier HTML: {e}")
            return