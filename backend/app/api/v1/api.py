from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    registrations,
    journey,
    gala,
    admin_gala,
    admin_core,
    admin_res,
    admin_hotel,
    admin_vehicles,
    admin_dashboard,
    admin_notifications,
    allocations,
)

router = APIRouter()

# Public
router.include_router(auth.router, prefix="/auth", tags=["auth"])

# User
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(registrations.router, prefix="/registrations", tags=["registrations"])
router.include_router(journey.router, prefix="/journey", tags=["journey"])

# Gala
router.include_router(gala.router, prefix="/gala", tags=["gala"])

# Admin
router.include_router(admin_core.router, prefix="/admin", tags=["admin-core"])
router.include_router(admin_res.router, prefix="/admin/resources", tags=["admin-resources"])
router.include_router(admin_hotel.router, prefix="/admin/hotels", tags=["admin-hotels"])
router.include_router(admin_vehicles.router, prefix="/admin/vehicles", tags=["admin-vehicles"])
router.include_router(admin_gala.router, prefix="/admin/gala", tags=["admin-gala"])
router.include_router(admin_dashboard.router, prefix="/admin/dashboard", tags=["admin-dashboard"])
router.include_router(admin_notifications.router, prefix="/admin/notifications", tags=["admin-notifications"])
router.include_router(allocations.router, prefix="/admin/allocations", tags=["admin-allocations"])
