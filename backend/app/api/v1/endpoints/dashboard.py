from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.deps import require_admin_role
from app.db.session import get_db
from app.schemas import EventStatistics
import datetime

router = APIRouter(dependencies=[Depends(require_admin_role)])

@router.get("/stats", response_model=EventStatistics)
def get_stats(db: Session = Depends(get_db)):
    # Logic count từ DB
    return EventStatistics(
        event_id="demo", event_name="Demo", status="ACTIVE",
        total_registered=0, total_participating=0,
        total_flights=0, total_flight_slots=0, allocated_flight_slots=0, available_flight_slots=0,
        total_gala_seats=0, confirmed_gala_seats=0, available_gala_seats=0,
        total_hotel_rooms_assigned=0, last_updated=datetime.datetime.now()
    )