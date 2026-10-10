const sqlite3 = require('sqlite3');

/**
 * Abre a conexão SQLite e expõe uma API baseada em Promises.
 * Transações são serializadas: o driver usa uma única conexão, então duas
 * transações concorrentes não podem ficar abertas ao mesmo tempo.
 */
function openDatabase(filename) {
    return new Promise((resolve, reject) => {
        const raw = new sqlite3.Database(filename, (err) => (err ? reject(err) : resolve(wrap(raw))));
    });
}

function wrap(raw) {
    const db = {
        run: (sql, params = []) => new Promise((resolve, reject) => {
            raw.run(sql, params, function onRun(err) {
                if (err) return reject(err);
                resolve({ lastID: this.lastID, changes: this.changes });
            });
        }),
        get: (sql, params = []) => new Promise((resolve, reject) => {
            raw.get(sql, params, (err, row) => (err ? reject(err) : resolve(row)));
        }),
        all: (sql, params = []) => new Promise((resolve, reject) => {
            raw.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows)));
        }),
        exec: (sql) => new Promise((resolve, reject) => {
            raw.exec(sql, (err) => (err ? reject(err) : resolve()));
        }),
        close: () => new Promise((resolve, reject) => {
            raw.close((err) => (err ? reject(err) : resolve()));
        }),
    };

    let queue = Promise.resolve();
    db.transaction = (work) => {
        const result = queue.then(async () => {
            await db.run('BEGIN');
            try {
                const value = await work(db);
                await db.run('COMMIT');
                return value;
            } catch (err) {
                await db.run('ROLLBACK');
                throw err;
            }
        });
        queue = result.catch(() => {});
        return result;
    };

    return db;
}

module.exports = { openDatabase };
