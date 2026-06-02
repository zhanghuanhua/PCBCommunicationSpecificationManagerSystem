from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.database import init_db
from app.routers import pages


app = FastAPI(title="EAP-EQP Interface Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages.router)


@app.on_event("startup")
def on_startup() -> None:
    init_db()
