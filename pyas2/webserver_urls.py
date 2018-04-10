# -*- coding: utf-8 -*-

from django.conf.urls import url, include
from django.contrib import admin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import views as auth_views

from . import views, urls as pyas2_urls

admin.autodiscover()

staff_required = user_passes_test(lambda u: u.is_staff)
superuser_required = user_passes_test(lambda u: u.is_superuser)

urlpatterns = [
    url(r'^login.*', auth_views.login, {'template_name': 'admin/login.html'}, name='login'),
    url(r'^logout.*', auth_views.logout, {'next_page': 'home'}, name='logout'),
    url(r'^password_change/$', auth_views.password_change, name='password_change'),
    url(r'^password_change/done/$', auth_views.password_change_done, name='password_change_done'),
    ###   PYAS2 - URLS  ###
    url(r'^pyas2/', include(pyas2_urls, namespace='pyas2', app_name='pyas2')),
    ### PYAS2 - ADMIN ###
    url(r'^pyas2adm/', include(admin.site.urls)),
    # catch-all
    url(r'^.*', login_required(views.home, login_url='login'), name='home'),
]

handler500 = 'pyas2.views.server_error'
handler400 = 'pyas2.views.client_error'
