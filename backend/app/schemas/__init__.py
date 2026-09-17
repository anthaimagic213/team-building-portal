from app.schemas.auth import (
    LoginRequest,
    TokenResponse,
    RefreshTokenRequest,
)

from app.schemas.user import (
    TeamBase,
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserListItem as UserListItemSchema,
)

from app.schemas.event import (
    EventStatus,
    EventBase,
    EventCreate,
    EventUpdate,
    EventResponse,
)

from app.schemas.register import (
    RegistrationCreate,
    RegistrationUpdate,
    RegistrationResponse,
)

from app.schemas.admin import (
    EventStatistics,
    TeamStatistics,
    UserListItem,
    FlightStatistics,
    VehicleStatistics,
    ExportRequest,
)

from app.schemas.resource import (
    FlightCreate,
    FlightUpdate,
    FlightResponse,
    VehicleCreate,
    VehicleUpdate,
    VehicleResponse,
)

from app.schemas.allocation import (
    FlightAllocationResult,
    ManualFlightAdjustment,
    VehicleAllocationResult,
    ManualVehicleAdjustment,
    HotelImportResult,
)

from app.schemas.gala import (
    SeatStatus,
    GalaTurnStatus,
    GalaConfigCreate,
    GalaConfigUpdate,
    GalaConfigResponse,
    GalaSeatCreate,
    GalaSeatUpdate,
    GalaSeatResponse,
    SeatLockRequest,
    SeatConfirmRequest,
    SeatReleaseRequest,
    GalaSeatingLayout,
    GalaTeamTurnResponse,
)

from app.schemas.journey import (
    JourneyFlightInfo,
    JourneyVehicleInfo,
    JourneyHotelInfo,
    JourneyGalaInfo,
    EventScheduleItem,
    NotificationItem,
    MyJourneyResponse,
    JourneySummary,
)

from app.schemas.notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    EmailTemplate,
)

__all__ = [
    # Auth
    "LoginRequest",
    "TokenResponse",
    "RefreshTokenRequest",

    # User & Team
    "TeamBase",
    "TeamCreate",
    "TeamUpdate",
    "TeamResponse",
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserListItemSchema",

    # Event
    "EventStatus",
    "EventBase",
    "EventCreate",
    "EventUpdate",
    "EventResponse",

    # Registration
    "RegistrationCreate",
    "RegistrationUpdate",
    "RegistrationResponse",

    # Admin Dashboard
    "EventStatistics",
    "TeamStatistics",
    "UserListItem",
    "FlightStatistics",
    "VehicleStatistics",
    "ExportRequest",

    # Resources
    "FlightCreate",
    "FlightUpdate",
    "FlightResponse",
    "VehicleCreate",
    "VehicleUpdate",
    "VehicleResponse",

    # Allocation
    "FlightAllocationResult",
    "ManualFlightAdjustment",
    "VehicleAllocationResult",
    "ManualVehicleAdjustment",
    "HotelImportResult",

    # Gala
    "SeatStatus",
    "GalaTurnStatus",
    "GalaConfigCreate",
    "GalaConfigUpdate",
    "GalaConfigResponse",
    "GalaSeatCreate",
    "GalaSeatUpdate",
    "GalaSeatResponse",
    "SeatLockRequest",
    "SeatConfirmRequest",
    "SeatReleaseRequest",
    "GalaSeatingLayout",
    "GalaTeamTurnResponse",

    # Journey
    "JourneyFlightInfo",
    "JourneyVehicleInfo",
    "JourneyHotelInfo",
    "JourneyGalaInfo",
    "EventScheduleItem",
    "NotificationItem",
    "MyJourneyResponse",
    "JourneySummary",

    # Notification
    "NotificationCreate",
    "NotificationResponse",
    "NotificationListResponse",
    "EmailTemplate",
]
