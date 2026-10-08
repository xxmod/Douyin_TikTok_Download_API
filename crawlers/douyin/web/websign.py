"""Douyin's ``x-secsdk-web-signature``, in pure Python.
"""

from __future__ import annotations

import hashlib
import time
from collections.abc import Iterable, Mapping, Sequence
from urllib.parse import quote

#: String #39 of the VM's table. Per project; this one is douyin_web.
SALT = "A96D855A08C0A9707F8BEF0D9A527E4E"

#: Where the SDK looks for the visitor id, in this order, first non-empty wins.
UIFID_COOKIE_NAMES: tuple[str, ...] = (
    "uifid",
    "uifid_temp",
    "uifidtemp",
    "UIFID",
    "UIFID_TEMP",
    "UIFIDTEMP",
)

#: The cookie that IS `verifyFp` and `fp`, verbatim.
VERIFY_FP_COOKIE = "s_v_web_id"

SIGNATURE_PARAM = "x-secsdk-web-signature"
UIFID_PARAM = "uifid"
TIMESTAMP_PARAM = "timestamp"
VERIFY_FP_PARAMS: tuple[str, ...] = ("verifyFp", "fp")

#: Sent alongside the query parameters.
EXPIRE_HEADER = "x-secsdk-web-expire"


def pick_uifid(cookies: Mapping[str, str] | None) -> str | None:
    """The visitor id the signature is bound to, from the identity's own jar."""
    for name in UIFID_COOKIE_NAMES:
        value = (cookies or {}).get(name)
        if value:
            return value
    return None


def encode_pairs(pairs: Iterable[tuple[str, str]]) -> str:
    """Serialize like the JavaScript ``URLSearchParams.toString()`` the SDK uses."""
    return "&".join(f"{quote(k, safe='*-._')}={quote(v, safe='*-._')}" for k, v in pairs)


def sign(
    pairs: Sequence[tuple[str, str]],
    uifid: str,
    *,
    timestamp: int | None = None,
) -> tuple[str, str, dict[str, str]]:
    """Return ``(query, signature, headers)`` for a request."""
    stamp = str(int(time.time() if timestamp is None else timestamp))
    covered = list(pairs)
    if not any(name == UIFID_PARAM for name, _ in covered):
        covered.append((UIFID_PARAM, uifid))
    covered.append((TIMESTAMP_PARAM, stamp))
    query = encode_pairs(covered)
    signature = hashlib.md5(f"{uifid}_{stamp}_{SALT}_{query}".encode()).hexdigest()
    headers = {
        UIFID_PARAM: uifid,
        SIGNATURE_PARAM: signature,
        EXPIRE_HEADER: stamp,
    }
    return f"{query}&{SIGNATURE_PARAM}={signature}", signature, headers


__all__ = [
    "EXPIRE_HEADER",
    "SALT",
    "SIGNATURE_PARAM",
    "UIFID_COOKIE_NAMES",
    "VERIFY_FP_COOKIE",
    "VERIFY_FP_PARAMS",
    "encode_pairs",
    "pick_uifid",
    "sign",
]
