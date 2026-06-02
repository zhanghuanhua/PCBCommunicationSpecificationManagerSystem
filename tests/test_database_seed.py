from sqlmodel import Session, SQLModel, create_engine, select

from app.models import ApiInterface, InterfaceDirection
from app.seed import seed_demo_data


def test_seed_demo_data_creates_initial_interface():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)

    seed_demo_data(engine)

    with Session(engine) as session:
        interface = session.exec(select(ApiInterface)).one()

    assert interface.code == "EQP-EAP-001"
    assert interface.name == "连线检查"
    assert interface.direction == InterfaceDirection.EQP_TO_EAP
    assert interface.caller == "EQP"
    assert interface.provider == "EAP"
