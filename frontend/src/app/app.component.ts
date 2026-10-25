import { Component, inject, signal } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize, switchMap } from 'rxjs';
import { LoggerService } from './core/logger.service';
import {
    GardenApiService, Exposure, SoilType, RequirementLevel, PlantSuggestion
} from './core/garden-api.service';
import { isValidPhoto } from './core/photo-validation';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [
        MatToolbarModule, MatButtonModule, MatCardModule, MatCheckboxModule,
        MatFormFieldModule, MatInputModule, MatSelectModule
    ],
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
    readonly waterAvailability = signal<RequirementLevel>('MODERATE');
    readonly maintenancePreference = signal<RequirementLevel>('LOW');
    readonly evergreenPreferred = signal(true);
    readonly privacyScreeningRequired = signal(false);
    readonly desiredHeightCm = signal<number | null>(null);
    readonly suggestions = signal<PlantSuggestion[]>([]);
    readonly loading = signal(false);
    readonly apiMessage = signal('Renseignez votre jardin et ses préférences.');
    readonly filename = signal('');
    readonly preview = signal('');
    readonly message = signal('Choisissez une photo pour commencer.');

    submitGarden(): void {
        if (!this.gardenName().trim() || !this.location().trim() || this.loading()) {
            this.apiMessage.set('Renseignez le nom et la localisation.');
            return;
        }
        const height = this.desiredHeightCm();
        if (height !== null && (!Number.isInteger(height) || height < 20 || height > 3000)) {
            this.apiMessage.set('La hauteur souhaitée doit être comprise entre 20 et 3000 cm.');
            return;
        }
        this.loading.set(true);
        this.suggestions.set([]);
        this.gardenApi.createGarden({
            name: this.gardenName().trim(),
            location: this.location().trim(),
            exposure: this.exposure(),
            soilType: this.soilType()
        }).pipe(
            switchMap(garden => this.gardenApi.savePreferences(garden.id, {
                waterAvailability: this.waterAvailability(),
                maintenancePreference: this.maintenancePreference(),
                evergreenPreferred: this.evergreenPreferred(),
                privacyScreeningRequired: this.privacyScreeningRequired(),
                desiredHeightCm: this.desiredHeightCm()
            }).pipe(switchMap(() => this.gardenApi.getRecommendations(garden.id)))),
            finalize(() => this.loading.set(false))
        ).subscribe({
            next: response => {
                this.suggestions.set(response.plants);
                this.apiMessage.set(
                    'Préférences enregistrées. Suggestions de démonstration : le moteur IA ne les utilise pas encore.'
                );
            },
            error: () => {
                this.apiMessage.set(
                    'Une étape a échoué (création, préférences ou recommandations). Réessayez après vérification du backend.'
                );
            }
        });
    }

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
