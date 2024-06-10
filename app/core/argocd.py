import subprocess

from app.core.config import settings
from app.core.logging import logger
    

def refresh_app(app_name):
    version_res = subprocess.run(["argocd", "version", "--client"], capture_output=True, text=True)
    if version_res.check_returncode():
        logger.warning(f"argocd app not exist on host.")
        return
    try:
        res = subprocess.run(
            ["argocd", 
            "login",
            "--username",
            settings.ARGOCD_USERNAME,
            "--password",
            settings.ARGOCD_PASSWORD,
            "--grpc-web",
            settings.ARGOCD_URL,
            "--grpc-web-root-path",
            "/grpc-api",
            "--config",
            "/app/config"],
            capture_output=True, 
            text=True
        )
        if res.check_returncode():
            logger.warning("argocd can not login: " + version_res.stderr)
            return
        res = subprocess.run(
            ["argocd", 
            "--config",
            "/app/config",
            "app",
            "get",
            app_name,
            "--refresh"],
            capture_output=True, 
            text=True
        )
        if res.check_returncode():
            logger.warning(f"argocd can not refresh app {app_name}: " + version_res.stderr)
            return
    except Exception as e:
        logger.warning(f"argocd can not refresh app {app_name}: " + str(e))