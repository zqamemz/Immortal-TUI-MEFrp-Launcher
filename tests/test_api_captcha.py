import unittest
from unittest.mock import Mock, patch

from sml.api.client import MEFrpAPI


class APICaptchaTests(unittest.TestCase):
    def setUp(self):
        config_patcher = patch("sml.api.client.Config")
        self.addCleanup(config_patcher.stop)
        config_patcher.start()
        self.api = MEFrpAPI()

    @patch("sml.api.client.verify_captcha", return_value="implicit-token")
    def test_login_injects_implicit_token(self, verify):
        response = Mock()
        response.text = '{"code": 200, "data": {"token": "access-token"}}'
        response.json.return_value = {"code": 200, "data": {"token": "access-token"}}
        response.headers = {}
        self.api._session.post = Mock(return_value=response)

        token = self.api.login("user", "password")

        self.assertEqual(token, "access-token")
        verify.assert_called_once()
        self.assertEqual(
            self.api._session.post.call_args.kwargs["json"]["captchaToken"],
            "implicit-token",
        )

    @patch("sml.api.client.verify_captcha", return_value="implicit-token")
    def test_sign_in_injects_implicit_token(self, verify):
        self.api._post = Mock(return_value="ok")
        self.assertEqual(self.api.sign_in(), "ok")
        self.api._post.assert_called_once_with(
            "/auth/user/sign", json_data={"captchaToken": "implicit-token"}
        )
        verify.assert_called_once()

    @patch("sml.api.client.verify_captcha", return_value="implicit-token")
    def test_reset_access_key_injects_implicit_token(self, verify):
        self.api._post = Mock(return_value={"token": "new"})
        self.assertEqual(self.api.reset_access_key(), {"token": "new"})
        self.api._post.assert_called_once_with(
            "/auth/user/tokenReset", json_data={"captchaToken": "implicit-token"}
        )
        verify.assert_called_once()


if __name__ == "__main__":
    unittest.main()
