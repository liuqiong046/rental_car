"""API router assembly for versioned rental_car routes."""

from fastapi import APIRouter

from app.apps.admin.router import router as admin_router
from app.apps.auth.router import router as auth_router
from app.apps.cities.router import router as cities_router
from app.apps.identity.router import router as identity_router
from app.apps.orders.router import router as orders_router
from app.apps.payments.router import router as payments_router
from app.apps.system.router import router as system_router
from app.apps.users.router import router as users_router
from app.apps.vehicles.router import router as vehicles_router
from app.apps.wholesale_orders.router import router as wholesale_orders_router
from app.core.config import settings

api_router = APIRouter(prefix=settings.api_v1_prefix)
api_router.include_router(admin_router)
api_router.include_router(auth_router)
api_router.include_router(cities_router)
api_router.include_router(identity_router)
api_router.include_router(orders_router)
api_router.include_router(payments_router)
api_router.include_router(system_router)
api_router.include_router(users_router)
api_router.include_router(vehicles_router)
api_router.include_router(wholesale_orders_router)

# TODO(WF-P0-13/WF-P0-20): 对齐两端 H5 和 PRD，继续补齐 manager-todos、
# work-orders、deposits、renewals、early-returns、after-sales、complaints、
# finance、refunds、settlements、messages、audit-logs 和 P0 回归路由。
