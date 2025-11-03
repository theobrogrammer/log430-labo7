# Labo 07 – Architecture Event-Driven, Event Sourcing et Pub/Sub

<img src="https://upload.wikimedia.org/wikipedia/commons/2/2a/Ets_quebec_logo.png" width="250">    
ÉTS - LOG430 - Architecture logicielle - Chargé de laboratoire: Gabriel C. Ullmann, Automne 2025.

## 🎯 Objectifs d'apprentissage

- Comprendre les concepts de producteurs et consommateurs d'événements avec [Apache Kafka](https://kafka-python.readthedocs.io/en/master/apidoc/modules.html)
- Appliquer l'event sourcing pour maintenir et consulter l'historique des événements

## ⚙️ Setup

Notre magasin a grandi et nous souhaitons maintenant améliorer l'engagement client via des notifications automatisées. Différents événements dans notre application (création d'utilisateur, nouvelle commande, changement de statut) peuvent déclencher l'envoi de courriels. Dans ce laboratoire, nous créerons **Coolriel**, un microservice de gestion des notifications event-driven qui générera les courriels HTML sans les envoyer réellement (la configuration et utilisation d'un serveur SMTP étant hors du scope de ce cours).

### 1. Changez de branche du labo 05

Comme dans le labo précédent, nous allons utiliser une version légèrement modifiée du labo 5 qui apporte quelques modifications dans le code. Dans les dépôt `log430-a25-labo5`, changez à la branche `feature/labo07`. Pour changer de branche en utilisant votre terminal, vous pouvez exécuter `git checkout nom_du_branch` dans le répertoire de chaque dépôt.

### 2. Clonez le dépôt du labo 07

Créez votre propre dépôt à partir du dépôt gabarit (template). Vous pouvez modifier la visibilité pour le rendre privé si vous voulez.

```bash
git clone https://github.com/[votredepot]/log430-labo7-emails
cd log430-labo7-emails
```

Ensuite, veuillez faire les étapes de setup suivantes pour **tous les dépôts**.

### 3. Créez un fichier .env

Créez un fichier `.env` basé sur `.env.example`. Dans ce labo, nous n'avons pas d'informations d'authentification de base de données dans le fichier `.env`, alors il n'y a rien à cacher. Vous pouvez utiliser les mêmes paramètres du fichier `.env.example` dans le `.env`, et modifier selon le besoin.

### 4. Vérifiez le réseau Docker

Le réseau `labo05-network` créé lors du Labo 05 sera réutilisé parce que nous allons intégrer Coolriel avec le Store Manager. Si vous ne l'avez pas encore créé, exécutez :

```bash
docker network create labo05-network
```

### 5. Préparez l'environnement de développement

Démarrez les conteneurs de TOUS les services. Suivez les mêmes étapes que pour les derniers laboratoires.

```bash
docker compose build
docker compose up -d
```

## 🧪 Activités pratiques

> ⚠️ ATTENTION : Dans ce laboratoire, nous allons analyser et modifier des fichiers dans les dépôts `log430-a25-labo5` (`store_manager`) et `log430-labo7-emails` (`coolriel`). Veuillez faire attention à l'énoncé de chaque activité afin de savoir quel dépôt utiliser.

### 1. Analysez l'architecture

Examinez les fichiers `src/orders/commands/write_user.py` (`store_manager`) et `src/handlers/user_created_handler.py` (`coolriel`) et réfléchissez sur le flux d'événements. Utilisez la collection Postman du labo 5 pour ajouter quelques utilisateurs et observez les messages dans le terminal des deux applications (par exemple, via Docker Desktop).

> ⚠️ ATTENTION: N'oubliez pas qu'il n'est pas possible d'ajouter deux utilisateurs à notre base de données avec la même adresse e-mail. Pour plus de détails, veuillez consulter `db-init/init.sql` dans l'application Store Manager.

> 💡 **Question 1** : Quelle est la différence entre la communication entre `store_manager` et `coolriel` dans ce labo, et la communication entre `store_manager` et `payments_api` que nous avons implémentée pendant le labo 5 ? Expliquez avec des extraits de code ou des diagrammes.

### 2. Implémentez un handler de suppression d'utilisateur

Dans le microservice `coolriel`, complétez l'implémentation de `src/handlers/user_deleted_handler.py` pour gérer les événements de suppression d'utilisateur. Le handler doit :

- Consommer les événements du topic `user-events` avec type = `UserDeleted`
- Générer un template de courriel d'au revoir en utilisant les données qui sont dans le message déclenché par l'événement `UserDeleted`
- Enregistrer le HTML résultant dans le disque

Également dans `store_manager`, modifiez les méthodes dans `src/orders/commands/write_user.py` selon les besoins.

### 3. Ajoutez des types d'utilisateur

Dans le `store_manager`, modifiez `db-init/init.sql` pour ajouter la colonne `user_type_id` à la table `User`. Créez une table `UserType` pour faire la distinction entre trois types d'utilisateurs : clients, employés et directeurs du magasin. Relecionez `UserType` et `User` en utilisant `FOREIGN KEY`.

```sql
    -- User types table
    DROP TABLE IF EXISTS user_types;
    CREATE TABLE user_types (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(15) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    INSERT INTO user_types (name) VALUES
    ('Client'), -- 1
    ('Employee'), -- 2
    ('Manager'); -- 3

    -- Users table
    DROP TABLE IF EXISTS users;
    CREATE TABLE users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        email VARCHAR(150) NOT NULL UNIQUE,
        user_type_id INT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        FOREIGN KEY (user_type_id) REFERENCES user_types(id) ON DELETE RESTRICT
    );
    INSERT INTO users (name, email, user_type_id) VALUES
    ('Ada Lovelace', 'alovelace@example.com', 1),
    ('Adele Goldberg', 'agoldberg@example.com', 1),
    ('Alan Turing', 'aturing@example.com', 1),
    ('Jane Doe', 'jdoe@magasinducoin.ca', 2),
    ('Da Boss', 'dboss@magasinducoin.ca', 3);
```

