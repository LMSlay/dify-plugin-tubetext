from typing import Any

from dify_plugin import ToolProvider
from dify_plugin.errors.tool import ToolProviderCredentialValidationError

from tubetext_client import TubeTextError, validate_token


class TubetextProvider(ToolProvider):
    def _validate_credentials(self, credentials: dict[str, Any]) -> None:
        try:
            validate_token(credentials.get("apify_api_token", ""))
        except TubeTextError as e:
            raise ToolProviderCredentialValidationError(str(e)) from None
