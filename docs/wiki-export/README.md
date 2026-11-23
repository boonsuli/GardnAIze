# Publication du Wiki GitHub officiel

Le Wiki GitHub est un dépôt Git séparé : `https://github.com/boonsuli/GardnAIze.wiki.git`. Une PR du dépôt principal **ne peut pas publier automatiquement** dans ce dépôt. Ce répertoire prépare la migration pour revue, sans modifier le Wiki existant.

## Après validation de la PR

1. Ouvrir https://github.com/boonsuli/GardnAIze/wiki et vérifier/créer la première page si le Wiki est vide.
2. Depuis le dossier parent de `GardnAIze` :

```bash
git clone https://github.com/boonsuli/GardnAIze.wiki.git
cd GardnAIze.wiki
# Vérifier si Home.md existe déjà avant de le remplacer.
ls -l Home.md 2>/dev/null || true
cp ../GardnAIze/docs/wiki-export/Home.md Home.md
git diff -- Home.md
git add Home.md
git commit -m "docs: publish GardnAIze developer guide to GitHub Wiki"
git push origin HEAD
```

3. Contrôler https://github.com/boonsuli/GardnAIze/wiki et les liens internes.
4. Dans une **PR ultérieure**, supprimer éventuellement `docs/WIKI.md` et `docs/wiki-export/` une fois le Wiki publié et validé.

Les conversations locales `docs/ChatGPT-conversation/`, les secrets et les photos privées ne doivent jamais être publiés dans le Wiki.
