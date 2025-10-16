from secrets import choice
from string import digits

from authorization_service.core.config import settings


def generate_numeric_otp(length: int | None = None) -> str:
    """Generate a numeric OTP of configured length."""
    n = length or settings.EMAIL_OTP_LENGTH
    alphabet = digits
    return "".join(choice(alphabet) for _ in range(n))
