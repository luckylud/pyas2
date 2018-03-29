# -*- coding: utf-8 -*-

import os
from django.core.management.base import BaseCommand
from django.core.handlers.wsgi import WSGIHandler
from django.utils.translation import ugettext as _
from pyas2 import pyas2init


class Command(BaseCommand):
    help = _('Starts PyAS2 receiver')

    def handle(self, *args, **options):
        try:
            import cherrypy
            from cherrypy import wsgiserver
        except Exception:
            raise ImportError(_('Dependency failure: cherrypy library is needed to start pyas2 %s' % pyas2init.gsettings['server']))

        cherrypy.config.update({
            'global': {
                'log.screen': False,
                'log.error_file': os.path.join(pyas2init.gsettings['log_dir'], 'cherrypyas2%s_error.log' % pyas2init.gsettings['server']),
                'server.environment': pyas2init.gsettings['environment']
            }
        })

        # cherrypy handling of django
        # was: servedjango = AdminMediaHandler(WSGIHandler())
        # but django does not need the AdminMediaHandler in this setup. is much faster.
        servedjango = WSGIHandler()

        # cherrypy uses a dispatcher in order to handle the serving of
        # static files and django.
        dispatcher = wsgiserver.WSGIPathInfoDispatcher(
            {'/%s' % pyas2init.gsettings.get('as2_uri'): servedjango,
            })

        pyas2receiver = wsgiserver.CherryPyWSGIServer(
            bind_addr=('0.0.0.0', pyas2init.gsettings['as2_port']),
            wsgi_app=dispatcher,
            server_name='pyas2-receiver'
        )

        if pyas2init.gsettings['protocol'] == 'https':
            # handle ssl: cherrypy < 3.2 always uses pyOpenssl. cherrypy >= 3.2
            # uses python buildin ssl (python >= 2.6 has buildin support for ssl).
            ssl_certificate = pyas2init.gsettings['ssl_certificate']
            ssl_private_key = pyas2init.gsettings['ssl_private_key']
            if ssl_certificate and ssl_private_key:
                if cherrypy.__version__ >= '3.2.0':
                    adapter_class = wsgiserver.get_ssl_adapter_class('builtin')
                    pyas2receiver.ssl_adapter = adapter_class(ssl_certificate, ssl_private_key)
                else:
                    # but: pyOpenssl should be there!
                    pyas2receiver.ssl_certificate = ssl_certificate
                    pyas2receiver.ssl_private_key = ssl_private_key
                pyas2init.logger.log(25, _('PyAS2 %s uses ssl (https).' % pyas2init.gsettings['server']))
        else:
            pyas2init.logger.log(25, _('PyAS2 %s uses plain http (no ssl).' % pyas2init.gsettings['server']))
        pyas2init.logger.info('PyAS2 config:')
        pyas2init.logger.info('root_dir        : %s' % pyas2init.gsettings['root_dir'])
        pyas2init.logger.info('pyas2 database  : %s' % pyas2init.gsettings['db_pyas2'])
        pyas2init.logger.info(
            _('PyAS2 %s listning at: ' % pyas2init.gsettings['server']) +
            '"%(protocol)s://%(as2_host)s:%(as2_port)s/%(as2_uri)s"' % pyas2init.gsettings)
        
        if pyas2init.gsettings['log_level'] in ['DEBUG',]:
            for k, v in pyas2init.gsettings.items():
                pyas2init.logger.debug('%s: %s' % (k, v))

        # start the cherrypy webserver.
        try:
            pyas2receiver.start()
        except KeyboardInterrupt:
            pyas2receiver.stop()
