Release History
===============

0.4.1 - 2018-04-11
~~~~~~~~~~~~~~~

* Webserver: Add cookies settings

* Update views.py specialy as2receive
         - Check AS2 validity of http request posted
         - Save raw incoming AS2 message
         - Cleaning

* Fix & Update for retryfailedas2comms
         - Fix increase of msg.retries, was increase by it own value each
           time, now is only increase by one.
           msg.retries is set to 0 by default at creation

* Fix & Update for sendasyncmdn
         - Fix for negative mdn 'unknown-trading-partner'
           Fir for mdn.omessage with no related partner or organization
         - Increase mdn.max_retries end set mdn.status to 'E' after MAXRETRIES

* Update models.py, Message, MDN, ...
         - Message.message_id is now a composite key (message_id, organization, partner),
           only for incomming message message_id#organization#partner
         - Delete related mdn when delete a message
         - add decorator @python_2_unicode_compatible
         - post_receive and post_send command are now trigered at
           message.save() if message.status is 'S' success.
         - Add default ordering for all tables queries

* Add pyas2 scripts:
           pyas2-webserver.py
           pyas2-receiver.py
           pyas2-daemon.py
           pyas2-sendas2message.py
           pyas2-sendasyncmdn.py
           pyas2-retryfailedcoms.py
           pyas2-migrate.py
           pyas2-shell.py
           pyas2-test.py
           pyas2-cleanas2server.py

* Fix send_message for ASYNC MDN
         - When async mdn is return immediatly after request.post by as2 parnter,
           message.status was saved to pending 'P' while as2receive already updated
           message.status to 'S' or 'E'

* Use multiprocess.Process to call management.call_command

* Fix and update sendmessage
         Fix: temp file was never closed

* Update logging Initialisation

* Add standalone as2 receiver and pyas2 webserver
         MEDIA_ROOT settings needed to cleanly store certificates for django
         Set up PYAS2 with environment variable:
             PYAS2_ROOT=/path/to/pyas2_data/
             or overide all pyas2.config.pyas2settings
             PYAS2_SETTINGS_FILE=/path/to/pyas2settings.py

         By default, there are two databases (default:webserver and pyas2)
         Populate databases:
                 pyas2-migrate.py

         run as2 receiver:
                 pyas2-receiver.py

         run pyas2 webserver:
                 pyas2-webserver.py

0.4.0 - 2017-01-27
~~~~~~~~~~~~~~~

* Cleaner handling of signature verifications
* Added test cases for sterling b2b integrator message and mdn
* Set `max_length` for file fields to manage long folder names.

0.3.8 - 2017-01-09
~~~~~~~~~~~~~~~~~~

* Give option to download certs from the admin.


0.3.7 - 2017-01-09
~~~~~~~~~~~~~~~~~~

* Use a function to get the certificate upload_to.

0.3.6 - 2017-01-05
~~~~~~~~~~~~~~~~~~

* Added view for downloading certificates from the admin.

0.3.5 - 2017-12-20
~~~~~~~~~~~~~~~~~~

* Renewed the certificates used in the django tests.

0.3.4 - 2017-08-17
~~~~~~~~~~~~~~~~~~

* Add migration to the distribution.

0.3.3 - 2017-04-04
~~~~~~~~~~~~~~~~~~

* Use pagination when listing messages in the GUI, also do not use Datatables.
* Set the request MDN field default value to False.

0.3.2 - 2017-03-07
~~~~~~~~~~~~~~~~~~

* Freeze versions of django and CherryPy in setup.py.

0.3.1 - 2016-10-03
~~~~~~~~~~~~~~~~~~

* Fixed pagination issue where it was showing only 25 messages and mdns.
* Added the admin command cleanas2server for deleting old data and logs.

0.3.0 - 2016-06-28
~~~~~~~~~~~~~~~~~~

* Added django test cases for testing each of the permutations as defined in RFC 4130 Section 2.4.2
* Code now follows the pep-8 standard
* Django admin commands now use argparse instead or optparse

0.2.3 - 2016-04-20
~~~~~~~~~~~~~~~~~~

* Added functionality to customize MDN messages at organization and partner levels.

0.2.2 - 2015-10-12
~~~~~~~~~~~~~~~~~~

* Fixes to take care of changes in Django 1.9.x

0.2.1 - 2015-10-12
~~~~~~~~~~~~~~~~~~

* Updated installation and upgrade documentation.

0.2 - 2015-10-11
~~~~~~~~~~~~~~~~

* Added option to disable verification of public certificates at the time of signature verification.
* Fixed bug in the send daemon.
* Added debug log statements.
* Added some internationlization to model fields.

0.1.2 - 2015-09-07
~~~~~~~~~~~~~~~~~~

* Created readthedocs documentation.
* Fixed bug where inbox and outbox folders were not created on saving partners and orgs.
* Fixed bug where MDN search was failing due to orphaned MDNs.

0.1.1 - 2015-09-04
~~~~~~~~~~~~~~~~~~

* Increased the max length of MODE_CHOICES model field.
* Detect Signature Algorithm from the MIME message for outbound messages.

0.1 - 2015-04-29
~~~~~~~~~~~~~~~~

* Initial release.

.. _`master`: https://github.com/abhishek-ram/pyas2 
