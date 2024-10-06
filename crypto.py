from Crypto.Util.Padding import pad
import codecs
from Crypto.Util.Padding import unpad
from Crypto.Cipher import AES

KEY = b"ILOVEFETIXFETIX!"
IV = b"!@#$FETIXEVENTiv"


def encrypt(text, key=KEY, iv=IV):
    cipher = AES.new(key, AES.MODE_CBC, iv)
    padded_text = pad(text.encode("utf-8"), AES.block_size)
    encrypted_data = cipher.encrypt(padded_text)
    return codecs.encode(encrypted_data, "hex").decode("utf-8")


def decrypt(data, key=KEY, iv=IV):
    data = codecs.decode(data, "hex")
    cipher = AES.new(key, AES.MODE_CBC, iv)
    return unpad(cipher.decrypt(data), AES.block_size).decode("utf-8")
