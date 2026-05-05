from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1 import router as api_v1

app = FastAPI(title="CUA-Lark API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_v1, prefix="/api/v1")