from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import HTTPException
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.database import db
from app.core.exceptions import (
    FoodBookException,
    foodbook_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Import route routers
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.taste_profiles import router as taste_router
from app.api.routes.restaurants import router as restaurants_router
from app.api.routes.branches import router as branches_router
from app.api.routes.menus import router as menus_router
from app.api.routes.reviews import router as reviews_router
from app.api.routes.saved_restaurants import router as saved_router
from app.api.routes.collections import router as collections_router
from app.api.routes.search import router as search_router
from app.api.routes.recommendations import router as rec_router

# Setup logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("foodbook.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("FoodBook Backend starting up...")
    logger.info(f"Connected to Supabase at: {settings.SUPABASE_URL}")
    yield
    # Shutdown
    logger.info("FoodBook Backend shutting down...")
    await db.close()


app = FastAPI(
    title="FoodBook API",
    description="AI-Powered Personalized Food Discovery & Recommendation Backend for Pakistan",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Configure CORS
origins = settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Custom Exception Handlers
app.add_exception_handler(FoodBookException, foodbook_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
if not settings.DEBUG:
    app.add_exception_handler(Exception, general_exception_handler)


# Health Check Endpoint



@app.get("/api/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "database": "connected",
        "version": "1.0.0"
    }


# Include API Routers under /api prefix
api_prefix = settings.API_V1_PREFIX.rstrip("/")

app.include_router(auth_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(taste_router, prefix=api_prefix)
app.include_router(restaurants_router, prefix=api_prefix)
app.include_router(branches_router, prefix=api_prefix)
app.include_router(menus_router, prefix=api_prefix)
app.include_router(reviews_router, prefix=api_prefix)
app.include_router(saved_router, prefix=api_prefix)
app.include_router(collections_router, prefix=api_prefix)
app.include_router(search_router, prefix=api_prefix)
app.include_router(rec_router, prefix=api_prefix)


# Also mount taste profile routes under /api/users/me/taste-profile for frontend convenience
@app.get(f"{api_prefix}/users/me/taste-profile", tags=["Taste Profiles"], include_in_schema=False)
async def get_user_taste_profile_alias(
    request: Request
):
    from app.api.routes.taste_profiles import get_my_taste_profile, get_taste_service
    from app.core.dependencies import get_current_user, get_token_from_header
    token = await get_token_from_header(request.headers.get("authorization"))
    user = await get_current_user(token=token, database=db)
    service = get_taste_service(db)
    return await get_my_taste_profile(current_user=user, service=service)


# Mount Frontend Single Page Application (SPA)
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../frontend"))
if os.path.isdir(frontend_dir):
    css_dir = os.path.join(frontend_dir, "css")
    js_dir = os.path.join(frontend_dir, "js")
    if os.path.isdir(css_dir):
        app.mount("/css", StaticFiles(directory=css_dir), name="css")
    if os.path.isdir(js_dir):
        app.mount("/js", StaticFiles(directory=js_dir), name="js")

    @app.get("/", tags=["Frontend"])
    async def serve_spa_index(request: Request):
        accept = request.headers.get("accept", "")
        # Standard browsers request text/html
        if "text/html" in accept:
            index_file = os.path.join(frontend_dir, "index.html")
            if os.path.exists(index_file):
                return FileResponse(index_file)
        return {
            "app": "FoodBook Backend API",
            "status": "online",
            "version": "1.0.0",
            "docs": "/docs",
            "environment": settings.ENVIRONMENT
        }



