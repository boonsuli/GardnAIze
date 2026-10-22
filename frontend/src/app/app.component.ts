import { Component, inject, signal } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { LoggerService } from './core/logger.service';
import { GardenApiService, Exposure, SoilType, PlantSuggestion } from './core/garden-api.service';
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
    private readonly gardenApi = inject(GardenApiService);

    readonly gardenName = signal('Mon jardin');
    readonly location = signal('Paris');
    readonly exposure = signal<Exposure>('FULL_SUN');
    readonly soilType = signal<SoilType>('UNKNOWN');
    readonly suggestions = signal<PlantSuggestion[]>([]);
    readonly loading = signal(false);
    readonly apiMessage = signal('Créez votre jardin pour recevoir trois suggestions de démonstration.');

    submitGarden(): void {
        if (!this.gardenName().trim() || !this.location().trim() || this.loading()) {
            this.apiMessage.set('Renseignez le nom et la localisation.');
            return;
        }

        this.loading.set(true);
        this.suggestions.set([]);
        this.gardenApi.createGarden({
            name: this.gardenName().trim(),
            location: this.location().trim(),
            exposure: this.exposure(),
            soilType: this.soilType()
        }).subscribe({
            next: (garden) => {
                this.gardenApi.getRecommendations(garden.id).subscribe({
                    next: (response) => {
                        this.suggestions.set(response.plants);
                        this.apiMessage.set('Suggestions indicatives : règles de démonstration, sans modèle IA.');
                        this.loading.set(false);
                    },
                    error: () => {
                        this.apiMessage.set('Jardin créé, mais le service de recommandations est indisponible.');
                        this.loading.set(false);
                    }
                });
            },
            error: () => {
                this.apiMessage.set('Impossible de contacter le backend.');
                this.loading.set(false);
            }
        });
    }


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
