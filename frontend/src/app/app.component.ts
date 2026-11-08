import { Component, OnDestroy, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { Subscription, timer } from 'rxjs';
import { GardenApiService } from './core/garden-api.service';
import { GardenQuestion, GardenAnalysisResponse } from './core/garden-context.model';
import { isValidPhoto } from './core/photo-validation';

type Step = 'photo' | 'confirm' | 'validating' | 'questions' | 'results';
type Status = 'info' | 'success' | 'error';

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
    readonly status = signal<Status>('info');
    readonly questions = signal<GardenQuestion[]>([]);
    readonly answers: Record<string, string | number | boolean | null> = {};
    readonly result = signal<GardenAnalysisResponse | null>(null);
    private photo: File | null = null;
    private photoId: string | null = null;
    private workflowSubscription = new Subscription();

    onFileSelected(event: Event): void {
        const input = event.target as HTMLInputElement;
        const file = input.files?.item(0);
        if (!file) return;
        if (!isValidPhoto(file.type, file.size)) {
            this.photo = null;
            this.photoId = null;
            this.releasePreview();
            this.showStatus('Photo invalide : JPEG, PNG ou WebP, 1 Mo maximum.', 'error');
            input.value = '';
            return;
        }
        this.releasePreview();
        this.photo = file;
        this.photoId = null;
        this.preview.set(URL.createObjectURL(file));
        this.filename.set(file.name);
        this.showStatus('Photo sélectionnée. Vérifiez la description puis envoyez.', 'info');
    }

    submitPhoto(): void {
        if (!this.photo || this.busy()) return;
        this.step.set('confirm');
        this.showStatus('Confirmez la photo et sa description avant tout envoi.', 'info');
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
        this.cancelWorkflow();
        this.step.set('photo');
        this.editingDescription.set(false);
        this.showStatus('Vous pouvez remplacer la photo ou modifier sa description.', 'info');
    }

    confirmPhoto(): void {
        if (!this.photo || this.busy() || this.editingDescription()) return;
        if (!isValidPhoto(this.photo.type, this.photo.size)) {
            this.showStatus('Format non pris en charge ou taille supérieure à 1 Mo.', 'error');
            return;
        }
        this.cancelWorkflow();
        this.busy.set(true);
        this.step.set('validating');
        this.showStatus('Enregistrement de la photo et de la description…', 'info');
        this.workflowSubscription.add(this.api.uploadPhoto(this.photo, this.description().trim()).subscribe({
            next: stored => {
                if (stored.status !== 'STORED' || !stored.photoId) {
                    this.rejectPhoto('Enregistrement de la photo non confirmé.');
                    return;
                }
                this.photoId = stored.photoId;
                this.showStatus('Photo enregistrée. Vérification ResNet-18 en cours…', 'info');
                this.validateStoredPhoto(stored.photoId);
            },
            error: () => this.rejectPhoto('Impossible de sauvegarder la photo. Réessayez.')
        }));
    }

    private validateStoredPhoto(photoId: string): void {
        this.workflowSubscription.add(this.api.validatePhoto(photoId).subscribe({
            next: validation => {
                if (validation.status === 'INVALID') {
                    this.rejectPhoto(validation.message || 'Photo non valide pour GDAI-VISION. Choisissez une autre photo.');
                    return;
                }
                if (validation.status === 'PENDING') {
                    this.showStatus('Validation ResNet-18 en cours…', 'info');
                    this.workflowSubscription.add(timer(1000).subscribe(() => this.validateStoredPhoto(photoId)));
                    return;
                }
                if (validation.status !== 'VALID') {
                    this.rejectPhoto('Réponse de validation inattendue.');
                    return;
                }
                this.busy.set(false);
                this.showStatus('Photo valide.', 'success');
                this.workflowSubscription.add(timer(2000).subscribe(() => this.loadQuestions(photoId)));
            },
            error: () => this.rejectPhoto('Service GDAI-VALID indisponible. Réessayez.')
        }));
    }

    private loadQuestions(photoId: string): void {
        this.busy.set(true);
        this.showStatus('Chargement du questionnaire…', 'info');
        this.workflowSubscription.add(this.api.getQuestions(photoId).subscribe({
            next: response => {
                if (!Array.isArray(response.questions) || response.questions.length < 5 ||
                    response.questions.length > 10) {
                    this.busy.set(false);
                    this.showStatus('Questionnaire invalide renvoyé par GDAI-BACK.', 'error');
                    return;
                }
                this.questions.set(response.questions);
                for (const question of response.questions) {
                    this.answers[question.id] = question.type === 'boolean' ? false : '';
                }
                this.busy.set(false);
                this.step.set('questions');
                this.showStatus('Répondez aux questions pour obtenir les plantes adaptées.', 'info');
            },
            error: () => {
                this.busy.set(false);
                this.showStatus('Impossible de charger les questions. Réessayez.', 'error');
            }
        }));
    }

    retryQuestions(): void {
        if (this.photoId && !this.busy()) this.loadQuestions(this.photoId);
    }

    submitContext(): void {
        if (!this.photoId || this.busy()) return;
        this.busy.set(true);
        this.showStatus('Analyse Random Forest en cours…', 'info');
        this.workflowSubscription.add(this.api.analyzeGarden({
            photoId: this.photoId, answers: { ...this.answers }
        }).subscribe({
            next: response => {
                this.result.set(response);
                this.busy.set(false);
                this.step.set('results');
                this.showStatus('Demande transmise à GDAI-BACK.', 'success');
            },
            error: () => {
                this.busy.set(false);
                this.showStatus('Analyse indisponible. Vos réponses sont conservées.', 'error');
            }
        }));
    }

    private rejectPhoto(message: string): void {
        this.busy.set(false);
        this.photoId = null;
        this.step.set('photo');
        this.showStatus(message, 'error');
    }

    private showStatus(message: string, status: Status): void {
        this.message.set(message);
        this.status.set(status);
    }

    private cancelWorkflow(): void {
        this.workflowSubscription.unsubscribe();
        this.workflowSubscription = new Subscription();
        this.busy.set(false);
    }

    ngOnDestroy(): void {
        this.cancelWorkflow();
        this.releasePreview();
    }

    private releasePreview(): void {
        if (this.preview()) URL.revokeObjectURL(this.preview());
        this.preview.set('');
    }
}
