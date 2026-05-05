import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
from app.core.config import settings

# Initialize standard Python logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="FileCutter API",
    description="Backend for the FileCutter local file-triaging tool.",
    version="0.1.0",
)

# Configure CORS for local frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
    ],  # Typical React/Vite dev ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory settings state (initialized from config)
class AppSettings(BaseModel):
    active_model: str = ""
    downloads_path: str = settings.downloads_path

app_state = AppSettings()

class SettingsUpdate(BaseModel):
    active_model: str
    downloads_path: str

@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to FileCutter API"}

@app.get("/api/models")
async def get_models():
    """Fetches the list of models from the LM Studio local server."""
    # Assuming LM Studio running locally provides models at /v1/models
    # We parse the base url from settings to get the base for /v1/models
    base_url = settings.lm_studio_url.replace('/chat/completions', '')
    models_url = f"{base_url}/models"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(models_url, timeout=5.0)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        logger.error(f"Failed to fetch models from LM Studio: {e}")
        # Return empty list if LM Studio is unreachable so the UI doesn't break
        return {"data": []}

@app.get("/api/health/lm_studio")
async def health_lm_studio():
    """Pings the LM Studio API to verify it's reachable."""
    base_url = settings.lm_studio_url.replace('/chat/completions', '')
    models_url = f"{base_url}/models"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(models_url, timeout=2.0)
            response.raise_for_status()
            return {"status": "ok"}
    except Exception as e:
        logger.warning(f"LM Studio health check failed: {e}")
        raise HTTPException(status_code=503, detail="LM Studio is unreachable")

@app.get("/api/settings")
async def get_settings():
    """Returns the current application settings."""
    return app_state

@app.post("/api/settings")
async def update_settings(new_settings: SettingsUpdate):
    """Updates the application state with the new settings."""
    app_state.active_model = new_settings.active_model
    app_state.downloads_path = new_settings.downloads_path

    # Optionally update the config or perform other side effects if necessary
    # In this context, we update the app_state which could be used by other parts of the app
    logger.info(f"Updated settings: model={app_state.active_model}, path={app_state.downloads_path}")
    return app_state
