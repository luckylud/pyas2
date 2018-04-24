Configuration
=======================
The global settings for ``pyAS2`` are kept in a single configuration dictionary named ``PYAS2`` in 
your `project's settings.py <https://docs.djangoproject.com/en/1.8/ref/settings/>`_ module. Below is a sample configuration:

.. code-block:: python

    PYAS2 = {
        'ENVIRONMENT': 'default',
        'DATADIR': '/path/to/pyas2/data',
        'MEDIAURI': 'pyas2',
        # As2 receiver ###
        'AS2HOST': 'localhost',  # set WAN IP or domaine hostname
        'AS2PORT': 8880,
        'AS2URI': 'as2receive',
        # MDN URL # uncomment to overide, default mdn url is build
        # this way  http(s)://AS2HOST:AS2PORT/AS2URI
        #'MDNURL': 'http(s)://localhost:8089/as2receive',
        'ASYNCMDNWAIT': 30,
        # https ########
        #'SSLCERTIFICATE': '/path_to_cert/server_cert.pem',
        #'SSLPRIVATEKEY': '/path_to_cert/server_privkey.pem',
        'LOGLEVEL': 'DEBUG',
        'LOGCONSOLE': True,
        'LOGCONSOLELEVEL': 'DEBUG',
        'MAXRETRIES': 5,
        'MAXARCHDAYS': 30,
        # DAEMON ###
        'DAEMONPORT': 16388,
        # Webserver ###
        'HOST': 'localhost',
        'PORT': 8890,
        'ENVIRONMENTTEXT': 'BETA',
        'ENVIRONMENTTEXTCOLOR': 'Yellow',
    }
    MEDIA_ROOT = os.path.join(PYAS2['DATADIR'], 'media')

The available settings along with their usage is described below:

+------------------------+----------------------------+------------------------------------------------+
| Settings Name          | Default Value              | Usage                                          |
+========================+============================+================================================+
| ENVIRONMENT            | production                 | The as2 server in development or production    |
+------------------------+----------------------------+------------------------------------------------+
| PORT                   | 8080                       | HTTP Port as2 server listens on                |
+------------------------+----------------------------+------------------------------------------------+
| SSLCERTIFICATE         | ``None``                   | Path to the SSL Public Key                     |
+------------------------+----------------------------+------------------------------------------------+
| SSLPRIVATEKEY          | ``None``                   | Path to the SSL Private Key                    |
+------------------------+----------------------------+------------------------------------------------+
| DATADIR                | ``Django Project Path``    | Full path to the base directory for storing    | 
|                        |                            | messages, MDNs, certificates and logs          |
+------------------------+----------------------------+------------------------------------------------+
| PYTHONPATH             | ``System Python Path``     | Path to the python executable, required with   |
|                        |                            | virtual environments                           |
+------------------------+----------------------------+------------------------------------------------+
| ENVIRONMENTTEXT        | ``None``                   | Text displayed on right of the logo. Useful    |
|                        |                            | to indicate different environments.            |
+------------------------+----------------------------+------------------------------------------------+
| ENVIRONMENTTEXTCOLOR   | Black                      | Color of the displayed PYTHONPATH. Use HTML    | 
|                        |                            | valid "color name" or #RGB values.             |
+------------------------+----------------------------+------------------------------------------------+
| LOGLEVEL               | INFO                       | Level for logging to log file. Values:         |
|                        |                            | DEBUG,INFO,STARTINFO,WARNING,ERROR or CRITICAL.| 
+------------------------+----------------------------+------------------------------------------------+
| LOGCONSOLE             | True                       | Console logging on (True) or off (False).      |
+------------------------+----------------------------+------------------------------------------------+
| LOGCONSOLELEVEL        | STARTINFO                  | level for logging to console/screen. Values:   | 
|                        |                            | DEBUG,INFO,STARTINFO,WARNING,ERROR or CRITICAL.| 
+------------------------+----------------------------+------------------------------------------------+
| MAXRETRIES             | 10                         | Maximum number of retries for failed outgoing  |
|                        |                            | messages                                       |
+------------------------+----------------------------+------------------------------------------------+
| MDNURL                 | ``None``                   | Return URL for receiving asynchronous MDNs from|
|                        |                            | partners.                                      |
+------------------------+----------------------------+------------------------------------------------+
| ASYNCMDNWAIT           | 30                         | Number of minutes to wait for asynchronous MDNs| 
|                        |                            | after which message will be marked as failed.  |
+------------------------+----------------------------+------------------------------------------------+
| MAXARCHDAYS            | 30                         | Number of days files and messages are kept in  |
|                        |                            | storage.                                       |
+------------------------+----------------------------+------------------------------------------------+
