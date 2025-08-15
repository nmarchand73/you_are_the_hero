# Guide de Review des EPUBs

Ce guide explique comment identifier et corriger les sections lors de la review des fichiers markdown générés par `epub_to_md.py`.

## Processus de Review

### 1. Génération du fichier de review
```bash
python scripts/epub_to_md.py "your_book.epub"
```

### 2. Review manuelle du fichier markdown
Le fichier sera généré dans `backend/data/reviews/your_book_review.md`

### 3. Indexation en base
```bash
cd backend
python app.py --index
```

## Comment identifier les sections spéciales

### 🏷️ **Titre du livre / Title page**

**Caractéristiques :**
- Contient le nom du livre
- Mention "livre dont vous êtes le héros" ou "gamebook"
- Parfois les crédits d'auteur/éditeur

**À chercher :**
- `titre`, `title`, `livre dont vous`, `hero`, `aventure`

**Action :** Remplacer par `## Titre du livre`

### 📋 **Règles du jeu / Rules**

**Caractéristiques :**
- Instructions sur comment jouer
- Explication des dés, combats, caractéristiques
- "Ce livre ne se lit pas comme un livre ordinaire"

**À chercher :**
- `règles`, `comment jouer`, `avant de commencer`, `ce livre ne se lit pas`

**Action :** Remplacer par `## Règles du jeu`

### 📖 **Introduction / Prologue**

**Caractéristiques :**
- Contexte de l'histoire
- Description du monde/époque
- Présentation du personnage
- Souvent avec des années (1869, etc.) ou lieux géographiques

**À chercher :**
- `introduction`, `prologue`, `contexte`
- References géographiques : "au nord du Texas", "dans les montagnes"
- Années : "1869", "au XIXe siècle"
- Setup de personnage : "vous êtes", "vous incarnez"

**Action :** Remplacer par `## Introduction`

### 🔢 **Sections numérotées**

**Caractéristiques :**
- Commencent par un numéro (généralement `#1`, `#2`, etc.)
- Contiennent l'histoire principale avec des choix
- Titre descriptif de la scène

**À chercher :**
- Pattern `#(\d+)` au début
- Choix à la fin pointant vers d'autres numéros

**Action :** Remplacer par `## Section X: titre descriptif`

## Exemples de corrections

### ❌ Avant (section mal identifiée)
```markdown
## Section inconnue (OEBPS/part0000.xhtml)
<!-- REVIEW: Please identify this section... -->

Bienvenue au Texas, en 1869. Vous êtes un mercenaire...
```

### ✅ Après (section correctement identifiée)
```markdown
## Introduction

Bienvenue au Texas, en 1869. Vous êtes un mercenaire...
```

### ❌ Avant (section d'introduction mal classée)
```markdown
## Introduction

#01
- Un paquet très spécial
Le saloon est vide, à l'exception d'un type affalé...
```

### ✅ Après (section numérotée correctement identifiée)
```markdown
## Section 1: un paquet très spécial

#01
- Un paquet très spécial  
Le saloon est vide, à l'exception d'un type affalé...
```

## Validation des choix

### Vérifier que les liens fonctionnent
- Chaque choix doit pointer vers une section existante
- Format : `[Texte du choix](#section-X-titre)`
- Tester avec Ctrl+Click pour vérifier la navigation

### Choix manquants
Si des choix ne sont pas détectés automatiquement, les ajouter manuellement :

```markdown
**Choices:**

- [Faire confiance à Jack](#section-2-premier-accrochage)
- [Suivre la proposition de Paul](#section-3-au-milieu-des-champs-de-maïs)
```

## Indicateurs de qualité

### ✅ Fichier prêt pour indexation
- Toutes les sections ont des titres clairs
- Pas de "Section inconnue" ou commentaires `<!-- REVIEW -->`
- Les choix pointent vers des sections valides
- Contenu lisible et complet

### ⚠️ Fichier nécessitant plus de review
- Beaucoup de sections "Introduction" (trop générique)
- Sections "inconnues" non identifiées
- Choix cassés ou manquants
- Contenu corrompu ou illisible

## Conseils pratiques

1. **Utilisez la recherche** : Ctrl+F pour trouver `<!-- REVIEW` et traiter toutes les sections marquées

2. **Vérifiez la logique** : L'ordre des sections doit suivre l'histoire (Titre → Règles → Introduction → Section 1 → ...)

3. **Testez la navigation** : Ctrl+Click sur quelques liens pour valider

4. **Sauvegardez avant indexation** : Le fichier markdown est votre source de vérité

## Workflow complet

```bash
# 1. Générer le review
python scripts/epub_to_md.py "book.epub"

# 2. Ouvrir dans un éditeur de texte
# Éditer backend/data/reviews/book_review.md
# Corriger les identifications et choix

# 3. Indexer en base  
cd backend
python app.py --index

# 4. Tester le jeu
python app.py
# Ouvrir http://localhost:5000
```