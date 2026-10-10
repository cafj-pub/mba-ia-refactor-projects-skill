function createUserModel(db) {
    return {
        findById(id, conn = db) {
            return conn.get('SELECT id, name, email FROM users WHERE id = ?', [id]);
        },

        findByEmail(email, conn = db) {
            return conn.get('SELECT id, name, email FROM users WHERE email = ?', [email]);
        },

        async create({ name, email, passwordHash }, conn = db) {
            const { lastID } = await conn.run('INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
                name, email, passwordHash,
            ]);
            return lastID;
        },

        // Matrículas e pagamentos são removidos via ON DELETE CASCADE.
        async deleteById(id, conn = db) {
            const { changes } = await conn.run('DELETE FROM users WHERE id = ?', [id]);
            return changes > 0;
        },
    };
}

module.exports = { createUserModel };
