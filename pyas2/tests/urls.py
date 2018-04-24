"""pyas2_test URL Configuration

"""
from django.conf.urls import url, include
from django.contrib import admin
# from django.contrib.auth import views as auth_views

urlpatterns = [
    # url(r'^login.*', auth_views.login, name='login'),
    url(r'^admin/', admin.site.urls),
    url(r'^pyas2/as2receive.*', include('pyas2.as2receiver_urls')),
    # url(r'^pyas2/', include('pyas2.urls')),
]
