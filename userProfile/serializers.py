from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import UserProfile

class CustomRegisterSerializer(RegisterSerializer):
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    date_of_birth = serializers.DateField(required=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, required=True)
    email = serializers.EmailField(required=True)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data.update({
            'first_name': self.validated_data.get('first_name', ''),
            'last_name': self.validated_data.get('last_name', ''),
            'date_of_birth': self.validated_data.get('date_of_birth', ''),
            'role': self.validated_data.get('role', ''),
            'email': self.validated_data.get('email', ''),
        })
        return data

    def save(self, request):
        user = super().save(request)
        cleaned_data = self.get_cleaned_data()
        user.first_name = cleaned_data.get('first_name')
        user.last_name = cleaned_data.get('last_name')
        user.date_of_birth = cleaned_data.get('date_of_birth')
        user.role = cleaned_data.get('role')
        user.save()
        return user
    

class CustomUserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ('pk', 'username', 'first_name', 'last_name', 'email', 'date_of_birth', 'role')
        read_only_fields = ('email',)