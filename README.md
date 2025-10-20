# Labo 07 – Architecture Event-Driven, Event Sourcing et Pub/Sub

<img src="https://upload.wikimedia.org/wikipedia/commons/2/2a/Ets_quebec_logo.png" width="250">    
ÉTS - LOG430 - Architecture logicielle - Chargé de laboratoire: Gabriel C. Ullmann, Automne 2025.

## 🎯 Objectifs d'apprentissage
- Comprendre les concepts de producteurs et consommateurs d'événements avec [Apache Kafka](https://kafka-python.readthedocs.io/en/master/apidoc/modules.html) et [Apache Zookeeper](https://zookeeper.apache.org/)
- Appliquer l'event sourcing pour maintenir et consulter l'historique des événements

## ⚙️ Setup

Notre magasin a grandi et nous souhaitons maintenant améliorer l'engagement client via des notifications automatisées. Différents événements dans notre application (création d'utilisateur, nouvelle commande, changement de statut) peuvent déclencher l'envoi de courriels. Dans ce laboratoire, nous créerons Coolriel, un microservice de gestion des notifications event-driven qui générera les templates HTML des courriels sans les envoyer réellement (la configuration d'un serveur SMTP étant hors du scope de ce cours).

### 1. Préparez les dépôts
Créez vos propres dépôts à partir des dépôts gabarits (templates). Utilisez le dépôt du labo 05 et clonez ce nouveau dépôt (log430-labo7-emails) :
```bash
git clone https://github.com/[votrenom]/log430-a25-labo5
cd log430-a25-labo5
git checkout feature/labo07
cd ..
git clone https://github.com/[votrenom]/log430-labo7-emails
cd log430-labo7-emails
```

### 2. Créez le réseau Docker
```bash
docker network create labo07-network
```

### 3. Configuration de l'environnement
Pour les **deux dépôts** :
- Créez un fichier `.env` basé sur `.env.example`
- Modifiez `docker-compose.yml` pour utiliser `labo07-network`
- Construisez et démarrez les conteneurs

```bash
docker compose build
docker compose up -d
```

### 4. Apache Zookeeper
Apache Zookeeper est une application de coordination d'applications distribuées en clusters qui fonctionne en tandem avec Kafka. Elle est indiqué dans notre `docker-compose.yml`. Bien que cela dépasse le cadre de notre laboratoire, je vous recommande de lire [cet article](https://www.openlogic.com/blog/using-kafka-zookeeper#how-kafka-and-zookeeper-are-used-01) pour en savoir plus.

## 🧪 Activités pratiques

### 1. Analysez l'architecture
Examinez les méthodes de création dans les fichiers `src/orders/commands/write_user.py` (store_manager, labo5) et `src/handlers/user_created_handler.py` (coolriel, labo7) et réfléchissez sur le flux d'événements. Utilisez la collection Postman du labo 5 pour ajouter quelques utilisateurs et observez les messages dans le terminal des deux applications (par exemple, via Docker Desktop).

> 💡 **Question 1** : Quelle est la différence entre la communication entre `store_manager` et `coolriel` dans ce labo, et la communication entre `store_manager` et `payments_api` que nous avons implémentée pendant le labo 5 ? Expliquez avec des extraits de code ou des diagrammes.

### 2. Implémentez un handler de suppression d'utilisateur
Dans le microservice `coolriel`, complétez l'implémentation de `src/handlers/user_deleted_handler.py` pour gérer les événements de suppression d'utilisateur. Le handler doit :
- Consommer les événements du topic `user-events` avec type = `UserDeleted`
- Générer un template de courriel d'au revoir en utilisant les données qui sont dans le message déclenché par l'événement `UserDeleted`
- Enregistrer le HTML résultant dans le disque

Également dans `store_manager`, modifiez les méthodes dans `src/orders/commands/write_user.py` selon les besoins.

### 3. Ajoutez des types d'utilisateur
Dans le `store_manager`, modifiez `db-init/init.sql` pour ajouter champ `user_type_id` à la table `User`. Créez une table `UserType` pour faire la distinction entre trois types d'utilisateurs : clients, employés et directeurs du magasin. Relecionez `UserType` et `User` en utilisant `FOREIGN KEY`.
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
Modifiez les handlers pour personnaliser le HTML des courriels selon le type d'utilisateur. Par exemple, si nous ajoutons un nouvel employé, au lieu d'envoyer le message `Merci d'avoir visité notre magasin`, nous devons envoyer `Salut et bienvenue dans l'équipe !`. Adaptez également le message d'au revoir.

> 📝 NOTE : Dans les applications réelles, fréquemment nous utilisons un [soft delete](https://www.geeksforgeeks.org/dbms/difference-between-soft-delete-and-hard-delete/) au lieu de vraiment supprimer un utilisateur de manière définitive pour conserver l'historique de l'utilisateur et éviter les suppressions accidentelles. Ici, par simplicité, nous faisons un vrai delete. De toute façon, nous allons utiliser Kafka pour conserver l'historique plus tard.

> 💡 **Question 3** : Comment avez-vous implémenté la vérification du type d'utilisateur ? Illustrez avec des captures d'écran ou des extraits de code.

### 5. Event sourcing avec Kafka
Kafka n'est pas configuré par défaut pour utiliser l'approche d'event sourcing. Ça veut dire que les messages qui sont déclenchés par les différents événements seulement passent par Kafka, mais ne restent pas là. Ajoutez ces variables dans le `docker-compose.yml` pour faire en sorte que Kafka garde les messages.

```yml
kafka:
    environment:
        KAFKA_LOG_RETENTION_HOURS: 168  # Garde les messages 7 jours
        KAFKA_LOG_RETENTION_BYTES: 1073741824  # 1GB max par partition
        KAFKA_LOG_SEGMENT_BYTES: 1073741824  # Taille des segments
```

Exécutez `docker compose restart kafka` pour redémarrer votre Kafka avec les nouvelles configurations. Ensuite, créez/supprimez quelques utilisateurs pour déclencher des événements et leur enregistrer dans Kafka. Pour vérifier si les événements étaient enregistrés, créez un nouveau consommateur `services/user_history_consumer.py` qui lit l'historique complet des événements du topic `user-events` et les sauvegarde dans un fichier JSON.

```python
consumer = KafkaConsumer(...)
```

Utilisez votre nouveau `user_history_consumer` dans `coolriel.py` pour tester. Si vous avez besoin de mieux comprendre la séquence des événements dans le code, utilisez les loggers pour enregistrer les messages sur le terminal.

> 💡 **Question 4** : Combien d'événements avez-vous récupérés dans l'historique ? Illustrez avec le fichier JSON généré.

## 📦 Livrables

- Un fichier .zip contenant l'intégralité du code source du projet Labo 07.
- Un rapport en .pdf répondant aux questions présentées dans ce document. Il est obligatoire d'illustrer vos réponses avec du code ou des captures d'écran/terminal.