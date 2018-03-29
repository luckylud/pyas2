# -*- coding: utf-8 -*-

import os
from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.handlers.wsgi import WSGIHandler
from django.utils.translation import ugettext as _
import pyas2
from pyas2 import pyas2init


class Command(BaseCommand):
    help = _('Starts PyAS2 web server')

    def handle(self, *args, **options):
        try:
            import cherrypy
            from cherrypy import wsgiserver
        except Exception:
            raise ImportError(_('Dependency failure: cherrypy library is needed to start the pyas2 %s' % pyas2init.gsettings['server']))

        cherrypy.config.update({
            'global': {
                'log.screen': False,
                'log.error_file': os.path.join(pyas2init.gsettings['log_dir'], 'cherrypyas2%s_error.log' % pyas2init.gsettings['server']),
                'server.environment': pyas2init.gsettings['environment']
            }
        })

        # cherrypy handling of static files
        staticdir = settings.STATIC_URL[1:-1] if settings.STATIC_ROOT else 'static'
        staticroot = os.path.dirname(settings.STATIC_ROOT) if settings.STATIC_ROOT else os.path.abspath(os.path.dirname(pyas2.__file__))
        pyas2init.logger.log(25, 'staticdir: %s' % staticdir)
        pyas2init.logger.log(25, 'staticroot: %s' % staticroot)
        conf = {
            '/': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': staticdir,
                'tools.staticdir.root': staticroot,
            }
        }
        servestaticfiles = cherrypy.tree.mount(None, staticdir, conf)

        # cherrypy handling of django
        # was: servedjango = AdminMediaHandler(WSGIHandler())
        # but django does not need the AdminMediaHandler in this setup. is much faster.
        servedjango = WSGIHandler()

        # cherrypy uses a dispatcher in order to handle the serving of
        # static files and django.
        dispatcher = wsgiserver.WSGIPathInfoDispatcher({
            '/': servedjango, 
            settings.STATIC_URL[:-1]: servestaticfiles
            })

        pyas2webserver = wsgiserver.CherryPyWSGIServer(
            bind_addr=('0.0.0.0', pyas2init.gsettings['port']),
            wsgi_app=dispatcher,
            server_name='pyas2-%s' % pyas2init.gsettings['server']
        )

        if pyas2init.gsettings['protocol'] == 'https':
            # handle ssl: cherrypy < 3.2 always uses pyOpenssl. cherrypy >= 3.2
            # uses python buildin ssl (python >= 2.6 has buildin support for ssl).
            ssl_certificate = pyas2init.gsettings['ssl_certificate']
            ssl_private_key = pyas2init.gsettings['ssl_private_key']
            if ssl_certificate and ssl_private_key:
                if cherrypy.__version__ >= '3.2.0':
                    adapter_class = wsgiserver.get_ssl_adapter_class('builtin')
                    pyas2webserver.ssl_adapter = adapter_class(ssl_certificate, ssl_private_key)
                else:
                    # but: pyOpenssl should be there!
                    pyas2webserver.ssl_certificate = ssl_certificate
                    pyas2webserver.ssl_private_key = ssl_private_key
                pyas2init.logger.log(25, _('PyAS2 %s uses ssl (https).' % pyas2init.gsettings['server']))
        else:
            pyas2init.logger.log(25, _('PyAS2 %s uses plain http (no ssl).' % pyas2init.gsettings['server']))
        pyas2init.logger.info('PyAS2 config:')
        # pyas2init.logger.info('root_dir        : %s' % pyas2init.gsettings['root_dir'])
        pyas2init.logger.info('pyas2 database    : %s' % pyas2init.gsettings['db_pyas2'])
        pyas2init.logger.info('default database  : %s' % pyas2init.gsettings['db_default'])
        pyas2init.logger.info(
            _('PyAS2 %s listning at: ' % pyas2init.gsettings['server']) +
            '%(protocol)s://%(host)s:%(port)s/' % pyas2init.gsettings)

        # start the cherrypy webserver.
        try:
            pyas2webserver.start()
        except KeyboardInterrupt:
            pyas2webserver.stop()
