function createEnrollmentModel(db) {
    return {
        async create({ userId, courseId }, conn = db) {
            const { lastID } = await conn.run('INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [userId, courseId]);
            return lastID;
        },
    };
}

module.exports = { createEnrollmentModel };
