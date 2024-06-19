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
    # Argocd
    ARGOCD_USERNAME: str = ''
    ARGOCD_PASSWORD: str = ''
    ARGOCD_URL: str = ''
    # Gitlab
    GITLAB_URL: str = ''
    GITLAB_ACCESS_TOKEN_MANIFEST: str = ''
    GITLAB_PROJECT_ID_MANIFEST: int = 1
    COMMIT_MESSAGE_CHANGE_ORDER_LOCK: str = 'Order lock have been changed by devops utils'
    # Services
    ORDER_FILE_PATH_MANIFEST: str = ''
    LEGACY_FILE_PATH_MANIFEST: str = ''
    ORDER_ARGOCD_APP_NAME: str = 'order'
    LEGACY_ARGOCD_APP_NAME: str = 'legacy'
    # redis
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ''
    # Kubernetes
    API_URL: str = ''
    API_TOKEN: str = ''
    # DB aggregations values
    AG_NAME: str = 'aggregation-sync'
    AG_NAMESPACE: str = ''
    AG_IMAGE_SCHEMA: str = ''
    AG_IMAGE_TABLES: str = ''
    AG_DB_USERNAME: str = ''
    AG_DB_HOST: str = ''
    AG_FILENAME: str = 'backup.sql'
    AG_DB_STAGING_HOST: str = ''
    AG_SECRET_NAME: str = ''
    AG_CPU_REQUEST: str = '30m'
    AG_MEMORY_REQUEST: str = '20Mi'
    AG_CPU_LIMIT: str = '300m'
    AG_MEMORY_LIMIT: str = '200Mi'

settings = Settings()
