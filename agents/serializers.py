from rest_framework import serializers
from .models import NetworkNode, Demand, AgentDecision

class NetworkNodeSerializer(serializers.ModelSerializer):
    inventory_ratio = serializers.SerializerMethodField()
    
    class Meta:
        model = NetworkNode
        fields = '__all__'
    
    def get_inventory_ratio(self, obj):
        if obj.inventory_capacity > 0:
            return obj.current_inventory / obj.inventory_capacity
        return 0


class DemandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demand
        fields = '__all__'


class AgentDecisionSerializer(serializers.ModelSerializer):
    source_node_name = serializers.CharField(source='source_node.name', read_only=True)
    destination_node_name = serializers.CharField(source='destination_node.name', read_only=True)
    source_node_code = serializers.CharField(source='source_node.code', read_only=True)
    destination_node_code = serializers.CharField(source='destination_node.code', read_only=True)
    
    
    class Meta:
        model = AgentDecision
        fields = '__all__'
    def get_source_node_name(self, obj):
        return obj.source_node.name if obj.source_node else None
    
    def get_source_node_code(self, obj):
        return obj.source_node.code if obj.source_node else None
    
    def get_destination_node_name(self, obj):
        return obj.destination_node.name if obj.destination_node else None
    
    def get_destination_node_code(self, obj):
        return obj.destination_node.code if obj.destination_node else None