const express = require('express');
const { asyncHandler } = require('../middlewares/asyncHandler');

function createRouter({ controllers, requireAdmin }) {
    const router = express.Router();

    router.post('/api/checkout', asyncHandler(async (req, res) => {
        // As chaves abreviadas do payload fazem parte do contrato público da API.
        const { usr, eml, pwd, c_id: courseId, card } = req.body || {};
        const enrollmentId = await controllers.checkout.checkout({ name: usr, email: eml, password: pwd, courseId, card });
        res.status(200).json({ msg: 'Sucesso', enrollment_id: enrollmentId });
    }));

    router.get('/api/admin/financial-report', requireAdmin, asyncHandler(async (req, res) => {
        res.json(await controllers.report.financialReport());
    }));

    router.delete('/api/users/:id', requireAdmin, asyncHandler(async (req, res) => {
        await controllers.user.deleteUser(req.params.id);
        res.send('Usuário deletado');
    }));

    return router;
}

module.exports = { createRouter };
