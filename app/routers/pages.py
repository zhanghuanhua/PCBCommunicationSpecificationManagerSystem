from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from app.database import get_session
from app.models import ApiInterface, InterfaceDirection

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/")
def home(request: Request, session: Session = Depends(get_session)):
    interfaces = session.exec(select(ApiInterface).order_by(ApiInterface.code)).all()
    return templates.TemplateResponse(
        request,
        "interfaces_list.html",
        {
            "request": request,
            "title": "接口管理工作台",
            "interfaces": interfaces,
        },
    )


@router.get("/interfaces/new")
def new_interface(request: Request):
    return templates.TemplateResponse(
        request,
        "interface_form.html",
        {
            "request": request,
            "title": "新增接口",
            "directions": InterfaceDirection,
        },
    )
