const crypto = require('crypto');

const KEY_LENGTH = 64;
const SALT_BYTES = 16;

function hashPassword(password) {
    const salt = crypto.randomBytes(SALT_BYTES).toString('hex');
    const hash = crypto.scryptSync(password, salt, KEY_LENGTH).toString('hex');
    return `scrypt$${salt}$${hash}`;
}

function generateRandomPassword() {
    return crypto.randomBytes(12).toString('base64url');
}

module.exports = { hashPassword, generateRandomPassword };
