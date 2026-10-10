from src.utils.errors import ValidationError


def require_dict(data, message="Dados inválidos"):
    if not isinstance(data, dict) or not data:
        raise ValidationError(message)
    return data


def require_fields(data, fields_with_messages):
    for field, message in fields_with_messages:
        if field not in data:
            raise ValidationError(message)


def to_number(value, message):
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValidationError(message)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            raise ValidationError(message)
    return value


def to_positive_int(value, message):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(message)
    return value


def optional_float(value, message):
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValidationError(message)
