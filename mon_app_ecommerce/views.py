from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from django.db.models import Q, Avg, Sum, Count
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.text import slugify
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.mail import send_mail
from datetime import timedelta
import random
import string
import secrets
import logging

logger = logging.getLogger(__name__)
from .models import (
    Product,
    Category,
    Customer,
    Seller,
    Cart,
    Order,
    OrderItem,
    Review,
    Address,
    EmailVerification,
)


# Helper function to get or create customer
def get_customer(user):
    customer, created = Customer.objects.get_or_create(user=user)
    return customer


def home(request):
    try:
        featured_products = Product.objects.filter(is_featured=True, is_active=True)[:8]
        categories = Category.objects.all()[:6]
        context = {
            "featured_products": featured_products,
            "categories": categories,
        }
        return render(request, "mon_app_ecommerce/home.html", context)
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        messages.error(
            request, "Une erreur est survenue lors du chargement de la page d'accueil."
        )
        context = {
            "featured_products": [],
            "categories": [],
        }
        return render(request, "mon_app_ecommerce/home.html", context)


def product_list(request):
    try:
        category_slug = request.GET.get("category")
        query = request.GET.get("q", "")

        products = Product.objects.filter(is_active=True)

        if category_slug:
            products = products.filter(category__slug=category_slug)

        if query:
            products = products.filter(
                Q(name__icontains=query) | Q(description__icontains=query)
            )

        try:
            paginator = Paginator(products, 12)
            page_number = request.GET.get("page")
            page_obj = paginator.get_page(page_number)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.get_page(1)

        categories = Category.objects.all()

        context = {
            "products": page_obj,
            "categories": categories,
            "selected_category": category_slug,
            "query": query,
        }
        return render(request, "mon_app_ecommerce/product_list.html", context)
    except Exception as e:
        logger.error(f"Error in product_list view: {str(e)}")
        messages.error(
            request, "Une erreur est survenue lors du chargement des produits."
        )
        context = {
            "products": [],
            "categories": [],
            "selected_category": None,
            "query": "",
        }
        return render(request, "mon_app_ecommerce/product_list.html", context)


def product_detail(request, slug):
    try:
        product = get_object_or_404(Product, slug=slug, is_active=True)
        reviews = Review.objects.filter(product=product)
        avg_rating = reviews.aggregate(Avg("rating"))["rating__avg"] or 0

        # Related products
        try:
            related_products = Product.objects.filter(
                category=product.category, is_active=True
            ).exclude(id=product.id)[:4]
        except Exception:
            related_products = []

        context = {
            "product": product,
            "reviews": reviews,
            "avg_rating": avg_rating,
            "related_products": related_products,
        }
        return render(request, "mon_app_ecommerce/product_detail.html", context)
    except Exception as e:
        logger.error(f"Error in product_detail view: {str(e)}")
        messages.error(
            request,
            "Une erreur est survenue lors du chargement des détails du produit.",
        )
        return redirect("product_list")


@login_required
def add_to_cart(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id, is_active=True)
        customer = get_customer(request.user)

        try:
            cart_item, created = Cart.objects.get_or_create(
                customer=customer, product=product, defaults={"quantity": 1}
            )

            if not created:
                cart_item.quantity += 1
                cart_item.save()

            messages.success(request, f"{product.name} ajouté au panier!")
        except Exception as e:
            logger.error(f"Error adding to cart: {str(e)}")
            messages.error(
                request, "Une erreur est survenue lors de l'ajout au panier."
            )

        return redirect("cart")
    except Exception as e:
        logger.error(f"Error in add_to_cart view: {str(e)}")
        messages.error(request, "Une erreur est survenue.")
        return redirect("product_list")


@login_required
def cart(request):
    try:
        customer = get_customer(request.user)
        cart_items = Cart.objects.filter(customer=customer)

        try:
            total = sum(item.total_price for item in cart_items)
        except Exception:
            total = 0

        context = {
            "cart_items": cart_items,
            "total": total,
        }
        return render(request, "mon_app_ecommerce/cart.html", context)
    except Exception as e:
        logger.error(f"Error in cart view: {str(e)}")
        messages.error(request, "Une erreur est survenue lors du chargement du panier.")
        context = {
            "cart_items": [],
            "total": 0,
        }
        return render(request, "mon_app_ecommerce/cart.html", context)


@login_required
def update_cart(request, cart_id):
    try:
        customer = get_customer(request.user)
        cart_item = get_object_or_404(Cart, id=cart_id, customer=customer)

        try:
            quantity = int(request.POST.get("quantity", 1))
        except (ValueError, TypeError):
            quantity = 1

        if quantity <= 0:
            try:
                cart_item.delete()
                messages.success(request, "Article retiré du panier!")
            except Exception as e:
                logger.error(f"Error deleting cart item: {str(e)}")
                messages.error(request, "Erreur lors de la suppression.")
        else:
            try:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Panier mis à jour!")
            except Exception as e:
                logger.error(f"Error updating cart: {str(e)}")
                messages.error(request, "Erreur lors de la mise à jour.")

        return redirect("cart")
    except Exception as e:
        logger.error(f"Error in update_cart view: {str(e)}")
        messages.error(request, "Une erreur est survenue.")
        return redirect("cart")


@login_required
def remove_from_cart(request, cart_id):
    try:
        customer = get_customer(request.user)
        cart_item = get_object_or_404(Cart, id=cart_id, customer=customer)

        try:
            cart_item.delete()
            messages.success(request, "Article retiré du panier!")
        except Exception as e:
            logger.error(f"Error removing from cart: {str(e)}")
            messages.error(request, "Erreur lors de la suppression.")

        return redirect("cart")
    except Exception as e:
        logger.error(f"Error in remove_from_cart view: {str(e)}")
        messages.error(request, "Une erreur est survenue.")
        return redirect("cart")


