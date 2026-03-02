# Guide d'administration du bot

Ce guide est destiné aux administrateurs du bot. Il explique les commandes d'administration disponibles et leur utilisation.

## Sommaire
- [Commandes de base](#commandes-de-base)
- [Gestion des utilisateurs](#gestion-des-utilisateurs)
- [Gestion des données](#gestion-des-données)
- [Gestion des calendriers](#gestion-des-calendriers)
- [Commandes avancées](#commandes-avancées)
- [Commandes Owner](#commandes-owner)
- [Exemples d'utilisation](#exemples-dutilisation)
---

## Commandes de base

### /actualiser
Met à jour une ressource (données Google, calendriers scolaires, setlists). Ignore le système de cooldown.
* **ressource**: La ressource à mettre à jour.

### /voir_logs
Envoie les logs des 4 dernières semaines, ceux des dernières 24h, et l'output de la console actuel.

### /couleur_intégrations
Change la couleur des intégrations Discord.
* **couleur**: Nouvelle couleur au format hexadécimal (ex: FFFFFF).

---

## Gestion des utilisateurs

### /ajouter_admin
Enregistrer quelqu’un comme admin.
* **membre**: Mentionner la personne concernée.

### /ajouter_membre
Ajoute un membre à la base de données.
* **membre**: Mentionne un membre.
* **mail**: Mail de l’utilisateur.
* **groupe**: Groupe de l’utilisateur.
* **sous-groupe**: Demi-groupe (uniquement si 1A ou 2A).

### /voir_membres
Consulte la liste de tous les membres inscrits.

### /supprimer_membre
Retire un membre.
* **mail**: Indique le mail.

---

## Gestion des données

### /nettoyer
Nettoie les données erronées de la base de données.

### /ajouter_setlist
Ajoute une setlist.
* **lien**: Lien de la setlist.

### /supprimer_setlist
Retire une setlist.

### /ajouter_instrument
Ajouter un instrument dans la BDD.
* **instrument_anglais**: Nom de l’instrument en anglais.
* **instrument_francais**: Nom de l’instrument en français.

### /supprimer_table
Vider toutes les entrées d’une table de la base de données.
* **table**: Indiquer la table à vider.

---

## Gestion des calendriers

### /ajouter_calendrier
Ajouter un calendrier Google pour vérifier les contraintes.
* **id**: ID du calendrier.

### /supprimer_calendrier
Retirer un calendrier Google (dangereux). Retire uniquement le calendrier du bot.
* **id**: ID du calendrier.

### /créer_calendrier
Créer un calendrier Google lié à une setlist.

### /lier_calendrier
Lier un calendrier Google à une setlist.
* **id**: ID du calendrier.

---

## Commandes avancées

### /créer_fils
Créer un fil par morceau dans ce salon.

### /actualiser_commandes
Actualise les commandes sur tous les serveurs.
* **password**: Phrase secrète.

---

## Commandes Owner

### /retirer_admin
(owner-only) Retirer les droits d’admin du bot à quelqu’un.
* **membre**: Mentionner la personne concernée.

### /ajouter_owner
(owner-only) Enregistrer quelqu’un comme owner.
* **membre**: Mentionner la personne concernée.

### /voir_owners
(owner-only) Affiche les owners.

### /réinit_db
(owner-only) Réinitialise la base de données.

---

## Exemples d'utilisation

### Ajout d'une setlist / lancement des répétitions

- Ajouter la setlist avec ```ajouter_setlist```
- Si le calendrier existe, vous pouvez utiliser ```ajouter_calendrier```, sinon faire ```créer_calendrier```
- Vérifier que la setlist est bien ajoutée avec ```info``` par exemple (au besoin faire ```actualiser```)
- Créer les threads avec ```créer_fils``` dans le salon créé à l'occasion