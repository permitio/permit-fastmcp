import pytest
from unittest.mock import AsyncMock, MagicMock
from permit_fastmcp.middleware.middleware import PermitMcpMiddleware
from permit_fastmcp.middleware.config import SETTINGS
from fastmcp.server.middleware import MiddlewareContext


class DummyRequest:
    def __init__(self, headers=None):
        self.headers = headers or {}


class DummyFastMcpContext:
    def __init__(self, headers=None):
        self.request_context = MagicMock()
        self.request_context.request = DummyRequest(headers=headers)


class DummyContext:
    def __init__(self, method, params=None, headers=None, source=None):
        self.method = method
        self.params = params or {}
        self.fastmcp_context = DummyFastMcpContext(headers=headers)
        self.source = source
        self.message = MagicMock()
        self.message.method = method
        self.message.params = self.params


@pytest.mark.asyncio
async def test_bypass_methods():
    # Should bypass authorization for bypassed methods
    mock_permit = MagicMock()
    middleware = PermitMcpMiddleware(permit_client=mock_permit)
    context = DummyContext(method="ping")
    called = False

    async def call_next(ctx):
        nonlocal called
        called = True
        return "bypassed"

    result = await middleware.on_message(context, call_next)
    assert result == "bypassed"
    assert called


@pytest.mark.asyncio
async def test_authorize_known_method_allowed():
    # Should authorize and allow known method
    mock_permit = AsyncMock()
    mock_permit.check.return_value = True
    middleware = PermitMcpMiddleware(permit_client=mock_permit)
    context = DummyContext(method="tools/list")

    async def call_next(ctx):
        return "allowed"

    result = await middleware.on_message(context, call_next)
    assert result == "allowed"
    mock_permit.check.assert_awaited()


@pytest.mark.asyncio
async def test_authorize_known_method_denied():
    # Should deny if not permitted
    mock_permit = AsyncMock()
    mock_permit.check.return_value = False
    middleware = PermitMcpMiddleware(permit_client=mock_permit)
    context = DummyContext(method="tools/list")

    async def call_next(ctx):
        return "should not get here"

    with pytest.raises(Exception) as exc:
        await middleware.on_message(context, call_next)
    assert "Unauthorized" in str(exc.value)
    mock_permit.check.assert_awaited()


@pytest.mark.asyncio
async def test_identity_extraction_fixed():
    # Should extract fixed identity
    SETTINGS.identity_mode = "fixed"
    middleware = PermitMcpMiddleware(permit_client=AsyncMock())
    context = DummyContext(method="tools/list")
    user_id, attrs = middleware._extract_principal_info(context)
    assert user_id == SETTINGS.identity_fixed_value
    assert attrs["type"] == "fixed_identity"


@pytest.mark.asyncio
async def test_identity_extraction_header():
    # Should extract identity from header
    SETTINGS.identity_mode = "header"
    SETTINGS.identity_header = "X-User"
    middleware = PermitMcpMiddleware(permit_client=AsyncMock())
    context = DummyContext(method="tools/list", headers={"X-User": "alice"})
    user_id, attrs = middleware._extract_principal_info(context)
    assert user_id == "alice"
    assert attrs["header"] == "X-User"


@pytest.mark.asyncio
async def test_identity_extraction_source():
    # Should extract identity from context.source
    SETTINGS.identity_mode = "source"
    middleware = PermitMcpMiddleware(permit_client=AsyncMock())
    context = DummyContext(method="tools/list", source="bob")
    user_id, attrs = middleware._extract_principal_info(context)
    assert user_id == "bob"
    assert attrs["type"] == "source_field"


@pytest.mark.asyncio
async def test_identity_extraction_jwt_valid(monkeypatch):
    import jwt as pyjwt
    import datetime

    SETTINGS.identity_mode = "jwt"
    SETTINGS.identity_header = "Authorization"
    SETTINGS.identity_jwt_secret = "mysecretkey"
    SETTINGS.jwt_algorithms = ["HS256"]
    payload = {
        "sub": "jwtuser",
        "iat": datetime.datetime.now(datetime.timezone.utc),
        "exp": datetime.datetime.now(datetime.timezone.utc)
        + datetime.timedelta(hours=1),
    }
    token = pyjwt.encode(payload, SETTINGS.identity_jwt_secret, algorithm="HS256")
    headers = {"Authorization": f"Bearer {token}"}
    middleware = PermitMcpMiddleware(permit_client=AsyncMock())
    context = DummyContext(method="tools/list", headers=headers)
    user_id, attrs = middleware._extract_principal_info(context)
    assert user_id == "jwtuser"
    assert "jwt" in attrs


@pytest.mark.asyncio
async def test_identity_extraction_jwt_missing_header():
    SETTINGS.identity_mode = "jwt"
    SETTINGS.identity_header = "Authorization"
    SETTINGS.identity_jwt_secret = "mysecretkey"
    SETTINGS.jwt_algorithms = ["HS256"]
    middleware = PermitMcpMiddleware(permit_client=AsyncMock())
    context = DummyContext(method="tools/list", headers={})
    user_id, attrs = middleware._extract_principal_info(context)
    assert user_id == "unknown"
    assert attrs["type"] == "missing_jwt_header"


@pytest.mark.asyncio
async def test_identity_extraction_jwt_invalid_token():
    SETTINGS.identity_mode = "jwt"
    SETTINGS.identity_header = "Authorization"
    SETTINGS.identity_jwt_secret = "mysecretkey"
    SETTINGS.jwt_algorithms = ["HS256"]
    headers = {"Authorization": "Bearer invalidtoken"}
    middleware = PermitMcpMiddleware(permit_client=AsyncMock())
    context = DummyContext(method="tools/list", headers=headers)
    user_id, attrs = middleware._extract_principal_info(context)
    assert user_id == "unknown"
    assert attrs["type"] == "jwt_error"


@pytest.mark.asyncio
async def test_bypass_methods_custom():
    # Test custom bypass methods
    mock_permit = MagicMock()
    middleware = PermitMcpMiddleware(
        permit_client=mock_permit, bypass_methods=["custom/method"]
    )
    context = DummyContext(method="custom/method")
    called = False

    async def call_next(ctx):
        nonlocal called
        called = True
        return "bypassed"

    result = await middleware.on_message(context, call_next)
    assert result == "bypassed"
    assert called


@pytest.mark.asyncio
async def test_audit_logging_enabled_and_disabled():
    # Should log when enabled, not when disabled
    mock_permit = AsyncMock()
    mock_permit.check.return_value = True
    # Enabled
    middleware = PermitMcpMiddleware(
        permit_client=mock_permit, enable_audit_logging=True
    )
    context = DummyContext(method="tools/list")

    async def call_next(ctx):
        return "allowed"

    result = await middleware.on_message(context, call_next)
    assert result == "allowed"
    # Disabled
    middleware = PermitMcpMiddleware(
        permit_client=mock_permit, enable_audit_logging=False
    )
    result = await middleware.on_message(context, call_next)
    assert result == "allowed"
