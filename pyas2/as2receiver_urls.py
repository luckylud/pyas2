"""
PyAs2 receiver root url 
Configure 'URI' in PYAS2 settings
'URI': 'pyas2/receive',
or
'URI': 'as2receive',
or 
...

"""
from django.conf.urls import url

from .views import as2receive


urlpatterns = [
    # as2 messages and MDN receive
    # configure 'URI' in PYAS2 settings 
    url(r'^.*', 
        as2receive,
        name='as2-receive'
    )
]
