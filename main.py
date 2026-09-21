from fastapi import FastAPI
from app.routers import resume_parser, users

app = FastAPI(
    title="Murialo AI Engine",
    description="AI Engine Murialo — modul kecerdasan buatan untuk rekrutmen",
    version="1.0.0"
)

app.include_router(resume_parser.router)
app.include_router(users.router)

@app.get("/")
def read_root():
    return {"message": "Murialo AI Engine is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
