from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def chat_response():
    return {"message": "Chat response stub"}
