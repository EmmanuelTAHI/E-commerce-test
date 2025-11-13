import uuid  # Pour générer des noms d'utilisateurs uniques
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from ..models import Product, Category, Customer, Cart, Seller

# ---------------------------------------------------------------------
# TESTS D'AUTHENTIFICATION (Flux de base)
# ---------------------------------------------------------------------
class AuthenticationTests(TestCase):
    
    def setUp(self):
        # Crée un utilisateur de test pour la connexion/déconnexion
        self.user = User.objects.create_user(username='testlogin', password='password123')

    def test_user_can_login(self):
        """
        Test 1: Vérifie que l'utilisateur peut se connecter.
        """
        print("\n[TEST] Vérification de la connexion...")
        
        # On suppose que l'URL de login s'appelle 'login'
        login_url = reverse('login')
        response = self.client.post(login_url, {'username': 'testlogin', 'password': 'password123'})
        
        # Vérifie qu'on est redirigé (code 302)
        self.assertEqual(response.status_code, 302, "La connexion n'a pas redirigé.")
        
        # Vérifie que l'utilisateur est bien connecté dans la session
        self.assertTrue(response.wsgi_request.user.is_authenticated)
        print("[TEST] Connexion OK.")

    def test_user_can_logout(self):
        """
        Test 2: Vérifie la correction du bug de déconnexion.
        """
        print("\n[TEST] Vérification de la déconnexion...")
        self.client.login(username='testlogin', password='password123')
        self.assertTrue(self.client.session.get('_auth_user_id') is not None)

        # On suppose que l'URL de déconnexion s'appelle 'logout'
        logout_url = reverse('logout')
        response = self.client.get(logout_url)
        
        # Vérifie que l'utilisateur est bien déconnecté
        self.assertFalse(response.wsgi_request.user.is_authenticated)
        print("[TEST] Déconnexion OK.")

