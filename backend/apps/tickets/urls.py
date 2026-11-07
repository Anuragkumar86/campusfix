from rest_framework.routers import SimpleRouter

from .views import TicketViewSet

router = SimpleRouter()
router.register("", TicketViewSet, basename="ticket")
urlpatterns = router.urls