@login_required
def checkout(request):
    try:
        customer = get_customer(request.user)
        cart_items = Cart.objects.filter(customer=customer)

        if not cart_items.exists():
            messages.warning(request, "Votre panier est vide!")
            return redirect("cart")

        addresses = customer.addresses.all()

        if request.method == "POST":
            try:
                address_id = request.POST.get("address")
                notes = request.POST.get("notes", "")

                if address_id:
                    try:
                        address = get_object_or_404(
                            Address, id=address_id, customer=customer
                        )
                        shipping_address = f"{address.street_address}, {address.city}, {address.state} {address.postal_code}, {address.country}"
                    except Exception as e:
                        logger.error(f"Error getting address: {str(e)}")
                        messages.error(
                            request, "Erreur lors de la récupération de l'adresse."
                        )
                        return redirect("checkout")
                else:
                    shipping_address = request.POST.get("new_address")
                    if not shipping_address:
                        messages.error(
                            request, "Veuillez fournir une adresse de livraison!"
                        )
                        return redirect("checkout")

                # Create order with pending payment status
                try:
                    order_number = "".join(
                        random.choices(string.ascii_uppercase + string.digits, k=10)
                    )
                    total_amount = sum(item.total_price for item in cart_items)
                except Exception as e:
                    logger.error(f"Error calculating total: {str(e)}")
                    messages.error(request, "Erreur lors du calcul du total.")
                    return redirect("checkout")

                try:
                    with transaction.atomic():
                        order = Order.objects.create(
                            customer=customer,
                            order_number=order_number,
                            total_amount=total_amount,
                            shipping_address=shipping_address,
                            notes=notes,
                            payment_status="pending",
                            status="pending",
                        )

                        for cart_item in cart_items:
                            OrderItem.objects.create(
                                order=order,
                                product=cart_item.product,
                                quantity=cart_item.quantity,
                                price=cart_item.product.final_price,
                            )
                except Exception as e:
                    logger.error(f"Error creating order: {str(e)}")
                    messages.error(
                        request,
                        "Erreur lors de la création de la commande. Veuillez réessayer.",
                    )
                    return redirect("checkout")

                return redirect("payment", order_id=order.id)
            except Exception as e:
                logger.error(f"Error in checkout POST: {str(e)}")
                messages.error(
                    request,
                    "Une erreur est survenue lors du traitement de la commande.",
                )
                return redirect("checkout")

        try:
            total = sum(item.total_price for item in cart_items)
        except Exception:
            total = 0

        context = {
            "cart_items": cart_items,
            "total": total,
            "addresses": addresses,
        }
        return render(request, "mon_app_ecommerce/checkout.html", context)
    except Exception as e:
        logger.error(f"Error in checkout view: {str(e)}")
        messages.error(request, "Une erreur est survenue.")
        return redirect("cart")


