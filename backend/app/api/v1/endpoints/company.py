from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def create_company():
    return {"message": "Create company stub"}

@router.get("/")
def get_company():
    return {"message": "Get company stub"}
