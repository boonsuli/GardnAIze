import { Component, inject, signal } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { finalize, forkJoin, switchMap } from 'rxjs';
import { LoggerService } from './core/logger.service';
import {
    GardenApiService, Exposure, SoilType, RequirementLevel, PlantSuggestion, QuestionnaireCatalog
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
    readonly location = signal('');
    readonly countryCode = signal('FR');
    readonly climate = signal('UNKNOWN');
    readonly gardenDescription = signal('');
    readonly photoConfirmed = signal(false);
    readonly photoReady = signal(false);
    readonly validationLoading = signal(false);
    readonly photoValidated = signal(false);
    readonly questionnaire = signal<QuestionnaireCatalog | null>(null);
    readonly dictionary = signal<Record<string, unknown>>({});
    readonly language = signal<'FR' | 'EN'>('FR');
    readonly answers = signal<Record<string, string>>({});
    readonly consentVisible = signal(false);
    readonly consentAccepted = signal(false);
    readonly workflowLoading = signal(false);
    private selectedPhoto: File | null = null;
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

    readonly countries = [
        { code: 'FR', label: 'France' },
        { code: 'BE', label: 'Belgique' },
        { code: 'CH', label: 'Suisse' },
        { code: 'ES', label: 'Espagne' },
        { code: 'IT', label: 'Italie' },
        { code: 'OTHER', label: 'Autre pays' }
    ];

    translate(key: string): string {
        const value = key.split('.').reduce<unknown>((node, part) => {
            if (node !== null && typeof node === 'object' && !Array.isArray(node)) {
                return (node as Record<string, unknown>)[part];
            }
            return undefined;
        }, this.dictionary());
        return typeof value === 'string' ? value : key;
    }

    setAnswer(key: string, value: string): void {
        this.answers.update(current => ({ ...current, [key]: value }));
        this.consentVisible.set(false);
    }

    allRequiredAnswered(): boolean {
        const catalog = this.questionnaire();
        return !!catalog && catalog.questions.every(q => !q.required || !!this.answers()[q.key]);
    }

    showConsent(): void {
        if (this.photoValidated() && this.allRequiredAnswered()) {
            this.consentVisible.set(true);
        }
    }

    refuseConsent(): void {
        this.resetPhotoWorkflow();
        this.message.set('Analyse externe refusée. Aucun envoi à Gemini Vision.');
    }

    acceptConsentAndSubmit(): void {
        const file = this.selectedPhoto;
        const catalog = this.questionnaire();
        if (!file || !catalog || !this.consentVisible() || !this.allRequiredAnswered()
                || this.workflowLoading()) {
            return;
        }
        this.consentAccepted.set(true);
        this.workflowLoading.set(true);
        this.message.set('Consentement confirmé. Demande transmise à GDAI-BACK…');
        this.gardenApi.createGarden({
            name: this.gardenName().trim() || 'Mon jardin',
            location: this.location().trim(),
            countryCode: this.countryCode(),
            climateRegion: this.climate(),
            exposure: (this.answers()['exposure'] || 'FULL_SUN') as Exposure,
            soilType: (this.answers()['soilType'] || 'UNKNOWN') as SoilType
        }).pipe(
            switchMap(garden => this.gardenApi.uploadPhoto(
                garden.id, file, this.gardenDescription().trim(),
                this.answers(), catalog.externalProcessingNoticeKey
            )),
            finalize(() => this.workflowLoading.set(false))
        ).subscribe({
            next: result => {
                this.message.set('GDAI-BACK a répondu. Statut du traitement : ' + result.photoStatus);
                this.consentVisible.set(false);
            },
            error: () => {
                this.message.set('Erreur de transmission ou d’analyse. Réessayez.');
                this.consentAccepted.set(false);
            }
        });
    }

    resetPhotoWorkflow(): void {
        const oldPreview = this.preview();
        if (oldPreview) {
            URL.revokeObjectURL(oldPreview);
        }
        this.selectedPhoto = null;
        this.preview.set('');
        this.filename.set('');
        this.photoReady.set(false);
        this.photoConfirmed.set(false);
        this.photoValidated.set(false);
        this.questionnaire.set(null);
        this.answers.set({});
        this.consentVisible.set(false);
        this.consentAccepted.set(false);
        this.gardenDescription.set('');
        this.location.set('');
        this.climate.set('UNKNOWN');
    }

    canConfirmPhoto(): boolean {
        return this.photoReady() && this.location().trim().length > 0 &&
            this.countryCode().length > 0 && this.gardenDescription().length <= 1000;
    }

    confirmPhotoDetails(): void {
        if (!this.canConfirmPhoto()) {
            this.message.set('Ajoutez une photo, un pays et une ville ou un code postal.');
            return;
        }
        const file = this.selectedPhoto;
        if (!file || this.validationLoading()) {
            return;
        }
        this.photoConfirmed.set(true);
        this.validationLoading.set(true);
        this.message.set('Validation GDAI-VALID en cours…');
        this.gardenApi.validatePhoto(file).pipe(
            switchMap(result => {
                if (!result.valid) {
                    throw new Error(result.reason || 'Photo non conforme');
                }
                return forkJoin({
                    catalog: this.gardenApi.getQuestionnaire(),
                    dictionary: this.gardenApi.loadDictionary(this.language())
                });
            }),
            finalize(() => this.validationLoading.set(false))
        ).subscribe({
            next: ({ catalog, dictionary }) => {
                this.photoValidated.set(true);
                this.questionnaire.set(catalog);
                this.dictionary.set(dictionary);
                this.message.set('Photo acceptée par GDAI-BACK. Répondez au questionnaire.');
            },
            error: error => {
                this.photoConfirmed.set(false);
                this.photoValidated.set(false);
                this.message.set(error instanceof Error ? error.message : 'Validation impossible');
            }
        });
    }

    editPhotoDetails(): void {
        this.photoConfirmed.set(false);
        this.photoValidated.set(false);
        this.questionnaire.set(null);
        this.answers.set({});
        this.consentVisible.set(false);
    }

    submitGarden(): void {
        if (!this.gardenName().trim() || !this.location().trim() || !this.countryCode() || this.loading()) {
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
            countryCode: this.countryCode(),
            climateRegion: this.climate(),
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
        const input = event.target as HTMLInputElement;
        const file = input.files?.item(0);
        if (!file) {
            return;
        }
        if (!isValidPhoto(file.type, file.size)) {
            this.message.set('Format invalide ou fichier de plus de 5 Mio.');
            this.selectedPhoto = null;
            this.photoReady.set(false);
            this.photoConfirmed.set(false);
            input.value = '';
            this.logger.warn('Invalid photo');
            return;
        }
        const previous = this.preview();
        if (previous) {
            URL.revokeObjectURL(previous);
        }
        this.selectedPhoto = file;
        this.preview.set(URL.createObjectURL(file));
        this.photoReady.set(true);
        this.editPhotoDetails();
        this.filename.set(file.name);
        this.message.set('Photo sélectionnée. Complétez la localisation puis confirmez.');
        this.logger.info('Photo selected');
    }
}
