from django.conf import settings
from django.shortcuts import render, get_object_or_404
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect
from django.contrib import messages
from django.utils import timezone
import random
import string
from .forms import CheckoutForm, CouponForm, RefundForm
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund, UserProfile
import stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
# import Item form .models
# Create your views here.

def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))



class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home-page.html"
    # make appropriate changes in the urls.py replacing the home function with HomeView


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {
                'object': order
            }
            return render(self.request, 'order_summary.html', context)
        
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return redirect('/') 
        
    


class ItemDetailView(DetailView):
    model = Item
    template_name = "product-page.html"


def products(request):
    return render(request, 'product-page.html')

def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
        return valid 

class CheckoutView(View):
    def get(self, *args, **kwargs):
        
        try:

            order = Order.objects.get(user=self.request.user,
            ordered=False)
            form = CheckoutForm()
            context = {
                'form': form,
                'couponform':CouponForm(),
                'order': order,
                'DISPLAY_COUPON_FORM':True
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type = 'S',
                default = True
                )
            if shipping_address_qs.exists():
                context.update({'default_shipping_address': shipping_address_qs[0]})
            
            billing_address_qs = Address.objects.filter(
                user=self.request.user,
                address_type = 'B',
                default = True
                )
            if billing_address_qs.exists():
                context.update({'default_billing_address': billing_address_qs[0]})
            
            return render(self.request, 'checkout-page.html', context)


        except ObjectDoesNotExist:
            messages.info(self.request, 'You do not have an active order')
            return redirect('core:checkout')
        #form

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or NONE)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get('use_default_address')
                if use_default_shipping:
                    print('Using default shipping address')
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type = 'S',
                        default = True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(self.request, 'No default shipping address available')
                        return redirect('core:checkout')
                else:
                    print('User is entering a new shipping address')
                    shipping_address1 = form.cleaned_data.get('shipping_address')
                    shipping_address2 = form.cleaned_data.get('shipping_address2')
                    shipping_country = form.cleaned_data.get('shipping_country')
                    shipping_zip = form.cleaned_data.get('shipping_zip')
               #     same_shipping_address = form.cleaned_data.get('same_shipping_address')
               #     save_info = form.cleaned_data.get('save_info')
                    

                    if is_valid_form([shipping_address1, shipping_country, shipping_zip]):

                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                            address_type='S'
                        )
                        shipping_address.save()
                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get('set_default_shipping')
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()
                    else:
                        messages.info(self.request, 'Please fill out the required shipping addresses')
                        #return redirect('core:checkout')
                

                use_default_billing = form.cleaned_data.get('use_default_billing')
                same_billing_address = form.cleaned_data.get('same_billing_address')
                if same_billing_address:
                    billing_address = shipping_address
                    billing_address.pk = None
                    billing_address.save()
                    billing_address.address_type = 'B'
                    billing_address.save()
                    order.billing_address = billing_address
                    order.save()
                elif use_default_billing:
                    print('Using the default billing address')
                    address_qs = Address.objects.filter(
                        user=self.request.user,
                        address_type = 'B',
                        default = True
                    )
                    if address_qs.exists():
                        billing_address = address_qs[0]
                        order.billing_address = billing_address
                        order.save()

                    else:
                        messages.info(self.request, 'No default billing address available')
                        return redirect('core:checkout')
                else:
                    print('User is entering a new billing address')
                    billing_address1 = form.cleaned_data.get('billing_address')
                    billing_address2 = form.cleaned_data.get('billing_address2')
                    billing_country = form.cleaned_data.get('billing_country')
                    billing_zip = form.cleaned_data.get('billing_zip')
               #     same_shipping_address = form.cleaned_data.get('same_shipping_address')
               #     save_info = form.cleaned_data.get('save_info')
                    

                    if is_valid_form([billing_address1, billing_country, billing_zip]):

                        billing_address = Address(
                            user=self.request.user,
                            street_address=billing_address1,
                            apartment_address=billing_address2,
                            country=billing_country,
                            zip=billing_zip,
                            address_type='B'
                        )
                        billing_address.save()
                        order.billing_address = billing_address
                        order.save()

                        set_default_billing = form.cleaned_data.get('set_default_billing')
                        if set_default_billing:
                            billing_address.default = True
                            billing_address.save()
                    else:
                        messages.info(self.request, 'Please fill out the required billing addresses')
                        #return redirect('core:checkout')
                payment_option = form.cleaned_data.get('payment_info')
                return redirect('core:payment', payment_option='Stripe')
                
               # if payment_option == 's':
               #     return redirect('core:payment', payment_option='Stripe')
               # elif payment_option == "p":
               #     return redirect('core:payment', payment_option='Paypal')
               # 
               # else:
               #     messages.warning(self.request, 'Invalid payment option slected')
               #     return redirect('core:checkout')

                

        
        except ObjectDoesNotExist:
            messages.error(self.request, 'You do not have an active order')
            return redirect('core:order-summary') 
       # print(self.request.POST)
