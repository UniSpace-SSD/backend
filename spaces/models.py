import uuid
from django.db import models


class SpaceType(models.TextChoices):
    ROOM = "ROOM", "Room"
    LAB = "LAB", "Laboratory"
    AUDITORIUM = "AUDITORIUM", "Auditorium"
    MEETING_ROOM = "MEETING_ROOM", "Meeting room"
    LIBRARY = "LIBRARY", "Library"


class Building(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True,
          primary_key=True, editable=False)
    
    name = models.CharField(max_length=255)
    
    address = models.CharField(max_length=255) # TODO: VALUE OBJECT

    def __str__(self) -> str:
        return f"{self.id} - {self.name}" # TODO


# Equipment available in spaces
class Equipment(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Space(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True,
          primary_key=True, editable=False)
    
    name = models.CharField(max_length=255)

    type = models.CharField(
        max_length=20,
        choices=SpaceType.choices,
        default=SpaceType.ROOM,
    )

    building = models.ForeignKey(
        Building,
        on_delete=models.PROTECT,
        related_name="spaces",
    )

    floor = models.IntegerField(
        help_text="Piano in cui si trova lo spazio",
        default=0,
    )

    capacity = models.PositiveIntegerField(
        help_text="Numero massimo di persone ammesse"
    )

    equipments = models.ManyToManyField(
        Equipment,
        related_name="spaces",
        blank=True,
    )

    def __str__(self) -> str:
        return f"{self.building.name} - {self.name}"