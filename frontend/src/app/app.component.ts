import { Component, inject, signal } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { LoggerService } from './core/logger.service';
import { isValidPhoto } from './core/photo-validation';

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

        if (!isValidPhoto(file.type, file.size)) {
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