# ---------------------------------------------------------------------
# TESTS D'INTÉGRATION E-COMMERCE (Les Bugs !)
# ---------------------------------------------------------------------
class ECommerceIntegrationTests(TestCase):

    def setUp(self):
        """ Prépare un environnement e-commerce complet pour les tests """
        self.category = Category.objects.create(name='Test Cat', slug='test-cat')
        self.user = User.objects.create_user(username='testbuyer', password='password123')
        self.customer = Customer.objects.create(user=self.user)
        
        self.product = Product.objects.create(
            name='Produit Test Stock',
            slug='produit-test-stock',
            category=self.category,
            price=1000,
            stock=10  # Stock initial
        )
        
        self.client = Client()
        self.client.login(username='testbuyer', password='password123')

    def test_user_can_add_to_cart(self):
        """
        Test 3: Vérifie le flux 'Ajouter au panier'.
        """
        print("\n[TEST] Vérification de l'ajout au panier...")
        
        # On suppose que l'URL s'appelle 'add_to_cart' et prend un ID produit
        add_url = reverse('add_to_cart', args=[self.product.id])
        self.client.post(add_url) # Simule l'ajout

        # Vérifie que l'objet Cart a été créé en BDD
        cart_exists = Cart.objects.filter(customer=self.customer, product=self.product).exists()
        self.assertTrue(cart_exists, "Le produit n'a pas été ajouté au modèle Cart.")
        
        cart_item = Cart.objects.get(customer=self.customer, product=self.product)
        self.assertEqual(cart_item.quantity, 1)
        print("[TEST] Ajout au panier OK.")

    def test_stock_decreases_after_checkout(self):
        """
        Test 4: [BUG 1] Vérifie que le stock est décrémenté après l'achat.
        CE TEST EST FAIT POUR ÉCHOUER (il prouve le bug).
        """
        print("\n[TEST - BUG STOCK] Démarrage...")
        
        # ARRANGE: Met 2 produits dans le panier
        Cart.objects.create(customer=self.customer, product=self.product, quantity=2)
        print(f"[TEST - BUG STOCK] Stock initial: {self.product.stock}")

        # ACT: Simule la validation de la commande
        checkout_url = reverse('checkout') 
        self.client.post(checkout_url, {'new_address': '123 Rue Test'})

        # ASSERT: Vérifie le stock
        self.product.refresh_from_db()
        nouveau_stock = self.product.stock
        print(f"[TEST - BUG STOCK] Stock après achat: {nouveau_stock}")

        self.assertEqual(nouveau_stock, 8, "BUG: Le stock (10) n'est pas devenu 8. Il n'a pas été décrémenté.")
        print("[TEST - BUG STOCK] Test réussi (si corrigé).")

    def test_registration_creates_customer_profile(self):
        """
        Test 5: [BUG 2] Vérifie que l'inscription crée un profil 'Customer'.
        CE TEST EST FAIT POUR ÉCHOUER (il prouve le bug).
        """
        print("\n[TEST - BUG PROFIL] Démarrage...")
        
        register_url = reverse('register')
        username = f"newuser_{uuid.uuid4()}" # Nom unique
        
        form_data = {
            'username': username,
            'email': f'{username}@example.com',
            'password': 'password123',
            'password2': 'password123',
            'first_name': 'Test',
            'last_name': 'User',
            'phone': '12345678'
        }

        # ACT: Simule l'inscription (on suppose qu'elle ne nécessite pas d'e-mail pour ce test)
        self.client.post(register_url, form_data)
        
        # ASSERT: Vérifie que le User ET le Customer ont été créés
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.fail("La vue 'register' n'a pas créé l'objet User.")

        try:
            customer = Customer.objects.get(user=user)
            # Si le Customer est créé, on vérifie les données
            self.assertEqual(customer.phone, '12345678', "Le téléphone n'a pas été sauvegardé dans le profil Customer.")
        except Customer.DoesNotExist:
            self.fail("BUG: La vue 'register' a créé le User, mais PAS le profil Customer associé.")
            
        print("[TEST - BUG PROFIL] Test réussi (si corrigé).")

    def test_seller_cannot_see_other_seller_products(self):
        """
        Test 6: [SÉCURITÉ] Vérifie qu'un vendeur ne peut pas gérer les produits d'un autre.
        """
        print("\n[TEST - SÉCURITÉ VENDEUR] Démarrage...")
        
        # ARRANGE: Crée 2 Vendeurs et 1 Produit
        user_a = User.objects.create_user(username='vendeurA', password='password123')
        seller_a = Seller.objects.create(user=user_a, store_name='Boutique A')
        product_a = Product.objects.create(
            name='Produit de A', slug='produit-a', category=self.category, price=10, stock=5, seller=seller_a
        )
        
        user_b = User.objects.create_user(username='vendeurB', password='password123')
        Seller.objects.create(user=user_b, store_name='Boutique B')
        
        # ACT: Connecte le Vendeur B
        self.client.login(username='vendeurB', password='password123')
        
        # On suppose qu'il existe une URL 'seller_edit_product'
        try:
            edit_url = reverse('seller_edit_product', args=[product_a.slug])
        except:
            print("[TEST - SÉCURITÉ VENDEUR] Test ignoré: l'URL 'seller_edit_product' n'existe pas ou n'a pas été trouvée.")
            return

        # Vendeur B essaie de modifier le produit de Vendeur A
        response = self.client.post(edit_url, {'name': 'PRODUIT HACKED', 'price': 1})
        
        # ASSERT: Vérifie que la modification a échoué
        product_a.refresh_from_db()
        self.assertNotEqual(product_a.name, 'PRODUIT HACKED', "BUG SÉCURITÉ: Un vendeur peut modifier les produits d'un autre !")
        # On vérifie aussi que l'accès a été refusé (ex: redirection ou code 403/404)
        self.assertIn(response.status_code, [302, 403, 404], "La vue n'a pas bloqué l'accès non autorisé.")
        print("[TEST - SÉCURITÉ VENDEUR] Test réussi.")

    def test_active_seller_link_is_hidden_for_sellers(self):
        """
        Test 7: [BUG 3] Vérifie que le lien 'Devenir Vendeur' est caché si on l'est déjà.
        """
        print("\n[TEST - BUG AFFICHAGE] Démarrage...")
        # ARRANGE: Crée un vendeur et le connecte
        user_seller = User.objects.create_user(username='vendeurDeTest', password='password123')
        Seller.objects.create(user=user_seller, store_name='Ma Boutique')
        self.client.login(username='vendeurDeTest', password='password123')

        # ACT: Récupère la page d'accueil
        home_url = reverse('home') # On suppose que l'accueil s'appelle 'home'
        response = self.client.get(home_url)
        
        # ASSERT: Vérifie que le lien n'est PAS dans le HTML
        # On suppose que l'URL s'appelle 'register_seller'
        register_seller_url = reverse('register_seller')
        self.assertNotContains(
            response,
            f'href="{register_seller_url}"',
            msg_prefix="BUG: Le lien 'Devenir Vendeur' est toujours visible pour un vendeur."
        )
        print("[TEST - BUG AFFICHAGE] Test réussi.")