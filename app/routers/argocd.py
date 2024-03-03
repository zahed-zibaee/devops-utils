import os


ARGOCD_USERNAME = os.getenv("ARGOCD_USERNAME")
ARGOCD_PASSWORD = os.getenv("ARGOCD_PASSWORD")
ARGOCD_URL = os.getenv("ARGOCD_URL")



def refresh_app():
    os.system(f"argocd login --username {ARGOCD_USERNAME} --password {ARGOCD_PASSWORD} --grpc-web {ARGOCD_URL} --grpc-web-root-path /grpc-api")
    
    # Refresh order app
    os.system("argocd app get staging-order --refresh")
    # Refresh legacy app
    os.system("argocd app get staging-legacy --refresh")