# -*- coding: utf-8 -*-

import email
from email.parser import HeaderParser
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotFound, HttpResponseRedirect, HttpResponseServerError, Http404
from django.shortcuts import render, redirect
from django.views.generic import ListView, DetailView
from django.views.generic.edit import View
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext as _
from django.contrib import messages
from django.core import management
from django.core.mail import mail_managers
from django import template
from multiprocessing import Process
import tempfile
import traceback

from . import models, forms, as2lib, as2utils, pyas2init, viewlib


def server_error(request, template_name='500.html'):
    """ the 500 error handler.
        Templates: `500.html`
        Context: None
        str().decode(): bytes->unicode
    """
    exc_info = traceback.format_exc(None).decode('utf-8', 'ignore')
    pyas2init.logger.error(_(u'Ran into server error: "%(error)s"'), {'error': str(exc_info)})
    temp = template.loader.get_template(template_name)   # You need to create a 500.html template.
    return HttpResponseServerError(temp.render(template.Context({'exc_info': exc_info})))


def client_error(request, template_name='400.html'):
    """ the 400 error handler.
        Templates: `400.html`
        Context: None
        str().decode(): bytes->unicode
    """
    exc_info = traceback.format_exc(None).decode('utf-8', 'ignore')
    pyas2init.logger.error(_(u'Ran into client error: "%(error)s"'), {'error': str(exc_info)})
    temp = template.loader.get_template(template_name)  # You need to create a 500.html template.
    return HttpResponseServerError(temp.render(template.Context({'exc_info': exc_info})))


def home(request, *kw, **kwargs):
    """ Default view, Displays the AS2 System Settings"""
    return render(request, 'pyas2/about.html', {'pyas2info': pyas2init.gsettings})


class MessageList(ListView):
    """Generic List view, displays list of messages in the system"""

    model = models.Message
    paginate_by = 25

    def get_queryset(self):
        if self.request.GET:
            qstring = dict()
            for param in self.request.GET.items():
                if param[1]:
                    if param[0] == 'dateuntil':
                        qstring['timestamp__lt'] = param[1]
                    elif param[0] == 'datefrom':
                        qstring['timestamp__gte'] = param[1]
                    elif param[0] in ['organization', 'partner']:
                        qstring[param[0] + '__as2_name'] = param[1]
                    elif param[0] == 'filename':
                        qstring['payload__name'] = param[1]
                    elif param[0] in ['direction', 'status', 'message_id']:
                        qstring[param[0]] = param[1]
            return models.Message.objects.filter(**qstring).order_by('-timestamp')
        return models.Message.objects.all().order_by('-timestamp')


class MessageDetail(DetailView):
    """ Generic detail view to display the message details"""
    model = models.Message

    def get_context_data(self, **kwargs):
        context = super(MessageDetail, self).get_context_data(**kwargs)
        context['logs'] = models.Log.objects.filter(message=kwargs['object']).order_by('timestamp')
        return context


class MessageSearch(View):
    """ Generic view with a form for searching messages in the system"""
    form_class = forms.MessageSearchForm
    template_name = 'pyas2/message_search.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            return HttpResponseRedirect(viewlib.url_with_querystring(reverse('pyas2:messages'), **form.cleaned_data))
        else:
            return render(request, self.template_name, {'form': form, 'confirm': False})


