"""SmartHQ MFA-aware OAuth login.

GE Appliances added an MFA (one-time code) step to the SmartHQ OAuth login. The
bundled ``gehomesdk`` (2026.5.4) only knows how to *skip* the MFA *enrollment*
nudge; it cannot complete an actual verification-code challenge, so accounts
with MFA enabled fail to authenticate.

This module drives the challenge end to end so the config flow can prompt the
user for the emailed code and obtain OAuth tokens. Crucially, the token response
includes a ``refresh_token`` that lets the integration reconnect unattended
without re-triggering MFA.

Flow (US, email method), reverse-engineered from the live login pages::

    GET  /oauth2/auth                                   -> login form (frmsignin)
    POST /oauth2/g_authenticate                         -> 302 /account/active/security/verify/options
    GET  /account/active/security/verify/options        -> method chooser (verifyOptionForm)
    POST /account/active/security/verify/sendtotp       -> "send code" interstitial
    POST /account/active/security/verify/sendtotp/process?emailType=MFA_VERIFICATION  -> sends email
    POST /account/active/security/verify/totpcode/process  -> 302 <redirect_uri>?code=...
    POST /oauth2/token                                  -> access_token + refresh_token

ponytail: this lives in the integration for now to ship a fix without waiting on
a new gehomesdk release. The permanent home is
``gehomesdk/clients/async_login_flows.py``; keep this in sync when upstreaming.
"""

import logging
from dataclasses import dataclass, field
from http.cookies import SimpleCookie
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

from aiohttp import BasicAuth, ClientSession
from bs4 import BeautifulSoup

from gehomesdk import GeAuthFailedError, GeAuthTermsRequiredError, GeGeneralServerError

try:
    # Reuse the SDK's endpoints/credentials so we stay in lockstep with the
    # pinned gehomesdk version. Fallback keeps us working if internals move.
    from gehomesdk.clients.const import (
        LOGIN_COOKIE_DOMAIN,
        LOGIN_REGION_COOKIE_NAME,
        LOGIN_REGIONS,
        LOGIN_URL,
        OAUTH2_CLIENT_ID,
        OAUTH2_CLIENT_SECRET,
        OAUTH2_REDIRECT_URI,
    )
except Exception:  # pragma: no cover - defensive fallback
    LOGIN_URL = "https://accounts.brillion.geappliances.com"
    LOGIN_REGIONS = {"US": "us-east-1", "EU": "eu-west-1"}
    LOGIN_REGION_COOKIE_NAME = "abgea_region"
    LOGIN_COOKIE_DOMAIN = "accounts.brillion.geappliances.com"
    OAUTH2_CLIENT_ID = "564c31616c4f7474434b307435412b4d2f6e7672"
    OAUTH2_CLIENT_SECRET = "6476512b5246446d452f697154444941387052645938466e5671746e5847593d"
    OAUTH2_REDIRECT_URI = "brillion.4e617a766474657344444e562b5935566e51324a://oauth/redirect"

_LOGGER = logging.getLogger(__name__)

MAX_REDIRECTS = 10

# MFA endpoints (not present in gehomesdk 2026.5.4).
_MFA_OPTIONS = "/account/active/security/verify/options"
_MFA_SENDTOTP = "/account/active/security/verify/sendtotp"
_MFA_SENDTOTP_PROCESS = "/account/active/security/verify/sendtotp/process?emailType=MFA_VERIFICATION"
_MFA_VERIFY = "/account/active/security/verify/totpcode/process"
_MFA_ENROLL_SKIP = "/account/active/redirect"
_TERMS_ACCEPT = "/oauth2/terms/accept"


@dataclass
class LoginResult:
    """Outcome of an authentication attempt."""

    token: Optional[dict] = None
    mfa_required: bool = False
    mfa_methods: List[str] = field(default_factory=list)


def _forms(html: str):
    return BeautifulSoup(html, "html.parser")


def _form_inputs(html: str, form_id: str) -> Dict[str, str]:
    form = _forms(html).find("form", id=form_id)
    if not form:
        return {}
    result: Dict[str, str] = {}
    for i in form.find_all("input"):
        name = i.get("name")
        if name:
            result[name] = i.get("value", "") or ""
    return result