@login_required
def payment(request, order_id):
    customer = get_customer(request.user)
    order = get_object_or_404(Order, id=order_id, customer=customer)

    # Only allow payment if order payment is pending
    if order.payment_status != "pending":
        messages.warning(request, "This order has already been processed!")
        return redirect("order_detail", order_id=order.id)

    if request.method == "POST":
        payment_method = request.POST.get("payment_method", "").strip()

        if not payment_method:
            messages.error(request, "Veuillez sélectionner une méthode de paiement!")
            return redirect("payment", order_id=order.id)

        # Handle Cash on Delivery (Paiement à la livraison)
        if payment_method == "Cash on Delivery":
            # For cash on delivery, payment is marked as pending until delivery
            order.payment_status = "pending"  # Will be paid on delivery
            order.status = "processing"
            order.payment_method = "Paiement à la livraison"
            order.save()

            # Delete cart items
            Cart.objects.filter(customer=customer).delete()

            # Send confirmation email for order (not payment since it's on delivery)
            try:
                from django.utils.html import strip_tags

                customer_name = customer.user.first_name or customer.user.username
                shipping_addr = order.shipping_address.replace("\n", "<br>")

                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #2196F3;">📦 Commande confirmée !</h2>

                        <p>Bonjour {customer_name},</p>

                        <p>Votre commande <strong>#{order.order_number}</strong> a été confirmée avec le paiement à la livraison !</p>

                        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Détails de la commande :</h3>
                            <p><strong>Numéro de commande :</strong> {order.order_number}</p>
                            <p><strong>Montant total :</strong> {order.total_amount} FCFA</p>
                            <p><strong>Méthode de paiement :</strong> Paiement à la livraison</p>
                            <p><strong>Date de commande :</strong> {order.created_at.strftime('%d/%m/%Y à %H:%M')}</p>
                        </div>

                        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Adresse de livraison :</h3>
                            <p>{shipping_addr}</p>
                        </div>

                        <h3>Articles commandés :</h3>
                        <ul style="list-style: none; padding: 0;">
                """

                for item in order.items.all():
                    html_message += f"""
                            <li style="padding: 10px; border-bottom: 1px solid #ddd;">
                                <strong>{item.product.name}</strong> -
                                Quantité: {item.quantity} -
                                Prix: {item.price} FCFA -
                                Sous-total: {item.subtotal} FCFA
                            </li>
                    """

                html_message += f"""
                        </ul>

                        <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-radius: 5px;">
                            <p style="margin: 0;"><strong>💡 Important :</strong></p>
                            <p style="margin: 5px 0;">Vous paierez {order.total_amount} FCFA en espèces ou par mobile money au moment de la livraison.</p>
                            <p style="margin: 5px 0;">Le livreur vous contactera avant la livraison pour confirmer l'adresse et le moment de la livraison.</p>
                        </div>

                        <p style="margin-top: 30px;">Merci pour votre achat !</p>

                        <p>Cordialement,<br><strong>L'équipe Shop</strong></p>
                    </div>
                </body>
                </html>
                """

                plain_message = strip_tags(html_message)

                send_mail(
                    subject=f"Confirmation de commande #{order.order_number} - Paiement à la livraison",
                    message=plain_message,
                    from_email=None,
                    recipient_list=[customer.user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                messages.warning(
                    request,
                    f"Commande confirmée mais échec d'envoi de l'email: {str(e)}",
                )

            messages.success(
                request,
                f"Commande #{order.order_number} confirmée ! Paiement à la livraison. Vous recevrez un email de confirmation.",
            )
            return redirect("order_detail", order_id=order.id)

        # Handle Credit Card payment
        elif payment_method == "Credit Card":
            card_number = (
                request.POST.get("card_number", "")
                .strip()
                .replace(" ", "")
                .replace("-", "")
            )
            card_name = request.POST.get("card_name", "").strip()
            expiry_month = request.POST.get("expiry_month", "").strip()
            expiry_year = request.POST.get("expiry_year", "").strip()
            cvv = request.POST.get("cvv", "").strip()

            # Validation for credit card
            if (
                not card_number
                or not card_name
                or not expiry_month
                or not expiry_year
                or not cvv
            ):
                messages.error(
                    request, "Veuillez remplir tous les champs de la carte de crédit!"
                )
                return redirect("payment", order_id=order.id)

            # Simulation de paiement - pour la démo, on accepte tous les paiements sauf si le numéro commence par '0' (simulation d'erreur)
            payment_successful = True
            if card_number.startswith("0"):
                payment_successful = False

        # Handle Mobile Money payments (Orange Money, Moov Money, MTN Money, Wave)
        elif payment_method in ["Orange Money", "Moov Money", "MTN Money", "Wave"]:
            phone_number = request.POST.get("phone_number", "").strip()

            # Validation for mobile money
            if not phone_number:
                messages.error(request, "Veuillez entrer votre numéro de téléphone!")
                return redirect("payment", order_id=order.id)

            # Simulation: mobile money payment is always successful (except if phone starts with 0)
            payment_successful = True
            if phone_number.startswith("0") and len(phone_number) == 1:
                payment_successful = False

        else:
            messages.error(request, "Méthode de paiement invalide!")
            return redirect("payment", order_id=order.id)

        # Process successful payment (for Credit Card and Mobile Money)
        if payment_successful:
            # Payment successful - update order
            order.payment_status = "paid"
            order.status = "processing"
            order.payment_method = payment_method
            order.payment_date = timezone.now()
            order.save()

            # Delete cart items after successful payment
            Cart.objects.filter(customer=customer).delete()

            # Send confirmation email
            try:
                from django.core.mail import send_mail
                from django.template.loader import render_to_string
                from django.utils.html import strip_tags

                subject = f"Confirmation de commande #{order.order_number}"

                # Create email content
                customer_name = customer.user.first_name or customer.user.username
                payment_date_str = order.payment_date.strftime("%d/%m/%Y à %H:%M")
                shipping_addr = order.shipping_address.replace("\n", "<br>")

                html_message = f"""
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <h2 style="color: #4CAF50;">✅ Paiement confirmé !</h2>

                        <p>Bonjour {customer_name},</p>

                        <p>Nous avons le plaisir de vous confirmer que votre paiement pour la commande <strong>#{order.order_number}</strong> a été effectué avec succès !</p>

                        <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Détails de la commande :</h3>
                            <p><strong>Numéro de commande :</strong> {order.order_number}</p>
                            <p><strong>Montant total :</strong> {order.total_amount} FCFA</p>
                            <p><strong>Méthode de paiement :</strong> {order.payment_method}</p>
                            <p><strong>Date de paiement :</strong> {payment_date_str}</p>
                        </div>

                        <div style="background-color: #e3f2fd; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <h3 style="margin-top: 0;">Adresse de livraison :</h3>
                            <p>{shipping_addr}</p>
                        </div>

                        <h3>Articles commandés :</h3>
                        <ul style="list-style: none; padding: 0;">
                """

                for item in order.items.all():
                    html_message += f"""
                            <li style="padding: 10px; border-bottom: 1px solid #ddd;">
                                <strong>{item.product.name}</strong> -
                                Quantité: {item.quantity} -
                                Prix: {item.price} FCFA -
                                Sous-total: {item.subtotal} FCFA
                            </li>
                    """

                html_message += f"""
                        </ul>

                        <div style="margin-top: 20px; padding: 15px; background-color: #fff3cd; border-radius: 5px;">
                            <p style="margin: 0;"><strong>💡 Prochaine étape :</strong></p>
                            <p style="margin: 5px 0;">Votre commande est maintenant en cours de traitement. Vous recevrez un email de confirmation lorsque votre commande sera expédiée.</p>
                            <p style="margin: 5px 0;">Vous pouvez suivre l'état de votre commande sur votre compte.</p>
                        </div>

                        <p style="margin-top: 30px;">Merci pour votre achat !</p>

                        <p>Cordialement,<br><strong>L'équipe Shop</strong></p>
                    </div>
                </body>
                </html>
                """

                plain_message = strip_tags(html_message)

                send_mail(
                    subject=subject,
                    message=plain_message,
                    from_email=None,  # Uses DEFAULT_FROM_EMAIL
                    recipient_list=[customer.user.email],
                    html_message=html_message,
                    fail_silently=False,
                )
            except Exception as e:
                # Email failed but payment is successful
                messages.warning(
                    request,
                    f"Payment successful but failed to send confirmation email: {str(e)}",
                )

            messages.success(
                request,
                f"Payment successful! Order #{order.order_number} confirmed. A confirmation email has been sent.",
            )
            return redirect("order_detail", order_id=order.id)
        else:
            # Payment failed
            order.payment_status = "failed"
            order.save()
            messages.error(
                request, "Payment failed! Please check your card details and try again."
            )
            return redirect("payment", order_id=order.id)

    context = {
        "order": order,
    }
    return render(request, "mon_app_ecommerce/payment.html", context)


@login_required
def order_history(request):
    try:
        customer = get_customer(request.user)
        orders = Order.objects.filter(customer=customer).order_by("-created_at")

        context = {
            "orders": orders,
        }
        return render(request, "mon_app_ecommerce/order_history.html", context)
    except Exception as e:
        logger.error(f"Error in order_history view: {str(e)}")
        messages.error(
            request,
            "Une erreur est survenue lors du chargement de l'historique des commandes.",
        )
        context = {
            "orders": [],
        }
        return render(request, "mon_app_ecommerce/order_history.html", context)


@login_required
def order_detail(request, order_id):
    try:
        customer = get_customer(request.user)
        order = get_object_or_404(Order, id=order_id, customer=customer)

        context = {
            "order": order,
        }
        return render(request, "mon_app_ecommerce/order_detail.html", context)
    except Exception as e:
        logger.error(f"Error in order_detail view: {str(e)}")
        messages.error(
            request,
            "Une erreur est survenue lors du chargement des détails de la commande.",
        )
        return redirect("order_history")


@login_required
def account(request):
    try:
        customer = get_customer(request.user)
        addresses = customer.addresses.all()

        if request.method == "POST":
            if "add_address" in request.POST:
                try:
                    Address.objects.create(
                        customer=customer,
                        street_address=request.POST.get("street_address"),
                        city=request.POST.get("city"),
                        state=request.POST.get("state"),
                        postal_code=request.POST.get("postal_code"),
                        country=request.POST.get("country", "United States"),
                        is_default=request.POST.get("is_default") == "on",
                    )
                    messages.success(request, "Adresse ajoutée!")
                except Exception as e:
                    logger.error(f"Error adding address: {str(e)}")
                    messages.error(request, "Erreur lors de l'ajout de l'adresse.")
                return redirect("account")

            if "update_profile" in request.POST:
                try:
                    user = request.user
                    user.first_name = request.POST.get("first_name", user.first_name)
                    user.last_name = request.POST.get("last_name", user.last_name)
                    user.email = request.POST.get("email", user.email)
                    user.save()

                    customer.phone = request.POST.get("phone", customer.phone)
                    customer.save()

                    messages.success(request, "Profil mis à jour!")
                except Exception as e:
                    logger.error(f"Error updating profile: {str(e)}")
                    messages.error(request, "Erreur lors de la mise à jour du profil.")
                return redirect("account")

        context = {
            "customer": customer,
            "addresses": addresses,
        }
        return render(request, "mon_app_ecommerce/account.html", context)
    except Exception as e:
        logger.error(f"Error in account view: {str(e)}")
        messages.error(request, "Une erreur est survenue.")
        return redirect("home")


def register(request):
    try:
        if request.method == "POST":
            try:
                username = request.POST.get("username", "").strip()
                email = request.POST.get("email", "").strip()
                password = request.POST.get("password", "")
                password2 = request.POST.get("password2", "")
                first_name = request.POST.get("first_name", "").strip()
                last_name = request.POST.get("last_name", "").strip()

                # Validation
                if not username or not email or not password:
                    messages.error(request, "Tous les champs sont obligatoires!")
                    return redirect("register")

                if password != password2:
                    messages.error(request, "Les mots de passe ne correspondent pas!")
                    return redirect("register")

                if len(password) < 8:
                    messages.error(
                        request, "Le mot de passe doit contenir au moins 8 caractères!"
                    )
                    return redirect("register")

                from django.contrib.auth.models import User

                # Check if username already exists
                try:
                    if User.objects.filter(username=username).exists():
                        messages.error(request, "Ce nom d'utilisateur existe déjà!")
                        return redirect("register")
                except Exception as e:
                    logger.error(f"Error checking username: {str(e)}")
                    messages.error(
                        request, "Erreur lors de la vérification du nom d'utilisateur."
                    )
                    return redirect("register")

                # Check if email already exists
                try:
                    if User.objects.filter(email=email).exists():
                        messages.error(request, "Cet email est déjà enregistré!")
                        return redirect("register")
                except Exception as e:
                    logger.error(f"Error checking email: {str(e)}")
                    messages.error(
                        request, "Erreur lors de la vérification de l'email."
                    )
                    return redirect("register")

                # Generate 6-digit verification code
                try:
                    verification_code = "".join(
                        secrets.choice(string.digits) for _ in range(6)
                    )
                except Exception as e:
                    logger.error(f"Error generating verification code: {str(e)}")
                    messages.error(
                        request, "Erreur lors de la génération du code de vérification."
                    )
                    return redirect("register")

                # Save verification code
                try:
                    EmailVerification.objects.filter(
                        email=email
                    ).delete()  # Delete old codes
                    verification = EmailVerification.objects.create(
                        email=email, code=verification_code
                    )
                except Exception as e:
                    logger.error(f"Error creating verification: {str(e)}")
                    messages.error(
                        request, "Erreur lors de la création du code de vérification."
                    )
                    return redirect("register")

                # Store registration data in session for after verification
                try:
                    request.session["reg_username"] = username
                    request.session["reg_email"] = email
                    request.session["reg_password"] = password
                    request.session["reg_first_name"] = first_name
                    request.session["reg_last_name"] = last_name
                    request.session["verification_id"] = verification.id
                except Exception as e:
                    logger.error(f"Error storing session: {str(e)}")
                    messages.error(
                        request, "Erreur lors de l'enregistrement des données."
                    )
                    return redirect("register")

                # Send verification email
                try:
                    send_mail(
                        subject="Verify Your Email - Shop",
                        message=f"""
