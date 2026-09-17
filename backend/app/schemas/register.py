from pydantic import BaseModel, Field
from enum import Enum


class DesiredShift(str, Enum):
    """
    Flight shift preference.
    
    - SHIFT_1: Morning/daytime shift (before 17:00)
    - SHIFT_2: Evening shift (after 17:00)
    """
    SHIFT_1 = "SHIFT_1"
    SHIFT_2 = "SHIFT_2"


class RegistrationBase(BaseModel):
    """
    Base schema for employee registration.
    
    Captures participation confirmation, shift preference, and vehicle needs.
    """
    is_participating: bool = Field(
        ..., 
        description="Whether employee confirms participation in the event"
    )
    event_id: str | None = Field(None, description="Event being registered for")
    team_id: str | None = Field(None, description="Team selected for this Event")
    desired_shift: DesiredShift | None = Field(
        None, 
        description="Preferred flight shift: SHIFT_1 (before 17:00) or SHIFT_2 (after 17:00)"
    )
    
    # Vehicle needs for 4 transportation routes
    needs_vehicle_route_1: bool = Field(
        default=False, 
        description="Needs vehicle for Route 1: HN/HCM → Airport"
    )
    needs_vehicle_route_2: bool = Field(
        default=False, 
        description="Needs vehicle for Route 2: Airport → Hotel"
    )
    needs_vehicle_route_3: bool = Field(
        default=False, 
        description="Needs vehicle for Route 3: Hotel → Airport"
    )
    needs_vehicle_route_4: bool = Field(
        default=False, 
        description="Needs vehicle for Route 4: Airport → HN/HCM"
    )
    
    pickup_location_route_1: str | None = Field(
        None, 
        description="Preferred pickup location for Route 1"
    )
    pickup_location_route_4: str | None = Field(
        None, 
        description="Preferred pickup location for Route 4"
    )
    
    comments: str | None = Field(
        None, 
        max_length=1000, 
        description="Employee's wishes, suggestions, or special requests"
    )


class RegistrationCreate(RegistrationBase):
    """
    Schema for submitting registration.
    
    Requires agreement to terms before submission.
    """
    agreed_to_terms: bool = Field(
        ..., 
        description="User must agree to event terms and cancellation policy"
    )
    event_id: str
    team_id: str | None = None


class RegistrationUpdate(BaseModel):
    """
    Schema for updating registration.
    
    Only allowed when event status is REGISTRATION_OPEN.
    """
    event_id: str
    team_id: str | None = None
    desired_shift: DesiredShift | None = None
    needs_vehicle_route_1: bool | None = None
    needs_vehicle_route_2: bool | None = None
    needs_vehicle_route_3: bool | None = None
    needs_vehicle_route_4: bool | None = None
    pickup_location_route_1: str | None = None
    pickup_location_route_4: str | None = None
    comments: str | None = None


class RegistrationResponse(RegistrationBase):
    """
    Registration response showing current status and allocations.
    
    Enables RAG to answer: 'Am I registered?', 'What flight am I on?'
    """
    id: str = Field(..., description="Registration UUID")
    user_id: str = Field(..., description="User UUID")
    event_id: str = Field(..., description="Event UUID")
    
    # Allocation results (populated after admin runs allocation)
    allocated_flight_id: str | None = Field(None, description="Assigned flight UUID")
    allocated_flight_code: str | None = Field(None, description="Assigned flight code")
    
    allocated_vehicle_1_id: str | None = Field(None, description="Assigned vehicle for Route 1")
    allocated_vehicle_2_id: str | None = Field(None, description="Assigned vehicle for Route 2")
    allocated_vehicle_3_id: str | None = Field(None, description="Assigned vehicle for Route 3")
    allocated_vehicle_4_id: str | None = Field(None, description="Assigned vehicle for Route 4")
    
    hotel_room_code: str | None = Field(None, description="Assigned hotel room number")
    
    class Config:
        from_attributes = True


class CancelVehicleRequest(BaseModel):
    """
    Request to cancel vehicle assignment for a specific route.
    
    Allows users to opt out of vehicle after allocation if they find alternative transport.
    """
    route_number: int = Field(..., ge=1, le=4, description="Route number to cancel (1-4)")
    reason: str | None = Field(None, description="Reason for cancellation")
