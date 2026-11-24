# Candidate garden–plant matrix V1

50 synthetic garden scenarios × 40 candidate taxa = 2,000 candidate pairs.
A pair is not a recommendation. All labels remain null and PENDING until
horticultural evidence is reviewed. No API calls or database writes.

From gdai-plant:
```sh
python -m unittest discover -s tests -p 'test_build_candidate_pairs.py'
python -m matching.build_candidate_pairs
```

Outputs under data/matching: JSON, CSV and quality report. Preserve source
datasets unchanged. CSV empty label fields represent unknown, never zero.
Next: document plant traits with provenance, resolve contradictions and
evaluate climate, exposure, drainage, water and mature dimensions before
preferences. Keep unknown cases out of training. Rule-derived labels are
not expert ground truth. Evaluate with garden-group splits and independent
reviewed labels where available.
