from app.routers import lock, product_tax_moadian, prometheus, components_routes
from app.core.feature_status import feature_status

def get_active_features():
    features = []
    if feature_status('lock'):
        features.append(lock)
    if feature_status('product_tax_moadian'):
        features.append(product_tax_moadian)
    if feature_status('prometheus'):
        features.append(prometheus)
    if feature_status('components_routes'):
        features.append(components_routes)
    return features
