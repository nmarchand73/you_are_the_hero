# Product Requirements Document (PRD)
## Jeu Interactif "Dont Vous Êtes le Héros" avec Support EPUB

### 1. Vue d'ensemble du produit

#### 1.1 Vision
Créer une application web simple permettant de jouer à des livres-jeux interactifs en important des fichiers EPUB existants et en utilisant la mécanique narrative d'inkjs pour gérer les choix et le déroulement de l'histoire.

#### 1.2 Objectifs principaux
- Permettre l'import et la lecture de fichiers EPUB de type "livre dont vous êtes le héros"
- Offrir une expérience de jeu interactive simple et intuitive
- Utiliser inkjs pour gérer la logique narrative et les choix
- Commencer avec un MVP minimal et évolutif

#### 1.3 Public cible
- Joueurs nostalgiques des livres-jeux classiques
- Nouveaux joueurs découvrant le genre
- Créateurs de contenu interactif cherchant une plateforme simple

---

### 2. Fonctionnalités du MVP (Version 1.0)

#### 2.1 Fonctionnalités essentielles

##### Import de fichiers EPUB
- **Description**: Permettre l'upload d'un fichier .epub depuis l'ordinateur de l'utilisateur
- **Critères d'acceptation**:
  - Accepte uniquement les fichiers .epub
  - Taille maximale: 50MB
  - Validation du format EPUB
  - Message d'erreur clair si le fichier n'est pas compatible

##### Extraction et conversion EPUB → Ink
- **Description**: Parser le contenu EPUB et le convertir en format compatible inkjs
- **Critères d'acceptation**:
  - Extraction du texte des chapitres/sections
  - Identification des liens entre sections (numéros de paragraphes)
  - Conversion en syntaxe ink basique
  - Gestion des erreurs de parsing

##### Interface de lecture simple
- **Description**: Interface minimaliste pour lire et naviguer dans l'histoire
- **Critères d'acceptation**:
  - Zone de texte principale pour afficher le contenu
  - Boutons de choix clairs et accessibles
  - Police lisible et ajustable
  - Mode sombre/clair

##### Système de choix
- **Description**: Présentation et gestion des choix narratifs via inkjs
- **Critères d'acceptation**:
  - Affichage des choix disponibles
  - Navigation vers la section correspondante
  - Historique des choix (retour arrière simple)

##### Sauvegarde de progression
- **Description**: Sauvegarder l'état du jeu localement
- **Critères d'acceptation**:
  - Sauvegarde automatique à chaque choix
  - Possibilité de reprendre une partie
  - Stockage en localStorage
  - Un seul slot de sauvegarde par livre

---

### 3. Architecture technique

#### 3.1 Stack technologique
```
Frontend:
- HTML5/CSS3
- JavaScript (ES6+)
- inkjs (gestion narrative)
- epub.js ou JSZip (parsing EPUB)

Stockage:
- localStorage (sauvegarde)
- IndexedDB (cache des livres convertis)

Hébergement:
- Application web statique
- Pas de backend requis pour le MVP
```

#### 3.2 Architecture des composants

```
┌─────────────────────────────────────┐
│         Interface Utilisateur        │
│  (HTML/CSS - Affichage & Contrôles)  │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│         Gestionnaire de Jeu          │
│    (Coordination des composants)     │
└──────┬───────────────────┬──────────┘
       │                   │
┌──────▼──────┐    ┌───────▼─────────┐
│ Parser EPUB │    │  Moteur inkjs   │
│             │    │ (Logique narrative)│
└─────────────┘    └─────────────────┘
       │                   │
       └─────────┬─────────┘
                 │
        ┌────────▼────────┐
        │   Stockage      │
        │  (localStorage) │
        └─────────────────┘
```

#### 3.3 Flux de données

1. **Import**: Utilisateur → Fichier EPUB → Parser
2. **Conversion**: Parser → Format Ink → Moteur inkjs
3. **Jeu**: inkjs → Interface → Choix utilisateur → inkjs
4. **Sauvegarde**: État inkjs → localStorage

---

### 4. Spécifications détaillées

#### 4.1 Format de conversion EPUB → Ink

##### Exemple de conversion basique:
```ink
// EPUB: Paragraphe 1
=== section_1 ===
Vous êtes dans une forêt sombre. 
Un chemin se divise en deux.

+ [Prendre le chemin de gauche] -> section_15
+ [Prendre le chemin de droite] -> section_22

// EPUB: Paragraphe 15
=== section_15 ===
Le chemin de gauche mène à une clairière...
-> END

// EPUB: Paragraphe 22  
=== section_22 ===
Le chemin de droite descend vers une rivière...
-> END
```

#### 4.2 Structure de données

##### État de jeu:
```javascript
{
  bookId: "unique-book-hash",
  bookTitle: "Le Sorcier de la Montagne de Feu",
  currentSection: "section_1",
  inkState: {}, // État sérialisé d'inkjs
  history: ["section_1", "section_15"],
  timestamp: "2024-01-15T10:30:00Z"
}
```

