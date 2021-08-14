from django.contrib import admin
from django.forms import ModelForm
from django.conf import settings
from django.utils.html import format_html
from .models import PaymentMethod, CustomField
from stripe.api_resources import WebhookEndpoint
from paypalrestsdk.api import Api
from paypalrestsdk.notifications import Webhook
from urllib.parse import urljoin
import os


class PaymentMethodForm(ModelForm):
    def clean(self):
        if self.cleaned_data.get('provider') == 'paypal' and not self.cleaned_data.get('environment'):
            self.add_error('environment', 'PayPal needs environment details to setup')
            return

        pass

    class Meta:
        model = PaymentMethod
        fields = ['provider', 'secret_key', 'client_key', 'environment', 'is_active']
    pass


@admin.register(PaymentMethod)
class PaymentMethodRegister(admin.ModelAdmin):
    form = PaymentMethodForm
    empty_value_display = 'N/A'
    list_display = ['payment_gateway', 'environment', 'wh_id', 'is_active', 'client_key']
    list_display_links = ['payment_gateway']

    fieldsets = (
        (
            'Select Payment Provider', {
                'description': 'Select type of payment provider to configure and environment',
                'fields': ('provider', 'environment')
            }
        ),
        (
            'Configure Keys', {
                'description': 'Goto API dashboard, copy and paste keys here',
                'fields': ('client_key', 'secret_key')
            }
        ),
        (
            'Meta Information', {
                'description': 'Configure payment meta information',
                'fields': ('is_active',)
            }
        )
    )

    def delete_model(self, request, obj: PaymentMethod):
        if obj.wh_id and obj.provider == 'paypal':
            self.message_user(request, 'Delete webhook id %s manually from dashboard' % obj.wh_id)
            obj.wh_id = None
        elif obj.wh_id and obj.provider == 'stripe':
            WebhookEndpoint.delete(obj.wh_id, api_key=obj.secret_key)
            obj.wh_id = None
        elif obj.provider == 'razorpay':
            self.message_user(request, 'Please delete the webhook from the dashboard to avoid errors')
        return super(PaymentMethodRegister, self).delete_model(request, obj)

    def save_model(self, request, obj: PaymentMethod, form, change):
        if obj.is_active:
            PaymentMethod.objects.exclude(id=obj.id).filter(provider=obj.provider, is_active=True).update(is_active=False)
            pass

        if obj.provider == 'razorpay':
            self.message_user(request, format_html('Add a webhook URL with endpoint "<strong>%s/webhooks/razorpay</strong>" in your razorpay dashboard' % settings.BASE_URL))
        elif os.getenv('CI') == 'True':
            self.message_user(request, 'CI Test Run')
        elif obj.provider == 'paypal' and not obj.wh_id and os.getenv('CI') is not None:
            api = Api({
                'mode': 'sandbox' if obj.environment == 'dev' else 'live',
                'client_id': obj.client_key,
                'client_secret': obj.secret_key
            })
            wh = Webhook(api=api, attributes={
                'event_types': [{'name': 'BILLING.SUBSCRIPTION.RENEWED'}, {'name': 'BILLING.SUBSCRIPTION.ACTIVATED'}],
                'url': urljoin(settings.BASE_URL, 'webhooks/paypal').replace('http://', 'https://')
            })
            if not wh.create():
                raise ValueError('Webhook creation failed')
            obj.wh_id = wh.to_dict().get('id')
        elif obj.provider == 'stripe' and not obj.wh_id and os.getenv('CI') is not None:
            wh = WebhookEndpoint.create(
                enabled_events=['invoice.paid'],
                url=urljoin(settings.BASE_URL, 'webhooks/stripe'),
                description='Generated by DonorGrid',
                api_key=obj.secret_key)
            obj.wh_id = wh.get('id')
        return super(PaymentMethodRegister, self).save_model(request, obj, form, change)

    def payment_gateway(self, obj: PaymentMethod):
        name = [*filter(lambda x: x[0] == obj.provider, PaymentMethod.PaymentProvider.choices)][0][1]
        return name
    pass


@admin.register(CustomField)
class CustomFieldRegister(admin.ModelAdmin):
    empty_value_display = 'N/A'
    list_display = ['name', 'type', 'placeholder']

    fieldsets = (
        (
            'Basic Details', {
                'description': 'Add basic details of custom fields like name and type',
                'fields': ('name', 'type')
            }
        ),
        (
            'Other Settings', {
                'description': 'Provide additional information for donors',
                'fields': ('placeholder', ('attributes', 'help_text'))
            }
        )
    )
    pass
