from rest_framework import serializers
from .models import Reservation, ReservationStatus
from spaces.models import Space


class ReservationSerializer(serializers.ModelSerializer):
    space = serializers.PrimaryKeyRelatedField(
        queryset=Space.objects.all()
    )
    created_by = serializers.ReadOnlyField(source="created_by.id")
    status = serializers.ChoiceField(choices=ReservationStatus.choices, read_only=True)
    cancelled_at = serializers.DateTimeField(read_only=True) 

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
            "cancelled_at", 
        ]
        read_only_fields = [
            "id", "created_by", "status", 
            "created_at", "updated_at", "cancelled_at"  
        ]

    def validate(self, attrs):
        request = self.context["request"]
        user = request.user

        start = attrs.get("start_at")
        end = attrs.get("end_at")
        space = attrs.get("space")

        # In update
        if self.instance:
            start = start or self.instance.start_at
            end = end or self.instance.end_at
            space = space or self.instance.space

        # Admin NON possono creare reservations proprie
        if not self.instance and (user.is_staff or user.is_superuser):
            raise serializers.ValidationError(
                {"detail": "Admins are not allowed to create reservations."}
            )

        # Studente: prenotazione solo nello stesso giorno
        if getattr(user, "role", None) == "student" and start and end:
            if start.date() != end.date():
                raise serializers.ValidationError(
                    {"detail": "Students can only create reservations within the same day."}
                )

        # Controllo overlapping per lo stesso utente
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
                    {"detail": "You already have a reservation in this timeslot."}
                )

        return attrs

    def create(self, validated_data):
        return super().create(validated_data)