from django.core.validators import RegexValidator

class PhoneNumberValidator(RegexValidator):
    regex = r"^09\d{9}$"
    code = "phone invalid"
    message = "phone invalid"

validate_phone_number = PhoneNumberValidator()
