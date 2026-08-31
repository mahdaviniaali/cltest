from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import ads, auth, crawl, inspector, searches, taxonomy
from app.db.engine import recover_interrupted_jobs, upgrade_schema
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    upgrade_schema()
    recover_interrupted_jobs()
    yield


app = FastAPI(title="Bama Crawler API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(searches.router, prefix="/api")
app.include_router(ads.router, prefix="/api")
app.include_router(crawl.router, prefix="/api")
app.include_router(inspector.router, prefix="/api")
app.include_router(taxonomy.router, prefix="/api")


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
