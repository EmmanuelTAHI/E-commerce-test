from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from .models import Product, Category, Customer, Cart, Order

class StockIntegrationTest(TestCase):

    def setUp(self):
        """ Préparation d'un faux environnement (client, produit) """
        self.category = Category.objects.create(name='Test Cat', slug='test-cat')
        self.product = Product.objects.create(
            name='Produit Stock Test',
            slug='produit-stock-test',
            category=self.category,
            price=1000,
            stock=10  # <-- Stock initial
        )
        self.user = User.objects.create_user(username='testuser', password='password123')
        # On lie l'utilisateur au modèle Customer
        self.customer = Customer.objects.create(user=self.user)
        
        self.client = Client()
        self.client.login(username='testuser', password='password123')

    def test_stock_decreases_after_checkout(self):
        """
        Teste si la vue 'checkout' décrémente le stock du produit.
        CE TEST VA ÉCHOUER (ce qui prouve ton bug).
        """
        print("\n[TEST D'INTÉGRATION] Démarrage...")
        
        # ARRANGE: On crée un VRAI panier dans la BDD pour ce client
        # (Au lieu de simuler une session)
        Cart.objects.create(
            customer=self.customer,
            product=self.product,
            quantity=2
        )
        print(f"[TEST D'INTÉGRATION] Stock initial: {self.product.stock}")

        # ACT: On simule l'envoi du formulaire de 'checkout'
        # (On suppose que ton URL s'appelle 'checkout')
        checkout_url = reverse('checkout') 
        self.client.post(checkout_url, {'new_address': '123 Rue Test'})

        # ASSERT: On recharge le produit depuis la BDD
        self.product.refresh_from_db()
        nouveau_stock = self.product.stock
        print(f"[TEST D'INTÉGRATION] Stock après achat: {nouveau_stock}")

        # Le test vérifie si 10 est devenu 8.
        self.assertEqual(nouveau_stock, 8, "BUG: Le stock n'a pas été décrémenté après la commande.")
        print("[TEST D'INTÉGRATION] Test réussi.")