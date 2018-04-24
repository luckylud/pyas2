import os
from django.core.files import File
from django.test import TestCase, Client
from email import utils as emailutils
from email.parser import HeaderParser
from email import message_from_string
from itertools import izip
import shutil

from pyas2 import models, pyas2init, as2lib


FIXTURES_DIR = os.path.join((os.path.dirname(
    os.path.abspath(__file__))),  'fixtures')
TEST_DIR = os.path.join(pyas2init.gsettings.get('root_dir'), 'test')
if not os.path.isdir(TEST_DIR):
    os.mkdir(TEST_DIR)
for f in ['testmessage.edi', 'si_signed_cmp.msg', 'si_signed.mdn']:
    shutil.copyfile(os.path.join(FIXTURES_DIR, f),
                    os.path.join(TEST_DIR, f))


class AS2SendReceiveTest(TestCase):
    """Test cases for the AS2 server and client.
    We will be testing each permutation as defined in RFC 4130 Section 2.4.2
    """
    @classmethod
    def setUpTestData(cls):
        # Every test needs a client.
        cls.client = Client()
        cls.header_parser = HeaderParser()

        # Load the client and server certificates
        cls.server_key = models.PrivateCertificate()
        cls.server_key.certificate.save('as2server.pem',
                                        File(open(os.path.join(FIXTURES_DIR, 'as2server.pem'), 'r')))
        cls.server_key.certificate_passphrase = 'password'
        cls.server_key.save()

        cls.server_crt = models.PublicCertificate()
        cls.server_crt.certificate.save('as2server.crt',
                                        File(open(os.path.join(FIXTURES_DIR, 'as2server.crt'), 'r')))
        cls.server_crt.save()

        cls.client_key = models.PrivateCertificate()
        cls.client_key.certificate.save('as2client.pem',
                                        File(open(os.path.join(FIXTURES_DIR, 'as2client.pem'), 'r')))
        cls.client_key.certificate_passphrase = 'password'
        cls.client_key.save()

        cls.client_crt = models.PublicCertificate()
        cls.client_crt.certificate.save('as2client.crt',
                                        File(open(os.path.join(FIXTURES_DIR, 'as2client.crt'), 'r')))
        cls.client_crt.save()

        # Setup the server organization and partner
        models.Organization.objects.create(
            name='Server Organization',
            as2_name='as2server',
            encryption_key=cls.server_key,
            signature_key=cls.server_key
        )
        models.Partner.objects.create(
            name='Server Partner',
            as2_name='as2client',
            target_url=pyas2init.gsettings['mdn_url'],
            compress=False,
            mdn=False,
            signature_key=cls.client_crt,
            encryption_key=cls.client_crt
        )

        # Setup the client organization and partner
        cls.organization = models.Organization.objects.create(
            name='Client Organization',
            as2_name='as2client',
            encryption_key=cls.client_key,
            signature_key=cls.client_key
        )

        # Initialise the payload i.e. the file to be transmitted
        cls.payload = models.Payload.objects.create(
            name='testmessage.edi',
            file=os.path.join(TEST_DIR, 'testmessage.edi'),
            content_type='application/edi-consent'
        )

    def testEndpoint(self):
        """ Test if the as2 reveive endpoint is active """

        response = self.client.get(pyas2init.gsettings.get('as2_uri', '/pyas2/as2receive'))
        self.assertEqual(response.status_code, 200)

    def testNoEncryptMessageNoMdn(self):
        """ Test Permutation 1: Sender sends un-encrypted data and does NOT request a receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                mdn=False)

        # Build and send the message to server
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testNoEncryptMessageMdn(self):
        """ Test Permutation 2: Sender sends un-encrypted data and requests an unsigned receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                mdn=True)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testNoEncryptMessageSignMdn(self):
        """ Test Permutation 3: Sender sends un-encrypted data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                mdn=True,
                                                mdn_mode='SYNC',
                                                mdn_sign='sha1',
                                                signature_key=self.server_crt)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptMessageNoMdn(self):
        """ Test Permutation 4: Sender sends encrypted data and does NOT request a receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                mdn=False)

        # Build and send the message to server
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptMessageMdn(self):
        """ Test Permutation 5: Sender sends encrypted data and requests an unsigned receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                mdn=True)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptMessageSignMdn(self):
        """ Test Permutation 6: Sender sends encrypted data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                mdn=True,
                                                mdn_mode='SYNC',
                                                mdn_sign='sha1',
                                                signature_key=self.server_crt)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testSignMessageNoMdn(self):
        """ Test Permutation 7: Sender sends signed data and does NOT request a receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=False)

        # Build and send the message to server
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testSignMessageMdn(self):
        """ Test Permutation 8: Sender sends signed data and requests an unsigned receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True)

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testSignMessageSignMdn(self):
        """ Test Permutation 9: Sender sends signed data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True,
                                                mdn_sign='sha1')

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptSignMessageNoMdn(self):
        """ Test Permutation 10: Sender sends encrypted and signed data and does NOT request a receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                mdn=False)

        # Build and send the message to server
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptSignMessageMdn(self):
        """ Test Permutation 11: Sender sends encrypted and signed data and requests an unsigned receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True)

        # Setup the message object and build the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptSignMessageSignMdn(self):
        """ Test Permutation 12: Sender sends encrypted and signed data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True,
                                                mdn_sign='sha1')

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testCompressEncryptSignMessageSignMdn(self):
        """ Test Permutation 13: Sender sends compressed, encrypted and signed data and requests an signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=True,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True,
                                                mdn_sign='sha1')

        # Setup the message object and buid the message
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)

        # Check if a 200 response was received
        self.assertEqual(response.status_code, 200)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Process the MDN for the in message and check status
        AS2SendReceiveTest.buildMdn(in_message, response)
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

    def testEncryptSignMessageAsyncSignMdn(self):
        """ Test Permutation 14: Sender sends encrypted and signed data and requests an Asynchronous signed receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True,
                                                mdn_mode='ASYNC',
                                                mdn_sign='sha1')
        self.run_async_test(partner)


    def testEncryptSignMessageAsyncMdn(self):
        """ Test Permutation 15: Sender sends encrypted and signed data and requests an Asynchronous receipt. """

        # Create the partner with appropriate settings for this case
        partner = models.Partner.objects.create(name='Client Partner',
                                                as2_name='as2server',
                                                target_url=pyas2init.gsettings['mdn_url'],
                                                compress=False,
                                                encryption='des_ede3_cbc',
                                                encryption_key=self.server_crt,
                                                signature='sha1',
                                                signature_key=self.server_crt,
                                                mdn=True,
                                                mdn_mode='ASYNC',
                                                mdn_sign='')
        self.run_async_test(partner)


    def run_async_test(self, partner):
        # Setup the message object and build the message, do not send it
        message_id = emailutils.make_msgid().strip('<>')
        in_message, response = self.buildSendMessage(message_id, partner)
        pyas2init.logger.info('Message created: %s' % in_message)
        # AS2SendReceiveTest.printLogs(in_message)

        # Check if message was processed successfully
        out_message = models.Message.objects.get(message_id__startswith=message_id, direction='IN')
        pyas2init.logger.info('Message received: %s' % out_message)
        # AS2SendReceiveTest.printLogs(out_message)
        self.assertEqual(out_message.status, 'S')

        # Check if input and output files are the same
        self.assertTrue(AS2SendReceiveTest.compareFiles(self.payload.file, out_message.payload.file))

        # Process the ASYNC MDN for the in message and check status
        http_headers = {}
        for header, value in out_message.mdn._headers().items():
            key = 'HTTP_%s' % header.replace('-', '_').upper()
            http_headers[key] = value

        with open(out_message.mdn.file, 'rb') as mdn_file:
            mdn_content = mdn_file.read()

        # Send the async mdn and check for its status
        content_type = http_headers.pop('HTTP_CONTENT_TYPE')
        response = self.client.post(pyas2init.gsettings.get('as2_uri', '/pyas2/as2receive'),
                                    data=mdn_content,
                                    content_type=content_type,
                                    **http_headers)
        self.assertEqual(response.status_code, 200)

        in_message = models.Message.objects.get(message_id__startswith=message_id, direction='OUT')
        # AS2SendReceiveTest.printLogs(in_message)
        self.assertEqual(in_message.status, 'S')

    def buildSendMessage(self, message_id, partner):
        """ Function builds the message and posts the request. """

        message = models.Message.objects.create(message_id=message_id,
                                                partner=partner,
                                                organization=self.organization,
                                                direction='OUT',
                                                status='IP',
                                                payload=self.payload)
        processed_payload = as2lib.build_message(message)

        # Set up the Http headers for the request
        http_headers = {}
        for header, value in message._headers().items():
            key = 'HTTP_%s' % header.replace('-', '_').upper()
            http_headers[key] = value
        http_headers['HTTP_MESSAGE_ID'] = message_id
        content_type = http_headers.pop('HTTP_CONTENT_TYPE')
        # Post the request and return the response
        response = self.client.post(pyas2init.gsettings.get('as2_uri', '/pyas2/as2receive'),
                                    data=processed_payload,
                                    content_type=content_type,
                                    **http_headers)
        return message, response

    @staticmethod
    def buildMdn(out_message, response):
        mdn_content = ''
        for key in ['message-id', 'content-type', ]:
            mdn_content += '%s: %s\n' % (key, response[key])
        mdn_content = '%s\n%s' % (mdn_content, response.content)
        as2lib.save_mdn(out_message, mdn_content)

    @staticmethod
    def printLogs(message):
        logs = models.Log.objects.filter(message=message)
        for log in logs:
            print (log.status, log.text)

    @staticmethod
    def compareFiles(filename1, filename2):
        with open(filename1, "rtU") as a:
            with open(filename2, "rtU") as b:
                # Note that "all" and "izip" are lazy
                # (will stop at the first line that's not identical)
                return all(lineA == lineB for lineA, lineB in izip(a.xreadlines(), b.xreadlines()))


