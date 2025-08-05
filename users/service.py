from django.core.cache import cache

def is_phone_number_validated(phone_number : str) -> bool:
    if cache.get(f"verified:{phone_number}"):
        return True
    return False

