# -*- coding: utf-8 -*-

import os
import subprocess
from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible
from django.utils.translation import ugettext as _
from email.parser import HeaderParser
from string import Template

from . import pyas2init, as2utils


# Initialize the pyas2 settings and loggers
pyas2init.initialize()

STATIC_URL = '/static/'
if hasattr(pyas2init.gsettings['settings'], 'STATIC_URL'):
    STATIC_URL = pyas2init.gsettings['settings'].STATIC_URL or STATIC_URL

# Set default entry for selects
DEFAULT_ENTRY = ('', '---------')

MSG_ID_SEP = '#'


# Set the storage directory for certificates
def get_certificate_path(instance, filename):
    return '/'.join((pyas2init.gsettings['media_uri'], 'certificates', filename))


@python_2_unicode_compatible
class PrivateCertificate(models.Model):
    certificate = models.FileField(
        max_length=500, upload_to=get_certificate_path)
    ca_cert = models.FileField(
        max_length=500, upload_to=get_certificate_path,
        verbose_name=_('Local CA Store'), null=True, blank=True)
    certificate_passphrase = models.CharField(max_length=100)

    def __str__(self):
        return os.path.basename(self.certificate.name)


@python_2_unicode_compatible
class PublicCertificate(models.Model):
    certificate = models.FileField(
        max_length=500, upload_to=get_certificate_path)
    ca_cert = models.FileField(
        max_length=500, upload_to=get_certificate_path,
        verbose_name=_('Local CA Store'), null=True, blank=True)
    verify_cert = models.BooleanField(
        verbose_name=_('Verify Certificate'), default=True,
        help_text=_('Uncheck this option to disable certificate verification.'))

    def __str__(self):
        return os.path.basename(self.certificate.name)


