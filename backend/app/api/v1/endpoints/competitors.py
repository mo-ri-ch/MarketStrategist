from fastapi import APIRouter

router = APIRouter()

@router.post("/")
def add_competitor():
    return {"message": "Add competitor stub"}

@router.get("/")
def list_competitors():
    return {"message": "List competitors stub"}
