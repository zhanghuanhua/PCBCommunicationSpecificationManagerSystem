from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import engine, init_db
from app.routers import exports, imports, interfaces, pages


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.engine = engine
    init_db()
    yield


app = FastAPI(title="EAP-EQP Interface Manager", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages.router)
app.include_router(interfaces.router)
app.include_router(exports.router)
app.include_router(imports.router)
