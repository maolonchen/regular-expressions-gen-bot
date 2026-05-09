import os


class ChatModelConfig:
    NAME: str = os.getenv("CHAT_MODEL_NAME", "")
    BASE_URL: str = os.getenv("CHAT_MODEL_API_URL", "")
    API_KEY: str = os.getenv("CHAT_API_KEY", "")
    MAX_TOKENS: int = os.getenv("MAX_TOKENS", 65536)
    TEMPERATURE: int = os.getenv("TEMPERATURE", 0.9)
    MAX_CONCURRENCY: int = os.getenv("MAX_CONCURRENCY", 2)


class Config:

    CHAT_MODEL_CONFIG = ChatModelConfig()

    # Validation settings
    MAX_REGEX_LENGTH: int = int(os.getenv("MAX_REGEX_LENGTH", "1000"))
    MAX_EXECUTION_TIME: float = float(os.getenv("MAX_EXECUTION_TIME", "1.0"))
    MAX_MATCHES: int = int(os.getenv("MAX_MATCHES", "1000"))

    # Iterative refinement settings
    MAX_CORRECTION_ATTEMPTS: int = int(os.getenv("MAX_CORRECTION_ATTEMPTS", "20"))
    CORRECTION_TIMEOUT: float = float(os.getenv("CORRECTION_TIMEOUT", "30.0"))

    # API settings
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8765"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    SAMPLE_INPUT_MAX_LENGTH: int = int(os.getenv("SAMPLE_INPUT_MAX_LENGTH", "10000"))

    @classmethod
    def validate(cls) -> None:
        assert cls.MAX_REGEX_LENGTH > 0, "MAX_REGEX_LENGTH must be positive"
        assert cls.MAX_EXECUTION_TIME > 0, "MAX_EXECUTION_TIME must be positive"
        assert cls.MAX_CORRECTION_ATTEMPTS > 0, "MAX_CORRECTION_ATTEMPTS must be positive"
        assert cls.CORRECTION_TIMEOUT > 0, "CORRECTION_TIMEOUT must be positive"


config = Config()
config.validate()
