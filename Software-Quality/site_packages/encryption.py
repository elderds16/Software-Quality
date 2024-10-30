import os
import pickle
import random
from math import gcd

class RSA:
    """
    RSA encryption and decryption class using public and private keys
    """
    public_key = None
    private_key = None
    keys_directory = os.path.join(os.path.dirname(os.path.abspath(__file__)), '../backend/keys')

    def __init__(self):
        # Initialize RSA keys
        if self.public_key is None or self.private_key is None:
            self.public_key, self.private_key = self.initialize_keys()

    def generate_prime_candidate(self, length):
        """
        Generate a prime candidate
        :param length: which is the bit length of the prime
        :return:
        """
        p = random.getrandbits(length)
        p |= (1 << length - 1) | 1
        return p

    def is_prime(self, n, k=128):
        """
        Miller-Rabin primality test
        :param n: which is the number to test
        :param k: which is the number of tests to run
        :return:
        """
        if n == 2 or n == 3:
            return True
        if n % 2 == 0:
            return False
        s = 0
        r = n - 1
        while r & 1 == 0:
            s += 1
            r //= 2
        for _ in range(k):
            a = random.randrange(2, n - 1)
            x = pow(a, r, n)
            if x != 1 and x != n - 1:
                j = 1
                while j < s and x != n - 1:
                    x = pow(x, 2, n)
                    if x == 1:
                        return False
                    j += 1
                if x != n - 1:
                    return False
        return True

    def generate_prime_number(self, length=1024):
        """
        Generate a prime number
        :param length: which is the bit length of the prime
        :return:
        """
        p = 4
        while not self.is_prime(p, 128):
            p = self.generate_prime_candidate(length)
        return p

    def modinv(self, a, m):
        """
        Modular inverse using extended Euclidean algorithm
        :param a: which is the number
        :param m: which is the modulo
        :return:
        """
        m0, x0, x1 = m, 0, 1
        if m == 1:
            return 0
        while a > 1:
            q = a // m
            m, a = a % m, m
            x0, x1 = x1 - q * x0, x0
        if x1 < 0:
            x1 += m0
        return x1

    def generate_keypair(self, keysize):
        """
        Generate an RSA keypair with a given keysize
        :param keysize: which is the bit length of the key
        :return:
        """
        p = self.generate_prime_number(keysize // 2)
        q = self.generate_prime_number(keysize // 2)
        n = p * q
        phi = (p - 1) * (q - 1)
        e = random.randrange(1, phi)
        g = gcd(e, phi)
        while g != 1:
            e = random.randrange(1, phi)
            g = gcd(e, phi)
        d = self.modinv(e, phi)
        return ((e, n), (d, n))

    def encrypt(self, plaintext):
        """
        Encrypt the plaintext using the public key and return the ciphertext
        :param plaintext: which is the text to encrypt
        :return:
        """
        if not plaintext:
            return None

        e, n = self.public_key
        cipher = [pow(ord(char), e, n) for char in plaintext]
        # Serialize the list of integers to bytes using pickle
        return pickle.dumps(cipher)

    def decrypt(self, ciphertext):
        """
        Decrypt the ciphertext using the private key and return the plaintext
        :param ciphertext: which is the text to decrypt
        :return:
        """
        try:
            if not ciphertext or ciphertext == b'\xef\xbb\xbf':
                return None

            d, n = self.private_key
            # Deserialize the bytes back into a list of integers

            cipher = pickle.loads(ciphertext)
            plain = [chr(pow(char, d, n)) for char in cipher]
            return ''.join(plain)
        except Exception as e:
            print(ciphertext, e)

    def save_keys(self, public_key, private_key):
        """
        Save the public and private keys to files for future use
        :param public_key:
        :param private_key:
        :return:
        """
        if not os.path.exists(self.keys_directory):
            os.makedirs(self.keys_directory)
        with open(os.path.join(self.keys_directory, 'public_key.pem'), 'wb') as pub_file:
            pickle.dump(public_key, pub_file)
        with open(os.path.join(self.keys_directory, 'private_key.pem'), 'wb') as priv_file:
            pickle.dump(private_key, priv_file)

    def load_keys(self):
        """
        Load the public and private keys from files into memory
        :return:
        """
        with open(os.path.join(self.keys_directory, 'public_key.pem'), 'rb') as pub_file:
            self.public_key = pickle.load(pub_file)
        with open(os.path.join(self.keys_directory, 'private_key.pem'), 'rb') as priv_file:
            self.private_key = pickle.load(priv_file)
        return self.public_key, self.private_key

    def initialize_keys(self):
        """
        Initialize the public and private keys by generating them or loading them from files
        :return:
        """
        if not os.path.exists(self.keys_directory) or not os.path.isfile(os.path.join(self.keys_directory, 'public_key.pem')) or not os.path.isfile(os.path.join(self.keys_directory, 'private_key.pem')):
            self.public_key, self.private_key = self.generate_keypair(64)
            self.save_keys(self.public_key, self.private_key)
        else:
            self.load_keys()
        return self.public_key, self.private_key
