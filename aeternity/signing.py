import os
from collections import namedtuple

from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from ecdsa import SECP256k1, SigningKey

alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'


def base58encode(bytes):
    accu = sum(i << idx * 8 for idx, i in enumerate(reversed(bytes)))
    if accu == 0:
        return alphabet[0]
    retval = ''
    while accu > 0:
        accu, b58 = divmod(accu, 58)
        retval = alphabet[b58] + retval
    return retval


def base58decode(base58str):
    retval = b''
    accu = 0
    for c in base58str:
        accu += accu * 57 + alphabet.index(c)
    while accu > 0:
        accu, b256 = divmod(accu, 256)
        retval = bytes([b256]) + retval
    return retval


SignedTransaction = namedtuple('SignedTransaction', ['transaction', 'signatures'])


class KeyPair:
    def __init__(self, public, private):
        self.public = public
        self.private = private
        self.signing_key = SigningKey.from_der(self.private)

    def sign_transaction(self, transaction):
        transaction_hash = base58decode(transaction.tx_hash.split('$')[1])
        signature = self.signing_key.sign(transaction_hash)
        return SignedTransaction(
            transaction=transaction,
            signatures=[signature]
        )
    #
    # initializers
    #

    @classmethod
    def generate(cls):
        raise NotImplementedError()

    @classmethod
    def decrypt_key(cls, key_content, password):
        hash = SHA256.new()
        if isinstance(password, str):
            password = password.encode('utf-8')
        hash.update(password)
        password_digest = hash.digest()
        aes = AES.new(password_digest, AES.MODE_ECB)
        return aes.decrypt(key_content)

    @classmethod
    def read_from_files(cls, public_key_file, private_key_file, password):
        with open(public_key_file, 'rb') as fh:
            public = cls.decrypt_key(fh.read(), password)
        with open(private_key_file, 'rb') as fh:
            private = cls.decrypt_key(fh.read(), password)
        return KeyPair(public, private)

    @classmethod
    def read_from_dir(cls, directory, password):
        return cls.read_from_files(
            os.path.join(directory, 'key.pub'),
            os.path.join(directory, 'key'),
            password
        )
