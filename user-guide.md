# Documentation des Commandes Utilisateur

---

## Commandes de gestion de compte

### **/connexion**
S’ajouter à la base de données.
Sélectionner un groupe scolaire sans choisir de sous-groupe déclenche une erreur si le groupe n'est pas un groupe FISA ou d'approfondissement.

**Attention**: Dans certains cas précis, l'enregistrement peut avoir eu lieu malgré une erreur, vérifier avec ```/profil``` et modifier toute valeur erronée avec la commande correspondante (```/mail```, ```/groupe```, ```/pseudo```).
* **mail** : Ton adresse mail TN.net
* **groupe** : Groupe scolaire auquel tu appartiens (laisser vide si extérieur)
* **sous-groupe** : Sous-groupe de TD (laisser vide si pas de sous-groupe existant)

---

### **/mail**
Change l’adresse mail associée au compte.
* **mail** : La nouvelle adresse mail (TN.net)

---

### **/groupe**
Change le groupe associé au compte.
* **groupe** : Le nouveau groupe (laisser vide si extérieur)
* **sous-groupe** : Le sous-groupe de TD (laisser vide si pas de sous-groupe)

---

### **/pseudo**
Change le pseudo associé au compte.
* **pseudo** : Ton nouveau pseudo (Prénom NOM par défaut)

---

### **/profil**
Consulte le profil d’une personne. Laisse vide pour consulter ton profil.
* **membre** : Mentionner la personne désirée (elle ne recevra pas de notification)

---

## Commandes liées aux Contraintes

### **/indisponibilité**
Ajoute une contrainte ponctuelle.
Paramètres:
* **jour** : Jour de la contrainte
* **début** : Heure de début de la contrainte (optionnel)
* **fin** : Heure de fin de la contrainte (optionnel)

Le format de date est très flexible, voici quelques exemples de date:
* Pour le **jour**: *vendredi*, *demain*, *24/10*, *24/10/25*, *24 janvier 2025*, *24-10-25*
* Pour les **horaires**: *midi*, *16h*, *16:00*, *18h24m*, *14-30*

---

### **/indisponibilité\_récurrente**
Ajoute une contrainte récurrente.
* **jour** : Jour de la semaine de l’indisponibilité (peut être « Tous »)
* **début** : Heure de début de l’indisponibilité
* **fin** : Heure de fin de l’indisponibilité

**Exemple:** ```/indisponibilité_récurrente jour:lundi début:20h fin:22h30```

---

### **/supprimer\_indisponibilité**
Pour retirer une contrainte.

Affiche un message interactif pour sélectionner une contrainte et la supprimer.

---

### **/voir\_indisponibilités**
Consulter les contraintes.

Affiche un message interactif affichant les contraintes à la semaine.

---

### **/obtenir\_calendrier**

Affiche un message interactif pour obtenir le lien vers le calendrier de la setlist choisie.

---

### **/demander\_actualisation**
Demande la mise à jour d'un calendrier.
* **calendrier** : Indiquer la ressource à mettre à jour (Calendriers google, calendriers scolaires)

La mise à jour se fait dans les 15 minutes suivant la demande d'utilisateurs (une actualisation dans les 15 prochaines minutes suivant la commande, peu importe le nombre de personnes l'ayant demandé).

---

## Commandes liées aux répétitions

### **/ajouter\_répète**
Ajoute un nouveau créneau de répétition pour un morceau.

Ici aussi les formats sont très flexibles (voir plus haut pour des exemples).

* **jour** : Jour de la répétition
* **début** : Heure de début de la répétition
* **durée** : Durée de la répétition
* **morceau** : Si tu ne te trouves pas dans un fil, nom du morceau concerné par la répétition

**Note:** Une regex est effectuée sur le titre, donc si le nom n'est pas entier la recherche devrait fonctionner

---

### **/trouver\_repète**
* **morceau** : Nom du morceau (laisser vide si tu es dans le fil correspondant)

Affiche un message interactif montrant successivement:
* Un emploi du temps prenant en compte toutes les indisponibilités des musiciens, réservations du local, cours, pour la sélection de la semaine
* Ce même emploi du temps pour la sélection de la journée
* Un bilan des indisponibilités cette journée-là
* Un emploi du temps de la journée affichant les trous possibles et permettant la sélection du créneau pour une répétition.

**Note:** le calendrier est automatiquement mis à jour. En cas d'erreur, penser à vérifier dans le Google Calendar avant de réitérer la commande, il peut y avoir de la désynchronisation entre ce qui est affiché dans le bot et le calendrier.

Pour forcer une répétition, utiliser ```/ajouter_répète```, mais vérifiez à nouveau le Google Calendar, et demandez l'actualisation si nécessaire.

---

### **/info**
Consulter les morceaux d’une personne. Laisse vide pour consulter tes morceaux.
* **membre** : Mentionner la personne désirée (elle ne recevra pas de notification)
* **affichage** : Niveau d’information

---

### **/morceau**
Obtenir des informations concernant un morceau en particulier.
* **morceau** : Nom du morceau (peut être vide si tu te trouves dans un fil portant le nom du morceau !)

**Note:** une regex est effectué sur le titre

---

### **/voir\_répètes**
Affiche une liste de toutes les répétitions planifiées.

# FAQ

---

## J'ai ajouté une répète manuellement dans le calendrier mais elle n'apparaît pas dans le bot.

C'est probablement que le le lieu de la répétition n'a pas été indiqué comme étant *local*. Le local n'est donc pas réservé et le bot ignore cette répétition.

---