Hello {first_name},

Thank you for registering with Shop!

Your verification code is: {verification_code}

Please enter this code on the verification page to complete your registration.

This code will expire in 10 minutes.

If you did not request this, please ignore this email.

Best regards,
Shop Team
                        """,
                        from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings
                        recipient_list=[email],
                        fail_silently=False,
                    )
                    messages.success(request, f"Code de vérification envoyé à {email}!")
                    return redirect("verify_email")
                except Exception as e:
                    logger.error(f"Error sending email: {str(e)}")
                    messages.error(request, f"Échec de l'envoi de l'email: {str(e)}")
                    return redirect("register")
            except Exception as e:
                logger.error(f"Error in register POST: {str(e)}")
                messages.error(
                    request, "Une erreur est survenue lors de l'inscription."
                )
                return redirect("register")

        return render(request, "mon_app_ecommerce/register.html")
    except Exception as e:
        logger.error(f"Error in register view: {str(e)}")
        messages.error(request, "Une erreur est survenue.")
        return render(request, "mon_app_ecommerce/register.html")


def verify_email(request):
    if request.method == "POST":
        code = request.POST.get("code")
        verification_id = request.session.get("verification_id")

        if not verification_id:
            messages.error(request, "No pending verification found!")
            return redirect("register")

        try:
            verification = EmailVerification.objects.get(id=verification_id)

            # Check if code matches
            if verification.code == code:
                # Check if not expired (10 minutes)
                if timezone.now() > verification.created_at + timedelta(minutes=10):
                    messages.error(
                        request, "Verification code expired! Please register again."
                    )
                    request.session.flush()
                    return redirect("register")

                # Verify email
                verification.verified = True
                verification.save()

                # Get registration data from session
                username = request.session.get("reg_username")
                email = request.session.get("reg_email")
                password = request.session.get("reg_password")
                first_name = request.session.get("reg_first_name")
                last_name = request.session.get("reg_last_name")

                from django.contrib.auth.models import User

                # Create user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                )

                # Clear session
                request.session.flush()

                # Login user
                login(request, user)

                messages.success(request, "Email verified! Registration successful!")
                return redirect("home")
            else:
                messages.error(request, "Invalid verification code!")
        except EmailVerification.DoesNotExist:
            messages.error(request, "Verification code not found!")
            return redirect("register")

    return render(request, "mon_app_ecommerce/verify_email.html")


def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully!")
    return redirect("home")


def login_view(request):
    try:
        if request.method == "POST":
            try:
                username = request.POST.get("username", "").strip()
                password = request.POST.get("password", "")

                if not username or not password:
                    messages.error(request, "Veuillez remplir tous les champs!")
                    return render(request, "mon_app_ecommerce/login.html")

                user = authenticate(request, username=username, password=password)

                if user is not None:
                    try:
                        login(request, user)
                        messages.success(
                            request, f"Bienvenue, {user.first_name or user.username}!"
                        )
                        return redirect("home")
                    except Exception as e:
                        logger.error(f"Error during login: {str(e)}")
                        messages.error(request, "Erreur lors de la connexion.")
                else:
                    messages.error(
                        request, "Nom d'utilisateur ou mot de passe invalide!"
                    )
            except Exception as e:
                logger.error(f"Error in login POST: {str(e)}")
                messages.error(request, "Une erreur est survenue lors de la connexion.")

        return render(request, "mon_app_ecommerce/login.html")
    except Exception as e:
        logger.error(f"Error in login_view: {str(e)}")
        messages.error(request, "Une erreur est survenue.")
        return render(request, "mon_app_ecommerce/login.html")


@login_required
def add_review(request, product_id):
    try:
        product = get_object_or_404(Product, id=product_id)
        customer = get_customer(request.user)

        if request.method == "POST":
            try:
                rating = int(request.POST.get("rating", 5))
                comment = request.POST.get("comment", "")

                if not comment:
                    messages.error(request, "Veuillez ajouter un commentaire!")
                    return redirect("product_detail", slug=product.slug)

                if rating < 1 or rating > 5:
                    messages.error(request, "La note doit être entre 1 et 5!")
                    return redirect("product_detail", slug=product.slug)

                Review.objects.update_or_create(
                    product=product,
                    customer=customer,
                    defaults={"rating": rating, "comment": comment},
                )

                messages.success(request, "Avis ajouté!")
            except (ValueError, TypeError):
                messages.error(request, "Note invalide!")
            except Exception as e:
                logger.error(f"Error adding review: {str(e)}")
                messages.error(request, "Erreur lors de l'ajout de l'avis.")

            return redirect("product_detail", slug=product.slug)

        return redirect("product_detail", slug=product.slug)
    except Exception as e:
        logger.error(f"Error in add_review view: {str(e)}")
        messages.error(request, "Une erreur est survenue.")
        return redirect("product_list")


@staff_member_required
def dashboard(request):
    from django.utils import timezone
    from datetime import timedelta

    # Gestion des catégories
    if request.method == "POST" and "add_category" in request.POST:
        name = request.POST.get("category_name")
        description = request.POST.get("category_description", "")
        slug = slugify(name)

        if name:
            try:
                Category.objects.create(name=name, slug=slug, description=description)
                messages.success(request, f'Catégorie "{name}" créée avec succès!')
            except Exception as e:
                messages.error(request, f"Erreur: {str(e)}")
        return redirect("dashboard")

    # Gestion des produits
    if request.method == "POST" and "add_product" in request.POST:
        name = request.POST.get("product_name")
        description = request.POST.get("product_description", "")
        price = request.POST.get("product_price")
        discount_price = request.POST.get("product_discount_price") or None
        category_id = request.POST.get("product_category")
        stock = request.POST.get("product_stock", 0)
        is_featured = request.POST.get("product_featured") == "on"
        is_active = request.POST.get("product_active") == "on"
        slug = slugify(name)

        if name and price and category_id:
            try:
                category = Category.objects.get(id=category_id)
                product = Product.objects.create(
                    name=name,
                    slug=slug,
                    description=description,
                    price=price,
                    discount_price=discount_price,
                    category=category,
                    stock=stock,
                    is_featured=is_featured,
                    is_active=is_active,
                )
                messages.success(request, f'Produit "{name}" créé avec succès!')
            except Exception as e:
                messages.error(request, f"Erreur: {str(e)}")
        return redirect("dashboard")

    # Suppression de catégorie
    if request.method == "POST" and "delete_category" in request.POST:
        category_id = request.POST.get("category_id")
        try:
            category = Category.objects.get(id=category_id)
            category_name = category.name
            category.delete()
            messages.success(request, f'Catégorie "{category_name}" supprimée!')
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")
        return redirect("dashboard")

    # Suppression de produit
    if request.method == "POST" and "delete_product" in request.POST:
        product_id = request.POST.get("product_id")
        try:
            product = Product.objects.get(id=product_id)
            product_name = product.name
            product.delete()
            messages.success(request, f'Produit "{product_name}" supprimé!')
        except Exception as e:
            messages.error(request, f"Erreur: {str(e)}")
        return redirect("dashboard")

    # Calcul des statistiques
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    # Revenus
    total_revenue = Order.objects.aggregate(total=Sum("total_amount"))["total"] or 0

    revenue_today = (
        Order.objects.filter(created_at__date=today).aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    revenue_week = (
        Order.objects.filter(created_at__gte=week_ago).aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    revenue_month = (
        Order.objects.filter(created_at__gte=month_ago).aggregate(
            total=Sum("total_amount")
        )["total"]
        or 0
    )

    # Commandes
    total_orders = Order.objects.count()
    pending_orders = Order.objects.filter(status="pending").count()
    processing_orders = Order.objects.filter(status="processing").count()
    shipped_orders = Order.objects.filter(status="shipped").count()
    delivered_orders = Order.objects.filter(status="delivered").count()
    orders_today = Order.objects.filter(created_at__date=today).count()
    orders_week = Order.objects.filter(created_at__gte=week_ago).count()

    # Produits
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    featured_products = Product.objects.filter(is_featured=True).count()
    low_stock_products = Product.objects.filter(stock__lt=10).count()
    out_of_stock_products = Product.objects.filter(stock=0).count()

    # Catégories
    total_categories = Category.objects.count()

    # Clients
    total_customers = Customer.objects.count()
    new_customers_today = Customer.objects.filter(user__date_joined__date=today).count()
    new_customers_week = Customer.objects.filter(
        user__date_joined__gte=week_ago
    ).count()

    # Paniers actifs
    active_carts = Cart.objects.count()

    # Avis
    total_reviews = Review.objects.count()
    avg_rating = Review.objects.aggregate(Avg("rating"))["rating__avg"] or 0

    # Commandes récentes
    recent_orders = Order.objects.select_related("customer__user").order_by(
        "-created_at"
    )[:10]

    # Produits les plus vendus
    top_products = (
        Product.objects.annotate(total_sold=Sum("orderitem__quantity"))
        .filter(total_sold__isnull=False)
        .order_by("-total_sold")[:5]
    )

    # Catégories
    categories = Category.objects.all()

    # Produits
    products = Product.objects.select_related("category").order_by("-created_at")[:20]

    context = {
        # Statistiques de revenus
        "total_revenue": total_revenue,
        "revenue_today": revenue_today,
        "revenue_week": revenue_week,
        "revenue_month": revenue_month,
        # Statistiques de commandes
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "processing_orders": processing_orders,
        "shipped_orders": shipped_orders,
        "delivered_orders": delivered_orders,
        "orders_today": orders_today,
        "orders_week": orders_week,
        # Statistiques de produits
        "total_products": total_products,
        "active_products": active_products,
        "featured_products": featured_products,
        "low_stock_products": low_stock_products,
        "out_of_stock_products": out_of_stock_products,
        # Autres statistiques
        "total_categories": total_categories,
        "total_customers": total_customers,
        "new_customers_today": new_customers_today,
        "new_customers_week": new_customers_week,
        "active_carts": active_carts,
        "total_reviews": total_reviews,
        "avg_rating": round(avg_rating, 1) if avg_rating else 0,
        # Données pour la gestion
        "categories": categories,
        "products": products,
        "recent_orders": recent_orders,
        "top_products": top_products,
    }

    return render(request, "mon_app_ecommerce/dashboard.html", context)


# Helper function to get or check seller
def get_seller(user):
    try:
        seller = Seller.objects.get(user=user)
        return seller
    except Seller.DoesNotExist:
        return None


def is_seller(user):
    return Seller.objects.filter(user=user, is_active=True).exists()


@login_required
def register_seller(request):
    """Vue pour l'inscription d'un vendeur"""
    # Vérifier si l'utilisateur est déjà vendeur
    if is_seller(request.user):
        messages.info(request, "Vous êtes déjà inscrit comme vendeur!")
        return redirect("seller_dashboard")

    if request.method == "POST":
        try:
            store_name = request.POST.get("store_name", "").strip()
            store_description = request.POST.get("store_description", "").strip()
            phone = request.POST.get("phone", "").strip()
            email = request.POST.get("email", "").strip()
            address = request.POST.get("address", "").strip()
            city = request.POST.get("city", "").strip()
            country = request.POST.get("country", "Côte d'Ivoire").strip()

            # Validation
            if not store_name or not phone or not email or not address or not city:
                messages.error(
                    request, "Veuillez remplir tous les champs obligatoires!"
                )
                return redirect("register_seller")

            # Vérifier si le nom de boutique existe déjà
            if Seller.objects.filter(store_name=store_name).exists():
                messages.error(
                    request,
                    "Ce nom de boutique existe déjà! Veuillez en choisir un autre.",
                )
                return redirect("register_seller")

            # Vérifier si l'email est déjà utilisé par un autre vendeur
            if Seller.objects.filter(email=email).exclude(user=request.user).exists():
                messages.error(
                    request, "Cet email est déjà utilisé par un autre vendeur!"
                )
                return redirect("register_seller")

            # Créer le profil vendeur
            seller = Seller.objects.create(
                user=request.user,
                store_name=store_name,
                store_description=store_description,
                phone=phone,
                email=email,
                address=address,
                city=city,
                country=country,
                is_verified=False,  # Nécessite vérification par admin
                is_active=True,
            )

            messages.success(
                request,
                f'Inscription réussie! Votre boutique "{store_name}" est en attente de vérification par un administrateur.',
            )
            return redirect("seller_dashboard")

        except Exception as e:
            messages.error(
                request, f"Une erreur est survenue lors de l'inscription: {str(e)}"
            )
            return redirect("register_seller")

    return render(request, "mon_app_ecommerce/register_seller.html")


@login_required
def seller_dashboard(request):
    """Tableau de bord du vendeur pour gérer ses produits"""
    try:
        seller = get_seller(request.user)

        if not seller:
            messages.info(
                request,
                "Vous devez vous inscrire comme vendeur pour accéder à cette page.",
            )
            return redirect("register_seller")

        if not seller.is_active:
            messages.warning(
                request,
                "Votre compte vendeur est désactivé. Contactez un administrateur.",
            )
            return redirect("home")

        # Récupérer les produits du vendeur
        products = Product.objects.filter(seller=seller).order_by("-created_at")

        # Statistiques
        total_products = products.count()
        active_products = products.filter(is_active=True).count()
        inactive_products = products.filter(is_active=False).count()
        low_stock_products = products.filter(stock__lt=10).count()
        out_of_stock_products = products.filter(stock=0).count()

        # Commandes contenant des produits du vendeur
        from django.db.models import Sum

        seller_orders = (
            Order.objects.filter(items__product__seller=seller)
            .distinct()
            .order_by("-created_at")[:10]
        )

        # Total des ventes
        total_sales = seller.get_total_sales()

        # Gestion de la mise à jour du profil
        if request.method == "POST" and "update_profile" in request.POST:
            try:
                seller.store_name = request.POST.get("store_name", seller.store_name)
                seller.store_description = request.POST.get(
                    "store_description", seller.store_description
                )
                seller.phone = request.POST.get("phone", seller.phone)
                seller.email = request.POST.get("email", seller.email)
                seller.address = request.POST.get("address", seller.address)
                seller.city = request.POST.get("city", seller.city)
                seller.country = request.POST.get("country", seller.country)
                seller.save()
                messages.success(request, "Profil mis à jour avec succès!")
                return redirect("seller_dashboard")
            except Exception as e:
                messages.error(request, f"Erreur lors de la mise à jour: {str(e)}")

        # Suppression de produit
        if request.method == "POST" and "delete_product" in request.POST:
            try:
                product_id = request.POST.get("product_id")
                product = get_object_or_404(Product, id=product_id, seller=seller)
                product_name = product.name
                product.delete()
                messages.success(
                    request, f'Produit "{product_name}" supprimé avec succès!'
                )
                return redirect("seller_dashboard")
            except Exception as e:
                messages.error(request, f"Erreur lors de la suppression: {str(e)}")

        context = {
            "seller": seller,
            "products": products,
            "total_products": total_products,
            "active_products": active_products,
            "inactive_products": inactive_products,
            "low_stock_products": low_stock_products,
            "out_of_stock_products": out_of_stock_products,
            "seller_orders": seller_orders,
            "total_sales": total_sales,
        }
        return render(request, "mon_app_ecommerce/seller_dashboard.html", context)

    except Exception as e:
        messages.error(request, f"Une erreur est survenue: {str(e)}")
        return redirect("home")


@login_required
def add_product_by_seller(request):
    """Vue pour qu'un vendeur publie un produit"""
    try:
        seller = get_seller(request.user)

        if not seller:
            messages.info(
                request,
                "Vous devez vous inscrire comme vendeur pour publier des produits.",
            )
            return redirect("register_seller")

        if not seller.is_active:
            messages.warning(
                request,
                "Votre compte vendeur est désactivé. Contactez un administrateur.",
            )
            return redirect("home")

        categories = Category.objects.all()

        if request.method == "POST":
            try:
                name = request.POST.get("name", "").strip()
                description = request.POST.get("description", "").strip()
                price = request.POST.get("price", "").strip()
                discount_price = request.POST.get("discount_price", "").strip() or None
                category_id = request.POST.get("category")
                stock = request.POST.get("stock", "0").strip()
                is_featured = request.POST.get("is_featured") == "on"
                is_active = request.POST.get("is_active", "on") == "on"
                image = request.FILES.get("image")

                # Validation
                if not name or not description or not price or not category_id:
                    messages.error(
                        request, "Veuillez remplir tous les champs obligatoires!"
                    )
                    return redirect("add_product_by_seller")

                if not image:
                    messages.error(request, "Veuillez ajouter une image au produit!")
                    return redirect("add_product_by_seller")

                try:
                    price = float(price)
                    if price < 0:
                        raise ValueError("Le prix ne peut pas être négatif")
                except ValueError:
                    messages.error(request, "Prix invalide!")
                    return redirect("add_product_by_seller")

                if discount_price:
                    try:
                        discount_price = float(discount_price)
                        if discount_price < 0:
                            raise ValueError("Le prix réduit ne peut pas être négatif")
                        if discount_price >= price:
                            raise ValueError(
                                "Le prix réduit doit être inférieur au prix normal"
                            )
                    except ValueError as e:
                        messages.error(request, f"Prix réduit invalide: {str(e)}")
                        return redirect("add_product_by_seller")

                try:
                    stock = int(stock)
                    if stock < 0:
                        raise ValueError("Le stock ne peut pas être négatif")
                except ValueError:
                    messages.error(request, "Stock invalide!")
                    return redirect("add_product_by_seller")

                try:
                    category = Category.objects.get(id=category_id)
                except Category.DoesNotExist:
                    messages.error(request, "Catégorie invalide!")
                    return redirect("add_product_by_seller")

                # Générer un slug unique
                base_slug = slugify(name)
                slug = base_slug
                counter = 1
                while Product.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                # Créer le produit
                product = Product.objects.create(
                    name=name,
                    slug=slug,
                    description=description,
                    price=price,
                    discount_price=discount_price,
                    category=category,
                    seller=seller,
                    stock=stock,
                    is_featured=is_featured,
                    is_active=is_active,
                    image=image,
                )

                messages.success(request, f'Produit "{name}" publié avec succès!')
                return redirect("seller_dashboard")

            except Exception as e:
                messages.error(
                    request, f"Erreur lors de la publication du produit: {str(e)}"
                )
                return redirect("add_product_by_seller")

        context = {
            "seller": seller,
            "categories": categories,
        }
        return render(request, "mon_app_ecommerce/add_product.html", context)

    except Exception as e:
        messages.error(request, f"Une erreur est survenue: {str(e)}")
        return redirect("home")


