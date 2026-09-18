from fastapi import APIRouter

router = APIRouter(prefix="/resume-parser", tags=["Resume Parser"])

@router.get("/")
def resume_parser_status():
    return {"module": "resume-parser", "status": "ready"}