class PaymentView(View):
    def get(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        if order.billing_address:
            context = {
                'order':order,
                'DISPLAY_COUPON_FORM': False
            }
            
            return render(self.request, 'payment.html', context)
        else:
            messages.warning(self.request, 'You have not added a billing address')
            return redirect('core:checkout')
    
    def post(self, *args, **kwargs):
        order = Order.objects.get(user=self.request.user, ordered=False)
        form = PaymentForm(self.request.POST)
        userprofile = UserProfile.objects.get(user=self.request.user)
        if form.is_valid():
            token = form.cleaned_data.get('stripeToken')
            save = form.cleaned_data.get('save')
            use_default = form.cleaned_data.get('use_default')

            if save:
                if userprofile.stripe_customer_id != '' and userprofile.stripe_customer_id is not None:
                    customer = stripe.Customer.retrieve(
                        userprofile.stripe_customer_id
                    )
                    customer.sources.create(source=token)
                else:
                    customer = stripe.Customer.create(
                        email = self.request.user.email,
                    )
                    customer.sources.create(source=token)
                    userprofile.stripe_customer_id = customer['id']
                    userprofile.one_click_purchasing = True
                    userprofile.save()
        
        amount = int(order.get_total_price() * 100)

        try:
            if use_default or save:
                charge = stripe.Charge.create(
                    amount = amount,
                    currency ='usd',
                    customer=userprofile.stripe_customer_id
                )
            else:

                charge = stripe.Charge.create(
                amount=amount,
                currency="usd",
                source=token, # obtained with Stripe.js
                idempotency_key='u1GZH95JdKwgOIWu'
                )

            #create payment
            payment = Payment()
            payment.stripe_charge_id = charge('id')
            payment.user = self.request.user
            payment.amount = order.get_total_price()
            payment.save()

            #assign the payment to the order

            order_items = order.items.all()
            order_items.update(ordered=True)
            for item in order_items:
                item.save()

            order.ordered = True
            order.payment = payment
            order.ref_code = create_ref_code()
            order.save()
            messages.success(self.request, 'Your order was successfull')
            return redirect('/')
        except stripe.error.CardError as e:
            # Since it's a decline, stripe.error.CardError will be caught
            body = e.json_body
            err = body.get('error', {})
            messages.error(self.request, f'{err.get("message")}')
            return redirect('/')
            
        except stripe.error.RateLimitError as e:
            # Too many requests made to the API too quickly
            messages.error(self.request, 'Rate limit error')
            return redirect('/')

        except stripe.error.InvalidRequestError as e:
            # Invalid parameters were supplied to Stripe's API
            messages.error(self.request, 'Invalid parameters')
            return redirect('/')

        except stripe.error.AuthenticationError as e:
            # Authentication with Stripe's API failed
            # (maybe you changed API keys recently)
            messages.error(self.request,'Not authenticated')
            return redirect('/')

        except stripe.error.APIConnectionError as e:
            # Network communication with Stripe failed
            messages.error(self.request, 'Network error')
            return redirect('/')

        except stripe.error.StripeError as e:
            # Display a very generic error to the user, and maybe send
            # yourself an email
            messages.error(self.request, 'Something went wrong. You were not charged. Please try again')
            return redirect('/')

        except Exception as e:
            # Something else happened, completely unrelated to Stripe
            # send an email to me
            messages.error(self.request, 'An unexepected error occured, we have been notified.')
            return redirect('/')


       

        

        
@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item,
    user=request.user,
    ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, 'This item quantity was updated')
            return redirect('core:products', slug=slug)
        else:
            order.items.add(order_item)
            messages.info(request, 'This item was added to your cart')
            return redirect('core:products', slug=slug)
    #if the order item does not exist
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, 'This item was added to your cart')
        return redirect('core:products', slug=slug)
    return redirect('core:products', slug=slug)

