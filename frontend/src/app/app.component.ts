import { Component, inject, signal } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { LoggerService } from './core/logger.service';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [MatToolbarModule, MatButtonModule, MatCardModule],
    templateUrl: './app.component.html',
    styleUrl: './app.component.scss'
})
export class AppComponent {
    private readonly logger = inject(LoggerService);

    readonly filename = signal('');
    readonly preview = signal('');
    readonly message = signal('Choisissez une photo pour commencer.');

    onFileSelected(event: Event): void {
        const file = (event.target as HTMLInputElement).files?.item(0);

        if (!file) {
            return;
        }

        const allowedTypes = ['image/jpeg', 'image/png', 'image/webp'];

        if (!allowedTypes.includes(file.type) || file.size > 10 * 1024 * 1024) {
            this.message.set('Format invalide ou fichier de plus de 10 Mo.');
            this.logger.warn('Invalid photo');
            return;
        }

        const previous = this.preview();

        if (previous) {
            URL.revokeObjectURL(previous);
        }

        this.preview.set(URL.createObjectURL(file));
        this.filename.set(file.name);
        this.message.set('Photo sélectionnée. Analyse IA bientôt disponible.');
        this.logger.info('Photo selected');
    }
}
