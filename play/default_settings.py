_DB = 'play'

MONGO_URI = 'mongodb://127.0.0.1:27017/{}'.format(_DB)
WTF_CSRF_SECRET_KEY = 'abcabcabcabc'
SECRET_KEY = 'sdklfjoi4o2ij34foi23j'


CELERY_TIMEZONE = 'Europe/London'
CELERY_ENABLE_UTC = True
BROKER_URL = MONGO_URI
CELERY_IGNORE_RESULT = True
CELERY_RESULT_BACKEND = MONGO_URI
CELERY_MONGODB_BACKEND_SETTINGS = {
    'database': _DB
}
