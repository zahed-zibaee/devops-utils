from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.logging import logger


def mysql_url_builder(username, password, host, port, database):
    return f"mysql://{username}:{password}@{host}:{port}/{database}"

def postgres_url_builder(username, password, host, port, database):
    return f"postgresql+psycopg2://{username}:{password}@{host}:{port}/{database}"
    
engine_mysql_write = create_engine(
    mysql_url_builder(
        username=settings.DB_MYSQL_WRITE_USERNAME,
        password=settings.DB_MYSQL_WRITE_PASSWORD,
        host=settings.DB_MYSQL_WRITE_HOST,
        port=settings.DB_MYSQL_WRITE_PORT,
        database=settings.DB_MYSQL_WRITE_DATABASE
    ),
    pool_timeout=1200,  
    pool_size=5,  
    max_overflow=10,  
    pool_recycle=-1,  
    pool_pre_ping=True,  
    connect_args={
        "connect_timeout": 10,
        "init_command": "SET SESSION innodb_lock_wait_timeout = 1200"
    }
)

engine_mysql_read = create_engine(
    mysql_url_builder(
        username=settings.DB_MYSQL_READ_USERNAME,
        password=settings.DB_MYSQL_READ_PASSWORD,
        host=settings.DB_MYSQL_READ_HOST,
        port=settings.DB_MYSQL_READ_PORT,
        database=settings.DB_MYSQL_READ_DATABASE
    ),
    pool_timeout=60,  
    pool_size=5,  
    max_overflow=10,  
    pool_recycle=-1,  
    pool_pre_ping=True,  
    connect_args={
        "connect_timeout": 10,  
        "init_command": "SET SESSION innodb_lock_wait_timeout = 120"
    }
)

engine_postgres_read = create_engine(
    postgres_url_builder(
        username=settings.DB_POSTGRES_READ_USERNAME,
        password=settings.DB_POSTGRES_READ_PASSWORD,
        host=settings.DB_POSTGRES_READ_HOST,
        port=settings.DB_POSTGRES_READ_PORT,
        database=settings.DB_POSTGRES_READ_DATABASE
    ),
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,  
    pool_recycle=-1,
    pool_pre_ping=True
)

engine_postgres_write = create_engine(
    postgres_url_builder(
        username=settings.DB_POSTGRES_WRITE_USERNAME,
        password=settings.DB_POSTGRES_WRITE_PASSWORD,
        host=settings.DB_POSTGRES_WRITE_HOST,
        port=settings.DB_POSTGRES_WRITE_PORT,
        database=settings.DB_POSTGRES_WRITE_DATABASE
    ),
    pool_timeout=60,
    pool_size=5,
    max_overflow=10,  
    pool_recycle=-1,
    pool_pre_ping=True
)
 
SessionLocalWrite = sessionmaker(autocommit=False, autoflush=False, bind=engine_mysql_write)
SessionLocalRead = sessionmaker(autocommit=False, autoflush=False, bind=engine_mysql_read)

PostgresSessionLocalWrite = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres_write)
PostgresSessionLocalRead = sessionmaker(autocommit=False, autoflush=False, bind=engine_postgres_read)

Base = declarative_base()

def get_db_mysql_write():
    db = SessionLocalWrite()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the write mysql database: {e}")
        raise
    finally:
        db.close()

def get_db_mysql_read():
    db = SessionLocalRead()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the read mysql database: {e}")
        raise
    finally:
        db.close()

def get_db_postgres_read():
    db = PostgresSessionLocalRead()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the read postgres database: {e}")
        raise
    finally:
        db.close()

def get_db_postgres_write():
    db = PostgresSessionLocalWrite()
    try:
        yield db
    except SQLAlchemyError as e:
        logger.error(f"Error connecting to the write postgres database: {e}")
        raise
    finally:
        db.close()