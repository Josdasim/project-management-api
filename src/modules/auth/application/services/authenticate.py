from src.modules.auth.application.interfaces.account_repository import AccountRepository
from src.modules.auth.application.interfaces.token_provider import TokenProvider
from src.modules.auth.domain.entities import Account
from src.modules.auth.domain.enums import AccountStatus
from src.modules.auth.domain.exceptions import InvalidTokenError


class AuthenticateService:
    def __init__(self, account: AccountRepository, token_provider: TokenProvider) -> None:
        self._account = account
        self._token_provider = token_provider

    def authenticate(self, access_token: str) -> Account:
        account_id = self._token_provider.decode_access_token(access_token)
        account = self._account.get_by_id(account_id)

        if account is None or account.status != AccountStatus.ACTIVE:
            raise InvalidTokenError

        return account
