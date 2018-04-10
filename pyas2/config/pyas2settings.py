'''
PYAS2_SETTINGS_FILE
You can overide this default file with you own.

    Linux:
    Add to $HOME/.bashrc
    export PYAS2_SETTINGS_FILE=/path/to/pyas2settings.py

    Windows:
    Add user or system var:
    PYAS2_SETTINGS_FILE=c:\\path\\to\\pyas2settings.py

'''
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'kx_ec2t3k1!o3iad-mucfny3gsk+9+^clskqoktxb0v4_^9ve&'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

PYAS2_ENV = os.environ.get('PYAS2_ENV', 'default')
PYAS2_ROOT = os.environ.get('PYAS2_ROOT',
        os.path.join(os.path.dirname(__file__), 'pyas2_%s' % PYAS2_ENV))

MEDIA_ROOT = os.path.join(PYAS2_ROOT, 'media')

MEDIA_URL = '/media/'  # Default, but not used
# SECURITY WARNING: don't serve /media to MEDIA_ROOT folder
# with file server (Apache, nginx, ...) without security (auth, ...)
# publics and privates certificates are located in (/media/pyas2/certificates)


PYAS2 = {
    'ENVIRONMENT': PYAS2_ENV,
    'DATADIR': PYAS2_ROOT,
    'MEDIAURI': 'pyas2',
    # As2 receiver ###
    'AS2HOST': 'localhost',  # set WAN IP or domaine hostname
    'AS2PORT': 8880,
    'AS2URI': 'as2receive',
    # MDN URL # uncomment to overide, default mdn url is build
    # this way  http(s)://AS2HOST:AS2PORT/AS2URI
    #'MDNURL': 'http(s)://localhost:8089/as2receive',
    'ASYNCMDNWAIT': 30,
    # https ########
    #'SSLCERTIFICATE': '/path_to_cert/server_cert.pem',
    #'SSLPRIVATEKEY': '/path_to_cert/server_privkey.pem',
    'LOGLEVEL': 'DEBUG',
    'LOGCONSOLE': True,
    'LOGCONSOLELEVEL': 'DEBUG',
    'MAXRETRIES': 5,
    'MAXARCHDAYS': 30,
    # DAEMON ###
    'DAEMONPORT': 16388,
    # Webserver ###
    'HOST': 'localhost',
    'PORT': 8890,
    'ENVIRONMENTTEXT': 'BETA',
    'ENVIRONMENTTEXTCOLOR': 'Yellow',
}

# Webserver
ALLOWED_HOSTS = [PYAS2['HOST'],]

# as2receiver ALLOWED_HOSTS is updated 
# this way ALLOWED_HOSTS = AS2_ALLOWED_HOSTS
AS2_ALLOWED_HOSTS = [PYAS2['AS2HOST'],]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PYAS2_ROOT, 'db',
            'pyas2webserver_%s.sqlite3' % PYAS2_ENV),
    },
    'pyas2': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(PYAS2_ROOT, 'db',
            'pyas2_%s.sqlite3' % PYAS2_ENV),
    }
}

DATABASE_ROUTERS = ['pyas2.dbrouter.Pyas2dbRouter',]

#********* sessions cookies *************************
SESSION_COOKIE_NAME = 'pyas2-%s' % PYAS2_ENV
SESSION_EXPIRE_AT_BROWSER_CLOSE = True    # True: always log in when browser is closed
SESSION_COOKIE_AGE = 28800                # Inactivity Expiration time of cookie in seconds
SESSION_SAVE_EVERY_REQUEST = True         # if True: SESSION_COOKIE_AGE is interpreted as: since last activity
# Settings for CSRF cookie.
CSRF_COOKIE_NAME = 'gsvtpyas2%s' % PYAS2_ENV
CSRF_COOKIE_DOMAIN = None
CSRF_COOKIE_PATH = '/'
CSRF_COOKIE_SECURE = False
