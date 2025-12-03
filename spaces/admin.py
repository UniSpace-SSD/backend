from django.contrib import admin

from spaces.models import Building, Equipment, Space

admin.site.register(Space)
admin.site.register(Building)
admin.site.register(Equipment)