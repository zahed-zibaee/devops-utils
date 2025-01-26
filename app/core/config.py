from pydantic_settings import BaseSettings


def get_git_head():
    with open('app/git-head', 'r') as file:
        return file.read()
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
    # PostgreSQL write config
    DB_POSTGRES_WRITE_HOST: str = '127.0.0.1'
    DB_POSTGRES_WRITE_DATABASE_ACCESS: str = 'accssmngmnt'
    DB_POSTGRES_WRITE_DATABASE_LEGACY: str = 'legacy'
    DB_POSTGRES_WRITE_USERNAME: str = 'postgres'
    DB_POSTGRES_WRITE_PORT: str = '5432'
    DB_POSTGRES_WRITE_PASSWORD: str = ''
    # PostgreSQL write config
    DB_POSTGRES_READ_HOST: str = '127.0.0.1'
    DB_POSTGRES_READ_DATABASE_ACCESS: str = 'accssmngmnt'
    DB_POSTGRES_READ_DATABASE_LEGACY: str = 'legacy'
    DB_POSTGRES_READ_USERNAME: str = 'postgres'
    DB_POSTGRES_READ_PORT: str = '5432'
    DB_POSTGRES_READ_PASSWORD: str = ''
    # Toggle Feature
    DISABLED_FEATURES: list = []  
    # Argocd
    ARGOCD_USERNAME: str = ''
    ARGOCD_PASSWORD: str = ''
    ARGOCD_URL: str = ''
    # Gitlab
    GITLAB_URL: str = 'https://gitlab.snappcloud.io'
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
    REDIS_PASSWORD: str | None = None
    # Kubernetes
    K8S_API_URL: str = ''
    K8S_API_TOKEN: str = ''
    # DB aggregations values
    DB_PG_AG_USERNAME: str = ''
    DB_PG_AG_HOST: str = ''
    DB_PG_AG_STAGING_HOST: str = ''
    DB_PG_AG_SECRET_NAME: str = ''
    # Job access sync
    JOB_ACCESS_NAME: str = 'access-sync'
    JOB_ACCESS_IMAGE: str = 'reg.snapp.supply/access-sync:v1.0.3'
    JOB_ACCESS_SECRET: str = 'access-sync'
    JOB_ACCESS_CONFIG_MAP: str = 'access-sync'
    JOB_ACCESS_NAMESPACE: str = 'snappsupply-staging'
    # Job Aggregation sync 
    JOB_AG_SECRET: str = 'aggregation-sync'
    JOB_AG_CONFIG_MAP: str = 'aggregation-sync'
    JOB_AG_SYNC_IMAGE_VIEWS: str = 'reg.snapp.supply/aggregation-tables-backup:v1'
    JOB_AG_SYNC_IMAGE_TABLES: str = 'reg.snapp.supply/aggregation-tables-backup:v1'
    JOB_AG_SYNC_NAME: str = 'aggregation-sync'
    JOB_AG_SYNC_SOURCE_NAMESPACE: str = 'snappsupply-staging'
    # Jobs
    JOB_CPU_REQUEST: str = '30m'
    JOB_MEMORY_REQUEST: str = '20Mi'
    JOB_CPU_LIMIT: str = '300m'
    JOB_MEMORY_LIMIT: str = '200Mi'
    # Hash
    GIT_HASH: str = get_git_head()
    

settings = Settings()
