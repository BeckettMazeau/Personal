import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to FileCutter API"}