##### Métadonnées du livre:
```javascript
{
  id: "unique-book-hash",
  title: "Titre du livre",
  author: "Auteur",
  coverImage: "data:image/...",
  sections: 400,
  lastPlayed: "2024-01-15T10:30:00Z"
}
```

---

### 5. Interface utilisateur (UI/UX)

#### 5.1 Écrans principaux

##### Écran d'accueil
- Zone de drop pour importer un EPUB
- Liste des livres déjà importés
- Bouton "Continuer" pour reprendre la dernière partie

##### Écran de jeu
```
┌────────────────────────────────────┐
│     [Titre du livre]    [Menu]     │
├────────────────────────────────────┤
│                                    │
│   Texte de la section actuelle     │
│   ...                              │
│   ...                              │
│                                    │
├────────────────────────────────────┤
│  ┌──────────────────────────────┐  │
│  │ > Choix 1                    │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │ > Choix 2                    │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
```

#### 5.2 Responsive Design
- Mobile-first approach
- Adaptation tablette et desktop
- Gestes tactiles pour mobile (swipe pour retour)

---

### 6. Roadmap de développement

#### Phase 1: MVP (4 semaines)
- [ ] Setup environnement de développement
- [ ] Intégration inkjs
- [ ] Parser EPUB basique
- [ ] Interface de jeu minimale
- [ ] Système de sauvegarde simple

#### Phase 2: Améliorations (4 semaines)
- [ ] Support des images dans les EPUB
- [ ] Multiple slots de sauvegarde
- [ ] Système d'inventaire basique
- [ ] Statistiques de jeu

#### Phase 3: Fonctionnalités avancées (8 semaines)
- [ ] Éditeur ink intégré
- [ ] Partage de livres convertis
- [ ] Mode multijoueur asynchrone
- [ ] Achievements et progression

---

### 7. Critères de succès

#### 7.1 Métriques techniques
- Temps de chargement < 3 secondes
- Conversion EPUB < 10 secondes
- Taux de crash < 0.1%
- Support navigateurs: Chrome, Firefox, Safari, Edge

#### 7.2 Métriques utilisateur
- Taux de rétention J1: > 40%
- Temps moyen de session: > 15 minutes
- Taux de complétion d'un livre: > 20%
- Note satisfaction: > 4/5

#### 7.3 KPIs MVP
- 100 utilisateurs actifs première semaine
- 10 livres EPUB testés avec succès
- 0 bug critique en production

---

### 8. Risques et mitigation

| Risque | Probabilité | Impact | Mitigation |
|--------|------------|--------|------------|
| Formats EPUB incompatibles | Élevée | Moyen | Créer un convertisseur flexible avec fallbacks |
| Performance sur mobile | Moyenne | Élevé | Optimisation aggressive, lazy loading |
| Complexité de conversion ink | Moyenne | Moyen | Commencer simple, itérer |
| Droits d'auteur | Faible | Élevé | Usage personnel uniquement, disclaimer |

---

### 9. Contraintes et limitations

#### 9.1 Limitations techniques
- Pas de support des EPUB avec DRM
- Limite de taille de fichier (50MB)
- Pas de synchronisation cloud dans le MVP
- Support limité des médias (audio/vidéo)

#### 9.2 Contraintes légales
- Usage personnel uniquement
- Pas de redistribution de contenu
- Respect des droits d'auteur

---

### 10. Prochaines étapes

1. **Validation du concept**: Prototype avec un EPUB simple
2. **Setup technique**: Environnement de développement
3. **Proof of Concept**: Conversion EPUB → ink fonctionnelle
4. **Développement itératif**: Sprints de 2 semaines
5. **Tests utilisateurs**: Avec 5-10 beta testeurs
6. **Launch MVP**: Version web publique

---

### Annexes

#### A. Ressources
- [inkjs Documentation](https://github.com/y-lohse/inkjs)
- [EPUB Specification](https://www.w3.org/publishing/epub3/)
- [epub.js Library](https://github.com/futurepress/epub.js/)

#### B. Exemples de livres-jeux EPUB
- Collection "Défis Fantastiques"
- "Sorcellerie!" series
- Livres-jeux du domaine public

#### C. Prototype de code
```javascript
// Exemple d'initialisation
import { Story } from 'inkjs';

class GameEngine {
  constructor() {
    this.story = null;
    this.currentBook = null;
  }
  
  async loadEPUB(file) {
    const epubContent = await this.parseEPUB(file);
    const inkScript = this.convertToInk(epubContent);
    this.story = new Story(inkScript);
  }
  
  continue() {
    if (this.story.canContinue) {
      const text = this.story.Continue();
      return {
        text,
        choices: this.story.currentChoices
      };
    }
  }
  
  makeChoice(index) {
    this.story.ChooseChoiceIndex(index);
    this.saveState();
    return this.continue();
  }
}
```