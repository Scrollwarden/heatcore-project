# HeatCore - Fronzen worlds
Arrivé dans un système solaire en perdition, dans lequel aucune planète n'est viable, l'équipage du 24PP crois sa fin arrivée. Heureusement, des Cœurs de chaleurs sont détectés, qui lui permettraient de repartir.  
Vous, pilote de la navette d'exploration, devrez visiter les nombreux mondes d'Ambera pour récolter l'énergie laissée là par de mystérieux prédécesseurs.  
Qui sait ce que vous découvrirez d'autres ici ?

## 📋 Sommaire
1. **[📥 Installation et dépendances](#-installation-et-dépendances)**
2. **[⏯️ Lancement du jeu](#%EF%B8%8F-lancement-du-jeu)**
3. **[🎮 Règles du jeu](#-règles-du-jeu)**
4. **[🧨 Bugs et problèmes connus](#-bugs-et-problèmes-connus)**
5. **[⚙️ Description technique du projet](#%EF%B8%8F-description-technique-du-projet)**
6. **[👥 Crédits](#-crédits)**

## 📥 Installation et dépendances
### Environnement virtuel (recommandation)
Afin de lancer ce projet dans de bonnes conditions, nous recommandons fortement la création d'un **environnement virtuel**.  
Avant de créer un venv, assurez-vous de vérifier les [dépendances](#dépendances), notamment la version python.  
Il peut être créé avec la commande suivante :
```
python -m venv chemin/nom_du_venv
```
*⚠️ Ce venv doit être créé dans le dossier `heatcore-project`.*

Son activation se fait différement selon le terminal utilisé :
- Pour **bash** et **zsh** : ```source nom_du_venv/bin/activate```
- Pour **cmd** : ```nom_du_venv\Scripts\activate.bat```
- Pour **PowerShell** ```nom_du_venv\Scripts\Activate.ps1```

Sa désactivation se fait avec `deactivate`.

Pour plus de détails, consultez la [page officielle de python](https://docs.python.org/3/library/venv.html).

### Plateformes compatibles
Ce projet a été testé pour Linux Mint, Windows et Mac. Toutefois, certaines plateformes requièrent une attention particulière

#### 🪟 Windows
La bibliothèque noise étant mal conçue pour cette plateforme, il est nécessaire de télécharger le [Build Tools C++](https://visualstudio.microsoft.com/visual-cpp-build-tools/). Elle pèse autour de 7Go.  
Cette bibliothèque est nécessaire pour la génération du monde. Il s'agit de la plus rapide qui ne nécessite pas d'être compilée à la main. Des bibliothèques plus lentes auraient rendu le projet injouable.
Une aide à l'installation peut se trouver sur [ce forum StackOverflow](https://stackoverflow.com/questions/64261546/how-to-solve-error-microsoft-visual-c-14-0-or-greater-is-required-when-inst).

#### 🐧 Linux
Une fuite mémoire a été remarquée sur le projet quelques jours avant la création de la première version jouable du projet (tag v1.0.0). Son origine reste inconnue.  
Depuis le commit de la v1.0.0, ce problème pourtant régulier n'a plus été observé. Il est considéré comme réglé après de longues heures de tests intensifs en jeu sans reproduction.  
Les utilisateurs de Linux de sont toutefois pas à l'abri de le voir reparaître, car nous ne sommes pas en mesure d'assurer sa disparition.

### Dépendances
Ce projet nécessite la version de **python 3.12** a minima.  
Ce projet nécessite l'importation des bibliothèques contenues dans le fichier `requirements.txt`.
L'installation de ces bibliothèques se fait avec la commande suivante :
```
pip install -r requirements.txt
```
*⚠️ ce processus peut prendre du temps, notamment pour les bibliothèques comme TensorFlow.*

## ⏯️ Lancement du jeu
Pour lancer le jeu, exécutez selon votre Système d'Exploitation le fichier `start.cmd`, `start.sh`, ou `start.py` avec une application capable d'éxecuter un fichier python si aucun ne fonctionne.  
L'écran de menu devrait s'afficher.
Si l'écran est trop grand ou trop petit, vous pouvez régler manuellement sa taille en modifiant les constantes `SCREEN_WIDTH` et `SCREEN_HEIGHT` aux valeurs en pixels voulues.
Ces constantes se trouvent dans le dossier `engine/options.py`.

Vous pouvez regarder et modifier les contrôles dans le sous-menu **contrôles**.  
Le jeu démarre lorsque vous appyez sur **Jouer** ou **Nouvelle partie**. A l'avenir, **Nouvelle partie** permettra de repartir de zéro et **Jouer** deviendra **Continuer** la partie en cours.

## 🎮 Règles du jeu
### Contrôles
*Rappel : Vous pouvez à tout moment regarder et modifier certains contrôles dans le sous-menu **contrôles**.*
- Les **déplacements** sont gérés par défaut avec les touches `Z`⬆️ `Q`⬅️ et `D`➡️. La marche arrière n'est pas possible.
- Les **interactions**, qui permettent d'entrer dans certaines zones, sont gérées par défaut avec la touche `E`🚪.
- En jeu, vous pouvez utiliser la `molette`🖱️ pour **modifier l'angle de vue**, et le `clique gauche`🖱️ pour **zoomer**.
- Lorsque vous êtes en jeu, la touche `ESCAPE`🔙 permet de **revenir au menu**.
- Lorsque vous êtes dans la **stucture inconnue**, le `clique gauche`🖱️ permet de jouer, et le `clique droit`🖱️ de tourner le cube pour changer l'angle de vue.

### Objectif et conditions de victoire.
Les règles du jeu sont annoncées dans l'introduction qui suit la création d'une partie, et que vous pouvez revoir à tout moment en appuyant sur **Revoir l'introduction**.  

Comme elles sont données de manière implicite et en même temps que le contexte, nous les explicitons ici :
1. **Objectif :** Le joueur doit récolter un total de 11 HeatCores (Cœurs de chaleur) : 2 pour le décollage et 9 pour sauver la mission. Il doit ensuite retourner vers l'atterrisseur.
2. **Contraintes :** Le joueur doit rentrer avant la nuit, sous peine de perdre tous ses HeatCores. Lorsqu'il commande le décollage de l'aterrisseur, le joueur perd 2 HeatCores.
3. **Victoire :** Le joueur gagne lorsqu'il commande le décollage à l'atterisseur et qu'il possède encore 9 HeatCores (sans compter les deux consommés au décollage).
4. **Cube :** Le joueur et l'IA doivent aligner 3 de leurs pions sur n'importe quelle face du cube. Chaque tour permet au choix de poser un pion ou de tourner une rangée.

#### HUD (Interface en jeu)
La barre en haut de l'écran représente la boussole du vaisseau.
- Les marqueurs **noirs** indiquent la positions de HeatCores.
- Le marqueur **jaune** indique la position de l'atterrisseur.
- Le marqueur **rose** indique la position de la structure inconnue.

La barre à droite de l'écran indique le nombre de HeatCore récoltés. La couleur rouge foncée indique que le HeatCore est récolté mais sera consommé au décollage.

## 🧨 Bugs et problèmes connus
- **Fuite de mémoire sous Linux.**
  Une fuite de mémoire d'origine inconnue a occuré sous Linux Mint. Le problème n'a plus été observé depuis la v1.0.0 du projet, mais nous ne pouvons garantir sa disparition effective.
- **Mauvaise génération des mondes.**
  Certaines graines de génération causent des patterns répétés en lignes droites à certains endroits du monde.
  Le problème est courant dans le domaine de la génération procédurale, et nous n'avions ni le temps ni les compétences nécessaires pour le résoudre.

## ⚙️ Description technique du projet
Le dossier `engine` contiens tout le programme relatif à l'affichage en 3D du jeu, les interfaces affichées et les interactions du joueur avec le monde.  
Le dossier `intel_arti` contiens les fichiers qui ont permis la création des modèles d'IA qui jouent sur le cube, ainsi que le code qui permet de les utiliser sur le cube.  
Le dossier `models` contiens les données des modèles d'IA utilisés en jeu.  
Le dossier `3D data` contiens les données relatives aux objets 3D qui ne sont pas générés procéduralement.  
Le dossier `Musics` contiens les fichiers audios utilisés pour le jeu.  
Le dossier `txt` concerne tous les éléménents qui ne sont pas du programme mais  qui sont affichés, dans les interfaces par exemple.  
Les dossiers `saves` et `logs` sont vides par défaut, et contiendront les sauvegardes de progression et les logs du jeu.  

## 👥 Crédits
### Cadre de réalisation
Ce projet a été créé dans le contexte des [Trophées NSI](https://trophees-nsi.fr/), pour l'édition 2025.

### L'équipe PP42
Ce projet est la seconde création de l'équipe **PP42**, composée de Matthew Batt, Gaspard Dupin, Cosmo Pinot et Lou Schanen.  

### Autres intervenants
La musique __*The Road Ahead*__, thème d'exploration, a été créée par Christiaan Dekker et publiée sur NewGrounds. Son accord nous a été donné pour l'usage de son œuvre dans le projet.

### Usage de l'IA
Les agents textuels Chat-GPT et Mistral AI ont été utilisés comme outils durant le projet, aux fins suivantes :
- Rechercher des bibliothèques et des outils adaptés aux besoins du projet.
- Vérifier le code de certaines fonctions.
- Coder des fonctions de référence qui nous ont servies de modèle pour certaines fonctions complexes du programme.
- Remplir certaines docstrings.
- Corriger de nombreuses fautes d'orthographe.

Nous avons pris la décision de mentionner ces usages par soucis d'honnêtetée et parce que nous nous sentons légitimes de l'avoir fait.
Nous n'avons pas entièrement créé ce projet par IA, c'aurait été impossible au vu de sa taille, et l'usage de ces nouveaux outils ne nous a pas épargné
de très nombreuses heures de travail. Ce projet a été initié en fin Août et finalisé (en retard) le 25 Mars à la demande de notre professeur de NSI.
Nous avons travaillés parfois jusqu'à très tard (minuit passé) pour mener ce projet a bien. La répartition des tâche a occupé presque toutes les semaines de notre
calendrier, y compris les vacances.