class PayloadView(View):
    """ Displays the actual payload for an AS2 message along with the message headers."""
    template_name = 'pyas2/file_view.html'

    def get(self, request, pk, *args, **kwargs):
        try:
            message = models.Message.objects.get(message_id=pk)
            payload = message.payload
            if request.GET['action'] == 'downl':
                # Returns the payload contents as an attachment, thus enabling users to download the data
                response = HttpResponse(content_type=payload.content_type)
                disposition_type = 'attachment'
                response['Content-Disposition'] = disposition_type + '; filename=' + payload.name
                response.write(as2utils.readdata(payload.file))
                return response
            elif request.GET['action'] == 'this':
                # Displays the payload contents, Formatting is applied based on the content type of the message.
                file_obj = dict()
                file_obj['name'] = payload.name
                file_obj['id'] = pk
                file_obj['content'] = as2utils.readdata(payload.file, charset='utf-8', errors='ignore')
                if payload.content_type == 'application/EDI-X12':
                    file_obj['content'] = viewlib.indent_x12(file_obj['content'])
                elif payload.content_type == 'application/EDIFACT':
                    file_obj['content'] = viewlib.indent_edifact(file_obj['content'])
                elif payload.content_type == 'application/XML':
                    file_obj['content'] = viewlib.indent_xml(file_obj['content'])
                file_obj['direction'] = message.get_direction_display()
                file_obj['type'] = 'AS2 MESSAGE'
                file_obj['headers'] = dict(HeaderParser().parsestr(message.headers or '').items())
                return render(request, self.template_name, {'file_obj': file_obj})
        except Exception:
            return render(request, self.template_name, {'error_content': _(u'No such file.')})


class MDNList(ListView):
    model = models.MDN
    paginate_by = 25

    def get_queryset(self):
        if self.request.GET:
                query_string = dict()
                for param in self.request.GET.items():
                    if param[1]:
                        if param[0] == 'dateuntil':
                            query_string['timestamp__lt'] = param[1]
                        elif param[0] == 'datefrom':
                            query_string['timestamp__gte'] = param[1]
                        elif param[0] in ['status', 'message_id']:
                            query_string[param[0]] = param[1]
                        elif param[0] == 'omessage_id':
                            query_string['omessage__message_id'] = param[1]
                        elif param[0] in ['mdn_mode']:
                            query_string['omessage__'+param[0]] = param[1]
                        elif param[0] in ['organization', 'partner']:
                            query_string['omessage__'+param[0]+'__as2_name'] = param[1]
                return models.MDN.objects.filter(**query_string).order_by('-timestamp')
        return models.MDN.objects.all().order_by('-timestamp')


class MDNSearch(View):
    form_class = forms.MDNSearchForm
    template_name = 'pyas2/mdn_search.html'

    def get(self, request, *args, **kwargs):
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            return HttpResponseRedirect(viewlib.url_with_querystring(reverse('pyas2:mdns'), **form.cleaned_data))
        else:
            return render(request, self.template_name, {'form': form})


class MDNView(View):
    template_name = 'pyas2/file_view.html'

    def get(self, request, pk, *args, **kwargs):
        try:
            mdn = models.MDN.objects.get(message_id=pk)
            if request.GET['action'] == 'downl':
                response = HttpResponse(content_type='multipart/report')
                disposition_type = 'attachment'
                response['Content-Disposition'] = disposition_type + '; filename=' + pk + '.mdn'
                response.write(as2utils.readdata(mdn.file))
                return response
            elif request.GET['action'] == 'this':
                file_obj = dict()
                file_obj['name'] = pk + '.mdn'
                file_obj['id'] = pk
                file_obj['content'] = as2utils.readdata(mdn.file, charset='utf-8', errors='ignore')
                file_obj['direction'] = mdn.get_status_display()
                file_obj['type'] = 'AS2 MDN'
                file_obj['headers'] = dict(HeaderParser().parsestr(mdn.headers or '').items())
                return render(request, self.template_name, {'file_obj': file_obj})
        except Exception:
            return render(request, self.template_name, {'error_content': _(u'No such file.')})


class SendMessage(View):
    """Generic view for sending messages to partners. Form allows for selecting organization, partner and file to
    be transmitted."""

    form_class = forms.SendMessageForm
    template_name = 'pyas2/sendmessage.html'

    def get(self, request, *args, **kwargs):
        # Return the form on get
        form = self.form_class()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        # On post transmit the uploaded file
        form = self.form_class(request.POST, request.FILES)
        if form.is_valid():
            f = request.FILES.get('file')
            # Save uploaded file to a temporary location
            temp = tempfile.NamedTemporaryFile(suffix='_%s' % f.name, delete=False)
            if f.multiple_chunks:
                for chunk in f.chunks():
                    temp.write(chunk)
            else:
                temp.write(f.read())
            temp.close()
            lijst = [
                'sendas2message',
                '--delete',
                form.cleaned_data['organization'],
                form.cleaned_data['partner'],
                temp.name
            ]
            pyas2init.logger.info(_('Send message started with parameters: "%(parameters)s"'),
                                  {'parameters': str(lijst)})

            # Call django management command "sendas2message" to transfer the file to partner
            messages.add_message(request, messages.INFO,
                                 _('Sending file %(file)s to partner %(partner)s ...' % {
                                     'file': f.name,
                                     'partner': form.cleaned_data['partner']
                                 }))
            try:
                p = Process(target=management.call_command, args=lijst)
                p.start()
            except Exception as msg:
                notification = _('Errors while trying to run send message: "%s".') % msg
                messages.add_message(request, messages.INFO, notification)
                pyas2init.logger.error(notification)
        return render(request, self.template_name, {'form': form})


