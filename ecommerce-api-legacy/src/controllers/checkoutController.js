const { NotFoundError, PaymentDeniedError, ValidationError } = require('../utils/errors');
const { PAYMENT_STATUS } = require('../services/paymentGateway');
const { hashPassword, generateRandomPassword } = require('../services/passwordHasher');

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CARD_PATTERN = /^\d{12,19}$/;

function validateCheckout({ name, email, password, courseId, card }) {
    if (!name || !email || !courseId || !card) throw new ValidationError();

    const normalizedCourseId = Number(courseId);
    const normalizedCard = String(card);
    if (!EMAIL_PATTERN.test(String(email))) throw new ValidationError();
    if (!Number.isInteger(normalizedCourseId) || normalizedCourseId <= 0) throw new ValidationError();
    if (!CARD_PATTERN.test(normalizedCard)) throw new ValidationError();

    return {
        name: String(name),
        email: String(email),
        password: password ? String(password) : null,
        courseId: normalizedCourseId,
        card: normalizedCard,
    };
}

function createCheckoutController({ db, models, paymentGateway, logger }) {
    async function findOrCreateUser({ name, email, password }, tx) {
        const existing = await models.user.findByEmail(email, tx);
        if (existing) return existing.id;
        // Sem senha informada, gera uma aleatória (o usuário deve redefini-la).
        const passwordHash = hashPassword(password || generateRandomPassword());
        return models.user.create({ name, email, passwordHash }, tx);
    }

    return {
        /** Processa a compra de um curso e retorna o id da matrícula criada. */
        async checkout(input) {
            const checkout = validateCheckout(input);

            const course = await models.course.findActiveById(checkout.courseId);
            if (!course) throw new NotFoundError('Curso não encontrado');

            const status = paymentGateway.charge({ card: checkout.card, amount: course.price });
            if (status !== PAYMENT_STATUS.PAID) throw new PaymentDeniedError();

            const { userId, enrollmentId } = await db.transaction(async (tx) => {
                const userId = await findOrCreateUser(checkout, tx);
                const enrollmentId = await models.enrollment.create({ userId, courseId: course.id }, tx);
                await models.payment.create({ enrollmentId, amount: course.price, status }, tx);
                await models.auditLog.record(`Checkout curso ${course.id} por ${userId}`, tx);
                return { userId, enrollmentId };
            });

            logger.info(`Checkout concluído: curso ${course.id}, usuário ${userId}, matrícula ${enrollmentId}`);
            return enrollmentId;
        },
    };
}

module.exports = { createCheckoutController };
