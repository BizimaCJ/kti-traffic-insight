from django.db import models


class Intersection(models.Model):
    class NodeType(models.TextChoices):
        TERMINAL = "TERMINAL", "Terminal"
        JUNCTION = "JUNCTION", "Junction"

    name = models.CharField(max_length=120, unique=True)
    node_type = models.CharField(max_length=20, choices=NodeType.choices, default=NodeType.JUNCTION)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    # Position on the schematic map shown in the app (0-100 on both axes)
    map_x = models.FloatField(default=50)
    map_y = models.FloatField(default=50)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name


class Road(models.Model):
    name = models.CharField(max_length=160, unique=True)
    length_km = models.FloatField()
    start_intersection = models.ForeignKey(Intersection, on_delete=models.PROTECT, related_name="roads_starting")
    end_intersection = models.ForeignKey(Intersection, on_delete=models.PROTECT, related_name="roads_ending")

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.name
