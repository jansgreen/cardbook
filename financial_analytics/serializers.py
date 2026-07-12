from rest_framework import serializers

from billing.models import Invoice, Payment, Refund
from companies.models import Company
from financial_analytics.models import CommissionPayment, ReferralClick
from referrals.models import Commission
from subscriptions.models import Subscription


class SubscriptionSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id", "company", "company_name", "stripe_customer_id", "stripe_subscription_id",
            "plan", "unit_amount", "currency", "status", "billing_interval",
            "current_period_start", "current_period_end", "cancel_at_period_end",
            "trial_start", "trial_end", "created_at", "updated_at",
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "company", "company_name", "subscription", "stripe_invoice_id", "invoice_number",
            "subtotal", "tax", "total", "amount_paid", "amount_due", "currency", "status",
            "hosted_invoice_url", "invoice_pdf", "due_date", "paid_at", "created_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="company.name", read_only=True)
    plan = serializers.CharField(source="subscription.plan", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "company", "company_name", "subscription", "plan", "invoice",
            "stripe_payment_intent_id", "stripe_invoice_id", "amount", "currency", "status",
            "payment_method", "stripe_fee", "net_amount", "paid_at", "created_at",
        ]


class RefundSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source="payment.company.name", read_only=True)
    payment_amount = serializers.DecimalField(source="payment.amount", read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = Refund
        fields = [
            "id", "payment", "company_name", "payment_amount", "stripe_refund_id",
            "amount", "reason", "status", "processed_by", "created_at",
        ]


class CommissionSerializer(serializers.ModelSerializer):
    agent_name = serializers.SerializerMethodField()
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = Commission
        fields = [
            "id", "agent", "agent_name", "company", "company_name", "subscription", "payment",
            "plan_name", "payment_amount", "commission_percentage", "commission_amount",
            "status", "approved_by", "paid_by", "created_at", "approved_at", "paid_at",
        ]

    def get_agent_name(self, obj):
        return obj.agent.user.get_full_name() or obj.agent.user.username


class CommissionPaymentSerializer(serializers.ModelSerializer):
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = CommissionPayment
        fields = [
            "id", "agent", "agent_name", "total_amount", "currency", "payment_method",
            "transaction_reference", "notes", "paid_by", "paid_at", "created_at",
        ]

    def get_agent_name(self, obj):
        return obj.agent.user.get_full_name() or obj.agent.user.username


class ReferralClickSerializer(serializers.ModelSerializer):
    agent_name = serializers.SerializerMethodField()

    class Meta:
        model = ReferralClick
        fields = ["id", "agent", "agent_name", "referral_code", "ip_address", "user_agent", "source_url", "landing_page", "created_at"]

    def get_agent_name(self, obj):
        return obj.agent.user.get_full_name() or obj.agent.user.username


class FinanceCompanySerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    active_plan = serializers.SerializerMethodField()
    active_status = serializers.SerializerMethodField()
    mrr = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ["id", "logo", "name", "owner", "owner_email", "email", "active_plan", "active_status", "mrr", "created_at"]

    def get_active_subscription(self, obj):
        return obj.subscriptions.order_by("-updated_at").first()

    def get_active_plan(self, obj):
        subscription = self.get_active_subscription(obj)
        return subscription.plan if subscription else None

    def get_active_status(self, obj):
        subscription = self.get_active_subscription(obj)
        return subscription.status if subscription else None

    def get_mrr(self, obj):
        subscription = self.get_active_subscription(obj)
        return subscription.normalized_mrr if subscription else 0
