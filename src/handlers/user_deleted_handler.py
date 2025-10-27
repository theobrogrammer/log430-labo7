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
    """Handles UserDeleted events"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        super().__init__()
    
    def get_event_type(self) -> str:
        return "UserDeleted"
    
    def handle(self, event_data: Dict[str, Any]) -> None:
        # TODO: implémentation basée sur UserCreated
        user_id = 0
        name = "None"
        email = "None"
        datetime = "YYYY-MM-DD HH:mm:ss"
        filename = "None"

        self.logger.debug(f"Courriel HTML généré à {name} (ID: {user_id}) at {filename}")