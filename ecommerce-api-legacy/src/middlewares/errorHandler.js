const { AppError } = require('../utils/errors');

function createErrorHandler(logger) {
    // O Express reconhece error handlers pela aridade 4, por isso `next` é declarado.
    return (err, req, res, next) => {
        if (err instanceof AppError) return res.status(err.statusCode).send(err.message);
        if (err.type === 'entity.parse.failed') return res.status(400).send('Bad Request');

        logger.error(`Erro não tratado em ${req.method} ${req.path}: ${err.stack || err}`);
        return res.status(500).send('Erro interno');
    };
}

module.exports = { createErrorHandler };
