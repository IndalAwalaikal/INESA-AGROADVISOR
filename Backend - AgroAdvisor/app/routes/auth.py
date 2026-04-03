from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import os

router = APIRouter(prefix="/api/auth", tags=["Auth"])

class LoginRequest(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(request: LoginRequest):
    # Read credentials strictly from environment variables
    valid_user = os.getenv("ADMIN_USERNAME")
    valid_pass = os.getenv("ADMIN_PASSWORD")
    valid_token = os.getenv("ADMIN_TOKEN", "fallback-token-but-should-be-in-env")
    
    if not valid_user or not valid_pass:
        raise HTTPException(status_code=500, detail="Konfigurasi admin belum diatur di server.")
        
    if request.username == valid_user and request.password == valid_pass:
        return {
            "sukses": True, 
            "pesan": "Login berhasil",
            "token": valid_token
        }
    
    raise HTTPException(status_code=401, detail="Username atau password salah")
