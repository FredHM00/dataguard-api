"""Agregador da v1: um prefixo por dominio."""

from fastapi import APIRouter

from app.api.v1 import audit, auth, records, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(records.router, prefix="/records", tags=["records"])
api_router.include_router(audit.router, prefix="/audit-logs", tags=["audit"])
