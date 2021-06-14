import binascii
import os

from cryptography.hazmat.primitives.asymmetric import ec
from ecies import encrypt, decrypt, hex2prv, hex2pub
from ecies.utils import generate_eth_key


def ecies_key_generation():
    private_key = ec.generate_private_key(ec.SECP384R1())
    public_key = private_key.public_key()
    
    priv_key = generate_eth_key()
    priv_key_hex = priv_key.to_hex()
    pub_key_hex = priv_key.public_key.to_hex()
    return priv_key_hex, pub_key_hex


def save_keys_to_file(private_key_hex, public_key_hex, filename):
    # encrypt key first
    #from symmetric_encryption import sym_encrypt
    with open("private_keys/ecies/" + filename, 'wb') as out:
        #out.write(sym_encrypt(private_key_hex, enc_password))
        out.write(private_key_hex)

    filename = filename.replace("eciesprivkey", "eciespubkey")
    with open("public_keys/ecies/" + filename, 'w') as out:
        out.write(public_key_hex)


def load_private_key_from_file(filename):
    try:
        with open("private_keys/ecies/" + filename, 'rb') as out:
            key = out.read()
        return key.decode("utf-8")
    except FileNotFoundError:
        print("Can't find key oops")


def load_public_key_from_file(filename):
    try:
        with open("public_keys/ecies/" + filename, 'r') as out:
            key = out.read()
        return key
    except FileNotFoundError:
        print("Can't find key oops")


def encryptt(pub_key_hex, message):
    encrypted = binascii.hexlify(encrypt(pub_key_hex, bytes(message)))
    return encrypted.decode("utf-8")


def decryptt(priv_key_hex, cipher_text):
    decrypted = decrypt(priv_key_hex, binascii.unhexlify(cipher_text))
    return decrypted


def list_public_keys():
    files = os.listdir("public_keys/ecies")
    for f in files:
        key = load_public_key_from_file(f)

def list_private_keys():
    files = os.listdir("private_keys/ecies")
    for f in files:
        with open("private_keys/ecies/" + f, 'r') as out:
            key = out.read()

def verify(public_key_hex, sig, message):
    public_key = hex2pub(public_key_hex)
    if public_key.verify(binascii.unhexlify(sig), message.encode("utf-8")):
        return True
    else:
        return False

def sign(private_key_hex, message):
    private_key = hex2prv(private_key_hex)
    signature = private_key.sign(message.encode("utf-8"))
    return binascii.hexlify(signature).decode("utf-8")