from rest_framework import serializers

from .models import CompanyMember


class CompanyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanyMember
        fields = ["id", "company", "user", "role", "is_active", "created_at"]
        read_only_fields = ["id", "company", "is_active", "created_at"]

    def validate_role(self, role):
        request = self.context.get("request")
        company = self.context.get("company")
        if role == CompanyMember.ROLE_OWNER and company and request and company.owner_id != request.user.id:
            raise serializers.ValidationError("Only the company owner can assign the owner role.")
        return role

    def validate(self, attrs):
        company = self.context.get("company")
        user = attrs.get("user")

        if self.instance and user and user != self.instance.user:
            raise serializers.ValidationError({"user": ["A membership user cannot be changed."]})

        if not self.instance and company and user:
            exists = CompanyMember.objects.filter(company=company, user=user).exists()
            if exists:
                raise serializers.ValidationError({"user": ["This user is already a member of this company."]})

        return attrs
