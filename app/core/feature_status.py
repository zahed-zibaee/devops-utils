from app.core.config import settings

def feature_status(feature):
    if feature in settings.DISABLED_FEATURES:
        return False
    else: 
        return True