@python_2_unicode_compatible
class Organization(models.Model):
    name = models.CharField(verbose_name=_('Organization Name'), max_length=100)
    as2_name = models.CharField(verbose_name=_('AS2 Identifier'), max_length=100, primary_key=True)
    email_address = models.EmailField(null=True, blank=True)
    encryption_key = models.ForeignKey(PrivateCertificate, related_name='enc_org', null=True, blank=True)
    signature_key = models.ForeignKey(PrivateCertificate, related_name='sign_org', null=True, blank=True)
    confirmation_message = models.CharField(
        verbose_name=_('Confirmation Message'),
        max_length=300,
        null=True,
        blank=True,
        help_text=_('Use this field to send a customized message in the MDN Confirmations for this Organization')
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Partner(models.Model):
    CONTENT_TYPE_CHOICES = (
        ('application/EDI-X12', 'application/EDI-X12'),
        ('application/EDIFACT', 'application/EDIFACT'),
        ('application/edi-consent', 'application/edi-consent'),
        ('application/XML', 'application/XML'),
    )
    ENCRYPT_ALG_CHOICES = (
        ('des_ede3_cbc', '3DES'),
        ('des_cbc', 'DES'),
        ('aes_128_cbc', 'AES-128'),
        ('aes_192_cbc', 'AES-192'),
        ('aes_256_cbc', 'AES-256'),
        ('rc2_40_cbc', 'RC2-40'),
    )
    SIGN_ALG_CHOICES = (
        # ('md5', 'MD5'),
        ('sha1', 'SHA-1'),
        # ('sha256', 'SHA-256'),
        # ('sha384', 'SHA-384'),
        # ('sha512', 'SHA-512'),
    )
    MDN_TYPE_CHOICES = (
        ('SYNC', 'Synchronous'),
        ('ASYNC', 'Asynchronous'),
    )
    confirmation_message = models.CharField(
        verbose_name=_('Confirmation Message'),
        max_length=300,
        null=True,
        blank=True,
        help_text=_('Use this field to send a customized message in the MDN Confirmations for this Partner')
    )
    name = models.CharField(verbose_name=_('Partner Name'), max_length=100)
    as2_name = models.CharField(verbose_name=_('AS2 Identifier'), max_length=100, primary_key=True)
    email_address = models.EmailField(null=True, blank=True)
    http_auth = models.BooleanField(verbose_name=_('Enable Authentication'), default=False)
    http_auth_user = models.CharField(max_length=100, null=True, blank=True)
    http_auth_pass = models.CharField(max_length=100, null=True, blank=True)
    https_ca_cert = models.FileField(
        max_length=500, upload_to=get_certificate_path,
        verbose_name=_('HTTPS Local CA Store'), null=True, blank=True)
    target_url = models.URLField()
    subject = models.CharField(max_length=255, default=_('EDI Message sent using pyas2'))
    content_type = models.CharField(max_length=100, choices=CONTENT_TYPE_CHOICES, default='application/edi-consent')
    compress = models.BooleanField(verbose_name=_('Compress Message'), default=True)
    encryption = models.CharField(max_length=20, verbose_name=_('Encrypt Message'), choices=ENCRYPT_ALG_CHOICES,
                                  null=True, blank=True)
    encryption_key = models.ForeignKey(PublicCertificate, related_name='enc_partner', null=True, blank=True)
    signature = models.CharField(max_length=20, verbose_name=_('Sign Message'), choices=SIGN_ALG_CHOICES, null=True,
                                 blank=True)
    signature_key = models.ForeignKey(PublicCertificate, related_name='sign_partner', null=True, blank=True)
    mdn = models.BooleanField(verbose_name=_('Request MDN'), default=False)
    mdn_mode = models.CharField(max_length=20, choices=MDN_TYPE_CHOICES, null=True, blank=True)
    mdn_sign = models.CharField(max_length=20, verbose_name=_('Request Signed MDN'), choices=SIGN_ALG_CHOICES,
                                null=True, blank=True)
    keep_filename = models.BooleanField(
        verbose_name=_('Keep Original Filename'),
        default=False,
        help_text=_(
            'Use Original Filename to to store file on receipt, use this option'
            ' only if you are sure partner sends unique names')
    )
    cmd_send = models.TextField(
        verbose_name=_('Command on Message Send'),
        null=True,
        blank=True,
        help_text=_(
            'Command executed after successful message send, replacements are $filename, $sender, '
            '$recevier, $messageid and any message header such as $Subject')
    )
    cmd_receive = models.TextField(
        verbose_name=_('Command on Message Receipt'),
        null=True,
        blank=True,
        help_text=_(
            'Command executed after successful message receipt, replacements are $filename, $fullfilename, '
            '$sender, $recevier, $messageid and any message header such as $Subject')
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Message(models.Model):
    DIRECTION_CHOICES = (
        ('IN', _('Inbound')),
        ('OUT', _('Outbound')),
    )
    STATUS_CHOICES = (
        ('S', _('Success')),
        ('E', _('Error')),
        ('W', _('Warning')),
        ('P', _('Pending')),
        ('R', _('Retry')),
        ('IP', _('In Process')),
    )
    STATUS_ICONS = {
        'S': 'admin/img/icon_success.gif',
        'E': 'admin/img/icon_error.gif',
        'W': 'admin/img/icon_alert.gif',
        'P': 'admin/img/icon_clock.gif',
        'R': 'admin/img/icon_alert.gif',
        'IP': 'images/icon-pass.gif',
    }
    MODE_CHOICES = (
        ('SYNC', _('Synchronous')),
        ('ASYNC', _('Asynchronous')),
    )
    message_id = models.CharField(max_length=100, primary_key=True)
    headers = models.TextField(null=True)
    direction = models.CharField(max_length=5, choices=DIRECTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    adv_status = models.CharField(max_length=255, null=True)
    organization = models.ForeignKey(Organization, null=True)
    partner = models.ForeignKey(Partner, null=True)
    payload = models.OneToOneField(
        'Payload', null=True, related_name='message')
    compressed = models.BooleanField(default=False)
    encrypted = models.BooleanField(default=False)
    signed = models.BooleanField(default=False)
    mdn = models.OneToOneField('MDN', null=True, related_name='omessage')
    mic = models.CharField(max_length=100, null=True)
    mdn_mode = models.CharField(max_length=5, choices=MODE_CHOICES, null=True)
    retries = models.IntegerField(default=0)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return self.message_id

    def msg_id(self):
        return self.message_id.split(MSG_ID_SEP)[0]

    def _headers(self):
        return dict(HeaderParser().parsestr(self.headers or '').items())

    def _parse_cmd(self, cmd):
        """Create command from template, replace variables in the command"""
        variables = {
            'filename': self.payload.name,
            'fullfilename': self.full_filename,
            'sender': self.organization.as2_name,
            'recevier': self.partner.as2_name,
            'messageid': self.msg_id()
        }
        variables.update(self._headers())
        return Template(cmd).safe_substitute(variables)

    def run_post_send(self, *args, **kwargs):
        """Execute command after successful send, can be used to notify successful sends"""
        if self.partner.cmd_send:
            command = self._parse_cmd(self.partner.cmd_send)
            info = '%s "%s"' % (_('Executing post send command:'), command)
            pyas2init.logger.info(info)
            Log.objects.create(message=self, status='S', text=info)
            subprocess.Popen(command.split(' '))

    def run_post_receive(self, *args, **kwargs):
        """Execute command after successful receive, can be used to call the edi program for further processing"""
        if self.partner.cmd_receive:
            command = self._parse_cmd(self.partner.cmd_receive)
            info = '%s "%s"' % (_('Executing post receive command:'), command)
            pyas2init.logger.info(info)
            Log.objects.create(message=self, status='S', text=info)
            subprocess.Popen(command.split(' '))

    def save(self, *args, **kwargs):
        full_filename = kwargs.pop('full_filename', '')
        if not self.timestamp and self.direction == 'IN':
            if not self.organization:
                self.organization = Organization.objects.filter(as2_name=self._headers().get('as2-to')).first()
            if not self.partner:
                self.partner = Partner.objects.filter(as2_name=self._headers().get('as2-from')).first()
            if not self.organization or not self.partner:
                self.status = 'E'
                self.message_id += MSG_ID_SEP + self._headers().get('as2-to', 'NONE')
                self.message_id += MSG_ID_SEP + self._headers().get('as2-from', 'NONE')
            # Create composite key (message_id, organization, partner)
            elif self.organization and self.organization.as2_name:
                self.message_id += MSG_ID_SEP + self.organization.as2_name
                if self.partner and self.partner.as2_name:
                    self.message_id += MSG_ID_SEP + self.partner.as2_name

        if self.timestamp and self.status == 'S':
            this = Message.objects.get(pk=self.pk)
            ######################################
            # Run post receive/send command
            # message need to be saved like this:
            # message.save(full_filename='/path/to/file')
            # path to message to file $fullfilename
            ######################################
            if this.status != self.status:
                pyas2init.logger.debug('full_filename passed to save: %s' % full_filename)
                self.full_filename = full_filename
                # Run post receive
                if self.direction == 'IN' and self.partner.cmd_receive:
                    self.run_post_receive()
                # Run post send
                elif self.direction == 'OUT' and self.partner.cmd_send:
                    self.run_post_send()
        super(Message, self).save(*args, **kwargs)

    def status_icon(self):
        return '<img alt="%(title)s" src="%(static)s%(icon)s" title="%(title)s" style="width: 1em;" />' % {'title': self.get_status_display(), 'static': STATIC_URL, 'icon': self.STATUS_ICONS.get(self.status)}

    status_icon.allow_tags = True
    status_icon.short_description = 'Status'


@python_2_unicode_compatible
class Payload(models.Model):
    name = models.CharField(max_length=100)
    content_type = models.CharField(max_length=255)
    file = models.CharField(max_length=500)

    def __str__(self):
        return self.name


@python_2_unicode_compatible
class Log(models.Model):
    STATUS_CHOICES = (
        ('S', _('Success')),
        ('E', _('Error')),
        ('W', _('Warning')),
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    message = models.ForeignKey(Message, related_name='logs')
    text = models.CharField(max_length=255)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return '%s_%s_%s' % (self.message.direction, self.message, self.status)

    def status_icon(self):
        return '<img alt="%(title)s" src="%(static)s%(icon)s" title="%(title)s" style="width: 1em;" />' % {'title': self.get_status_display(), 'static': STATIC_URL, 'icon': Message.STATUS_ICONS.get(self.status)}

    status_icon.allow_tags = True
    status_icon.short_description = 'Status'


@python_2_unicode_compatible
class MDN(models.Model):
    STATUS_CHOICES = (
        ('S', _('Sent')),
        ('R', _('Received')),
        ('P', _('Pending')),
        ('E', _('Error')),  # Pending go to Error after max retry
    )
    message_id = models.CharField(max_length=100, primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    file = models.CharField(max_length=500)
    headers = models.TextField(null=True)
    return_url = models.URLField(null=True)
    signed = models.BooleanField(default=False)
    retries = models.IntegerField(default=0)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return self.message_id

    def _headers(self):
        return dict(HeaderParser().parsestr(self.headers or '').items())


def getorganizations():
    return [DEFAULT_ENTRY] + [(l, '%s (%s)' % (l, n)) for (l, n) in
                              Organization.objects.values_list('as2_name', 'name')]


def getpartners():
    return [DEFAULT_ENTRY] + [(l, '%s (%s)' % (l, n)) for (l, n) in Partner.objects.values_list('as2_name', 'name')]


@receiver(post_delete, sender=Message)
def post_delete_message(sender, instance, *args, **kwargs):
    """ Delete related mdn """
    if instance.mdn:
        instance.mdn.delete()


@receiver(post_save, sender=Organization)
def check_odirs(sender, instance, created, **kwargs):
    partners = Partner.objects.all()
    for partner in partners:
        as2utils.dirshouldbethere(
            as2utils.join(pyas2init.gsettings['root_dir'], 'messages', instance.as2_name, 'inbox', partner.as2_name))
        as2utils.dirshouldbethere(
            as2utils.join(pyas2init.gsettings['root_dir'], 'messages', partner.as2_name, 'outbox', instance.as2_name))


@receiver(post_save, sender=Partner)
def check_pdirs(sender, instance, created, **kwargs):
    orgs = Organization.objects.all()
    for org in orgs:
        as2utils.dirshouldbethere(
            as2utils.join(pyas2init.gsettings['root_dir'], 'messages', org.as2_name, 'inbox', instance.as2_name))
        as2utils.dirshouldbethere(
            as2utils.join(pyas2init.gsettings['root_dir'], 'messages', instance.as2_name, 'outbox', org.as2_name))


def update_dirs():
    partners = Partner.objects.all()
    orgs = Organization.objects.all()
    for partner in partners:
        for org in orgs:
            as2utils.dirshouldbethere(
                as2utils.join(pyas2init.gsettings['root_dir'], 'messages', org.as2_name, 'inbox', partner.as2_name))
    for org in orgs:
        for partner in partners:
            as2utils.dirshouldbethere(
                as2utils.join(pyas2init.gsettings['root_dir'], 'messages', partner.as2_name, 'outbox', org.as2_name))
