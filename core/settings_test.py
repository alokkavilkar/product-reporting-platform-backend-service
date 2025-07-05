from .settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('TEST_DB_NAME'),          
        'USER': os.environ.get('TEST_DB_USER'),           
        'PASSWORD': os.environ.get('TEST_DB_PASSWORD'),  
        'HOST': os.environ.get('TEST_DB_HOST'),  
        'PORT': os.environ.get('TEST_DB_PORT'),             
        'OPTIONS': {
            'sslmode': os.environ.get('TEST_DB_SSLMODE'),
        }
    }
}

assert not DATABASES['default']['NAME'] in ['prod_db_name', 'real_prod']
