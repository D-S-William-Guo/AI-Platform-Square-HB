from dataclasses import dataclass

from fastapi import HTTPException

from .config import Settings


@dataclass(frozen=True)
class AuthProviderDescriptor:
    mode: str
    display_name: str
    login_url: str
    local_login_enabled: bool
    configured: bool
    message: str


class BaseIdentityProvider:
    mode = "local"
    display_name = "本地账号登录"

    def __init__(self, settings_obj: Settings):
        self.settings = settings_obj

    def describe(self) -> AuthProviderDescriptor:
        raise NotImplementedError

    def ensure_password_login_allowed(self) -> None:
        if self.mode != "local":
            raise HTTPException(
                status_code=409,
                detail=f"当前环境已切换到 {self.display_name}，请通过统一登录入口访问。",
            )

    def exchange_assertion(self, assertion: str) -> None:
        raise HTTPException(
            status_code=501,
            detail=f"{self.display_name} 已预留接入点，但尚未完成断言交换实现。",
        )


class LocalIdentityProvider(BaseIdentityProvider):
    mode = "local"
    display_name = "本地账号登录"

    def describe(self) -> AuthProviderDescriptor:
        return AuthProviderDescriptor(
            mode=self.mode,
            display_name=self.display_name,
            login_url="",
            local_login_enabled=True,
            configured=True,
            message="当前环境启用本地账号登录。",
        )


class OAIdentityProvider(BaseIdentityProvider):
    mode = "oa"
    display_name = "OA 统一登录"

    def describe(self) -> AuthProviderDescriptor:
        login_url = self.settings.oa_sso_login_url.strip()
        return AuthProviderDescriptor(
            mode=self.mode,
            display_name=self.display_name,
            login_url=login_url,
            local_login_enabled=False,
            configured=bool(login_url),
            message=(
                "当前环境启用 OA 统一登录。"
                if login_url
                else "当前环境已切换到 OA 统一登录，但尚未配置 OA 登录入口。"
            ),
        )


class ExternalSSOIdentityProvider(BaseIdentityProvider):
    mode = "external_sso"
    display_name = "第三方统一登录"

    def describe(self) -> AuthProviderDescriptor:
        login_url = self.settings.external_sso_login_url.strip()
        return AuthProviderDescriptor(
            mode=self.mode,
            display_name=self.display_name,
            login_url=login_url,
            local_login_enabled=False,
            configured=bool(login_url),
            message=(
                "当前环境启用第三方统一登录。"
                if login_url
                else "当前环境已切换到第三方统一登录，但尚未配置登录入口。"
            ),
        )


def get_identity_provider(settings_obj: Settings) -> BaseIdentityProvider:
    provider_map = {
        "local": LocalIdentityProvider,
        "oa": OAIdentityProvider,
        "external_sso": ExternalSSOIdentityProvider,
    }
    provider_cls = provider_map.get(settings_obj.auth_provider_mode, LocalIdentityProvider)
    return provider_cls(settings_obj)
