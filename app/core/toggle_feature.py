from app.routers import job_sync_access, job_sync_aggregation_schema, order_lock, product_tax_moadian,\
    prometheus, components_routes, component, access_management, monitoring, products_daily_purchased
from app.core.feature_flag import feature_status

def get_active_features():
    features = []
    if feature_status('order_lock'):
        features.append(order_lock)
    if feature_status('product_tax_moadian'):
        features.append(product_tax_moadian)
    if feature_status('prometheus'):
        features.append(prometheus)
    if feature_status('components_routes'):
        features.append(components_routes)
    if feature_status('component'):
        features.append(component)
    if feature_status('aggregation'):
        features.append(job_sync_aggregation_schema)
    if feature_status('access_management'):
        features.append(access_management)
        features.append(job_sync_access)
    if feature_status('monitoring'):
        features.append(monitoring)
    if feature_status('products_daily_purchased'):
        features.append(products_daily_purchased)
    return features
