from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


def mysql_url_builder(username , password, host, port, database):
    return f"mysql://{username}:{password}@{host}:{port}/{database}"
    
engine_mysql_write = create_engine(
        url = mysql_url_builder(
            username = settings.DB_MYSQL_WRITE_USERNAME,
            password = settings.DB_MYSQL_WRITE_PASSWORD,
            host = settings.DB_MYSQL_WRITE_HOST,
            port = settings.DB_MYSQL_WRITE_PORT, 
            database = settings.DB_MYSQL_WRITE_DATABASE
        )
    )
engine_mysql_read = create_engine(
        url = mysql_url_builder(
            username = settings.DB_MYSQL_READ_USERNAME,
            password = settings.DB_MYSQL_READ_PASSWORD,
            host = settings.DB_MYSQL_READ_HOST,
            port = settings.DB_MYSQL_READ_PORT, 
            database = settings.DB_MYSQL_READ_DATABASE
        )
    )
 
session_mysql_write = sessionmaker(autocommit=False, autoflush=False, bind=engine_mysql_write)
session_mysql_read = sessionmaker(autocommit=False, autoflush=False, bind=engine_mysql_write)

def get_db_mysql_write():
    db = session_mysql_write()
    try:
        yield db
    finally:
        db.close()

def get_db_mysql_read():
    db = session_mysql_read()
    try:
        yield db
    finally:
        db.close()
