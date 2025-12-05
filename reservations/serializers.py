from rest_framework import serializers
from django.utils import timezone
from .models import Reservation, ReservationStatus
from spaces.models import Space


class ReservationSerializer(serializers.ModelSerializer):
    space = serializers.PrimaryKeyRelatedField(
        queryset=Space.objects.all()
    )
    created_by = serializers.ReadOnlyField(source="created_by.id")
    status = serializers.ChoiceField(choices=ReservationStatus.choices, read_only=True)

    class Meta:
        model = Reservation
        fields = [
            "id",
            "space",
            "created_by",
            "header",
            "start_at",
            "end_at",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_by", "status", "created_at", "updated_at"]

    def validate(self, attrs):
        start = attrs.get("start_at")
        end = attrs.get("end_at")

        if self.instance:
            start = start or self.instance.start_at
            end = end or self.instance.end_at

        # controllo overlapping "utente"
        user = self.context["request"].user
        if user.is_authenticated and start and end:
            qs = Reservation.objects.filter(
                created_by=user,
                status__in=[ReservationStatus.PENDING, ReservationStatus.CONFIRMED],
            ).filter(
                start_at__lt=end,
                end_at__gt=start,
            )
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError(
                    "You already have a reservation in this timeslot."
                )


        return attrs

    def create(self, validated_data):
        return super().create(validated_data)
