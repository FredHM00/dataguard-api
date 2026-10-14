"""Agregador da v1: um prefixo por dominio."""

from fastapi import APIRouter

from app.api.v1 import auth, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
