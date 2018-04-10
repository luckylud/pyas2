# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.translation import ugettext as _
from datetime import timedelta
from email.parser import HeaderParser
import requests

from pyas2 import models, pyas2init


class Command(BaseCommand):
    help = _('Send all pending asynchronous mdns to your trading partners')

    def handle(self, *args, **options):
        # First part of script sends asynchronous MDNs for inbound messages received from partners
        # Fetch all the pending asynchronous MDN objects
        pyas2init.logger.info(_('Sending all pending asynchronous MDNs'))
        in_pending_mdns = models.MDN.objects.filter(status='P')  # , timestamp__gt=time_threshold) --> why do this?

        for pending_mdn in in_pending_mdns:
            pending_mdn.retries += 1
            # Parse the MDN headers from text
            header_parser = HeaderParser()
            mdn_headers = header_parser.parsestr(pending_mdn.headers)
            try:
                # Set http basic auth if enabled in the partner profile
                auth = None
                verify = True
                if pending_mdn.omessage.partner:
                    if pending_mdn.omessage.partner.http_auth:
                        auth = (pending_mdn.omessage.partner.http_auth_user, pending_mdn.omessage.partner.http_auth_pass)

                    # Set the ca cert if given in the partner profile
                    if pending_mdn.omessage.partner.https_ca_cert:
                        verify = pending_mdn.omessage.partner.https_ca_cert.path

                # Post the MDN message to the url provided on the original as2 message
                with open(pending_mdn.file, 'rb') as payload:
                    requests.post(pending_mdn.return_url,
                                  auth=auth,
                                  verify=verify,
                                  headers=dict(mdn_headers.items()),
                                  data=payload)
                pending_mdn.status = 'S'
                models.Log.objects.create(message=pending_mdn.omessage,
                                          status='S',
                                          text=_('Successfully sent asynchronous mdn to partner'))
            except Exception as e:
                pyas2init.logger.error('%s %s\n%s' % (
                                       _('Error while sending asynchronous MDNs'),
                                       pending_mdn, e))
                if pending_mdn.retries > pyas2init.gsettings['max_retries']:
                    pending_mdn.status = 'E'
                if hasattr(pending_mdn, 'omessage'):
                    models.Log.objects.create(message=pending_mdn.omessage,
                                              status='E',
                                              text=_('Failed to send asynchronous mdn to partner, '
                                                     'error is {0:s}'.format(e)))
                    if pending_mdn.status == 'E':
	                models.Log.objects.create(message=pending_mdn.omessage,
                                          status='E',
                                          text=_('MDN exceeded maximum retries, marked as error'))

            finally:
                pending_mdn.save()

        # Second Part of script checks if MDNs have been received for outbound messages to partners
        pyas2init.logger.info(_('Marking messages waiting for MDNs for more than {0:d} minutes'.format(
            pyas2init.gsettings['async_mdn_wait'])))

        # Find all messages waiting MDNs for more than the set async mdn wait time
        time_threshold = timezone.now() - timedelta(minutes=pyas2init.gsettings['async_mdn_wait'])
        out_pending_msgs = models.Message.objects.filter(status='P', direction='OUT', timestamp__lt=time_threshold)

        # Mark these messages as erred
        for pending_msg in out_pending_msgs:
            status_txt = _('Failed to receive asynchronous MDN within the threshold limit')
            pending_msg.status = 'E'
            pending_msg.adv_status = status_txt
            models.Log.objects.create(message=pending_msg, status='E', text=status_txt)
            pending_msg.save()

        pyas2init.logger.info(_('Successfully processed all pending mdns'))
