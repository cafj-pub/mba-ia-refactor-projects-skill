const express = require('express');

const { openDatabase } = require('./database/connection');
const { createSchema, seed } = require('./database/schema');
const { createUserModel } = require('./models/userModel');
const { createCourseModel } = require('./models/courseModel');
const { createEnrollmentModel } = require('./models/enrollmentModel');
const { createPaymentModel } = require('./models/paymentModel');
const { createAuditLogModel } = require('./models/auditLogModel');
const { createPaymentGateway } = require('./services/paymentGateway');
const { createCheckoutController } = require('./controllers/checkoutController');
const { createReportController } = require('./controllers/reportController');
const { createUserController } = require('./controllers/userController');
const { createRouter } = require('./routes');
const { requireAdminToken } = require('./middlewares/requireAdminToken');
const { createErrorHandler } = require('./middlewares/errorHandler');
const { createLogger } = require('./utils/logger');

/** Composition root: cria banco, models, services e controllers e monta a aplicação Express. */
async function createApp(config) {
    const logger = createLogger(config.logLevel);
    const db = await openDatabase(config.databaseFile);
    await createSchema(db);
    await seed(db);

    const models = {
        user: createUserModel(db),
        course: createCourseModel(db),
        enrollment: createEnrollmentModel(db),
        payment: createPaymentModel(db),
        auditLog: createAuditLogModel(db),
    };
    const paymentGateway = createPaymentGateway({ apiKey: config.paymentGatewayKey, logger });

    const controllers = {
        checkout: createCheckoutController({ db, models, paymentGateway, logger }),
        report: createReportController({ models }),
        user: createUserController({ models, logger }),
    };

    if (!config.adminToken) logger.warn('ADMIN_TOKEN não configurado: rotas administrativas bloqueadas');

    const app = express();
    app.use(express.json());
    app.use(createRouter({ controllers, requireAdmin: requireAdminToken(config.adminToken) }));
    app.use(createErrorHandler(logger));

    return { app, db, logger };
}

module.exports = { createApp };
