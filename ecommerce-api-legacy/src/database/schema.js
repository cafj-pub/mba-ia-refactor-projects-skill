const { hashPassword } = require('../services/passwordHasher');
const { PAYMENT_STATUS } = require('../services/paymentGateway');

const SCHEMA = `
    PRAGMA foreign_keys = ON;
    CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT, email TEXT UNIQUE, pass TEXT);
    CREATE TABLE IF NOT EXISTS courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER);
    CREATE TABLE IF NOT EXISTS enrollments (
        id INTEGER PRIMARY KEY,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        course_id INTEGER REFERENCES courses(id)
    );
    CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY,
        enrollment_id INTEGER REFERENCES enrollments(id) ON DELETE CASCADE,
        amount REAL,
        status TEXT
    );
    CREATE TABLE IF NOT EXISTS audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME);
`;

async function createSchema(db) {
    await db.exec(SCHEMA);
}

// Dados de demonstração (apenas desenvolvimento).
async function seed(db) {
    const { count } = await db.get('SELECT COUNT(*) AS count FROM courses');
    if (count > 0) return;

    await db.transaction(async (tx) => {
        await tx.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
            'Leonan', 'leonan@fullcycle.com.br', hashPassword('123'),
        ]);
        await tx.run('INSERT INTO courses (title, price, active) VALUES (?, ?, 1), (?, ?, 1)', [
            'Clean Architecture', 997.0, 'Docker', 497.0,
        ]);
        await tx.run('INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
        await tx.run('INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, ?)', [PAYMENT_STATUS.PAID]);
    });
}

module.exports = { createSchema, seed };
