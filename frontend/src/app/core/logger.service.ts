import { Injectable } from '@angular/core';

export type LogLevel = 'DEBUG' | 'INFO' | 'WARN' | 'ERROR' | 'OFF';

const weights: Record<LogLevel, number> = {
    DEBUG: 10,
    INFO: 20,
    WARN: 30,
    ERROR: 40,
    OFF: 100
};

@Injectable({
    providedIn: 'root'
})
export class LoggerService {
    private level: LogLevel = 'INFO';

    setLevel(level: LogLevel): void {
        this.level = level;
    }

    debug(message: string): void {
        if (weights[this.level] <= 10) {
            console.debug(message);
        }
    }

    info(message: string): void {
        if (weights[this.level] <= 20) {
            console.info(message);
        }
    }

    warn(message: string): void {
        if (weights[this.level] <= 30) {
            console.warn(message);
        }
    }

    error(message: string): void {
        if (weights[this.level] <= 40) {
            console.error(message);
        }
    }
}
