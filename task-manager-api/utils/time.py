from datetime import datetime, timezone


def utcnow():
    """Instante atual em UTC como datetime naive — o formato já gravado no banco.

    Substitui `datetime.utcnow()`, deprecated desde o Python 3.12.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
