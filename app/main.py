from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routers import pages


app = FastAPI(title="EAP-EQP Interface Manager")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(pages.router)
