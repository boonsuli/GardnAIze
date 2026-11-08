import { Component, OnDestroy, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { GardenApiService } from './core/garden-api.service';
import { GardenContext, GardenAnalysisResponse } from './core/garden-context.model';
import { isValidPhoto } from './core/photo-validation';

type Step = 'photo' | 'confirm' | 'questions' | 'results';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [MatToolbarModule, MatButtonModule, MatCardModule, MatIconModule, FormsModule],
    templateUrl: './app.component.html',
    styleUrl: './app.component.scss'
})
export class AppComponent implements OnDestroy {
    private readonly api = inject(GardenApiService);
    readonly step = signal<Step>('photo');
    readonly preview = signal('');
    readonly filename = signal('');
    readonly description = signal('');
    readonly editingDescription = signal(false);
    readonly descriptionDraft = signal('');
    readonly busy = signal(false);
    readonly message = signal('Sélectionnez une photo de jardin et décrivez-la.');
    readonly result = signal<GardenAnalysisResponse | null>(null);
    readonly context: GardenContext = {
        location: '', exposure: 'FULL_SUN', soilType: 'UNKNOWN',
        watering: 'MODERATE', maintenance: 'LOW', style: 'MIXED',
        maxHeightCm: null, privacyScreen: false
    };
    private photo: File | null = null;
    private photoId: string | null = null;

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        const file = input.files?.item(0);
        if (!file) return;
        if (!isValidPhoto(file.type, file.size)) {
            this.message.set('Photo invalide : JPEG, PNG ou WebP, 1 Mo maximum.');
            input.value = '';
            return;
        }
        this.releasePreview();
        this.photo = file;
        this.photoId = null;
        this.preview.set(URL.createObjectURL(file));
        this.filename.set(file.name);
        this.message.set('Photo sélectionnée. Ajoutez une description et envoyez.');
    }

    submitPhoto(): void {
        if (!this.photo || this.busy()) return;
        this.busy.set(true);
        this.message.set('Envoi et validation de la photo…');
        this.api.uploadPhoto(this.photo, this.description().trim()).subscribe({
            next: response => {
                this.busy.set(false);
                if (response.status !== 'VALID' || !response.photoId) {
                    this.message.set(response.message || 'Photo non conforme. Veuillez réessayer.');
                    return;
                }
                this.photoId = response.photoId;
                this.editingDescription.set(false);
                this.step.set('confirm');
                this.message.set('Vérifiez la photo et sa description avant de poursuivre.');
            },
            error: () => {
                this.busy.set(false);
                this.message.set('Échec de l’envoi. Réessayez sans perdre vos données.');
            }
        });
    }

    editDescription(): void {
        this.descriptionDraft.set(this.description());
        this.editingDescription.set(true);
    }

    saveDescription(): void {
        this.description.set(this.descriptionDraft().trim());
        this.editingDescription.set(false);
    }

    clearDescription(): void {
        this.descriptionDraft.set('');
        this.description.set('');
        this.editingDescription.set(false);
    }

    cancelConfirmation(): void {
        this.step.set('photo');
        this.editingDescription.set(false);
        this.message.set('Vous pouvez remplacer la photo ou modifier sa description.');
    }

    confirmPhoto(): void {
        if (!this.photoId || this.busy() || this.editingDescription()) return;
        this.step.set('questions');
        this.message.set('Photo confirmée. Complétez le questionnaire.');
    }

    submitContext(): void {
        if (!this.photoId || !this.context.location.trim() || this.busy()) return;
        this.busy.set(true);
        this.message.set('Analyse de votre jardin en cours…');
        this.api.analyzeGarden({
            photoId: this.photoId,
            description: this.description(),
            context: {
                ...this.context,
                location: this.context.location.trim(),
                maxHeightCm: this.context.maxHeightCm === null ||
                    this.context.maxHeightCm === 0 ? null : Number(this.context.maxHeightCm)
            }
        }).subscribe({
            next: response => {
                this.result.set(response);
                this.busy.set(false);
                this.step.set('results');
                this.message.set('Demande transmise à GDAI-BACK.');
            },
            error: () => {
                this.busy.set(false);
                this.message.set('Analyse indisponible. Vos réponses sont conservées.');
            }
        });
    }

    backToConfirmation(): void { this.step.set('confirm'); }
    ngOnDestroy(): void { this.releasePreview(); }

    private releasePreview(): void {
        if (this.preview()) URL.revokeObjectURL(this.preview());
        this.preview.set('');
    }
}
