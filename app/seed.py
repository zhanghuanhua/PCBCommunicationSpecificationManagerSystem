from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, select

from app.database import engine as default_engine
from app.database import init_db
from app.models import ApiInterface, InterfaceDirection


def seed_demo_data(engine: Engine | None = None) -> None:
    active_engine = engine or default_engine
    if engine is None:
        init_db()
    else:
        SQLModel.metadata.create_all(active_engine)

    with Session(active_engine) as session:
        existing = session.exec(select(ApiInterface)).first()
        if existing:
            return

        demo = ApiInterface(
            code="EQP-EAP-001",
            name="连线检查",
            direction=InterfaceDirection.EQP_TO_EAP,
            api_name="EQP_AliveCheck",
            caller="EQP",
            provider="EAP",
            requirement="EQP 检查与 EAP 是否连线",
            scenario="EQP 定时检查 EAP 联机状态",
            service_description="EQP 检查与 EAP 是否连线",
        )
        session.add(demo)
        session.commit()


if __name__ == "__main__":
    seed_demo_data()
