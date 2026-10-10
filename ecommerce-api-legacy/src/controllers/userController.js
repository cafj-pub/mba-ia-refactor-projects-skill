const { NotFoundError, ValidationError } = require('../utils/errors');

function createUserController({ models, logger }) {
    return {
        /** Remove o usuário e, em cascata, suas matrículas e pagamentos. */
        async deleteUser(rawId) {
            const userId = Number(rawId);
            if (!Number.isInteger(userId) || userId <= 0) throw new ValidationError();

            const deleted = await models.user.deleteById(userId);
            if (!deleted) throw new NotFoundError('Usuário não encontrado');

            logger.info(`Usuário ${userId} deletado com matrículas e pagamentos`);
        },
    };
}

module.exports = { createUserController };