#try this
@login_required
def add_to_cart_again(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_item, created = OrderItem.objects.get_or_create(item=item,
    user=request.user,
    ordered=False)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item.quantity += 1
            order_item.save()
            messages.info(request, 'This item quantity was updated')
            return redirect('core:order-summary')
        else:
            order.items.add(order_item)
            messages.info(request, 'This item was added to your cart')
            return redirect('core:order-summary')
    #if the order item does not exist
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, 'This item was added to your cart')
        return redirect('core:order-summary')
    return redirect('core:products', slug=slug)
#end of trial

@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user,
    ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item =  OrderItem.objects.filter(item=item,
            user=request.user,
            ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, 'This item was removed from your cart')
            return redirect('core:products', slug=slug)
        else:
            #add s message saying the order does not contain the item
            messages.info(request, 'This item was not in your cart')
            return redirect('core:products', slug=slug)
    else:
        #add a message sayng the user doesnt have an order
        messages.info(request, 'You do not have an active order')
        return redirect('core:products', slug=slug)

#tryn this again
@login_required
def remove_from_cart_again(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user,
    ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item =  OrderItem.objects.filter(item=item,
            user=request.user,
            ordered=False)[0]
            order.items.remove(order_item)
            messages.info(request, 'This item was removed from your cart')
            return redirect('core:order-summary')
        else:
            #add s message saying the order does not contain the item
            messages.info(request, 'This item was not in your cart')
            return redirect('core:order-summary')
    else:
        #add a message sayng the user doesnt have an order
        messages.info(request, 'You do not have an active order')
        return redirect('core:order-summary')
#end of trial
    
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user,
    ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        #check if order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item =  OrderItem.objects.filter(item=item,
            user=request.user,
            ordered=False)[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item) 
            
            messages.info(request, 'This item quantity was updated')
            return redirect('core:order-summary')
        else:
            #add s message saying the order does not contain the item
            messages.info(request, 'This item was not in your cart')
            return redirect('core:products', slug=slug)
    else:
        #add a message sayng the user doesnt have an order
        messages.info(request, 'You do not have an active order')
        return redirect('core:products', slug=slug)


def get_coupon(request, code):
    try:
        coupon = Coupon.objects.get(code=code)
        return coupon

    except ObjectDoesNotExist:
        messages.info(request, 'This coupon does not exist')
        return redirect('core:checkout')


class AddCouponView(View):
    def post(self, *args, **kwargs):
        form = CouponForm(self.request.POST or NONE)
        if form.is_valid():

            try:
                code = form.cleaned_data.get('code')
                order = Order.objects.get(user=self.request.user,
                ordered=False)
                order.coupon = get_coupon(self.request, code)
                order.save()
                messages.success(self.request, 'Successfully added coupon')
                return redirect('core:checkout')


            except ObjectDoesNotExist:
                messages.info(self.request, 'You do not have an active order')
                return redirect('core:checkout')
        return None

class RequestRefundView(View):
    def get(self, *args, **kwargs):
        form = RefundForm()
        context = {
            'form':form
        }
        return render(self.request, 'request_refund.html', context)
    def post(self, *args, **kwargs):
        form = RefundForm(self.request.POST)
        if form.is_valid():
            ref_code = form.cleaned_data.get('ref_code')
            message = form.cleaned_data.get('message')
            email = form.cleaned_data.get('email')
            try:
                order = Order.objects.get(ref_code=ref_code)
                order.refund_requested = True
                order.save()

                refund = Refund()
                refund.order = order
                refund.reason = message
                refund.email = email
                refund.save()

                messages.info(self.request, 'Your request was received')
                return redirect('core:request-refund')

            except ObjectDoesNotExist:
                messages.info(self.request, 'This order does not exist')
                return redirect('core:request-refund')
         
     


