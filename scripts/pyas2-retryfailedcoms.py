#!/usr/bin/env python

from pyas2.pyas2init import pyas2setup

pyas2server = 'process'
pyas2setup(pyas2server)

from django.core import management


if __name__ == '__main__':
    management.call_command('retryfailedas2comms')
