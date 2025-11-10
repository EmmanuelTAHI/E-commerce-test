from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from mon_app_ecommerce.models import (
    Category,
    Product,
    Customer,
    Seller,
    Cart,
    Order,
    OrderItem,
    Address
)
import json

class EcommerceIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Créer un utilisateur et un client
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.customer = Customer.objects.create(
            user=self.user,
            phone='1234567890'
        )
        
        # Créer un vendeur
        self.seller_user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='sellerpass123'
        )
        self.seller = Seller.objects.create(
            user=self.seller_user,
            store_name='Test Store',
            phone='0987654321',
            email='seller@example.com',
            address='123 Seller St',
            city='Test City'
        )
        
        # Créer une catégorie
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics',
            description='Electronic devices'
        )
        
        # Créer des produits
        self.product1 = Product.objects.create(
            name='Smartphone',
            slug='smartphone',
            description='A test smartphone',
            price=1000,
            category=self.category,
            seller=self.seller,
            stock=10
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

    def test_complete_purchase_flow(self):
        """Test the complete flow from browsing products to completing a purchase"""
        
        # 1. Connexion utilisateur
        login_successful = self.client.login(
            username='testuser',
            password='testpass123'
        )
        self.assertTrue(login_successful)
        
        # 2. Parcourir la liste des produits
        response = self.client.get(reverse('product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(len(response.context['products']) > 0)
        
        # 3. Voir les détails d'un produit
        response = self.client.get(
            reverse('product_detail', kwargs={'slug': self.product1.slug})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['product'], self.product1)
        
        # 4. Ajouter des produits au panier
        response = self.client.get(
            reverse('add_to_cart', kwargs={'product_id': self.product1.id})
        )
        self.assertEqual(response.status_code, 302)
        
        response = self.client.get(
            reverse('add_to_cart', kwargs={'product_id': self.product2.id})
        )
        self.assertEqual(response.status_code, 302)
        
        # 5. Vérifier le panier
        response = self.client.get(reverse('cart'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['cart_items']), 2)
        
        # 6. Passer à la caisse
        response = self.client.get(reverse('checkout'))
        self.assertEqual(response.status_code, 200)
        
        # 7. Soumettre la commande
        shipping_data = {
            'street_address': '123 Test St',
            'city': 'Test City',
            'state': 'Test State',
            'postal_code': '12345',
            'country': "Côte d'Ivoire",
            'payment_method': 'card'  # Ajout du mode de paiement
        }
        
        # Créer une adresse pour le client
        Address.objects.create(
            customer=self.customer,
            street_address=shipping_data['street_address'],
            city=shipping_data['city'],
            state=shipping_data['state'],
            postal_code=shipping_data['postal_code'],
            country=shipping_data['country'],
            is_default=True
        )
        
        response = self.client.post(reverse('checkout'), shipping_data)
        self.assertEqual(response.status_code, 302)
        
        # 8. Vérifier que la commande a été créée
        order = Order.objects.filter(customer=self.customer).last()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, 'pending')
        self.assertEqual(
            order.total_amount,
            self.product1.price + self.product2.price
        )
        
        # 9. Vérifier les éléments de la commande
        order_items = OrderItem.objects.filter(order=order)
        self.assertEqual(order_items.count(), 2)
        
        # 10. Vérifier que le panier est vide après la commande
        cart_items = Cart.objects.filter(customer=self.customer)
        self.assertEqual(cart_items.count(), 0)

class SellerIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        
        # Créer un vendeur
        self.seller_user = User.objects.create_user(
            username='seller',
            email='seller@example.com',
            password='sellerpass123'
        )
        self.seller = Seller.objects.create(
            user=self.seller_user,
            store_name='Test Store',
            phone='0987654321',
            email='seller@example.com',
            address='123 Seller St',
            city='Test City'
        )
        
        # Créer une catégorie
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )

    def test_seller_product_management(self):
        """Test the complete flow of a seller managing their products"""
        
        # 1. Connexion vendeur
        login_successful = self.client.login(
            username='seller',
            password='sellerpass123'
        )
        self.assertTrue(login_successful)
        
        # 2. Accéder au tableau de bord vendeur
        response = self.client.get(reverse('seller_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # 3. Ajouter un nouveau produit
        product_data = {
            'name': 'New Product',
            'description': 'A new test product',
            'price': 1500,
            'category': self.category.id,
            'stock': 15,
            'slug': 'new-product'  # Ajout du slug requis
        }
        response = self.client.post(reverse('add_product_by_seller'), product_data)
        self.assertEqual(response.status_code, 302)
        
        # 4. Vérifier que le produit a été créé
        new_product = Product.objects.filter(
            name='New Product',
            seller=self.seller
        ).first()
        self.assertIsNotNone(new_product)
        
        # 5. Modifier le produit
        edit_data = {
            'name': 'Updated Product',
            'description': 'An updated test product',
            'price': 2000,
            'category': self.category.id,
            'stock': 20
        }
        response = self.client.post(
            reverse('edit_product_by_seller', kwargs={'product_id': new_product.id}),
            edit_data
        )
        self.assertEqual(response.status_code, 302)
        
        # 6. Vérifier que le produit a été mis à jour
        updated_product = Product.objects.get(id=new_product.id)
        self.assertEqual(updated_product.name, 'Updated Product')
        self.assertEqual(updated_product.price, 2000)
        self.assertEqual(updated_product.stock, 20)