def resend_message(request, pk, *args, **kwargs):
    """ Function for resending an outbound message from the Message List View"""

    # Get the message to be resent
    orig_message = models.Message.objects.get(message_id=pk)

    # Copy the message payload to a temporary location
    temp = tempfile.NamedTemporaryFile(suffix='_%s' % orig_message.payload.name, delete=False)
    with open(orig_message.payload.file, 'rb+') as source:
        temp.write(source.read())

    # Call django management command "sendas2message" to transfer the file to partner
    lijst = [
        'sendas2message',
        orig_message.organization.as2_name,
        orig_message.partner.as2_name,
        temp.name
    ]
    pyas2init.logger.info(_(u'Re-send message started with parameters: "%(parameters)s"'), {'parameters': str(lijst)})
    try:
        p = Process(target=management.call_command, args=lijst)
        p.start()
    except Exception as msg:
        notification = _(u'Errors while trying to re-send message: "%s".') % msg
        messages.add_message(request, messages.INFO, notification)
        pyas2init.logger.info(notification)
    else:
        messages.add_message(request, messages.INFO, _(u'Re-Sending the message to your partner ......'))
    return redirect('pyas2:home')


def send_async_mdn(request, *args, **kwargs):
    """Send all pending asynchronous MDNs to all partners"""

    # Call django management command "sendasyncmdn" to transfer the file to partner
    lijst = ['sendasyncmdn']
    pyas2init.logger.info(_(u'Send async MDNs started with parameters: "%(parameters)s"'), {'parameters': str(lijst)})
    try:
        p = Process(target=management.call_command, args=lijst)
        p.start()
    except Exception as msg:
        notification = _(u'Errors while trying to run send async MDNs: "%s".') % msg
        messages.add_message(request, messages.INFO, notification)
    else:
        messages.add_message(request, messages.INFO, _(u'Sending all pending asynchronous MDNs .....'))
    return redirect('pyas2:home')


def retry_failed_comms(request, *args, **kwargs):
    """ Retry communications for all failed outbound messages"""

    lijst = ['retryfailedas2comms']
    pyas2init.logger.info(_(u'Retry Failed communications started with parameters: "%(parameters)s"'),
                          {'parameters': str(lijst)})
    try:
        p = Process(target=management.call_command, args=lijst)
        p.start()
    except Exception as msg:
        notification = _(u'Errors while trying to retrying failed communications: "%s".') % msg
        messages.add_message(request, messages.INFO, notification)
    else:
        messages.add_message(request, messages.INFO, _(u'Retrying failed communications .....'))
    return redirect('pyas2:home')


def cancel_retries(request, pk, *args, **kwargs):
    """ Cancel retries for a failed outbound message from the list messages view"""
    message = models.Message.objects.get(message_id=pk)
    message.status = 'E'
    models.Log.objects.create(message=message, status='S', text=_(u'User cancelled further retires for this message'))
    message.save()
    messages.add_message(request, messages.INFO, _(u'Cancelled retries for message %s' % pk))
    return redirect('pyas2:messages')


