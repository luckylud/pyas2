#!/usr/bin/env python

from pyas2.pyas2init import pyas2setup

pyas2server = 'pyas2webserver'
pyas2setup(pyas2server)

from django.conf import settings
from django.core import management


if __name__ == '__main__':
    management.call_command('migrate')
    if hasattr(settings, 'DATABASE_ROUTERS'):
        if settings.DATABASES.get('pyas2') and 'pyas2.dbrouter.Pyas2dbRouter' in settings.DATABASE_ROUTERS:
            management.call_command('migrate', '--database=pyas2')
