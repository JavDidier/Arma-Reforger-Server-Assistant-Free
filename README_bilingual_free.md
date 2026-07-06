# Arma Reforger Server Assistant — Free Version

**Arma Reforger Server Assistant Free Version** is a Windows assistant created by **JAVIDI STUDIO** to help users install, configure, and launch an Arma Reforger dedicated server more easily.

This public repository is used to present and distribute the **Free Version**.  
The source code is not included in this repository.

© 2026 JAVIDI STUDIO — All rights reserved.

---

## Français

### Présentation

**Arma Reforger Server Assistant Free Version** est un assistant Windows créé par **JAVIDI STUDIO** pour installer, configurer et lancer un serveur dédié Arma Reforger plus facilement.

Cette version Free permet :

- l’installation guidée de SteamCMD ;
- l’installation / mise à jour du serveur Arma Reforger via SteamCMD ;
- la génération simple du fichier `config.json` ;
- la création automatique d’un fichier `.bat` de lancement ;
- le lancement et l’arrêt du serveur ;
- la sauvegarde des dossiers et réglages de base ;
- la génération d’un rapport de problème.

### Non inclus dans la version Free

Ces fonctions sont réservées à la version Premium :

- gestion des mods en 1 clic ;
- presets de mods et ordre de chargement ;
- gestion de serveur en direct avec RCON ;
- kick / ban / restart depuis l’interface ;
- diagnostic réseau avancé ;
- profils serveur multiples ;
- éditeur JSON avancé ;
- scénarios et missions avancés.

---

## Installation utilisateur

### 1. Télécharger le logiciel

Télécharge la dernière version depuis l’onglet **Releases** du dépôt GitHub.

Le logiciel est généralement fourni sous forme de dossier compressé `.zip`.

Décompresse le dossier, puis lance :

```text
ArmaReforgerServerAssistantFree.exe
```

Si Windows affiche une alerte de sécurité, clique sur **Informations complémentaires**, puis **Exécuter quand même** uniquement si tu as téléchargé le logiciel depuis la source officielle JAVIDI STUDIO.

### 2. Créer deux dossiers

Sur le Bureau, crée par exemple deux dossiers :

```text
SteamCMD
ArmaReforgerServer
```

La version Free demande volontairement deux dossiers séparés :

- un dossier pour SteamCMD ;
- un dossier pour Arma Reforger Server.

### 3. Installer SteamCMD et le serveur

Dans le logiciel, va dans :

```text
1. Installation
```

Sélectionne :

```text
Dossier SteamCMD       -> ton dossier SteamCMD
Dossier du serveur     -> ton dossier ArmaReforgerServer
```

Puis clique sur :

```text
Tout installer en 1 clic
```

Le logiciel télécharge SteamCMD, l’initialise, puis installe le serveur dédié Arma Reforger.

### 4. Configurer le serveur

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

### 5. Ouvrir les ports de la box internet

Le logiciel ne peut pas ouvrir automatiquement les ports de ta box internet.

Dans l’interface de ta box, va généralement dans :

```text
Réseau > NAT/PAT
```

Puis crée les règles suivantes vers ton PC.

#### Port principal du serveur

```text
Nom : Arma Server
Port interne : 2001
Port externe : 2001
Protocole : UDP
Équipement : ton PC
```

#### Port optionnel pour la visibilité serveur

```text
Nom : Arma Server A2S
Port interne : 17777
Port externe : 17777
Protocole : UDP
Équipement : ton PC
```

Ne pas exposer le port RCON `19999` sur Internet si tu ne sais pas exactement ce que tu fais.

### 6. Lancer le serveur

Va dans :

```text
4. Lancer
```

Puis clique sur :

```text
Démarrer le serveur
```

---

## Version Premium

La version Premium ajoute notamment :

- gestion des mods en 1 clic ;
- gestion serveur en direct ;
- commandes RCON ;
- kick / ban / restart ;
- diagnostic réseau ;
- éditeur JSON avancé ;
- profils serveur ;
- gestion avancée des missions.

Site : http://javidistudio.fr

---

## Partenaire

Ce logiciel peut afficher un lien partenaire Shockbyte.

Lien affilié :  
https://shockbyte.com/billing/aff.php?aff=11359

---

## Droits d’auteur et utilisation

Copyright © 2026 **JAVIDI STUDIO**.  
Tous droits réservés.

La version Free peut être téléchargée et utilisée gratuitement pour gérer un serveur Arma Reforger personnel ou communautaire.