Exécutez `docker compose down -v`, `build` et `up -d` pour recréer la structure de la base de données. Adaptez `src/orders/commands/write_user.py` pour accepter et enregistrer des `user_type_id`. Utilisez la collection Postman du labo 5 toujours pour vous aider à tester l'ajout et suppression des utilisateurs.

> 💡 **Question 2** : Quelles méthodes avez-vous modifiez dans `src/orders/commands/write_user.py`? Illustrez avec des captures d'écran ou des extraits de code.

### 4. Adaptez les messages selon le type d'utilisateur

Modifiez les handlers dans `coolriel` pour personnaliser le HTML des courriels selon le type d'utilisateur. Par exemple, si nous ajoutons un nouvel employé, au lieu d'envoyer le message `Merci d'avoir visité notre magasin`, nous devons envoyer `Salut et bienvenue dans l'équipe !`. Adaptez également le message d'au revoir.

> 📝 NOTE : Dans les applications réelles, fréquemment nous utilisons un [soft delete](https://www.geeksforgeeks.org/dbms/difference-between-soft-delete-and-hard-delete/) au lieu de vraiment supprimer un utilisateur de manière définitive pour conserver l'historique de l'utilisateur et éviter les suppressions accidentelles. Ici, par simplicité, nous faisons un vrai delete. De toute façon, nous allons utiliser Kafka pour conserver l'historique plus tard.

> 💡 **Question 3** : Comment avez-vous implémenté la vérification du type d'utilisateur ? Illustrez avec des captures d'écran ou des extraits de code.

### 5. Préparez Kafka pour l'event sourcing

Kafka n'est pas configuré par défaut pour utiliser l'approche d'event sourcing. Ça veut dire que les messages qui sont déclenchés par les différents événements seulement passent par Kafka, mais ne restent pas là. Ajoutez ces variables dans le `docker-compose.yml` dans `coolriel` pour faire en sorte que Kafka garde les messages.

```yml
kafka:
  environment:
    KAFKA_LOG_RETENTION_HOURS: 168 # Garde les messages 7 jours
    KAFKA_LOG_RETENTION_BYTES: 1073741824 # Taille des partitions : 1GB
    KAFKA_LOG_SEGMENT_BYTES: 214748364 # Taille des log segments : 200MB (parties d'une partition sur le disque)
```

Exécutez `docker compose restart kafka` pour redémarrer votre Kafka avec les nouvelles configurations. Ensuite, créez/supprimez quelques utilisateurs pour déclencher des événements et leur enregistrer dans Kafka. 

> 💡 **Question 4** : Comment Kafka utilise-t-il son système de partitionnement pour atteindre des performances de lecture élevées ? Lisez [cette section](https://kafka.apache.org/24/documentation.html#intro_topics) de la documentation officielle à Kafka et expliquez quels sont les points principaux. 

### 6. Créez un consommateur historique

Pour lire les événements déjà enregistrés, complétez l'implémentation du consommateur dans `consumers/user_event_history_consumer.py` qui lit l'historique complet des événements du topic `user-events`. Il est important de donner à ce consommateur un `group_id` distinct, sinon il ne pourra pas lire la partition entière. 

> 📝 NOTE : Si deux consommateurs avec le même `group_id` essaient de lire une partition en même temps, Kafka répartira les partitions entre eux, et ainsi chaque consommateur lira une partie égale des événements (par example, une division 50/50 entre 2 consommateurs). Nous ne voulons pas utiliser cette fonctionnalité ici, mais elle existe pour faciliter la lecture en parallèle de grandes quantités d'événements.

De plus, utilisez le paramètre `auto_offset_reset=earliest` dans `UserEventHistoryConsumer` pour lire la sequence de messages depuis le début (earliest), pas depuis la fin (latest). Finalement, utilisez [json.dumps](https://docs.python.org/3/library/json.html) pour enregistrer les événements dans un fichier JSON sur le disque.

### 7. Utilisez votre nouveau consommateur

Utilisez votre nouveau `UserEventHistoryConsumer` dans `coolriel.py` pour tester. Créez la nouvelle instance et appelez la méthode `start` **avant** le `UserEventConsumer`. Une fois l'exécution du consommateur commence, l'exécution reste bloquée et n'importe quel code à la ligne suivante ne s'exécutera pas jusqu'à ce que le consommateur appelle sa méthode `stop`. Utilisez les loggers pour enregistrer les messages sur le terminal.

```python
    from consumers.user_event_history_consumer import UserEventHistoryConsumer
    consumer_service_history = UserEventHistoryConsumer(
        group_id=f"{config.KAFKA_GROUP_ID}-history",
        # ajoutez les autres paramètres (identiques à ceux utilisés dans UserEventConsumer)
    )
```

> 💡 **Question 5** : Combien d'événements avez-vous récupérés dans votre historique ? Illustrez avec le fichier JSON généré.

## 📦 Livrables

- Un fichier .zip contenant l'intégralité du code source du projet Labo 07.
- Un rapport en .pdf répondant aux questions présentées dans ce document. Il est obligatoire d'illustrer vos réponses avec du code ou des captures d'écran/terminal.
