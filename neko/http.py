"""
Performs HTTP requests asynchronously, validates HTTP responses.
"""
import atexit
import enum
import urllib.parse as urlparse

import aiohttp

from neko import log, strings

__all__ = ['StatusCode', 'is_success', 'HttpRequestError', 'request',
           'validate_uri']

_socket: aiohttp.ClientSession = None
_logger = log.Loggable.get_logger('neko.utils.http')


class HttpRequestError(RuntimeError):
    """Raised if something goes wrong."""
    def __init__(self, status, response):
        self.status = StatusCode(status)
        self.response = response

    def __str__(self):
        return str(self.status)


async def request(method, url, dont_validate=False, **kwargs):
    """
    Performs an HTTP request asynchronously. Check aiohttp.request
    for a list of all flags. This caches the connection in a pool.

    This opens the connection pool the first time that it is used.

    If a bad result is obtained, then an HttpRequestError is raised.

    :param method: the HTTP method to use (e.g. GET, POST, PUT)
    :param url: the URL to access.
    :param dont_validate: defaults to False. Set this to true to
            skip validation and just return the request.
    """
    global _socket
    if not _socket:
        _logger.info('Generating aiohttp ClientSession')
        _socket = aiohttp.ClientSession()
        atexit.register(lambda: _socket.close())
        _logger.info('Registered shutdown closure hook.')

    desc = f'{method.upper()} {url}'

    response = await _socket.request(method, url, **kwargs)
    _logger.info(
        ' '.join([
            desc,
            ' '.join(str(p) for p in kwargs.items()),
            str(StatusCode(response.status))
        ])
    )

    if not dont_validate and not is_success(response.status):
        raise HttpRequestError(response.status, response)
    else:
        return response


class StatusCode(enum.IntEnum):
    none = 0,
    # RFC 1XX

    # N.B. this is known as "continue", however this is a reserve-word
    # in Python, so I can't use it.
    continue_request = 100,
    switching_protocols = 101,
    processing = 102,
    early_hints = 103,

    # RFC 2XX
    ok = 200,
    created = 201,
    accepted = 202,
    non_authoritative_information = 203,
    no_content = 204,
    reset_content = 205,
    partial_content = 206,
    multi_status = 207,
    already_reported = 208,
    im_used = 226,

    # RFC 3XX
    multiple_choices = 300,
    moved_permanently = 301,
    found = 302,
    see_other = 303,
    not_modified = 304,
    use_proxy = 305,
    switch_proxy = 306,
    temporary_redirect = 307,
    permanent_redirect = 308,

    # RFC 4XX
    bad_request = 400,
    unauthorized = 401,
    payment_required = 402,
    forbidden = 403,
    not_found = 404,
    method_not_allowed = 405,
    not_acceptable = 406,
    proxy_authentication_required = 407,
    request_timeout = 408,
    conflict = 409,
    gone = 410,
    length_required = 411,
    precondition_failed = 412,
    payload_too_large = 413,
    uri_too_long = 414,
    unsupported_media_type = 415,
    range_not_satisfiable = 416,
    expectation_failed = 417,
    i_am_a_teapot = 418,
    misdirected_request = 421,
    unprocessable_entity = 422,
    locked = 423,
    failed_dependency = 424,
    upgrade_required = 426,
    precondition_required = 428,
    too_many_requests = 429,
    request_header_fields_too_large = 431,
    unavailable_for_legal_reasons = 451,

    # RFC 5XX
    internal_server_error = 500,
    not_implemented = 501,
    bad_gateway = 502,
    service_unavailable = 503,
    gateway_timeout = 504,
    http_version_not_supported = 505,
    variant_also_negotiates = 506,
    insufficient_storage = 507,
    loop_detected = 508,
    not_extended = 510,
    network_authentication_required = 511

    # UNOFFICIAL CODES
    checkpoint = 103,
    method_failure = 420,
    enhance_your_calm = 420,
    blocked_by_windows_parental_controls = 450,
    invalid_token = 498,
    token_required = 499,
    bandwidth_exceeded = 509,
    site_is_frozen = 530,
    network_read_timeout_error = 598,

    # UNOFFICIAL IIS
    login_timeout = 440,
    retry_with = 449,
    redirect = 451,

    # UNOFFICIAL NGINX
    no_response = 444,
    ssl_certificate_error = 495,
    ssl_certificate_required = 496,
    http_request_sent_to_https_port = 497,
    client_closed_request = 499,

    # CLOUDFLARE
    unknown_error = 520,
    web_server_is_down = 521,
    connection_timed_out = 522,
    origin_is_unreachable = 523,
    a_timeout_occurred = 524,
    ssl_handshake_failed = 525,
    invalid_ssl_certificate = 526,
    railgun_error = 527

    def __repr__(self):
        if self == self.continue_request:
            return '100_continue'
        else:
            return str(self.value) + '_' + (
                self.name
                if self.name or self == 0
                else 'unknown'
            )

    def __str__(self):
        return strings.underscore_to_space(repr(self))


_success_codes = {
    *range(200, 209),
    226,
    *range(301, 305),
    307,
    308
}


def is_success(code: StatusCode):
    """Determines if the code is successful or not."""
    return code in _success_codes


def validate_uri(uri):
    """Ensures the given URI is valid."""
    try:
        result = urlparse.urlparse(uri)
        assert result.scheme and result.netloc and result.path
    except BaseException:
        return False
    else:
        return True
