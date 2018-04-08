
from django.contrib import admin
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from . import models, forms


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


class MessageAdmin(admin.ModelAdmin):
    readonly_fields = [f.name for f in models.Message._meta.fields]
    list_display = ['message_id', 'status', 'direction', 'partner', 'timestamp']
    list_filter = ['direction', 'status', 'partner']
    search_fields = ['message_id']

    def has_add_permission(self, request):
        return False

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        extra_context['show_save'] = False
        return super(MessageAdmin, self).changeform_view(request, object_id, extra_context=extra_context)


class MdnAdmin(admin.ModelAdmin):
    list_display = ['message_id', 'status', 'signed', 'timestamp']
    list_filter = ['status', 'signed']
    search_fields = ['message_id']


admin.site.register(models.PrivateCertificate, PrivateCertificateAdmin)
admin.site.register(models.PublicCertificate, PublicCertificateAdmin)
admin.site.register(models.Organization, OrganizationAdmin)
admin.site.register(models.Partner, PartnerAdmin)
admin.site.register(models.Message, MessageAdmin)
admin.site.register(models.MDN, MdnAdmin)
