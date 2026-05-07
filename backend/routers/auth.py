from fastapi import APIRouter, HTTPException, Header
from typing import Optional

from backend.entities.requests import RegisterRequest, LoginRequest
from backend.services.auth_service import AuthorizationService, AuthError


router = APIRouter(prefix="/api", tags=['auth'])

_auth_service: Optional[AuthorizationService] = None

def init(service: AuthorizationService) -> None:
    global _auth_service
    _auth_service = service
    
def _get_token(authorization: Optional[str]) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Токен не передан")
    return authorization.split(" ", 1)[1]

@router.post("/register")
def register(body: RegisterRequest):
    try:
        result = _auth_service.register(body.username, body.password)
        return result
    except AuthError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(body: LoginRequest):
    try:
        result = _auth_service.login(body.username, body.password)
        return result
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
def logout(authorization: str = Header(None)):
    token = _get_token(authorization)   
    try:
        _auth_service.logout(token)
        return {"ok": True}
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.get("/me")
def me(authorization: str = Header(None)):
    token = _get_token(authorization)  
    try:
        user = _auth_service.get_current_user(token)
        return user.to_dict()
    except AuthError as e:
        raise HTTPException(status_code=401, detail=str(e))