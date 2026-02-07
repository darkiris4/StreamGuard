from sqlmodel import Session, SQLModel, create_engine

from core.config import settings


engine = create_engine(settings.database_url_sync, echo=False)
metadata = SQLModel.metadata


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    return Session(engine)
