import io
import json

from google.auth import _helpers
from google.auth import crypt
from OpenSSL import crypto


_JSON_FILE_PRIVATE_KEY = 'private_key'
_JSON_FILE_PRIVATE_KEY_ID = 'private_key_id'


class OpenSSLSigner(crypt.Signer):
    def __init__(self, private_key, key_id=None):
        self._key = private_key
        self._key_id = key_id

    @property
    def key_id(self):
        return self._key_id

    def sign(self, message):

        message = _helpers.to_bytes(message)
        return crypto.sign(self._key, message, u'sha256')

    @classmethod
    def from_string(cls, key, key_id=None):
        private_key = crypto.load_privatekey(crypto.FILETYPE_PEM, key)
        return cls(private_key, key_id=key_id)

    @classmethod
    def from_service_account_info(cls, info):
        if _JSON_FILE_PRIVATE_KEY not in info:
            raise ValueError(
                'The private_key field was not found in the service account '
                'info.')

        return cls.from_string(
            info[_JSON_FILE_PRIVATE_KEY],
            info.get(_JSON_FILE_PRIVATE_KEY_ID))

    @classmethod
    def from_service_account_file(cls, filename):
        with io.open(filename, 'r', encoding='utf-8') as json_file:
            data = json.load(json_file)

        return cls.from_service_account_info(data)
