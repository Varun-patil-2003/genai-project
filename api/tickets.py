from fastapi import APIRouter, HTTPException
from services.ticket_service import ticket_service
router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.get("/")
async def list_tickets():
    return ticket_service.get_all_tickets()

@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str):
    ticket = ticket_service.get_ticket_by_id(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket
