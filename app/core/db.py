from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError, OperationalError

from app.core.config import settings
from app.core.logging import logger


def postgres_url_builder(username, password, host, port, database):
    return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"

def create_pg_session(database, mode):
    selected_db  = {
        "write": {
            "access": settings.DB_POSTGRES_WRITE_DATABASE_ACCESS,
            "app-settings": settings.DB_POSTGRES_WRITE_DATABASE_APP_SETTINGS,
            "legacy": settings.DB_POSTGRES_WRITE_DATABASE_LEGACY,
            "order": settings.DB_POSTGRES_WRITE_DATABASE_ORDER,
            "order-dispatch": settings.DB_POSTGRES_WRITE_DATABASE_ORDER_DISPATCH,
            "otp": settings.DB_POSTGRES_WRITE_DATABASE_OTP,
            "payment": settings.DB_POSTGRES_WRITE_DATABASE_PAYMENT,
            "pricing": settings.DB_POSTGRES_WRITE_DATABASE_PRICING,
            "product": settings.DB_POSTGRES_WRITE_DATABASE_PRODUCT,
            "seller": settings.DB_POSTGRES_WRITE_DATABASE_SELLER,
            "supply-wallet": settings.DB_POSTGRES_WRITE_DATABASE_SUPPLY_WALLET,
            "user": settings.DB_POSTGRES_WRITE_DATABASE_USER,
            "voucher": settings.DB_POSTGRES_WRITE_DATABASE_VOUCHER,
            "wallet": settings.DB_POSTGRES_WRITE_DATABASE_WALLET,
        },
        "read": {
            "access": settings.DB_POSTGRES_READ_DATABASE_ACCESS,
            "app-settings": settings.DB_POSTGRES_READ_DATABASE_APP_SETTINGS,
            "legacy": settings.DB_POSTGRES_READ_DATABASE_LEGACY,
            "order": settings.DB_POSTGRES_READ_DATABASE_ORDER,
            "order-dispatch": settings.DB_POSTGRES_READ_DATABASE_ORDER_DISPATCH,
            "otp": settings.DB_POSTGRES_READ_DATABASE_OTP,
            "payment": settings.DB_POSTGRES_READ_DATABASE_PAYMENT,
            "pricing": settings.DB_POSTGRES_READ_DATABASE_PRICING,
            "product": settings.DB_POSTGRES_READ_DATABASE_PRODUCT,
            "seller": settings.DB_POSTGRES_READ_DATABASE_SELLER,
            "supply-wallet": settings.DB_POSTGRES_READ_DATABASE_SUPPLY_WALLET,
            "user": settings.DB_POSTGRES_READ_DATABASE_USER,
            "voucher": settings.DB_POSTGRES_READ_DATABASE_VOUCHER,
            "wallet": settings.DB_POSTGRES_READ_DATABASE_WALLET,
        }
    }.get(mode, {}).get(database)
    if not selected_db:
        raise ValueError(f"Database '{database}' not found for mode '{mode}'")
    
    engine = create_engine(
        postgres_url_builder(
            username=settings.DB_POSTGRES_WRITE_USERNAME if mode == "write" else settings.DB_POSTGRES_READ_USERNAME,
            password=settings.DB_POSTGRES_WRITE_PASSWORD if mode == "write" else settings.DB_POSTGRES_READ_PASSWORD,
            host=settings.DB_POSTGRES_WRITE_HOST if mode == "write" else settings.DB_POSTGRES_READ_HOST,
            port=settings.DB_POSTGRES_WRITE_PORT if mode == "write" else settings.DB_POSTGRES_READ_PORT,
            database=selected_db
        ),
        pool_timeout=60,
        pool_size=5,
        max_overflow=10,
        pool_recycle=1800,
        pool_pre_ping=True
    )
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


engine_postgres_aggregation_read = create_engine(
    postgres_url_builder(
        username=settings.DB_POSTGRES_AGGREGATION_READ_USERNAME,
        password=settings.DB_POSTGRES_AGGREGATION_READ_PASSWORD,
        host=settings.DB_POSTGRES_AGGREGATION_READ_HOST,
        port=settings.DB_POSTGRES_AGGREGATION_READ_PORT,
        database=settings.DB_POSTGRES_AGGREGATION_READ_DATABASE
    ),
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,  
    pool_recycle=1800,
    pool_pre_ping=True
)

engine_postgres_aggregation_write = create_engine(
    postgres_url_builder(
        username=settings.DB_POSTGRES_AGGREGATION_WRITE_USERNAME,
        password=settings.DB_POSTGRES_AGGREGATION_WRITE_PASSWORD,
        host=settings.DB_POSTGRES_AGGREGATION_WRITE_HOST,
        port=settings.DB_POSTGRES_AGGREGATION_WRITE_PORT,
        database=settings.DB_POSTGRES_AGGREGATION_WRITE_DATABASE
    ),
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,  
    pool_recycle=1800,
    pool_pre_ping=True
)

PostgresSessionLocalReadAggregation = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres_aggregation_read)
PostgresSessionLocalWriteAggregation = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres_aggregation_write)

def get_db_postgres(database, mode):
    db_session = create_pg_session(database, mode)
    db = db_session()
    try:
        yield db
    except OperationalError as e:
        logger.error(f"Operational error while connecting to the PostgreSQL {mode} database for {database}: {e}")
        db.rollback()  
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError as e:
        logger.error(f"Error with the PostgreSQL {mode} database for {database}: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()

def get_db_postgres_read(domain):
    """
    Return the read database session generator for the given domain.
    """
    return get_db_postgres(domain, 'read')

def get_db_postgres_write(domain):
    """
    Return the write database session generator for the given domain.
    """
    return get_db_postgres(domain, 'write')
      
def get_db_postgres_aggregation_read():
    db = PostgresSessionLocalReadAggregation()
    try:
        yield db
    except OperationalError as e:
        logger.error(f"Operational error while connecting to the PostgreSQL aggregation write database: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError as e:
        logger.error(f"Error with the PostgreSQL aggregation write database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
        
def get_db_postgres_aggregation_write():
    db = PostgresSessionLocalWriteAggregation()
    try:
        yield db
    except OperationalError as e:
        logger.error(f"Operational error while connecting to the PostgreSQL aggregation write database: {e}")
        raise HTTPException(status_code=500, detail="Database connection error")
    except SQLAlchemyError as e:
        logger.error(f"Error with the PostgreSQL aggregation write database: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
    finally:
        db.close()
