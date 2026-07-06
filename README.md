# Arma Reforger Server Assistant — Free Version

**Arma Reforger Server Assistant Free Version** est un assistant Windows créé par **JAVIDI STUDIO** pour installer, configurer et lancer un serveur dédié **Arma Reforger** plus facilement.

Cette version Free permet une installation guidée de **SteamCMD** et de **Arma Reforger Server**, la génération d'un `config.json`, puis le lancement du serveur depuis une interface simple.

> © 2026 JAVIDI STUDIO — Tous droits réservés.

---

## Fonctionnalités Free

- Installation guidée de SteamCMD.
- Installation / mise à jour du serveur Arma Reforger via SteamCMD.
- Génération simple du fichier `config.json`.
- Création automatique d'un fichier `.bat` de lancement.
- Lancement et arrêt du serveur.
- Sauvegarde des dossiers et réglages de base.
- Rapport de problème exportable.

## Non inclus dans la version Free

Ces fonctions sont réservées à la version Premium :

- Gestion des mods en 1 clic.
- Presets de mods et ordre de chargement.
- Gestion de serveur en direct avec RCON.
- Kick / ban / restart depuis l'interface.
- Diagnostic réseau avancé.
- Profils serveur multiples.
- Éditeur JSON avancé.
- Scénarios et missions avancés.

---

## Installation utilisateur

### 1. Créer deux dossiers

Sur le Bureau, crée par exemple deux dossiers :

```text
SteamCMD
ArmaReforgerServer
```

La version Free demande volontairement deux dossiers séparés :

- un dossier pour **SteamCMD** ;
- un dossier pour **Arma Reforger Server**.

### 2. Lancer le logiciel

Lance l'application Free, puis va dans :

```text
1. Installation
```

Sélectionne :

```text
Dossier SteamCMD          -> ton dossier SteamCMD
Dossier du serveur        -> ton dossier ArmaReforgerServer
```

Puis clique sur :

```text
Tout installer en 1 clic
```

Le logiciel va télécharger SteamCMD, l'initialiser, puis installer le serveur dédié Arma Reforger.

### 3. Configurer le serveur

Va dans :

```text
2. Configuration
```

Choisis :

- le nom du serveur ;
- le mot de passe serveur si besoin ;
- le mot de passe admin ;
- le nombre de joueurs ;
- le scénario ;
- le port du serveur.

Puis clique sur :

```text
Générer la configuration
```

### 4. Ouvrir les ports de la box

Le logiciel ne peut pas ouvrir automatiquement les ports de ta box internet.

À ouvrir dans l'interface de ta box, généralement dans **Réseau > NAT/PAT** :

```text
Arma Server
Port interne : 2001
Port externe : 2001
Protocole : UDP
Équipement : ton PC
```

Optionnel mais conseillé pour la visibilité du serveur :

```text
Arma Server A2S
Port interne : 17777
Port externe : 17777
Protocole : UDP
Équipement : ton PC
```

Ne pas exposer le port RCON `19999` sur Internet si tu ne sais pas exactement ce que tu fais.

### 5. Lancer le serveur

Va dans :

```text
4. Lancer
```

Puis clique sur :

```text
Démarrer le serveur
```

---

## Compiler en .exe

Depuis le dossier du projet :

```bat
py -m pip install --upgrade pyinstaller
py -m PyInstaller --onedir --windowed --clean --noupx --name "ArmaReforgerServerAssistantFree" "arma_reforger_server_assistant_free.py"
```

Le logiciel compilé sera disponible dans :

```text
dist/ArmaReforgerServerAssistantFree/
```

Il est conseillé de distribuer le dossier complet en `.zip`.

---

## Dépendances

- Windows
- Python 3.10 ou plus récent si lancé depuis le `.py`
- SteamCMD est téléchargé automatiquement par le logiciel

---

## Version Premium

La version Premium ajoute notamment :

- gestion des mods en 1 clic ;
- gestion serveur en direct ;
- commandes RCON ;
- kick / ban / restart ;
- diagnostic réseau ;
- éditeur JSON avancé ;
- profils serveur.

Site : **http://javidistudio.fr**

---

## Partenaire

Ce logiciel peut afficher un lien partenaire Shockbyte.

Lien affilié :  
`https://shockbyte.com/billing/aff.php?aff=11359`

---

## Droits d'auteur et utilisation

Copyright © 2026 **JAVIDI STUDIO**.  
Tous droits réservés.

La version Free peut être téléchargée et utilisée gratuitement pour gérer un serveur Arma Reforger personnel ou communautaire.

Sans autorisation écrite de JAVIDI STUDIO, il est interdit de :

- revendre ce logiciel ;
- modifier puis redistribuer ce logiciel ;
- retirer le nom JAVIDI STUDIO ;
- republier le logiciel sous un autre nom ;
- intégrer ce code dans un produit commercial ;
- vendre une version modifiée ou dérivée.

Ce dépôt est fourni pour la version Free officielle.  
Aucune licence open source n'est accordée sauf mention contraire explicite.

---

## Mentions

Arma Reforger est une marque de Bohemia Interactive.  
SteamCMD est un outil de Valve.  
JAVIDI STUDIO n'est pas affilié à Bohemia Interactive, Valve ou Shockbyte.
