from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core import mail
from decimal import Decimal
from mon_app_ecommerce.models import (
    Category,
    Product,
    Customer,
    Seller,
    Cart,
    Order,
    OrderItem,
    Address,
    Review,
    EmailVerification
)

class FullEcommerceIntegrationTest(TestCase):
    def setUp(self):
        # Création des données de base
        self.client = Client()
        
        # Création des utilisateurs
        self.customer_user = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='testpass123',
            first_name='Test',
            last_name='Customer'
        )
        self.customer = Customer.objects.create(
            user=self.customer_user,
            phone='1234567890'
        )
        
        self.seller_user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='sellerpass123'
        )
        self.seller = Seller.objects.create(
            user=self.seller_user,
            store_name='Test Store',
            store_description='A test store',
            phone='0987654321',
            email='seller@example.com',
            address='123 Seller St',
            city='Test City',
            country="Côte d'Ivoire"
        )
        
        # Création des catégories
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices'
        )
        
        # Création des produits
        self.product1 = Product.objects.create(
            name='Smartphone',
            slug='smartphone',
            description='A test smartphone',
            price=1000,
            category=self.category,
            seller=self.seller,
            stock=10,
            is_featured=True
        )
        
        self.product2 = Product.objects.create(
            name='Laptop',
            slug='laptop',
            description='A test laptop',
            price=2000,
            category=self.category,
            seller=self.seller,
            stock=5
        )

    def test_basic_user_workflow(self):
        """Test le flux de base d'un utilisateur"""
        # 1. Accès à la page d'accueil
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        
        # 2. Navigation dans les produits
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        
        # 3. Consultation d'un produit
        response = self.client.get(
            reverse('product_detail', kwargs={'slug': self.product1.slug})
        )
        self.assertEqual(response.status_code, 200)
        
        # 4. Connexion utilisateur
        login_successful = self.client.login(
            username='customer',
            password='testpass123'
        )
        self.assertTrue(login_successful)
        
        # 5. Accès au panier
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)

    def test_seller_product_management(self):
        """Test la gestion des produits par un vendeur"""
        # 1. Vérification des produits initiaux
        self.assertEqual(
            Product.objects.filter(seller=self.seller).count(),
            2  # les deux produits créés dans setUp
        )
        
        # 2. Vérification des statistiques du vendeur
        total_products = self.seller.get_total_products()
        active_products = self.seller.get_active_products()
        self.assertEqual(total_products, 2)
        self.assertEqual(active_products, 2)
        
        # 3. Désactivation d'un produit
        self.product1.is_active = False
        self.product1.save()
        
        # 4. Vérification après désactivation
        self.assertEqual(self.seller.get_active_products(), 1)
        
        # 5. Vérification de l'affichage des produits
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        products_in_list = response.context['products']
        self.assertNotIn(self.product1, products_in_list)  # Produit désactivé
        self.assertIn(self.product2, products_in_list)     # Produit actif

    def test_cart_workflow(self):
        """Test le processus du panier"""
        # 1. Connexion client
        self.client.login(username='customer', password='testpass123')
        
        # 2. Ajouter un produit au panier
        response = self.client.get(
            reverse('add_to_cart', kwargs={'product_id': self.product1.id})
        )
        self.assertEqual(response.status_code, 302)
        
        # 3. Vérifier le panier
        cart_item = Cart.objects.get(product=self.product1)
        self.assertEqual(cart_item.quantity, 1)
        self.assertEqual(cart_item.total_price, self.product1.price)
        
        # 4. Mettre à jour la quantité
        response = self.client.post(
            reverse('update_cart', kwargs={'cart_id': cart_item.id}),
            {'quantity': 2}
        )
        self.assertEqual(response.status_code, 302)
        
        # 5. Vérifier la mise à jour
        cart_item.refresh_from_db()
        self.assertEqual(cart_item.quantity, 2)
        self.assertEqual(cart_item.total_price, self.product1.price * 2)

    def test_product_review_workflow(self):
        """Test le processus d'ajout d'avis sur un produit"""
        # 1. Connexion client
        self.client.login(username='customer', password='testpass123')
        
        # 2. Ajouter un avis
        review_data = {
            'rating': 5,
            'comment': 'Excellent product!'
        }
        response = self.client.post(
            reverse('add_review', kwargs={'product_id': self.product1.id}),
            review_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 3. Vérifier l'avis
        review = Review.objects.get(
            product=self.product1,
            customer=self.customer
        )
        self.assertEqual(review.rating, 5)
        self.assertEqual(review.comment, 'Excellent product!')
        
        # 4. Vérifier la moyenne des avis
        response = self.client.get(
            reverse('product_detail', kwargs={'slug': self.product1.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['avg_rating'],
            5.0
        )

    def test_search_and_filter(self):
        """Test les fonctionnalités de recherche et de filtrage"""
        # 1. Recherche par mot-clé
        response = self.client.get(
            reverse('product_list'),
            {'q': 'smartphone'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.product1, response.context['products'])
        self.assertNotIn(self.product2, response.context['products'])
        
        # 2. Filtrage par catégorie
        response = self.client.get(
            reverse('product_list'),
            {'category': self.category.slug}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.product1, response.context['products'])
        self.assertIn(self.product2, response.context['products'])
        
        # 3. Recherche combinée
        response = self.client.get(
            reverse('product_list'),
            {
                'q': 'laptop',
                'category': self.category.slug
            }
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(self.product1, response.context['products'])
        self.assertIn(self.product2, response.context['products'])