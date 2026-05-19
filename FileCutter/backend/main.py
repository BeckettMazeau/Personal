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

# CORS: FileCutter is a single-user local tool. Only the Vite dev server origin
# is allowed. The legacy ":3000" entry was dropped — confirm with the Vite
# config if a non-default port is ever introduced.
# allow_credentials is False because the nonce flow uses an explicit request
# body field, not cookies.
#
# NOTE: uvicorn should be launched with --host 127.0.0.1 so the API never
# binds to external interfaces. The launcher owns that flag.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to FileCutter API"}
