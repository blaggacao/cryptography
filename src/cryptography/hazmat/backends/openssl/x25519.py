# This file is dual licensed under the terms of the Apache License, Version
# 2.0, and the BSD License. See the LICENSE file in the root of this repository
# for complete details.

from __future__ import absolute_import, division, print_function

from cryptography import utils
from cryptography.hazmat.backends.openssl.utils import _evp_pkey_derive
from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey, X25519PublicKey
)


@utils.register_interface(X25519PublicKey)
class _X25519PublicKey(object):
    def __init__(self, backend, evp_pkey):
        self._backend = backend
        self._evp_pkey = evp_pkey

    def public_bytes(self):
        ucharpp = self._backend._ffi.new("unsigned char **")
        res = self._backend._lib.EVP_PKEY_get1_tls_encodedpoint(
            self._evp_pkey, ucharpp
        )
        self._backend.openssl_assert(res == 32)
        self._backend.openssl_assert(ucharpp[0] != self._backend._ffi.NULL)
        data = self._backend._ffi.gc(
            ucharpp[0], self._backend._lib.OPENSSL_free
        )
        return self._backend._ffi.buffer(data, res)[:]


@utils.register_interface(X25519PrivateKey)
class _X25519PrivateKey(object):
    def __init__(self, backend, evp_pkey):
        self._backend = backend
        self._evp_pkey = evp_pkey

    def public_key(self):
        bio = self._backend._create_mem_bio_gc()
        res = self._backend._lib.i2d_PUBKEY_bio(bio, self._evp_pkey)
        self._backend.openssl_assert(res == 1)
        evp_pkey = self._backend._lib.d2i_PUBKEY_bio(
            bio, self._backend._ffi.NULL
        )
        self._backend.openssl_assert(evp_pkey != self._backend._ffi.NULL)
        evp_pkey = self._backend._ffi.gc(
            evp_pkey, self._backend._lib.EVP_PKEY_free
        )
        return _X25519PublicKey(self._backend, evp_pkey)

    def exchange(self, peer_public_key):
        if not isinstance(peer_public_key, X25519PublicKey):
            raise TypeError("peer_public_key must be X25519PublicKey.")

        return _evp_pkey_derive(
            self._backend, self._evp_pkey, peer_public_key
        )
