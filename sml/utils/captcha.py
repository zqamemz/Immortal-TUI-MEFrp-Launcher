"""ME Frp 隐式人机验证。"""

import hashlib
import math
from typing import Callable, Optional, Tuple

import requests

CAPTCHA_BASE_URL = "https://captcha.mefrp.com"
DEFAULT_SITE_ID = "2bf50e050d"
MAX_NONCE = 50_000_000
REQUEST_TIMEOUT = 30
_MASK32 = 0xFFFFFFFF


class CaptchaError(Exception):
    """隐式验证失败。"""


def _utf16_code_units(value: str):
    encoded = value.encode("utf-16-le", errors="surrogatepass")
    for offset in range(0, len(encoded), 2):
        yield encoded[offset] | (encoded[offset + 1] << 8)


def _fnv1a(value: str) -> int:
    hash_value = 2166136261
    for code_unit in _utf16_code_units(value):
        hash_value ^= code_unit
        hash_value += (
            (hash_value << 1)
            + (hash_value << 4)
            + (hash_value << 7)
            + (hash_value << 8)
            + (hash_value << 24)
        )
        hash_value &= _MASK32
    return hash_value


def _prng(seed: str, length: int) -> str:
    state = _fnv1a(seed)
    result = ""
    while len(result) < length:
        state ^= (state << 13) & _MASK32
        state &= _MASK32
        state ^= state >> 17
        state &= _MASK32
        state ^= (state << 5) & _MASK32
        state &= _MASK32
        result += f"{state:08x}"
    return result[:length]


def _sha256_hex(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _solve_single_challenge(
    token: str,
    index: int,
    salt_length: int,
    difficulty: int,
) -> int:
    salt = _prng(f"{token}{index}", salt_length)
    target = _prng(f"{token}{index}d", difficulty)
    base_hash = hashlib.sha256(salt.encode("utf-8"))
    for nonce in range(MAX_NONCE + 1):
        nonce_hash = base_hash.copy()
        nonce_hash.update(str(nonce).encode("ascii"))
        if nonce_hash.hexdigest().startswith(target):
            return nonce
    raise CaptchaError(
        f"PoW 求解超限 (idx={index}, target={target}, salt={salt[:8]}...)"
    )


def _response_root(response: requests.Response, stage: str) -> dict:
    body = response.text or ""
    if not response.ok:
        raise CaptchaError(
            f"{stage}失败: HTTP {response.status_code} | 响应体: {body[:1000] or '<空>'}"
        )
    try:
        payload = response.json()
    except ValueError:
        raise CaptchaError(f"{stage}接口返回非 JSON | 响应体: {body[:1000] or '<空>'}")
    if not isinstance(payload, dict):
        raise CaptchaError(f"{stage}接口响应结构无效")
    root = payload.get("data") or payload
    if not isinstance(root, dict):
        raise CaptchaError(f"{stage}接口响应结构无效")
    return root


def _positive_int(value, name: str) -> int:
    if isinstance(value, bool):
        raise CaptchaError(f"挑战参数解析失败: {name}={value}")
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise CaptchaError(f"挑战参数解析失败: {name}={value}")
    if number <= 0 or str(value).strip() not in {str(number), f"{number}.0"}:
        raise CaptchaError(f"挑战参数解析失败: {name}={value}")
    return number


def _fetch_challenge(
    session: requests.Session,
    endpoint: str,
) -> Tuple[str, int, int, int]:
    try:
        response = session.post(
            f"{endpoint}challenge", json={}, timeout=REQUEST_TIMEOUT
        )
    except requests.RequestException as exc:
        raise CaptchaError(f"获取挑战失败: {exc}")
    root = _response_root(response, "获取挑战")
    token = root.get("token")
    challenge = root.get("challenge")
    if not isinstance(token, str) or not token or not isinstance(challenge, dict):
        raise CaptchaError("挑战接口缺少 token/challenge")
    return (
        token,
        _positive_int(challenge.get("c"), "c"),
        _positive_int(challenge.get("s"), "s"),
        _positive_int(challenge.get("d"), "d"),
    )


def _redeem_solution(
    session: requests.Session,
    endpoint: str,
    token: str,
    solutions: list,
) -> str:
    try:
        response = session.post(
            f"{endpoint}redeem",
            json={"token": token, "solutions": solutions},
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise CaptchaError(f"提交解答失败: {exc}")
    root = _response_root(response, "提交解答")
    if root.get("success") is False:
        raise CaptchaError(f"服务端拒绝: {root.get('message', 'unknown')}")
    result_token = root.get("token")
    if not result_token:
        raise CaptchaError("服务端未返回 token")
    return str(result_token)


def format_captcha_progress(progress: int, operation: str) -> str:
    if progress < 30:
        return "正在获取验证挑战..."
    if progress < 70:
        return f"正在计算验证解答... {progress}%"
    if progress < 100:
        return "正在提交验证结果..."
    return f"验证完成，正在{operation}..."


def verify_captcha(
    session: Optional[requests.Session] = None,
    site_id: str = DEFAULT_SITE_ID,
    on_progress: Optional[Callable[[int], None]] = None,
) -> str:
    active_session = session or requests.Session()
    endpoint = f"{CAPTCHA_BASE_URL}/{site_id}/"

    if on_progress:
        on_progress(10)
    token, count, salt_length, difficulty = _fetch_challenge(active_session, endpoint)
    if on_progress:
        on_progress(30)

    solutions = []
    last_progress = 30
    for index in range(1, count + 1):
        solutions.append(
            _solve_single_challenge(token, index, salt_length, difficulty)
        )
        progress = 30 + math.floor((index / count) * 40 + 0.5)
        if on_progress and progress != last_progress:
            on_progress(progress)
            last_progress = progress

    if not solutions:
        raise CaptchaError("求解器未产生任何 nonce")
    result_token = _redeem_solution(active_session, endpoint, token, solutions)
    if on_progress:
        on_progress(100)
    return result_token
