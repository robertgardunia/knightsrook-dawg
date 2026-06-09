from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings  # noqa: F401 — validates env on import
from app.db import init_pool, close_pool
from app.log import configure_logging
from app.events import init_event_bus
from app.api.health import router as health_router
from app.api.topics import router as topics_router
from app.api.store import router as store_router
from app.api.experiment import router as experiment_router
from app.dashboard_stream import router as stream_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_pool()
    await init_event_bus()
    yield
    await close_pool()


app = FastAPI(title="knightsrook-dawg", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(topics_router)
app.include_router(store_router)
app.include_router(experiment_router)
app.include_router(stream_router)