class AS2SterlingIntegratorTest(TestCase):
    """Test cases against the Sterling B2B Integrator AS2 server."""

    @classmethod
    def setUpTestData(cls):
        # Every test needs a client.
        cls.client = Client()
        cls.header_parser = HeaderParser()

        # Load the client and server certificates
        cls.server_key = models.PrivateCertificate()
        cls.server_key.certificate.save('as2server.pem',
                                        File(open(os.path.join(FIXTURES_DIR, 'as2server.pem'), 'r')))
        cls.server_key.certificate_passphrase = 'password'
        cls.server_key.save()

        cls.si_public_key = models.PublicCertificate()
        cls.si_public_key.certificate.save('si_public_key.crt',
                                        File(open(os.path.join(FIXTURES_DIR, 'si_public_key.crt'), 'r')))
        cls.si_public_key.ca_cert.save('si_public_key.ca',
                                        File(open(os.path.join(FIXTURES_DIR, 'si_public_key.ca'), 'r')))
        cls.si_public_key.verify_cert = False
        cls.si_public_key.save()

        # Setup the server organization and partner
        cls.organization = models.Organization.objects.create(
            name='Server Organization',
            as2_name='as2server',
            encryption_key=cls.server_key,
            signature_key=cls.server_key
        )

        cls.partner = models.Partner.objects.create(
            name='Sterling B2B Integrator',
            as2_name='SIAS2PRD',
            target_url=pyas2init.gsettings['mdn_url'],
            compress=False,
            mdn=False,
            signature_key=cls.si_public_key,
            encryption_key=cls.si_public_key
        )

        # Initialise the payload i.e. the file to be transmitted
        cls.payload = models.Payload.objects.create(
            name='testmessage.edi',
            file=os.path.join(TEST_DIR, 'testmessage.edi'),
            content_type='application/edi-consent'
        )

    def test_process_message(self):
        with open(os.path.join(TEST_DIR, 'si_signed_cmp.msg')) as msg:
            raw_payload = msg.read()
            payload = message_from_string(raw_payload)
            message = models.Message.objects.create(
                message_id=payload.get('message-id').strip('<>'),
                direction='IN',
                status='IP',
                headers='as2-from: %s\nas2-to: %s\n' % (payload.get('as2-from'),
                                                        payload.get('as2-to'))
            )
            as2lib.save_message(message, payload, raw_payload)

    def test_process_mdn(self):
        message = models.Message.objects.create(
            message_id='151694007918.24690.7052273208458909245@ip-172-31-14-209.ec2.internal',
            partner=self.partner, organization=self.organization,
            direction='OUT', status='IP', payload=self.payload)

        with open(os.path.join(TEST_DIR, 'si_signed.mdn')) as mdn:
            as2lib.save_mdn(message, mdn.read())

