from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = 'devops-utils'
    PORT: int = 8000
    DEBUG: bool = True
    ENVIRONMENT: str = 'dev'
    # MYSQL WRITE config
    DB_MYSQL_WRITE_HOST: str = '127.0.0.1'
    DB_MYSQL_WRITE_DATABASE: str = 'mydatabase'
    DB_MYSQL_WRITE_USERNAME: str = 'root'
    DB_MYSQL_WRITE_PORT: str = '3306'
    DB_MYSQL_WRITE_PASSWORD: str = ''
    # MYSQL READ config
    DB_MYSQL_READ_HOST: str = '127.0.0.1'
    DB_MYSQL_READ_DATABASE: str = 'mydatabase'
    DB_MYSQL_READ_USERNAME: str = 'root'
    DB_MYSQL_READ_PORT: str = '3306'
    DB_MYSQL_READ_PASSWORD: str = ''    
    # Toggle Feature
    DISABLED_FEATURES: list = []  

settings = Settings()