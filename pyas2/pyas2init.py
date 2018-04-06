# -*- coding: utf-8 -*-

import logging
import os
import sys

from pyas2 import as2utils

# Declare global variables
gsettings = {}
logger = None
convertini2logger = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL,
    'STARTINFO': 25
}


def Pyas2settingsModname():
    ''' return pyas2 settings module name after appened it directory path sys.path,
    for import in as2receiver_settings.py and webserver_settings.py

    Linux:
    Add to $HOME/.bashrc
    export PYAS2_SETTINGS_FILE=/path/to/pyas2settings.py

    Windows:
    Add user or system var:
    PYAS2_SETTINGS_FILE=c:\\path\\to\\pyas2settings.py

    '''
    import pyas2.config

    default_path = os.path.dirname(pyas2.config.__file__)

    pyas2_settings_path = default_path
    default_modname = 'pyas2settings'
    modname = default_modname
    pyas2_settings_file = os.environ.get('PYAS2_SETTINGS_FILE')
    # PYAS2 custom settings
    if pyas2_settings_file:
        if not os.path.isfile(pyas2_settings_file):
            raise Exception('Custom pyas2 settings file not found: "%s"' % pyas2_settings_file)
        sys.stderr.write('Custom pyas2settings: %s\n' % pyas2_settings_file)
        pyas2_settings_path = os.path.dirname(pyas2_settings_file)
        try:
            init_file = os.path.join(pyas2_settings_path, '__init__.py')
            if not os.path.isfile(init_file):
                #sys.stderr.write('Creating %s\n' % init_file)
                open(init_file, 'w').close()
            modfile = os.path.basename(pyas2_settings_file)
            modname = modfile.split('.')[0]
        except Exception as e:
            sys.stderr.write('Import of custom pyas2 settings failled:\n%s' % e)
            sys.stderr.write('Using pyas2.default.pyas2settings\n')
            pyas2_settings_path = default_path
            modname = default_modname
    os.environ.setdefault('PYAS2_SETTINGS_FILE',
            os.path.join(pyas2_settings_path, '%s.py' % modname))
    if not pyas2_settings_path in sys.path:
        sys.path.append(pyas2_settings_path)
    sys.stderr.write('PYAS2_SETTINGS_FILE: %s\n' % os.environ.get('PYAS2_SETTINGS_FILE'))
    return modname


def pyas2setup(pyas2server):
    if pyas2server in ['receiver', 'daemon', 'process']:
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pyas2.as2receiver_settings")
    elif not os.environ.get('DJANGO_SETTINGS_MODULE'):
        if pyas2server == 'webserver':
            os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pyas2.webserver_settings")
        else:
            try:
                dj_settings = __import__(pyas2server)
                os.environ['DJANGO_SETTINGS_MODULE'] = dj_settings
            except:
                raise Exception('Could not use %s as django settings !' % pyas2server)
    import django
    if hasattr(django, 'setup'):
        django.setup()


