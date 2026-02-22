# Guide d'Architecture et de Contribution - ArtéBot

Ce document décrit l'architecture technique du projet ArtéBot, les conventions de code et les procédures de déploiement.

## 1. Architecture Générale

### 1.1. Vue d'ensemble

#### Description du flux principal
Le cœur du projet réside dans le fichier `bot.py`. Au lancement, ce script initialise l'objet `ArteBot`, qui hérite de la classe `commands.Bot` de la bibliothèque `discord.py`.

Le flux de démarrage est le suivant :
1.  **Initialisation** : La classe `ArteBot` est instanciée. Le constructeur met en place la configuration de base, notamment les `intents` Discord qui définissent les types d'événements que le bot recevra.
2.  **Chargement des commandes** : Les commandes "slash" (App Commands) définies dans les différents modules du répertoire `python/commands/` sont chargées dynamiquement.
3.  **Connexion à Discord** : Le bot se connecte à l'API Discord en utilisant le token fourni via les variables d'environnement.
4.  **Tâche de fond** : Une fois connecté, une tâche asynchrone (`scheduled_update`) est lancée. par `on_ready` Elle s'exécute en boucle pour actualiser périodiquement les données externes (calendriers Google, setlists Google Sheets).
5.  **Boucle d'événements** : Le bot entre dans sa boucle principale, prêt à recevoir et à traiter les interactions des utilisateurs (commandes, événements, etc.).



#### Interaction des composants
L'architecture du bot est modulaire pour séparer les responsabilités et faciliter la maintenance.

*   `bot.py` : Le chef d'orchestre. Il gère le cycle de vie du bot, la connexion à Discord et la tâche de fond. Il définit aussi  l'ensemble des commandes slash.
*   `python/commands/` : Ce répertoire contient des modules qui regroupent les commandes par fonctionnalité (gestion des utilisateurs, des musiques, des contraintes, etc.).
*   `python/db.py` : Ce module est l'unique interface avec la base de données SQLite. Il abstrait toutes les requêtes SQL et fournit des fonctions simples pour manipuler les données (ex: `get_user`, `add_song`).
*   `python/googleutils.py` : Gère toute l'interaction avec les APIs Google (Sheets et Calendar). Il s'occupe de l'authentification (voir [Python Quickstart](https://developers.google.com/workspace/docs/api/quickstart/python?hl=fr)) et de la récupération des données brutes.
*   `python/classes/`: Contient les classes de données (`Musician`, `Event`) qui structurent les informations manipulées par le bot.

### 1.2. Le Bot Discord (`bot.py`)

