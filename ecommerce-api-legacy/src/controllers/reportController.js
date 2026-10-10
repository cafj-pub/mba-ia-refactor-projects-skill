const { PAYMENT_STATUS } = require('../services/paymentGateway');

const UNKNOWN_STUDENT = 'Unknown';

function createReportController({ models }) {
    return {
        /** Receita e alunos por curso. */
        async financialReport() {
            const rows = await models.course.listEnrollmentPayments();
            const report = new Map();

            for (const row of rows) {
                if (!report.has(row.course_id)) {
                    report.set(row.course_id, { course: row.course_title, revenue: 0, students: [] });
                }
                if (row.enrollment_id === null) continue;

                const courseData = report.get(row.course_id);
                if (row.payment_status === PAYMENT_STATUS.PAID) courseData.revenue += row.payment_amount;
                courseData.students.push({
                    student: row.student_name ?? UNKNOWN_STUDENT,
                    paid: row.payment_amount ?? 0,
                });
            }

            return [...report.values()];
        },
    };
}

module.exports = { createReportController };
