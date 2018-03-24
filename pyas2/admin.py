import os
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from pyas2 import models, forms


class PrivateCertificateAdmin(admin.ModelAdmin):
    form = forms.PrivateCertificateForm
    list_display = ('__str__', 'download_link',)

    def download_link(self, obj):
        return '<a title="%s" href="%s?type=private&pk=%s">%s</a>' % (
                '%s %s' % (_('Download'), obj),
                reverse_lazy('pyas2:download_cert'),
                obj.pk,
                _('Download'))

    download_link.allow_tags = True
    download_link.short_description = "Download Link"


class PublicCertificateAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'download_link',)

    def download_link(self, obj):
        return '<a title="%s" href="%s?type=public&pk=%s">%s</a>' % (
                '%s %s' % (_('Download'), obj),
                reverse_lazy('pyas2:download_cert'),
                obj.pk,
                _('Download'))

    download_link.allow_tags = True
    download_link.short_description = "Download Link"


class PartnerAdmin(admin.ModelAdmin):
    form = forms.PartnerForm
    list_display = ['name', 'as2_name', 'target_url', 'encryption', 'encryption_key', 'signature', 'signature_key',
                    'mdn', 'mdn_mode']
    list_filter = ('name', 'as2_name')
    fieldsets = (
        (None, {
            'fields': (
                'name', 'as2_name', 'email_address', 'target_url', 'subject', 'content_type', 'confirmation_message')
        }),
        ('Http Authentication', {
            'classes': ('collapse', 'wide'),
            'fields': ('http_auth', 'http_auth_user', 'http_auth_pass', 'https_ca_cert')
        }),
        ('Security Settings', {
            'classes': ('collapse', 'wide'),
            'fields': ('compress', 'encryption', 'encryption_key', 'signature', 'signature_key')
        }),
        ('MDN Settings', {
            'classes': ('collapse', 'wide'),
            'fields': ('mdn', 'mdn_mode', 'mdn_sign')
        }),
        ('Advanced Settings', {
            'classes': ('collapse', 'wide'),
            'fields': ('keep_filename', 'cmd_send', 'cmd_receive')
        }),
    )


class OrganizationAdmin(admin.ModelAdmin):
    list_display = ['name', 'as2_name']
    list_filter = ('name', 'as2_name')


admin.site.register(models.PrivateCertificate, PrivateCertificateAdmin)
admin.site.register(models.PublicCertificate, PublicCertificateAdmin)
admin.site.register(models.Organization, OrganizationAdmin)
admin.site.register(models.Partner, PartnerAdmin)
admin.site.register(models.Message)
admin.site.register(models.MDN)