Sans autorisation écrite de JAVIDI STUDIO, il est interdit de :

- revendre ce logiciel ;
- modifier puis redistribuer ce logiciel ;
- retirer le nom JAVIDI STUDIO ;
- republier le logiciel sous un autre nom ;
- intégrer ce logiciel dans un produit commercial ;
- vendre une version modifiée ou dérivée.

Ce dépôt est fourni pour la version Free officielle.  
Aucune licence open source n’est accordée sauf mention contraire explicite.

---

## Mentions

Arma Reforger est une marque de Bohemia Interactive.  
SteamCMD est un outil de Valve.  
JAVIDI STUDIO n’est pas affilié à Bohemia Interactive, Valve ou Shockbyte.

---

# English

## Overview

**Arma Reforger Server Assistant Free Version** is a Windows assistant created by **JAVIDI STUDIO** to help users install, configure, and launch an Arma Reforger dedicated server more easily.

The Free Version includes:

- guided SteamCMD installation;
- Arma Reforger dedicated server installation / update through SteamCMD;
- simple `config.json` generation;
- automatic `.bat` launch file creation;
- server start and stop controls;
- basic folder and settings saving;
- problem report generation.

## Not included in the Free Version

The following features are reserved for the Premium Version:

- one-click mod management;
- mod presets and load order;
- live server management with RCON;
- kick / ban / restart from the interface;
- advanced network diagnostics;
- multiple server profiles;
- advanced JSON editor;
- advanced scenarios and mission management.

---

## User installation

### 1. Download the application

Download the latest version from the GitHub **Releases** section.

The application is usually provided as a compressed `.zip` folder.

Extract the folder, then run:

```text
ArmaReforgerServerAssistantFree.exe
```

If Windows shows a security warning, click **More info**, then **Run anyway** only if you downloaded the application from the official JAVIDI STUDIO source.

### 2. Create two folders

For example, create two folders on your Desktop:

```text
SteamCMD
ArmaReforgerServer
```

The Free Version intentionally uses two separate folders:

- one folder for SteamCMD;
- one folder for Arma Reforger Server.

### 3. Install SteamCMD and the server

In the application, open:

```text
1. Installation
```

Select:

```text
SteamCMD folder       -> your SteamCMD folder
Server folder         -> your ArmaReforgerServer folder
```

Then click:

```text
Install everything in 1 click
```

The assistant downloads SteamCMD, initializes it, and installs the Arma Reforger dedicated server.

### 4. Configure the server

Open:

```text
2. Configuration
```

Choose:

- server name;
- server password if needed;
- admin password;
- max players;
- scenario;
- server port.

Then click:

```text
Generate configuration
```

### 5. Open router / internet box ports

The application cannot automatically open ports on your router or internet box.

In your router settings, usually open:

```text
Network > NAT/PAT
```

Then create the following rules pointing to your PC.

#### Main server port

```text
Name: Arma Server
Internal port: 2001
External port: 2001
Protocol: UDP
Device: your PC
```

#### Optional server visibility port

```text
Name: Arma Server A2S
Internal port: 17777
External port: 17777
Protocol: UDP
Device: your PC
```

Do not expose the RCON port `19999` to the Internet unless you know exactly what you are doing.

### 6. Start the server

Open:

```text
4. Launch
```

Then click:

```text
Start server
```

---

## Premium Version

The Premium Version adds:

- one-click mod management;
- live server management;
- RCON commands;
- kick / ban / restart;
- network diagnostics;
- advanced JSON editor;
- server profiles;
- advanced mission management.

Website: http://javidistudio.fr

---

## Partner

This software may display a Shockbyte partner link.

Affiliate link:  
https://shockbyte.com/billing/aff.php?aff=11359

---

## Copyright and usage

Copyright © 2026 **JAVIDI STUDIO**.  
All rights reserved.

The Free Version may be downloaded and used free of charge to manage a personal or community Arma Reforger server.

Without written permission from JAVIDI STUDIO, you may not:

- resell this software;
- modify and redistribute this software;
- remove the JAVIDI STUDIO name;
- republish the software under another name;
- integrate this software into a commercial product;
- sell a modified or derivative version.

This repository is provided for the official Free Version.  
No open-source license is granted unless explicitly stated otherwise.

---

## Notices

Arma Reforger is a trademark of Bohemia Interactive.  
SteamCMD is a tool by Valve.  
JAVIDI STUDIO is not affiliated with Bohemia Interactive, Valve, or Shockbyte.
