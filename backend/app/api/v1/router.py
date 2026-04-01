from fastapi import APIRouter

from app.api.v1.endpoints import bids

api_router = APIRouter()
api_router.include_router(bids.router)
