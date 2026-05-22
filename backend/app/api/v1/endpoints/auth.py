from fastapi import APIRouter

router = APIRouter()

@router.post("/signup")
def signup():
    return {"message": "Signup stub"}

@router.post("/login")
def login():
    return {"message": "Login stub"}
