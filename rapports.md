
Objet : Rapport d'Audit et de Test - Application E-Commerce Django

À l'attention du Professeur,

Ce document détaille les résultats des tests effectués sur l'application E-Commerce Django. L'application a été clonée, installée et lancée avec succès dans un environnement de test local.

L'analyse fonctionnelle a révélé un code bien structuré, une interface utilisateur moderne (Tailwind/DaisyUI) et une documentation complète (README.md, QUICKSTART.md). Le parcours utilisateur principal (inscription, navigation, achat) est fonctionnel.

Cependant, les tests ont identifié trois anomalies fonctionnelles, dont une est considérée comme critique.

1. Analyse des Anomalies

🔴 Anomalie Critique : Non-décrémentation du stock après achat

Description : La logique métier de gestion des stocks n'est pas implémentée lors de la finalisation d'une commande. Après qu'une transaction est complétée, le stock disponible pour les articles achetés n'est pas mis à jour.

Scénario de Test (Reproduction) :

Précondition : Noter le stock d'un produit P (ex: 50 unités) via l'interface /admin/.

Action : Simuler un achat client pour une quantité Q (ex: 2 unités) du produit P.

Action : Finaliser la commande.

Résultat Observé : Le stock du produit P dans la base de données est inchangé (toujours 50 unités).

Résultat Attendu : Le stock du produit P devrait être P - Q (soit 48 unités).

Impact : Élevé. Cette anomalie permet des ventes illimitées sur des stocks finis, ce qui est incompatible avec les exigences fondamentales d'une application e-commerce.

🟡 Anomalie Moyenne : Logique d'affichage "Devenir Vendeur"

Description : Le lien de navigation "Devenir Vendeur" reste présent dans l'interface utilisateur (Navbar) même lorsque l'utilisateur connecté possède déjà le statut de vendeur ou d'administrateur.

Impact : Faible. Il s'agit d'une incohérence mineure de l'interface utilisateur (UI) qui peut prêter à confusion, mais n'affecte pas les fonctionnalités principales.

Recommandation : Modifier le template base.html pour conditionner l'affichage de ce lien à la fois à l'authentification de l'utilisateur et à l'absence du statut de vendeur (ex: {% if user.is_authenticated and not user.is_seller %}).

🟡 Anomalie Moyenne : Persistance des données utilisateur (Profil)

Description : Lors de la création d'un nouveau compte, les données complémentaires (ex: numéro de téléphone, adresse) ne sont pas persistées.

Impact : Moyen. Bien que l'authentification (User) fonctionne, le profil utilisateur (Customer ou Seller) n'est pas créé ou peuplé simultanément. L'utilisateur doit compléter ces informations manuellement post-inscription via la page account.html.

Recommandation : Modifier la vue register pour qu'elle crée et lie atomiquement l'objet User et l'objet Customer/Seller correspondant.

2. Rapport sur les Tests Techniques

Tests Unitaires (Serveur)

La commande standard de test Django a été exécutée :

Bash
python manage.py test
Résultat :

Ran 0 tests in 0.000s
NO TESTS RAN
Analyse : Le framework de test fonctionne, mais aucun cas de test automatisé n'est actuellement implémenté (mon_app_ecommerce/tests.py). La validation de l'application repose donc exclusivement sur des tests manuels.

Qualité du Code (HTML)

Des vérifications partielles via le validateur W3C ont été effectuées. Le code HTML généré par les templates est propre et ne présente pas d'erreurs structurelles bloquantes.

Synthèse

L'application est fonctionnelle à un niveau de démonstration, mais l'anomalie critique de gestion des stocks doit impérativement être corrigée avant toute considération de mise en production. Les autres anomalies, bien que moins prioritaires, devraient être traitées pour améliorer la robustesse et l'expérience utilisateur.

J'espère que ce rapport structuré vous sera utile.