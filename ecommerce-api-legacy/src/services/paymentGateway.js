const PAYMENT_STATUS = Object.freeze({ PAID: 'PAID', DENIED: 'DENIED' });

// Gateway simulado: cartões iniciados por este prefixo são aprovados.
const APPROVED_CARD_PREFIX = '4';

function maskCard(card) {
    return `****${String(card).slice(-4)}`;
}

function createPaymentGateway({ apiKey, logger }) {
    if (!apiKey) logger.warn('PAYMENT_GATEWAY_KEY não configurada: usando gateway simulado');
    return {
        charge({ card, amount }) {
            logger.info(`Processando pagamento de ${amount} no cartão ${maskCard(card)}`);
            return String(card).startsWith(APPROVED_CARD_PREFIX) ? PAYMENT_STATUS.PAID : PAYMENT_STATUS.DENIED;
        },
    };
}

module.exports = { createPaymentGateway, PAYMENT_STATUS };
