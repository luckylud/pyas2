"""
PyAs2 receiver root url
Set 'AS2URI' in PYAS2 settings
'AS2URI': 'pyas2/as2receive',
or
'AS2URI': 'whateveras2',

"""
from django.conf.urls import url

from ..views import as2receive


urlpatterns = [
    # as2 receiver (messages and async MDN)
    # Set 'AS2URI' in PYAS2 settings
    url(r'^.*',
        as2receive,
        name='as2-receive'
        )
]