def send_test_mail_managers(request, *args, **kwargs):
    """ Send a test email, used to confirm email settings"""
    try:
        mail_managers(_(u'testsubject'), _(u'test content of report'))
    except Exception:
        txt = as2utils.txtexc()
        messages.add_message(request, messages.INFO, _(u'Sending test mail failed.'))
        pyas2init.logger.info(_(u'Sending test mail failed, error:\n%(txt)s'), {'txt': txt})
        return redirect('pyas2:home')
    notification = _(u'Sending test mail succeeded.')
    messages.add_message(request, messages.INFO, notification)
    pyas2init.logger.info(notification)
    return redirect('pyas2:home')


def download_cert(request, *args, **kwargs):
    if request.method == 'GET':
        cert = None
        typ = request.GET.get('type')
        pk = request.GET.get('pk')
        name = request.GET.get('name')
        if typ == 'private':
            model = models.PrivateCertificate
        else:
            model = models.PublicCertificate
        if pk:
            cert = model.objects.filter(pk=pk).first()
        elif name:
            cert = model.objects.filter(certificate__endswith=name).first()

        if cert:
            response = HttpResponse(content_type='application/x-pem-file')
            disposition_type = 'attachment'
            response['Content-Disposition'] = disposition_type + '; filename=' + cert.certificate.name
            response.write(cert.certificate.read())
            return response

        notification = _('No certificate found.')
        messages.add_message(request, messages.INFO, notification)
        return redirect('pyas2:home')


