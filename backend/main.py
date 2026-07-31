import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from database.connection import SessionLocal, Base, engine
from database.seeding import seed_database
from app.config import settings

# Import routers
from routers import (
    auth_router, employees_router, assets_router, categories_router,
    licenses_router, repairs_router, announcements_router, guidelines_router,
    notifications_router, activity_router, dashboard_router
)

app = FastAPI(
    title="IT Asset Management System API",
    description="Backend API for Quadrant IT Services Full-Stack Application",
    version="1.0.0"
)

# CORS Middleware Setup
origins = settings.cors_origins_list
allow_cred = True
if "*" in origins:
    allow_cred = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=allow_cred,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup Event for Seeding Database
@app.on_event("startup")
def startup_event():
    # Make sure connection works and run seeding
    db = SessionLocal()
    try:
        seed_database(db)
    except Exception as e:
        print(f"Error seeding database during startup: {e}")
    finally:
        db.close()

# Register Routers
app.include_router(auth_router)
app.include_router(employees_router)
app.include_router(assets_router)
app.include_router(categories_router)
app.include_router(licenses_router)
app.include_router(repairs_router)
app.include_router(announcements_router)
app.include_router(guidelines_router)
app.include_router(notifications_router)
app.include_router(activity_router)
app.include_router(dashboard_router)

from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    print("FastAPI Validation Error Details:")
    print("Errors:", exc.errors())
    try:
        body = await request.json()
        print("Request JSON Body:", body)
    except Exception:
        body = await request.body()
        print("Request Raw Body:", body)
    
    formatted_errors = jsonable_encoder(exc.errors())
    error_msgs = []
    for err in formatted_errors:
        msg = err.get("msg", "Validation error").replace("Value error, ", "")
        error_msgs.append(msg)
    detail_str = "; ".join(error_msgs) if error_msgs else "Validation error"

    return JSONResponse(
        status_code=422,
        content={"detail": detail_str, "errors": formatted_errors}
    )

@app.get("/")
def read_root():
    return {
        "status": "online",
        "message": "IT Asset Management System Backend API is active",
        "database": "connected"
    }
