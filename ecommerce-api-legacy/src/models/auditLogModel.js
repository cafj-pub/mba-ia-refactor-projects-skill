function createAuditLogModel(db) {
    return {
        record(action, conn = db) {
            return conn.run("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [action]);
        },
    };
}

module.exports = { createAuditLogModel };
