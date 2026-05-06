import json
import os
from typing import List, Optional

class TickerService:
    def __init__(self):
        self.file_path = "data/sample_ticket/tickets.json"
    
    def get_all_tickets(self) -> List[dict]:
        if not os.path.exists(self.file_path):
            print(f"Warning: Database file not found at {self.file_path}. Have you run seed_db.py?")
            return []

        with open(self.file_path, 'r') as f:
            return json.load(f)
    
    def get_ticket_by_id(self, ticket_id: str) -> Optional[dict]:
        tickets = self.get_all_tickets()
        clean_id = str(ticket_id).strip()
        if clean_id.isdigit():
            clean_id = f"TICKET-{clean_id}"
        return next((t for t in tickets if t["id"].upper() == clean_id.upper()), None)

ticket_service = TickerService()
