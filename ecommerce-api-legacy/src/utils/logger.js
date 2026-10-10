const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

function createLogger(level = 'info') {
    const threshold = LEVELS[level] ?? LEVELS.info;
    const log = (name, write) => (message) => {
        if (LEVELS[name] <= threshold) write(`${new Date().toISOString()} ${name.toUpperCase()} ${message}`);
    };
    return {
        error: log('error', console.error),
        warn: log('warn', console.warn),
        info: log('info', console.log),
        debug: log('debug', console.log),
    };
}

module.exports = { createLogger };
