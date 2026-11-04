# Garden-photo classifier — scoped POC

This branch adds three reproducible notebooks for a **pretrained ResNet-18 transfer-learning experiment**. It does not claim a trained or deployed model.

## Run order

1. Collect legally reusable images in `datasets/images/garden_validation/{garden,not_garden,unusable}` and record source URL, author, license, collection date, labeler and garden/photographer group. **Do not commit photos or model weights.**
2. Run `notebooks/04_explore_garden_images.ipynb`.
3. Run `notebooks/05_train_garden_classifier.ipynb` (PyTorch, torchvision, Pillow, numpy, pandas, scikit-learn, matplotlib).
4. Create a genuinely independent `datasets/images/garden_test/{garden,not_garden,unusable}` dataset, then run `notebooks/06_evaluate_garden_classifier.ipynb`.

**Warning:** the training notebook currently uses a stratified image-level split; images from the same garden/photographer must be grouped before using metrics for jury claims. The evaluation notebook requires a separately held-out test directory.

## Dataset suitability

Perenual, Trefle and GBIF are useful for botanical metadata/taxonomy, **not automatically labeled garden-scene classification datasets**. Image licensing, source provenance and commercial reuse permissions must be checked individually. Plant presence cannot reliably identify soil type.

## Model storage and deployment

Keep model weights in `models/weights/` (Git-ignored); download/version them via a manifest with SHA-256 before starting a Docker service. The planned FastAPI inference endpoint is **not implemented in this PR**. For the Alyra RNCP38616 block 5, document preprocessing, model choice, head training, cross-entropy, held-out evaluation and deployment evidence separately.
