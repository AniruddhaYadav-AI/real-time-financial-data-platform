from financial_platform.core.config import Settings


def test_default_settings() -> None:
    """Test that settings load default values correctly."""
    settings = Settings()
    assert settings.APP_NAME == "Financial Data Platform"
    assert settings.APP_ENV in ["development", "staging", "production", "test"]
    assert isinstance(settings.DEBUG, bool)
    assert isinstance(settings.PORT, int)