@csrf_exempt
def as2receive(request, *args, **kwargs):
    """
       Function receives AS2 requests from partners.
       Checks whether its an AS2 message or an MDN and acts accordingly.
    """
    # Log requests
    pyas2init.logger.info('%(REMOTE_ADDR)s %(REQUEST_METHOD)s %(PATH_INFO)s%(QUERY_STRING)s' % request.META)

    if request.method == 'POST':
        as2_from = request.META.get('HTTP_AS2_FROM')
        as2_to = request.META.get('HTTP_AS2_TO')
        message_id = request.META.get('HTTP_MESSAGE_ID', '').strip('<>')

        # Check AS2 POST
        if not as2_from or not as2_to or not message_id:
            pyas2init.logger.error('%s: %s ' % (_('Invalid AS2 message received from:'), request.META['REMOTE_ADDR']))
            return HttpResponseBadRequest(_('Invalid AS2 message received.'))
        pyas2init.logger.info('MSG-ID %(HTTP_MESSAGE_ID)s RECEIVE '
                              'FROM <%(HTTP_AS2_FROM)s> TO <%(HTTP_AS2_TO)s>' % request.META)

        # Extract all the relevant headers from the http request
        headers = ''
        for key, value in request.META.items():
            if key.startswith('HTTP') and value:
                key = key.replace('HTTP_', '').replace('_', '-').lower()
                headers += '%s: %s\n' % (key, value)
        headers += 'content-length: %s\n' % request.META.get('CONTENT_LENGTH', '')
        headers += 'content-type: %s\n' % request.META.get('CONTENT_TYPE', '')

        pyas2init.logger.debug('REQUEST HEADERS:\n%s' % headers)

        # Process the posted AS2 message
        request_body = request.read()

        pyas2init.logger.debug('REQUEST BODY:\n%s' % request_body)

        raw_payload = '%s\n%s' % (headers, request_body)

        # Save raw AS2 message
        raw_filename = as2utils.storefile(pyas2init.gsettings['raw_receive_store'],
                                          models.MSG_ID_SEP.join((message_id,
                                                                  as2utils.unescape_as2name(as2_to),
                                                                  as2utils.unescape_as2name(as2_from))),
                                          raw_payload,
                                          True)
        pyas2init.logger.info('%s %s' % (_('Raw as2 message received stored:'), raw_filename))

        try:
            pyas2init.logger.debug('Check payload to see if its an AS2 Message or ASYNC MDN.')
            # Load the request header and body as a MIME Email Message
            payload = email.message_from_string(raw_payload)
            # Get the message sender and receiver AS2 IDs
            message_org = as2utils.unescape_as2name(payload.get('as2-to'))
            message_partner = as2utils.unescape_as2name(payload.get('as2-from'))
            message = None

            # Organisation
            org = models.Organization.objects.filter(as2_name=message_org).first()

            # Partner
            partner = models.Partner.objects.filter(as2_name=message_partner).first()

            # Check if this is an MDN message
            mdn_message = None
            if payload.get_content_type() == 'multipart/report':
                mdn_message = payload
            elif payload.get_content_type() == 'multipart/signed':
                for part in payload.walk():
                    if part.get_content_type() == 'multipart/report':
                        mdn_message = part

            # If this is an MDN, get the message ID and check if it exists
            if mdn_message:
                msg_id = None

                for part in mdn_message.walk():
                    if part.get_content_type() == 'message/disposition-notification':
                        msg_id = part.get_payload().pop().get('Original-Message-ID', '').strip('<>')
                        break
                pyas2init.logger.info('Asynchronous MDN received for AS2 message <%s> to Organization <%s> '
                                      'from Partner <%s>' % (msg_id, org, partner))
                try:
                    error404 = ''
                    if not org:
                        error404 = 'AS2 recipient no found'
                    if not partner:
                        error404 = ', '.join((error404, 'AS2 partner no found'))
                    # Get the related message from the db.
                    message = models.Message.objects.filter(
                                                message_id=msg_id,
                                                organization=org,
                                                partner=partner).first()
                    if not message:
                        error404 = ', '.join((error404, 'AS2 related message not found'))
                    if not partner or not org or not message:
                        raise Http404(error404)

                    models.Log.objects.create(message=message,
                                              status='S',
                                              text=_('Processing incoming asynchronous mdn'))
                    as2lib.save_mdn(message, raw_payload)

                except Http404 as e:
                    pyas2init.logger.error('Asynchronous MDN received for unknown AS2 message <%s>: %s' % (msg_id, e))
                    # Send 404 response
                    return HttpResponseNotFound(_('Unknown AS2 MDN received. Will not be processed'))

                except as2utils.As2Exception as e:
                    pyas2init.logger.error(e)
                    models.Log.objects.create(message=message,
                                              status=message.status,
                                              text=e)

                except Exception as e:
                    error = '%s %s' % (_('Failed to proceed AS2 ASYNC MDN:'), e)
                    pyas2init.logger.error(error)
                    if message:
                        message.status = 'E'
                        message.save()
                        models.Log.objects.create(message=message,
                                                  status=message.status,
                                                  text=error)
                        # Send mail here
                        as2utils.senderrorreport(message, error)

                finally:
                    # Send response to HTTP request
                    return HttpResponse(_('AS2 ASYNC MDN has been received'))

            else:
                try:
                    full_filename = ''
                    # Process the received AS2 message from partner
                    # Initialize the processing status variables
                    status, adv_status, status_message = '', '', ''

                    pyas2init.logger.info('Message received for Organization <%s> from Partner <%s>' %
                                          (org, partner))

                    # Raise duplicate message error in case message already exists in the system
                    if models.Message.objects.filter(partner=partner,
                                                     organization=org,
                                                     message_id__startswith=message_id).exists():
                        message = models.Message.objects.create(
                                                message_id='%s_%s' % (message_id, payload.get('date')),
                                                direction='IN',
                                                status='IP',
                                                headers=headers,
                                                organization=org,
                                                partner=partner)
                        raise as2utils.As2DuplicateDocument(_('Duplicate message received !'))

                    # Create a new message in the system
                    pyas2init.logger.debug('Creating incomming message entry in table ...')
                    message = models.Message.objects.create(
                                                        message_id=message_id,
                                                        direction='IN',
                                                        status='IP',
                                                        headers=headers,
                                                        organization=org,
                                                        partner=partner)

                    pyas2init.logger.debug('Message created: %s' % message)

                    # Process the received payload to extract the actual message from partner
                    payload = as2lib.save_message(message, payload, raw_payload)

                    # Get the inbox folder for this partner and organization
                    output_dir = as2utils.join(pyas2init.gsettings['root_dir'],
                                               'messages',
                                               message.organization.as2_name,
                                               'inbox',
                                               message.partner.as2_name)

                    # Get the filename from the header and if not there set to message id
                    if message.partner.keep_filename and payload.get_filename():
                        filename = payload.get_filename()
                    else:
                        filename = '%s.msg' % message.message_id

                    # Save the message content to the store and inbox
                    content = payload.get_payload(decode=True)
                    full_filename = as2utils.storefile(output_dir, filename, content, False)
                    store_filename = as2utils.storefile(pyas2init.gsettings['payload_receive_store'],
                                                        message.message_id,
                                                        content,
                                                        True)

                    models.Log.objects.create(message=message,
                                              status='S',
                                              text=_('Message saved successfully to %s' % full_filename))

                    message.payload = models.Payload.objects.create(name=filename,
                                                                    file=store_filename,
                                                                    content_type=payload.get_content_type())

                    # Set processing status
                    status = 'success'

                # Catch each of the possible exceptions while processing an as2 message
                except as2utils.As2DuplicateDocument as e:
                    status = 'warning'
                    adv_status = 'duplicate-document'
                    status_message = _('AS2 message error: %s' % e)

                except as2utils.As2PartnerNotFound as e:
                    status = 'error'
                    adv_status = 'unknown-trading-partner'
                    status_message = _('AS2 message error: %s' % e)

                except as2utils.As2InsufficientSecurity as e:
                    status = 'error'
                    adv_status = 'insufficient-message-security'
                    status_message = _('AS2 message error: %s' % e)

                except as2utils.As2DecryptionFailed as e:
                    status = 'decryption-failed'
                    adv_status = 'error'
                    status_message = _('AS2 message error: %s' % e)

                except as2utils.As2DecompressionFailed as e:
                    status = 'error'
                    adv_status = 'decompression-failed'
                    status_message = _('AS2 message error: %s' % e)

                except as2utils.As2InvalidSignature as e:
                    status = 'error'
                    adv_status = 'integrity-check-failed'
                    status_message = _('AS2 message error: %s' % e)

                except Exception as e:
                    txt = traceback.format_exc(None).decode('utf-8', 'ignore')
                    pyas2init.logger.error(_('Unexpected error while processing message %(msg)s, '
                                           'ERROR:\n%(txt)s\n%(e)s'), {'e': e, 'txt': txt, 'msg': message_id})
                    status = 'error'
                    adv_status = 'unexpected-processing-error'
                    status_message = _('An unexpected error occurred while processing AS2 message <%s>' % message_id)
                finally:
                    if message:
                        # Build the mdn for the message based on processing status
                        mdn_body, mdn_message = as2lib.build_mdn(message,
                                                                 status,
                                                                 adv_status=adv_status,
                                                                 status_message=status_message,
                                                                 full_filename=full_filename)

                        # Create the mdn response body and return the MDN to the http request
                        if mdn_body:
                            mdn_response = HttpResponse(mdn_body, content_type=mdn_message.get_content_type())
                            for key, value in mdn_message.items():
                                mdn_response[key] = value
                            return mdn_response
                    return HttpResponse(_('AS2 message has been received'))

        # Catch all exception in case of any kind of error in the system.
        except Exception as e:
            txt = traceback.format_exc(None).decode('utf-8', 'ignore')
            error_response = _('Fatal error while processing AS2 message <%s>' % message_id)
            pyas2init.logger.error(error_response)
            pyas2init.logger.error('ERROR:\n%s' % txt)
            pyas2init.logger.error('Exception:\n%s' % e)
            return HttpResponseServerError(error_response)
            # Send mail here
            # mail_managers(_('[pyAS2 Error Report] Fatal
            # error%(time)s')%{'time':request.META.get('HTTP_DATE')}, reporttxt)

    elif request.method == 'GET':
        '''
        if pyas2init.gsettings['log_level'] in ['DEBUG',]:
            for k, v in request.__dict__.items():
                if isinstance(v, dict):
                    for m, n in v.items():
                        pyas2init.logger.debug('%s %s: %s' % (k, m, n))
                    continue
                pyas2init.logger.debug('%s: %s' % (k, v))
        '''
        return HttpResponse(_('To submit an AS2 message, you must POST the message to this URL'))

    elif request.method == 'OPTIONS':
        response = HttpResponse()
        response['allow'] = ','.join(['POST', 'GET'])
        return response