#### Structure de la classe `ArteBot`
La classe `ArteBot` étend `commands.Bot` de [Discord.py](https://discordpy.readthedocs.io/en/stable/), ce qui lui donne toutes les fonctionnalités d'un bot Discord standard. La personnalisation principale est l'ajout de la tâche `scheduled_update`.

Toutes les 15 minutes, elle rafraîchit les événements des calendriers Google et les informations de la setlist depuis Google Sheets.

```python
# bot.py

@tasks.loop(minutes=15)
async def scheduled_update(self):
    for key in asking_refresh:
        if asking_refresh[key]:
            admin_commands.refresh(None, key, True)
            asking_refresh[key] = False
    self.last_update_call = time.time()
```

#### Gestion des commandes (App Commands)
Les commandes sont définies à l'aide du décorateur ou `@bot.tree.command()`. C'est une intégration des commandes slash avec une validation de types et des descriptions intégrées.

Toutes les commandes doivent strictement suivre la convention suivante:
__Exécuter la commande dans un `try`, et rediriger l'erreur dans le `except`__ voir [la section 5.2](#52-Gestion-des-Erreurs)

Cela implique que __toutes les erreurs doivent être traitées dans la fonction appelée.__

Ici un exemple de commande définie dans bot:
```python
# bot..py

@bot.tree.command(name="indisponibilité", description="Ajouter une contrainte ponctuelle")
@app_commands.describe(day="Jour de la contrainte", start="Heure de début de la contrainte (optionnel)", end="Heure de fin de la contrainte (optionnel)")
@app_commands.rename(day="jour", start="début", end="fin")
async def punctual_constraint(i: discord.Interaction, day: str, start: str = None, end: str = None):
    try:
        await i.response.send_message(embed=constraints_commands.punctual_constraint(i.user.id, day, start, end), ephemeral=True)

    except Exception as e:
        await i.response.send_message(embed=discordutils.failure_embed(message=str(e)), ephemeral=True)
```

Puis un exemple de code pour une commande:

_Note: toutes les fonctions doivent toujours retourner un `discord.Embed`, et les formatter avec une des trois fonctions de `discordutils.py`_: `info_embed`, `success_embed` ou `failure_embed`.
```python
# commands/user_commands.py

def change_mail(user_id: int, mail: str) -> discord.Embed:
    # Un premier try/except pour vérifier si l'adresse est correcte. Pour faire passer un message d'erreur, on raise une exception custom
    try:
        tools.parse_mail(mail)
    except:
        raise ValueError("Format de l’adresse mail incorrect !")
    # Afin d'afficher un message différent en fonction de l'erreur, on chaîne plusieurs except
    try:
        db.check_user(user_id)
        # Normalement, l'appel de db.run en dehors de db.py est à proscrire
        db.run("UPDATE User SET email = ? WHERE uuid = ?;", (mail, user_id))
    except db.UserNotFoundError:
        db.add_user(user_id, db.get_user_name_from_email(mail), mail, "")
    # Celui-ci récupère toute erreur qui n'est pas prise en compte/prévue,
    # on raise une FailureError: c'est un message d'erreur générique
    # pour éviter d'envoyer des erreurs sensibles à l'utilisateur 
    except:
        raise discordutils.FailureError

    return discordutils.success_embed(message="Adresse mail modifiée avec succès !")
```

#### Gestion des environnements (Debug/Production)
Le bot peut fonctionner dans deux modes : `DEBUG` et `PRODUCTION`. Le mode est déterminé par la variable d'environnement `DEBUG`.

*   Si `DEBUG=True`, le bot utilise le `DEV_TOKEN`.
*   Si `DEBUG=False` (ou n'est pas défini), le bot utilise le `DISCORD_TOKEN` de production.

Cela permet aux développeurs de tester de nouvelles fonctionnalités sur un serveur de test sans affecter le bot principal.

## 2. Infrastructure et Déploiement

### 2.1. Conteneurisation avec Docker

L'application est conçue pour être déployée à l'aide de [Docker](https://www.docker.com/), ce qui garantit un environnement d'exécution cohérent et reproductible.

#### Analyse du `Dockerfile`
Le `Dockerfile` définit les étapes pour construire l'image du bot.

*   **Image de base** : On part d'une image `python:3.11-slim`, qui est une version légère de Python, idéale pour la production.
*   **Gestion des dépendances** : Les dépendances Python sont listées dans `requirements.txt` et installées avec `pip`. C'est une pratique standard pour gérer les bibliothèques externes.
*   **Structure du conteneur** : Les répertoires nécessaires (`python/`, `sql/`, etc.) sont copiés dans le conteneur. Cela inclut le code source, les scripts SQL et les autres ressources.
*   **Point d'entrée** : Le conteneur exécute `entrypoint.sh` au démarrage. Ce script se contente de lancer le bot principal avec `python3 bot.py`.

```dockerfile
# Dockerfile

FROM python:3.11-slim

# ...

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# ...

RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
```

#### Orchestration avec `docker-compose.yml`
Pour faciliter le déploiement et la gestion des services, nous utilisons [Docker Compose](https://docs.docker.com/compose/).

*   **Gestion des volumes** : Deux volumes sont définis : `data_volume` et `db_volume`.
    *   `db_volume` monte le répertoire `database/` dans le conteneur. Cela assure que la base de données SQLite (`database.db`) persiste même si le conteneur est recréé.
    *   `data_volume` est utilisé pour les fichiers de configuration et de données qui peuvent être modifiés, comme `data.json`.
*   **Configuration via variables d'environnement** : Le fichier `docker-compose.yml` utilise `env_file: .env` pour charger les variables d'environnement (comme les tokens) depuis un fichier `.env` à la racine du projet. À l'exécution de `docker-compose up`, il faut donc avoir le fichier `.env` dans le même répertoire, puis il sera copié dans le conteneur.
*   **Montage des fichiers de secrets** : Les fichiers `token.json` et `credentials.json`, nécessaires pour l'authentification Google, sont montés directement dans le conteneur. Même remarque que pour `.env`.

### 2.3. Intégration Continue (GitLab CI)
Le projet inclut un fichier `.gitlab-ci.yml` qui configure un pipeline d'intégration continue simple sur GitLab.

Il y a une pipeline automatique de vérification du code pour éviter un leak de credentials, et un autre à lancer manuellement qui déclenche le build et le puch automatique d'une nouvelle image du conteneur.

#### Le fichier `.env`
Ce fichier (qui ne doit **jamais** être versionné avec Git) contient toutes les informations sensibles.
*   `DEV_TOKEN` : Le token du bot Discord de développement.
*   `DISCORD_TOKEN` : Le token du bot Discord de production.
*   `SCRIPT_ID` : L'identifiant du projet Google Apps Script (inutilisé).
*  `MAIN_CALENDAR_ID`: l'id du calendrier qui contient les répétitions/réservatinos du local en `id@group.calendar.google.com`
* `DEBUG` : `DEBUG=1` ou laisser vide (`DEBUG=`), pour activer/désactiver le mode de débogage (et indiquer quel token utiliser).
*   `OWNER_UUID` : L'ID de l'owner, qui a par défaut tous les droits. Sans celui-ci, aucune administration n'est faisable.

#### Authentification Google (`credentials.json`, `token.json`)
*   `credentials.json` : Ce fichier contient les informations d'identification de l'application OAuth 2.0 (client ID, client secret).
*   `token.json` : Ce fichier, qui doit exister avant le lancement, est géré pour le rafraîchissement automatique par `python/googleutils.py`. Il contient le jeton d'accès et de rafraîchissement. La création initiale de ce fichier est un processus manuel.
*   `token_init.py` : Utilisé pour créer le premier token (envoie une URL d'autorisation d'accès)

## 3. Gestion des Données

### 3.1. Base de Données SQLite

Le bot utilise [SQLite](https://sqlite.org/) comme base de données.

#### Schéma de la base de données (`sql/init.sql`)
Le schéma est défini dans `sql/init.sql`. Il est conçu pour stocker les relations entre les musiciens, leurs instruments, les morceaux et leurs contraintes de disponibilité.

*   `User` : Stocke les informations de base des utilisateurs Discord (ID Discord, nom, etc.).
*   `Song` : Contient le répertoire des morceaux, avec des détails comme le compositeur, le style et les instruments requis.
*   `SchoolEvent`, `GoogleEvent` : Ces tables stockent les événements importés depuis les calendriers (emplois du temps, événements personnels) qui agissent comme des contraintes de disponibilité.
*   `MusicianConstraint` : C'est une table centrale qui lie un musicien à une période d'indisponibilité, qu'elle soit ponctuelle ou récurrente.

#### Interaction avec la base de données (`python/db.py`)
*   **Approche** : Le projet utilise des requêtes SQL brutes via le module `sqlite3` .
*   **Conventions** : Toutes les interactions avec la base de données passent par les fonctions de `python/db.py`. Une fonction wrapper `db.run()` est utilisée pour exécuter les requêtes, ce qui centralise la gestion de la connexion et du curseur.
*   **Initialisation et réinitialisation** :
    *   `init.py` (à la racine) et `sql/init.sql` sont exécutés au premier démarrage du bot pour créer la structure de la base de données, et ajouter l'owner à la BDD au cas où elle aurait été effacée.
    *   `sql/reset.sql` est utilisé pour drop toutes les tables.

Toutes les fonctions définies dans ce fichiers sont censées utiliser la fonction `run`, et devraient être les seules à le faire, afin d'éviter de parsemer des requêtes partout dans le code (complexifie la possibilité de changer de sgbd plus tard).

### 3.2. Services Externes (Google API)

Le module `python/googleutils.py` est dédié à la communication avec les services Google.

#### Module `googleutils.py`
*   **Authentification** : Ce module gère le cycle de vie complet de l'authentification OAuth 2.0. Il utilise les `credentials.json` pour s'identifier et le `token.json` pour s'authentifier. Le plus important est qu'il sait comment utiliser le jeton de rafraîchissement pour obtenir un nouveau jeton d'accès lorsque l'ancien a expiré, garantissant un fonctionnement autonome.
*   **Interaction avec Google Sheets** : Le bot utilise l' [API Google Sheets](https://developers.google.com/workspace/sheets/api/guides/concepts) pour lire les données d'une feuille de calcul qui contient la setlist (liste des morceaux à jouer).
*   **Interaction avec Google Calendar** : L' [API Google Calendar](https://developers.google.com/workspace/calendar/api/guides/overview) est utilisée pour récupérer les événements des calendriers contenant les créneaux de répétitions et de réservation du local. Ces événements sont ensuite stockés dans la base de données comme des contraintes de d'indisponibilité.



## 4. Logique Métier et Traitements Complexes

### 4.1. Parsing et Normalisation des Données

Une grande partie de la complexité du bot réside dans sa capacité à comprendre des entrées humaines flexibles.

#### Parsing des entrées utilisateur (`python/tools.py`)
*   **`parse_mail`** : Cette fonction transforme une adresse email de la forme `prenom.nom@telecomnancy.net` en un nom formaté "Prénom NOM". 
*   **`parse_date` et `parse_time`** : Ces fonctions sont des points clés de l'intelligence du bot. Elles utilisent des expressions régulières pour interpréter un maximum de formats de date et d'heure fournis par l'utilisateur:
    *   Pour les heures : "12h51", "midi", "minuit".
    *   Pour les dates : "02-05-25", "2 mai 25", "demain", "mardi prochain".

#### Gestion du temps (`python/timeutils.py`)
Le projet manipule constamment des dates et des heures. Pour éviter les ambiguïtés liées aux fuseaux horaires et aux formats, une convention stricte est adoptée.

*   **Concept clé** : En interne, presque toutes les dates sont stockées et manipulées sous forme de **timestamps Epoch** (le nombre de secondes écoulées depuis le 1er janvier 1970) en faisant abstraction du fuseau horaire. C'est un format numérique non ambigu.
*   **Fonctions de conversion** : Le module `timeutils.py` fournit un ensemble complet de fonctions pour convertir ces timestamps vers et depuis d'autres formats. **Attention à bien lire la description de la fonction, certaines ne sont développées que pour des conversions avec Google Calendar par exemple**
*   **Calculs de semaine/jour** : Des fonctions comme `get_first_day_of_week` sont disponibles pour les fonctionnalités d'affichage par semaine. Elles permettent de calculer le début et la fin d'une semaine donnée à partir de n'importe quelle date.

### 4.2. Génération de Chaînes de Caractères (String Formatting)

Afficher des informations de manière claire et lisible est aussi important que de les traiter correctement.

#### Fonctions "user-friendly" (`python/tools.py`)
*   **`get_special_date_string`** : Au lieu d'afficher "22/02/2026", cette fonction transforme la date en une chaîne relative plus naturelle comme "**aujourd'hui**", "**demain**" ou "**mardi**".
*   **`formatted_time_span_string`** : C'est une fonction complexe qui génère une description textuelle d'un intervalle de temps. Elle gère de nombreux cas pour que la phrase soit la plus naturelle possible.
    *   Un événement de 8h à 18h devient "de **8 h** à **18 h**".
    *   Une contrainte de 0h à 9h devient "jusqu'à **9 h**".
    *   Une contrainte de 0h à 23h59 devient "**toute la journée**".

#### Construction des Timetables (`week_timetable_string_from_constraints`, `day_timetable_string_from_constraints`)
Ces fonctions dans `python/tools.py` sont responsables de la génération des grilles horaires visuelles qui sont affichées sur Discord.

 **Algorithme** : L'algorithme itère sur chaque créneau horaire de la journée. Pour chaque créneau, il vérifie s'il y a un chevauchement avec l'une des contraintes. La requête en BDD `request_blocking_events` est au cœur de cette logique. La disponibilité est ensuite traduite par un emoji différent dans la grille (`🟨` si le local est réservé, `🟥`  si quelqu'un est indisponible, `🟦` si quelqu'un a cours, `⬛` si le créneau est libre).

## 5. Qualité et Maintenance

### 5.1. Journalisation (Logging)

Une bonne journalisation est essentielle pour déboguer et surveiller l'application en production.

#### Configuration (`bot.py`)
Le système de logging est configuré au démarrage du bot. Il utilise plusieurs "handlers" pour diriger les logs vers différentes destinations.

*   **Niveaux et Formats** : Le logger est configuré au niveau `INFO`, ce qui signifie que les messages de débogage (`DEBUG`) ne seront pas affichés en production. Le format inclut l'heure, le niveau du log et le message.
*   **Handlers Multiples** :
    *   `FileHandler` (`discord.log`) : Écrit tous les logs de la session actuelle dans un fichier.
    *   `TimedRotatingFileHandler` (`last-24h.log`, `archive-hebdo.log`) : Crée des archives tournantes des logs. C'est très utile pour consulter l'historique sur plusieurs jours ou semaines.
    *   `StreamHandler` : Affiche les logs directement dans la console,.

### 5.2. Gestion des Erreurs

Une gestion robuste des erreurs améliore l'expérience utilisateur et la stabilité du bot.

*   **Blocs `try...except`** : La plupart des commandes encapsulent leur logique principale dans un bloc `try...except Exception as e`. Cela empêche une erreur inattendue de faire planter toute la commande et permet de signaler le problème proprement.
*   **Embeds d'échec (`discordutils.failure_embed`)** : Lorsqu'une erreur se produit, au lieu d'envoyer un message d'erreur cryptique, on utilise une fonction helper qui crée un "embed" Discord propre et formaté. L'option `ephemeral=True` est souvent utilisée pour que le message d'erreur ne soit visible que par l'utilisateur qui a lancé la commande.

### 5.3. Tests

Bien que le projet n'ait pas une suite de tests automatisés complète avec un framework comme [Pytest](https://docs.pytest.org/en/stable/), il dispose d'une base pour les tests unitaires.

#### Fichier `python/tools_test.py`
*   **Approche** : Ce fichier contient une série de tests pour les fonctions critiques de `tools.py` et `timeutils.py`. Les tests sont implémentés avec de simples `assert`. Si une assertion échoue, le programme s'arrête avec une erreur, indiquant une régression.
*   **Convention** : Tout nouveau contributeur qui ajoute ou modifie une fonction dans les modules utilitaires est fortement encouragé à ajouter des cas de test dans `tools_test.py`. Cela garantit que la fonction se comporte comme prévu et que les futures modifications ne casseront pas le code existant.

