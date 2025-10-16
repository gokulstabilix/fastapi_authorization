from fastapi import APIRouter

from authorization_service.api.v1.endpoints import users, auth

api_router = APIRouter()
api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(users.router, tags=["users"])
