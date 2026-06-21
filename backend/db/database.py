from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError

from backend.db.models import Base
from backend.config import DATABASE_URL

engine = create_engine(DATABASE_URL, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init_db(app=None):
    """Create DB tables if they do not exist."""
    try:
        Base.metadata.create_all(bind=engine)
        if app:
            app.logger.info('Database initialized (tables created)')
    except OperationalError as e:
        if app:
            app.logger.error('Could not initialize database: %s', e)
        else:
            print('Could not initialize database:', e)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

