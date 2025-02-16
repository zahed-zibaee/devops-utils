from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import logger


def postgres_url_builder(username, password, host, port, database):
    return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    
engine_postgres_read_access = create_engine(
    postgres_url_builder(
        username=settings.DB_POSTGRES_READ_USERNAME,
        password=settings.DB_POSTGRES_READ_PASSWORD,
        host=settings.DB_POSTGRES_READ_HOST,
        port=settings.DB_POSTGRES_READ_PORT,
        database=settings.DB_POSTGRES_READ_DATABASE_ACCESS
    ),
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,  
    pool_recycle=-1,
    pool_pre_ping=True
)

engine_postgres_write_access = create_engine(
    postgres_url_builder(
        username=settings.DB_POSTGRES_WRITE_USERNAME,
        password=settings.DB_POSTGRES_WRITE_PASSWORD,
        host=settings.DB_POSTGRES_WRITE_HOST,
        port=settings.DB_POSTGRES_WRITE_PORT,
        database=settings.DB_POSTGRES_READ_DATABASE_ACCESS
    ),
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,  
    pool_recycle=-1,
    pool_pre_ping=True
)

engine_postgres_read_legacy = create_engine(
    postgres_url_builder(
        username=settings.DB_POSTGRES_READ_USERNAME,
        password=settings.DB_POSTGRES_READ_PASSWORD,
        host=settings.DB_POSTGRES_READ_HOST,
        port=settings.DB_POSTGRES_READ_PORT,
        database=settings.DB_POSTGRES_READ_DATABASE_LEGACY
    ),
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,  
    pool_recycle=-1,
    pool_pre_ping=True
)

engine_postgres_write_legacy = create_engine(
    postgres_url_builder(
        username=settings.DB_POSTGRES_WRITE_USERNAME,
        password=settings.DB_POSTGRES_WRITE_PASSWORD,
        host=settings.DB_POSTGRES_WRITE_HOST,
        port=settings.DB_POSTGRES_WRITE_PORT,
        database=settings.DB_POSTGRES_READ_DATABASE_LEGACY
    ),
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,  
    pool_recycle=-1,
    pool_pre_ping=True
)

engine_postgres_aggregation = create_engine(
    postgres_url_builder(
        username=settings.DB_POSTGRES_AGGREGATION_USERNAME,
        password=settings.DB_POSTGRES_AGGREGATION_PASSWORD,
        host=settings.DB_POSTGRES_AGGREGATION_HOST,
        port=settings.DB_POSTGRES_AGGREGATION_PORT,
        database=settings.DB_POSTGRES_AGGREGATION_DATABASE
    ),
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,  
    pool_recycle=-1,
    pool_pre_ping=True
)

PostgresSessionLocalWriteAccess = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres_write_access)
PostgresSessionLocalReadAccess = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres_read_access)
PostgresSessionLocalWriteLegacy = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres_write_legacy)
PostgresSessionLocalReadLegacy = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres_read_legacy)
PostgresSessionLocalAggregation = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres_aggregation)


def Get_db_postgres_access_read():
    db = PostgresSessionLocalReadAccess()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the PostgreSQL read database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

def Get_db_postgres_access_write():
    db = PostgresSessionLocalWriteAccess()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the PostgreSQL write database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

def Get_db_postgres_legacy_read():
    db = PostgresSessionLocalReadLegacy()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the PostgreSQL read database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

def Get_db_postgres_legacy_write():
    db = PostgresSessionLocalWriteLegacy()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the PostgreSQL write database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
        
def Get_db_postgres_aggregation():
    db = PostgresSessionLocalAggregation()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the PostgreSQL read database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
