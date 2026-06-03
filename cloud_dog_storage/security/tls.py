"""
**************************************************
License: Apache 2.0
Ownership: Cloud-Dog, Viewdeck Engineering Ltd.
Description: TLS configuration helpers for HTTP and FTPS clients.
Standard: PS-85 (Storage Interfaces)
**************************************************
"""

from __future__ import annotations

import ssl
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from cloud_dog_storage.config.models import TlsConfig


def build_requests_verify(tls: TlsConfig) -> bool | str:
    """Build requests `verify` value from TLS config."""
    if tls.insecure_skip_verify:
        return False
    if tls.ca_bundle_path:
        return tls.ca_bundle_path
    return True


def build_ssl_context(tls: TlsConfig) -> ssl.SSLContext:
    """Build SSL context for FTPS and TLS-enabled clients."""
    context = ssl.create_default_context()
    if tls.insecure_skip_verify:
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        return context
    if tls.ca_bundle_path:
        context.load_verify_locations(cafile=tls.ca_bundle_path)
    return context
