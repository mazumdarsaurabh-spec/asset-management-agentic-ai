from django.contrib import admin
from .models import NetworkNode, Demand, AgentDecision

@admin.register(NetworkNode)
class NetworkNodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'node_type', 'current_inventory', 'inventory_capacity', 'is_active']
    list_filter = ['node_type', 'is_active']
    search_fields = ['code', 'name']

@admin.register(Demand)
class DemandAdmin(admin.ModelAdmin):
    list_display = ['node', 'quantity', 'forecast_quantity', 'period', 'timestamp']
    list_filter = ['period']
    search_fields = ['node__code', 'node__name']

@admin.register(AgentDecision)
class AgentDecisionAdmin(admin.ModelAdmin):
    list_display = ['agent_name', 'decision_type', 'urgency', 'source_node', 'destination_node','quantity', 'is_executed', 'created_at']
    list_filter = ['agent_name', 'decision_type', 'urgency', 'is_executed']
    search_fields = ['reason']

# Register your models here.