def initialize():
    """ Function initializes the global variables for pyAS2 """

    from django.conf import settings
    from django.utils.translation import ugettext as _
    global gsettings
    pyas2_settings = {}
    if not hasattr(settings, 'MEDIA_ROOT'):
        raise Exception(_('MEDIA_ROOT not set in pyas2settings.py !'))
    if hasattr(settings, 'PYAS2'):
        pyas2_settings = settings.PYAS2
    if not gsettings:
        gsettings['environment'] = pyas2_settings.get('ENVIRONMENT', 'default')
        gsettings['server'] = pyas2_settings.get('SERVER', 'server')
        gsettings['db_default'] = settings.DATABASES.get('default', {}).get('NAME', 'not_set')
        gsettings['db_pyas2'] = settings.DATABASES.get('pyas2', {}).get('NAME', gsettings['db_default'])
        gsettings['settings'] = settings
        gsettings['host'] = pyas2_settings.get('HOST', 'localhost')
        gsettings['port'] = pyas2_settings.get('PORT', 8088)
        gsettings['as2_host'] = pyas2_settings.get('AS2HOST', gsettings.get('host'))
        gsettings['as2_port'] = pyas2_settings.get('AS2PORT', 8089)
        gsettings['as2_uri'] = pyas2_settings.get('AS2URI', 'as2receive')
        gsettings['media_uri'] = pyas2_settings.get('MEDIAURI', 'pyas2')
        gsettings['ssl_certificate'] = pyas2_settings.get('SSLCERTIFICATE', None)
        gsettings['ssl_private_key'] = pyas2_settings.get('SSLPRIVATEKEY', None)
        gsettings['protocol'] = 'http'
        if gsettings.get('ssl_certificate') and gsettings.get('ssl_private_key'):
            gsettings['protocol'] += 's'
        gsettings['environment_text'] = pyas2_settings.get('ENVIRONMENTTEXT', 'Default')
        gsettings['environment_text_color'] = pyas2_settings.get('ENVIRONMENTTEXTCOLOR', 'Black')
        gsettings['daemon_port'] = pyas2_settings.get('DAEMONPORT', 16388)
        gsettings['python_path'] = pyas2_settings.get('PYTHONPATH', sys.executable)
        if os.environ.get('PYAS2_ROOT'):
            gsettings['root_dir'] = os.environ.get('PYAS2_ROOT')
        elif hasattr(settings, 'PYAS2_ROOT'):
            gsettings['root_dir'] = settings.PYAS2_ROOT
        else:
            gsettings['root_dir'] = pyas2_settings.get('DATADIR')
        if not gsettings.get('root_dir'):
            raise Exception(_('PYAS2_ROOT not set in settings or DATADIR not set in PYAS2 settings !'))
        if not os.path.isdir(gsettings['root_dir']):
            if not os.path.dirname(os.environ.get('PYAS2_SETTINGS_FILE')) in gsettings['root_dir'] and \
                    os.access(os.path.dirname(os.environ.get('PYAS2_SETTINGS_FILE')), os.W_OK):
                raise Exception(_('PYAS2_ROOT: %s\n is not a valid directory !' % gsettings['root_dir']))
            os.makedirs(gsettings['root_dir'])
            sys.stderr.write('PYAS2_ROOT created: %s\n' % gsettings['root_dir'])
        if not os.path.isdir(settings.MEDIA_ROOT):
            if not gsettings['root_dir'] in settings.MEDIA_ROOT:
                raise Exception(_('MEDIA_ROOT: %s\nMEDIA_ROOT is not a valid directory !' % settings.MEDIA_ROOT))
            os.makedirs(settings.MEDIA_ROOT)
            sys.stderr.write('MEDIA_ROOT created: %s\n' % settings.MEDIA_ROOT)
        gsettings['payload_receive_store'] = as2utils.join(
                gsettings['root_dir'], 'messages', '__store', 'payload', 'received')
        gsettings['payload_send_store'] = as2utils.join(gsettings['root_dir'], 'messages', '__store', 'payload', 'sent')
        gsettings['mdn_receive_store'] = as2utils.join(gsettings['root_dir'], 'messages', '__store', 'mdn', 'received')
        gsettings['mdn_send_store'] = as2utils.join(gsettings['root_dir'], 'messages', '__store', 'mdn', 'sent')
        gsettings['log_dir'] = as2utils.join(gsettings['root_dir'], 'logging')
        for sett in ['payload_receive_store', 'payload_send_store', 'mdn_receive_store', 'mdn_send_store', 'log_dir']:
            as2utils.dirshouldbethere(gsettings[sett])
        gsettings['log_level'] = pyas2_settings.get('LOGLEVEL', 'INFO')
        gsettings['log_console'] = pyas2_settings.get('LOGCONSOLE', True)
        gsettings['log_console_level'] = pyas2_settings.get('LOGCONSOLELEVEL', 'STARTINFO')
        gsettings['max_retries'] = pyas2_settings.get('MAXRETRIES', 30)
        gsettings['mdn_url'] = pyas2_settings.get('MDNURL',
	    '%(protocol)s://%(as2_host)s:%(as2_port)s/%(as2_uri)s' % gsettings)
        gsettings['async_mdn_wait'] = pyas2_settings.get('ASYNCMDNWAIT', 30)
        gsettings['max_arch_days'] = pyas2_settings.get('MAXARCHDAYS', 30)
        gsettings['minDate'] = 0 - gsettings['max_arch_days']

        # Init logging
        initserverlogging('pyas2%s_%s' % (gsettings['server'], gsettings['environment']))

        # Display infos
        logger.info('###########################################')
        logger.info('PYAS2 %s Initialised successfully.' % gsettings['server'])
        logger.info('PYAS2_SETTINGS_FILE: %s' % os.environ.get('PYAS2_SETTINGS_FILE'))
        logger.info('ENVIRONMENT: %s' % gsettings['environment'])
        logger.info('PYAS2_ROOT: %s' % gsettings['root_dir'])
        logger.info('MEDIA_ROOT: %s' % settings.MEDIA_ROOT)
        logger.info('PYAS2_MEDIA_URI: %s' % gsettings['media_uri'])
        logger.info('default database  : %s' % gsettings['db_default'])
        logger.info('pyas2 database    : %s' % gsettings['db_pyas2'])
        if hasattr(settings, 'DATABASE_ROUTERS'):
            logger.info('DATABASE_ROUTERS: %s' % settings.DATABASE_ROUTERS)
            if not settings.DATABASES.get('pyas2') and 'pyas2.dbrouter.Pyas2dbRouter' in settings.DATABASE_ROUTERS:
                err = _("Error: 'pyas2' database not set in DATABASES settings !")
                logger.error(err)
                raise Exception('%s\n' % err)
        if gsettings['server'] == 'webserver':
            logger.info('STATIC_ROOT: %s' % settings.STATIC_ROOT)
        logger.info('###########################################')


def initserverlogging(logname):
    # initialise file logging
    global logger
    logger = logging.getLogger(logname)
    logger.setLevel(convertini2logger[gsettings['log_level']])
    handler = logging.handlers.TimedRotatingFileHandler(
            os.path.join(gsettings['log_dir'], logname + '.log'),
            when='midnight', backupCount=10)
    fileformat = logging.Formatter("%(asctime)s %(levelname)-9s: %(message)s", '%Y%m%d %H:%M:%S')
    handler.setFormatter(fileformat)
    logger.addHandler(handler)
    # initialise console/screen logging
    if gsettings['log_console']:
        console = logging.StreamHandler()
        console.setLevel(convertini2logger[gsettings['log_console_level']])
        consoleformat = logging.Formatter("%(asctime)s %(levelname)-9s: %(message)s", '%Y%m%d %H:%M:%S')
        console.setFormatter(consoleformat)  # add formatter to console
        logger.addHandler(console)  # add console to logger
    return logger


def debug_infos():
    """ Display PyAS2 debug infos """

    global gsettings
    #pyas2_settings = {}
    #if hasattr(settings, 'PYAS2'):
    #    pyas2_settings = settings.PYAS2