@login_required
def edit_product_by_seller(request, product_id):
    """Vue pour qu'un vendeur modifie un de ses produits"""
    try:
        seller = get_seller(request.user)

        if not seller:
            messages.info(request, "Vous devez vous inscrire comme vendeur.")
            return redirect("register_seller")

        if not seller.is_active:
            messages.warning(request, "Votre compte vendeur est désactivé.")
            return redirect("home")

        product = get_object_or_404(Product, id=product_id, seller=seller)
        categories = Category.objects.all()

        if request.method == "POST":
            try:
                product.name = request.POST.get("name", product.name).strip()
                product.description = request.POST.get(
                    "description", product.description
                ).strip()

                try:
                    price = float(request.POST.get("price", product.price))
                    if price < 0:
                        raise ValueError("Le prix ne peut pas être négatif")
                    product.price = price
                except ValueError:
                    messages.error(request, "Prix invalide!")
                    return redirect("edit_product_by_seller", product_id=product_id)

                discount_price = request.POST.get("discount_price", "").strip() or None
                if discount_price:
                    try:
                        discount_price = float(discount_price)
                        if discount_price < 0:
                            raise ValueError("Le prix réduit ne peut pas être négatif")
                        if discount_price >= product.price:
                            raise ValueError(
                                "Le prix réduit doit être inférieur au prix normal"
                            )
                        product.discount_price = discount_price
                    except ValueError as e:
                        messages.error(request, f"Prix réduit invalide: {str(e)}")
                        return redirect("edit_product_by_seller", product_id=product_id)
                else:
                    product.discount_price = None

                try:
                    product.category = Category.objects.get(
                        id=request.POST.get("category")
                    )
                except (Category.DoesNotExist, ValueError):
                    messages.error(request, "Catégorie invalide!")
                    return redirect("edit_product_by_seller", product_id=product_id)

                try:
                    stock = int(request.POST.get("stock", product.stock))
                    if stock < 0:
                        raise ValueError("Le stock ne peut pas être négatif")
                    product.stock = stock
                except ValueError:
                    messages.error(request, "Stock invalide!")
                    return redirect("edit_product_by_seller", product_id=product_id)

                product.is_featured = request.POST.get("is_featured") == "on"
                product.is_active = request.POST.get("is_active", "on") == "on"

                # Gérer l'image si une nouvelle est fournie
                if "image" in request.FILES:
                    product.image = request.FILES["image"]

                # Mettre à jour le slug si le nom a changé
                new_slug = slugify(product.name)
                if new_slug != product.slug:
                    base_slug = new_slug
                    slug = base_slug
                    counter = 1
                    while (
                        Product.objects.filter(slug=slug)
                        .exclude(id=product.id)
                        .exists()
                    ):
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    product.slug = slug

                product.save()
                messages.success(
                    request, f'Produit "{product.name}" mis à jour avec succès!'
                )
                return redirect("seller_dashboard")

            except Exception as e:
                messages.error(request, f"Erreur lors de la mise à jour: {str(e)}")
                return redirect("edit_product_by_seller", product_id=product_id)

        context = {
            "seller": seller,
            "product": product,
            "categories": categories,
        }
        return render(request, "mon_app_ecommerce/edit_product.html", context)

    except Exception as e:
        messages.error(request, f"Une erreur est survenue: {str(e)}")
        return redirect("seller_dashboard")
