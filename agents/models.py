from django.db import models
import uuid

class NetworkNode(models.Model):
    NODE_TYPES = [
        ('DC', 'Distribution Center'),
        ('WH', 'Warehouse'),
        ('STORE', 'Store'),
        ('SUPPLIER', 'Supplier'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    node_type = models.CharField(max_length=20, choices=NODE_TYPES)
    
    # Location
    latitude = models.FloatField()
    longitude = models.FloatField()
    
    # Capacity
    inventory_capacity = models.IntegerField()
    current_inventory = models.IntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'network_nodes'
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Demand(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    node = models.ForeignKey(NetworkNode, on_delete=models.CASCADE, related_name='demands')
    quantity = models.IntegerField()
    forecast_quantity = models.IntegerField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    period = models.DateField()
    
    class Meta:
        db_table = 'demands'


class AgentDecision(models.Model):
    DECISION_TYPES = [
        ('REORDER', 'Reorder'),
        ('REDISTRIBUTE', 'Redistribute'),
        ('TRANSPORT', 'Transport'),
        ('SERVICE_ALERT', 'Service Alert'),
        ('FORECAST', 'Demand Forecast'),
    ]
    
    URGENCY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('CRITICAL', 'Critical'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_name = models.CharField(max_length=100)
    decision_type = models.CharField(max_length=20, choices=DECISION_TYPES)
    urgency = models.CharField(max_length=20, choices=URGENCY_LEVELS, default='MEDIUM')
    
    # Related entities
    source_node = models.ForeignKey(NetworkNode, on_delete=models.CASCADE, 
                                   related_name='source_decisions', null=True, blank=True)
    destination_node = models.ForeignKey(NetworkNode, on_delete=models.CASCADE,
                                        related_name='destination_decisions', null=True, blank=True)
    
    # Decision data
    quantity = models.IntegerField(null=True, blank=True)
    estimated_cost = models.FloatField(null=True, blank=True)
    reason = models.TextField()
    
    # Status
    is_executed = models.BooleanField(default=False)
    executed_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'agent_decisions'
    
    def __str__(self):
        return f"{self.agent_name} - {self.decision_type}"