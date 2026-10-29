# Garden-photo image acquisition (experimental)

Run from repository root:

```bash
python -m pip install requests pillow
python scripts/download_garden_images.py --per-class 30
```

The downloader uses Wikimedia Commons search and the `imageinfo` metadata endpoint, records source page, author, license and SHA-256, and downloads small **candidate** image subsets locally. Source search results are **not reliable ground-truth labels**; manually review and relabel all images before training. Images are excluded from Git by `.gitignore`.

**License caution:** the script filters on a limited set of permissive license strings, but automated Commons metadata can be incomplete, multiple licenses and other restrictions can exist, and attribution may be required. Review the original source page before using or redistributing each image, especially commercially.

**Data leakage:** a random image-level split does not prevent near-duplicate photos of the same garden from appearing in both training and test. Review and group by garden/photographer. Synthetic blurry/dark images are derived from validation images only; prepare an independent unusable test set.

**Limitations:** This script requires internet access on the developer machine and is not run by CI. It does not guarantee 30 images per class or a balanced dataset. It does not train ResNet-18. The training notebook requires all three classes, so collect and validate the data before running it.

Official API reference: https://commons.wikimedia.org/wiki/Commons:Machine-readable_data
