#!/usr/bin/env python3
#
# Copyright (C) 2022 VyOS maintainers and contributors
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2 or later as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import re
import sys

from cryptography.fernet import Fernet

from vyos.defaults import encrypt_magic
from vyos.tpm import clear_tpm_key
from vyos.tpm import init_tpm
from vyos.tpm import read_tpm_key
from vyos.tpm import write_tpm_key
from vyos.util import ask_input
from vyos.util import ask_yes_no

def encrypt_config_file(config_file, encrypted_out_file, key=None, save_to_tpm=True):
    """
    Encrypts config file with key
    If key is not specified, it will be generated (256 bit)
    Using cryptography.Fernet (AES-128 CBC)
    """
    if not os.path.exists(config_file):
        raise Exception('Config file does not exist')

    if not key:
        key = Fernet.generate_key()

    fernet = Fernet(key)
    encrypted_str = b''

    with open(config_file, 'rb') as f:
        encrypted_str = fernet.encrypt(f.read())

    with open(encrypted_out_file, 'wb') as f:
        f.write(encrypt_magic + encrypted_str)

    if save_to_tpm:
        try:
            clear_tpm_key()
        except:
            pass
        write_tpm_key(key)

    return True

def decrypt_config_file(encrypted_config_file, decrypted_out_file, key=None):
    """
    Decrypts config file with key
    If key is not specified, it will be read from TPM
    """
    if not os.path.exists(encrypted_config_file):
        raise Exception('Encrypted config file does not exist')

    if not key:
        key = read_tpm_key()

    fernet = Fernet(key)
    decrypted_str = b''

    with open(encrypted_config_file, 'rb') as f:
        encrypted_str = f.read()
        if not encrypted_str.startswith(encrypt_magic):
            raise Exception('Not a valid encrypted VyOS config')
        magic_len = len(encrypt_magic)
        decrypted_str = fernet.decrypt(encrypted_str[magic_len:])

    with open(decrypted_out_file, 'wb') as f:
        f.write(decrypted_str)

    return True

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Must specify config file and target file.")
        sys.exit(1)
    else:
        file_name = sys.argv[1]
        new_file_name = sys.argv[2]

    decrypt = '--decrypt' in sys.argv
    disable = '--disable' in sys.argv
    first_run = '--first-run' in sys.argv
    use_tpm = '--tpm' in sys.argv
    update_tpm = use_tpm and ('--upgrade' in sys.argv or first_run)

    key = None
    if (first_run and not ask_yes_no('Generate encryption key?', default=True)) or not use_tpm:
        while True:
            key = ask_input('Enter encryption key:', default=None)

            if len(key) == 32:
                break

            print('Invalid key - must be 32 characters, try again.')

    try:
        if disable or decrypt:
            decrypt_config_file(file_name, new_file_name, key=key)
            if use_tpm and disable:
                clear_tpm_key()
        else:
            encrypt_config_file(file_name, new_file_name, key=key, save_to_tpm=update_tpm)
            short_file_name = new_file_name.replace("/opt/vyatta/etc", "")
            print(f'Saved encrypted config file to {short_file_name}')

        if first_run or disable:
            os.unlink(file_name)

        if first_run:
            if not key:
                print('Back-up the encryption key in a safe place!')
                print('Encryption key: ' + read_tpm_key().decode('utf-8'))
    except Exception as e:
        word = 'decrypt' if disable or decrypt else 'encrypt'
        print(f'Failed to {word} config file: {e}')
