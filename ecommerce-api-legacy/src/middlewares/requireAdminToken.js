const crypto = require('crypto');
const { ForbiddenError } = require('../utils/errors');

function tokensMatch(provided, expected) {
    const a = Buffer.from(String(provided));
    const b = Buffer.from(expected);
    return a.length === b.length && crypto.timingSafeEqual(a, b);
}

/** Exige o header X-Admin-Token. Sem ADMIN_TOKEN configurado, as rotas ficam bloqueadas. */
function requireAdminToken(adminToken) {
    return (req, res, next) => {
        const provided = req.get('X-Admin-Token') || '';
        if (!adminToken || !tokensMatch(provided, adminToken)) return next(new ForbiddenError());
        return next();
    };
}

module.exports = { requireAdminToken };
