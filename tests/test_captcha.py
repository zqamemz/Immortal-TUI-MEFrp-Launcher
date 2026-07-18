import unittest
from unittest.mock import patch

from sml.utils import captcha


class FakeResponse:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.ok = 200 <= status_code < 300
        self.text = "payload"

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)


class CaptchaAlgorithmTests(unittest.TestCase):
    def test_fnv1a_vectors(self):
        self.assertEqual(captcha._fnv1a(""), 2166136261)
        self.assertEqual(captcha._fnv1a("abc"), 440920331)
        self.assertEqual(captcha._fnv1a("令牌😀"), 140938000)

    def test_prng_vectors(self):
        self.assertEqual(captcha._prng("", 24), "4622a6774f65af21aabfbe41")
        self.assertEqual(captcha._prng("abc", 24), "0bb9adb8ffd8e55f8d1de826")
        self.assertEqual(captcha._prng("令牌😀", 24), "f99815d29f672023170ccfd2")

    def test_pow_vector(self):
        self.assertEqual(captcha._prng("test-token1", 8), "7cceb122")
        self.assertEqual(captcha._prng("test-token1d", 2), "8a")
        self.assertEqual(
            captcha._solve_single_challenge("test-token", 1, 8, 2),
            38,
        )

    def test_verify_protocol_and_progress(self):
        session = FakeSession([
            FakeResponse({"data": {"token": "test-token", "challenge": {"c": 1, "s": 8, "d": 2}}}),
            FakeResponse({"token": "captcha-result"}),
        ])
        progress = []

        token = captcha.verify_captcha(session=session, on_progress=progress.append)

        self.assertEqual(token, "captcha-result")
        self.assertEqual(progress, [10, 30, 70, 100])
        self.assertEqual(
            session.calls[0],
            ("https://captcha.mefrp.com/2bf50e050d/challenge", {"json": {}, "timeout": 30}),
        )
        self.assertEqual(
            session.calls[1][0],
            "https://captcha.mefrp.com/2bf50e050d/redeem",
        )
        self.assertEqual(
            session.calls[1][1]["json"],
            {"token": "test-token", "solutions": [38]},
        )

    def test_rejects_invalid_challenge(self):
        session = FakeSession([
            FakeResponse({"token": "test", "challenge": {"c": 0, "s": 8, "d": 2}}),
        ])
        with self.assertRaises(captcha.CaptchaError):
            captcha.verify_captcha(session=session)


if __name__ == "__main__":
    unittest.main()
