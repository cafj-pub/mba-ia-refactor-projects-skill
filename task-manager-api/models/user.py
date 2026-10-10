import hashlib
import hmac
import re

from werkzeug.security import check_password_hash, generate_password_hash

from database import db
from utils.constants import DEFAULT_ROLE, ROLE_ADMIN
from utils.time import utcnow

# Formato gravado pela versão anterior (MD5 hex sem salt), aceito apenas para migração.
_LEGACY_MD5_HASH = re.compile(r'^[0-9a-f]{32}$')


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default=DEFAULT_ROLE)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utcnow)

    def to_dict(self):
        # O hash da senha nunca é serializado.
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'active': self.active,
            'created_at': str(self.created_at),
        }

    def set_password(self, raw_password):
        self.password = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        if _LEGACY_MD5_HASH.match(self.password or ''):
            legacy_hash = hashlib.md5(raw_password.encode()).hexdigest()
            is_valid = hmac.compare_digest(self.password, legacy_hash)
            if is_valid:
                self.set_password(raw_password)  # migra para o hash atual; o chamador faz commit
            return is_valid
        return check_password_hash(self.password, raw_password)

    def is_admin(self):
        return self.role == ROLE_ADMIN
