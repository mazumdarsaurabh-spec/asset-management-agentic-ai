from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'nodes', views.NetworkNodeViewSet, basename='networknode')
router.register(r'decisions', views.AgentDecisionViewSet, basename='agentdecision')
router.register(r'demands', views.DemandViewSet, basename='demand')

urlpatterns = [
    # The root path (/) now explicitly points to live_demo.html
    path('', views.live_demo_view, name='live_demo'),
    
    # API endpoints
    path('api/', include(router.urls)), 
    
    # Secondary demo dashboard view
    path('demo/', views.demo_dashboard_view, name='demo_dashboard'),
]