def _csrf(html: str) -> Optional[str]:
    soup = _forms(html)
    tag = soup.find("input", attrs={"name": "_csrf"})
    if tag and tag.get("value"):
        return tag.get("value")
    meta = soup.find("meta", attrs={"name": "_csrf"})
    if meta and meta.get("content"):
        return meta.get("content")
    return None


def _mfa_methods(html: str) -> List[str]:
    """Available MFA methods from the option chooser (buttons like email_btn=email)."""
    methods: List[str] = []
    for btn in _forms(html).find_all("button"):
        name = btn.get("name") or ""
        value = btn.get("value") or ""
        if name.endswith("_btn") and value:
            methods.append(value)
    return methods


def _code_from_location(location: str) -> Optional[str]:
    if not location:
        return None
    return parse_qs(urlparse(location).query).get("code", [None])[0]


def _raise_for_status(status: int, text: str = "") -> None:
    if 400 <= status < 500:
        raise GeAuthFailedError(f"Login failed ({status}) {text[:200]}")
    if status >= 500:
        raise GeGeneralServerError(f"Server error ({status})")


class GeSmartHqLogin:
    """Drives the SmartHQ OAuth login, including the MFA code challenge.

    Instances are single-use per login attempt but survive across config-flow
    steps: the aiohttp session's cookie jar carries the server session, and the
    CSRF token is cached on the instance between ``async_send_code`` and
    ``async_submit_code``.
    """

    def __init__(self, session: ClientSession):
        self._session = session
        self._csrf: Optional[str] = None
        self._mfa_type: str = "email"

    def _set_region_cookie(self, region: str) -> None:
        c = SimpleCookie()
        c[LOGIN_REGION_COOKIE_NAME] = LOGIN_REGIONS[region]
        c[LOGIN_REGION_COOKIE_NAME]["domain"] = LOGIN_COOKIE_DOMAIN
        c[LOGIN_REGION_COOKIE_NAME]["path"] = "/"
        c[LOGIN_REGION_COOKIE_NAME]["secure"] = True
        self._session.cookie_jar.update_cookies(c)

    async def async_login(self, username: str, password: str, region: str) -> LoginResult:
        """Submit credentials. Returns a token, or signals that MFA is required."""
        self._set_region_cookie(region)

        params = {
            "client_id": OAUTH2_CLIENT_ID,
            "response_type": "code",
            "access_type": "offline",
            "redirect_uri": OAUTH2_REDIRECT_URI,
        }
        async with self._session.get(f"{LOGIN_URL}/oauth2/auth", params=params) as resp:
            _raise_for_status(resp.status, await resp.text() if resp.status >= 400 else "")
            login_page = await resp.text()

        post = _form_inputs(login_page, "frmsignin")
        post["username"] = username
        post["password"] = password

        async with self._session.post(
            f"{LOGIN_URL}/oauth2/g_authenticate", data=post, allow_redirects=False
        ) as resp:
            _raise_for_status(resp.status)
            return await self._handle(resp)

    async def _handle(self, resp, depth: int = 0) -> LoginResult:
        if depth > MAX_REDIRECTS:
            raise GeAuthFailedError("Too many redirects during login")

        if resp.status in (301, 302, 303, 307, 308):
            location = resp.headers.get("Location", "")
            code = _code_from_location(location)
            if code:
                return LoginResult(token=await self._exchange_code(code))
            async with self._session.get(urljoin(LOGIN_URL, location), allow_redirects=False) as nxt:
                return await self._handle(nxt, depth + 1)

        if resp.status == 200:
            return await self._handle_html(await resp.text(), depth)

        raise GeAuthFailedError(f"Unexpected response status {resp.status}")

    async def _handle_html(self, html: str, depth: int = 0) -> LoginResult:
        # MFA verification challenge (account has MFA enabled) -> needs user input.
        if "verifyOptionForm" in html or _MFA_OPTIONS in html or "Verify It" in html:
            self._csrf = _csrf(html)
            methods = _mfa_methods(html) or ["email"]
            _LOGGER.info("SmartHQ MFA challenge detected; methods=%s", methods)
            return LoginResult(mfa_required=True, mfa_methods=methods)

        # Updated terms of service -> accept automatically.
        if _TERMS_ACCEPT in html:
            form_data: Dict[str, str] = {}
            soup = _forms(html)
            form = soup.find("form")
            if not form:
                raise GeAuthTermsRequiredError("Terms acceptance required")
            for i in form.find_all("input"):
                if i.get("name"):
                    form_data[i["name"]] = i.get("value", "") or ""
            form_data["developerTerms"] = "on"
            form_data["connected_terms"] = "on"
            async with self._session.post(
                f"{LOGIN_URL}{_TERMS_ACCEPT}", data=form_data, allow_redirects=False
            ) as resp:
                return await self._handle(resp, depth + 1)

        # MFA *enrollment* nudge -> skip (same behavior as gehomesdk).
        if "addMfaForm" in html or "/account/active/security/add/mfamethod" in html:
            soup = _forms(html)
            form = soup.find("form", id="addMfaForm")
            if form:
                form_data = {i["name"]: i.get("value", "") or ""
                             for i in form.find_all("input") if i.get("name")}
                async with self._session.post(
                    f"{LOGIN_URL}{_MFA_ENROLL_SKIP}", data=form_data, allow_redirects=False
                ) as resp:
                    return await self._handle(resp, depth + 1)

        # Application authorization prompt.
        form_data = _form_inputs(html, "frmsignin")
        if "authorized" in form_data:
            form_data["authorized"] = "yes"
            async with self._session.post(
                f"{LOGIN_URL}/oauth2/code", data=form_data, allow_redirects=False
            ) as resp:
                return await self._handle(resp, depth + 1)

        pane = _forms(html).find("div", id="alert_pane")
        if pane:
            raise GeAuthFailedError(f"Authentication failed: {pane.get_text(strip=True)}")
        raise GeAuthFailedError("Authentication failed for unknown reason.")

    async def async_send_code(self, method: str = "email") -> None:
        """Trigger delivery of the one-time code for the chosen method."""
        if not self._csrf:
            raise GeAuthFailedError("Missing session token for MFA")
        self._mfa_type = method
        data = {"mfaType": method, "_csrf": self._csrf}

        # Interstitial "send code" page.
        async with self._session.post(
            urljoin(LOGIN_URL, _MFA_SENDTOTP), data=data, allow_redirects=False
        ) as resp:
            _raise_for_status(resp.status)
            html = await resp.text()
        self._csrf = _csrf(html) or self._csrf

        # Actually send the code (email/SMS).
        data["_csrf"] = self._csrf
        async with self._session.post(
            urljoin(LOGIN_URL, _MFA_SENDTOTP_PROCESS), data=data, allow_redirects=False
        ) as resp:
            _raise_for_status(resp.status)
            html = await resp.text()
        self._csrf = _csrf(html) or self._csrf

    async def async_submit_code(self, code: str) -> dict:
        """Submit the code; returns the OAuth token dict on success."""
        if not self._csrf:
            raise GeAuthFailedError("Missing session token for MFA")
        data = {"mfaType": self._mfa_type, "totpCode": code.strip(), "_csrf": self._csrf}

        async with self._session.post(
            urljoin(LOGIN_URL, _MFA_VERIFY), data=data, allow_redirects=False
        ) as resp:
            if resp.status in (301, 302, 303, 307, 308):
                location = resp.headers.get("Location", "")
                direct = _code_from_location(location)
                if direct:
                    return await self._exchange_code(direct)
                result = await self._handle(resp)
                if result.token:
                    return result.token
                raise GeAuthFailedError("MFA succeeded but no authorization code was returned")
            if resp.status == 200:
                # Wrong/expired code re-renders the entry page; refresh CSRF for retry.
                html = await resp.text()
                self._csrf = _csrf(html) or self._csrf
                raise GeAuthFailedError("Invalid or expired verification code")
            _raise_for_status(resp.status)
            raise GeAuthFailedError(f"Unexpected response status {resp.status}")

    async def _exchange_code(self, code: str) -> dict:
        data = {
            "code": code,
            "client_id": OAUTH2_CLIENT_ID,
            "client_secret": OAUTH2_CLIENT_SECRET,
            "redirect_uri": OAUTH2_REDIRECT_URI,
            "grant_type": "authorization_code",
        }
        auth = BasicAuth(OAUTH2_CLIENT_ID, OAUTH2_CLIENT_SECRET)
        async with self._session.post(f"{LOGIN_URL}/oauth2/token", data=data, auth=auth) as resp:
            _raise_for_status(resp.status)
            token = await resp.json()
        if "access_token" not in token:
            raise GeAuthFailedError(f"Invalid token response: {token}")
        return token
