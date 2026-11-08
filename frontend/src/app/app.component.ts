import { Component, OnDestroy, inject, signal } from '@angular/core';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { FormsModule } from '@angular/forms';
import { GardenApiService } from './core/garden-api.service';
import { GardenContext, GardenAnalysisResponse } from './core/garden-context.model';
import { isValidPhoto } from './core/photo-validation';

type Step = 'photo' | 'confirm' | 'questions' | 'results';

@Component({
    selector: 'app-root',
    standalone: true,
    imports: [MatToolbarModule, MatButtonModule, MatCardModule, FormsModule],
    templateUrl: './app.component.html',
    styleUrl: './app.component.scss'
})
export class AppComponent implements OnDestroy {
    private readonly api = inject(GardenApiService);
    readonly step = signal<Step>('photo');
    readonly preview = signal('');
    readonly filename = signal('');
    readonly busy = signal(false);
    readonly message = signal('Sélectionnez une photo de jardin.');
    readonly result = signal<GardenAnalysisResponse | null>(null);
    readonly context: GardenContext = {
        location: '', exposure: 'FULL_SUN', soilType: 'UNKNOWN',
        watering: 'MODERATE', maintenance: 'LOW', style: 'MIXED',
        maxHeightCm: null, privacyScreen: false
    };
    private photo: File | null = null;
    private photoId: string | null = null;

    onFileSelected(event: Event): void {
        const file = (event.target as HTMLInputElement).files?.item(0);
        if (!file) return;
        if (!isValidPhoto(file.type, file.size)) {
            this.message.set('Photo invalide : JPEG, PNG ou WebP, 10 Mo maximum.');
            return;
        }
        this.releasePreview();
        this.photo = file;
        this.photoId = null;
        this.preview.set(URL.createObjectURL(file));
        this.filename.set(file.name);
        this.message.set('Vérifiez que cette photo représente bien le jardin à aménager.');
        this.step.set('confirm');
    }

    replacePhoto(): void {
        this.photo = null;
        this.photoId = null;
        this.releasePreview();
        this.step.set('photo');
    }

    confirmPhoto(): void {
        if (!this.photo || this.busy()) return;
        this.busy.set(true);
        this.message.set('Validation technique de la photo en cours…');
        this.api.uploadPhoto(this.photo).subscribe({
            next: response => {
                this.busy.set(false);
                if (response.status !== 'VALID' || !response.photoId) {
                    this.message.set(response.message || 'Photo non conforme. Veuillez en choisir une autre.');
                    return;
                }
                this.photoId = response.photoId;
                this.message.set('Photo validée. Complétez les informations sur votre jardin.');
                this.step.set('questions');
            },
            error: () => {
                this.busy.set(false);
                this.message.set('Service de validation indisponible. Réessayez.');
            }
        });
    }

    submitContext(): void {
        if (!this.photoId || !this.context.location.trim() || this.busy()) return;
        this.busy.set(true);
        this.message.set('Analyse de votre jardin en cours…');
        this.api.analyzeGarden({
            photoId: this.photoId,
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
                this.message.set('Analyse indisponible. Vos réponses sont conservées, réessayez.');
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
