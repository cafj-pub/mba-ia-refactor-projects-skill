const config = Object.freeze({
    port: Number(process.env.PORT) || 3000,
    databaseFile: process.env.DATABASE_FILE || ':memory:',
    // Segredos não têm default: devem vir do ambiente.
    paymentGatewayKey: process.env.PAYMENT_GATEWAY_KEY || '',
    adminToken: process.env.ADMIN_TOKEN || '',
    logLevel: process.env.LOG_LEVEL || 'info',
});

module.exports = config;
