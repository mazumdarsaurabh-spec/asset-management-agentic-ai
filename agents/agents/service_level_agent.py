from .base_agent import BaseAgent
from typing import Dict, List, Any

class ServiceLevelAgent(BaseAgent):
    """Agent responsible for monitoring service levels"""
    
    def __init__(self):
        super().__init__("ServiceLevelMonitor", priority=3)
        self.target_service_level = 0.95
        self.critical_threshold = 0.80
    
    def make_decision(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.validate_state(state, ['nodes', 'demands']):
            return []
        
        decisions = []
        nodes = state['nodes']
        demands = state.get('demands', {})
        transport_decisions = state.get('transport_decisions', [])
        
        for node in nodes:
            node_id = node['id']
            current_inventory = node['current_inventory']
            current_demand = demands.get(node_id, 0)
            
            if current_demand == 0:
                continue
            
            incoming_qty = sum(
                t['quantity'] for t in transport_decisions 
                if t.get('to_node_id') == node_id
            )
            
            total_available = current_inventory + incoming_qty
            service_level = min(total_available / current_demand, 1.0) if current_demand > 0 else 1.0
            
            if service_level < self.target_service_level:
                shortfall = max(0, current_demand - total_available)
                urgency = 'CRITICAL' if service_level < self.critical_threshold else 'HIGH'
                
                decisions.append({
                    'type': 'SERVICE_ALERT',
                    'agent': self.name,
                    'node_id': node_id,
                    'node_code': node['code'],
                    'current_service_level': service_level,
                    'target_service_level': self.target_service_level,
                    'shortfall': shortfall,
                    'urgency': urgency,
                    'reason': f"Service level at {service_level*100:.1f}%",
                    'metadata': {
                        'current_inventory': current_inventory,
                        'incoming_shipments': incoming_qty,
                        'current_demand': current_demand
                    }
                })
        
        return decisions