# Revue du lot A de 20 scénarios — 23 novembre 2026

Source : `pilot-20-new-v1.2.json`, comparé à `pilot-10-reviewed-v1.3.json`.
Revue de plausibilité et diversité, non expertise horticole ni vérité terrain.

- 20/20 ACCEPTED par le validateur local, 0 REVIEW_REQUIRED, 0 REJECTED.
- 9 scénarios du pilote précédent ; total brut 29, **pas 29 profils indépendants démontrés**.
- `FR-TEM-001` est très proche de `FR-PAR-01` : Île-de-France, plein soleil, LOAM, eau moyenne, hauteur 200 cm, largeur 150 cm, climat de transition. Différences : température minimale -7 vs -8 et humidité DRY_SUMMER vs WELL_DRAINED ; **à remplacer ou différencier significativement**.
- `FR-TEM-015` et `FR-IDF-09` sont deux noues argileuses humides en Île-de-France, mais diffèrent par exposition, dimensions et température : **variante défendable**, à conserver avec justification.
- `FR-TEM-019` décrit une dépression naturelle humide de vallée de la Somme, alors que `planting_context=RAIN_GARDEN` peut suggérer une noue aménagée : **à préciser** ; la texture et le drainage restent des hypothèses synthétiques.
- `FR-TEM-003` associe un sol drainant modérément et une humidité constamment élevée en Normandie ; possible mais nécessite de préciser l'apport d'eau ou la situation du terrain.
- Les 16 autres ne présentent pas de contradiction évidente à la lecture, mais cela ne remplace pas une validation indépendante.

## Suite recommandée

1. Garder le fichier Gemini brut inchangé.
2. Enregistrer les décisions de revue séparément, puis créer un dataset consolidé avec contrôle des doublons **inter-lots**.
3. Préparer le dernier lot en ciblant les profils absents, plutôt que 21 profils aléatoires.
4. Ne lancer aucun appel API supplémentaire sans action explicite de l'utilisateur.
