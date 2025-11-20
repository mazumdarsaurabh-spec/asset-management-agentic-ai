from .base_agent import BaseAgent
from typing import Dict, List, Any

class InventoryAgent(BaseAgent):
    """Agent responsible for inventory level management"""
    
    def __init__(self):
        super().__init__("InventoryManager", priority=2)
        self.reorder_point = 0.30  # 30% of capacity
        self.target_level = 0.70   # 70% of capacity
        self.safety_stock = 0.15   # 15% safety stock
    
    def make_decision(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.validate_state(state, ['nodes', 'demands']):
            return []
        
        decisions = []
        nodes = state['nodes']
        demands = state.get('demands', {})
        forecasts = state.get('forecasts', {})
        
        for node in nodes:
            if not node.get('is_active', True):
                continue
            
            node_id = node['id']
            inventory = node['current_inventory']
            capacity = node['inventory_capacity']
            inventory_ratio = inventory / capacity if capacity > 0 else 0
            
            # Get demand data
            current_demand = demands.get(node_id, 0)
            forecast_demand = forecasts.get(node_id, current_demand * 1.2)
            
            # Calculate days of supply
            days_of_supply = inventory / current_demand if current_demand > 0 else float('inf')
            
            # Reorder decision
            if inventory_ratio < self.reorder_point or days_of_supply < 7:
                order_quantity = int((self.target_level * capacity) - inventory)
                safety_qty = int(self.safety_stock * capacity)
                order_quantity += safety_qty
                
                urgency = self._calculate_urgency(inventory_ratio, days_of_supply)
                
                decisions.append({
                    'type': 'REORDER',
                    'agent': self.name,
                    'node_id': node_id,
                    'node_code': node['code'],
                    'quantity': order_quantity,
                    'urgency': urgency,
                    'reason': f"Inventory at {inventory_ratio*100:.1f}% ({days_of_supply:.1f} days supply)",
                    'metadata': {
                        'current_inventory': inventory,
                        'target_inventory': int(self.target_level * capacity),
                        'forecast_demand': forecast_demand,
                        'days_of_supply': days_of_supply
                    }
                })
                
                self.log_decision('REORDER', 
                                f"Reorder triggered for {node['code']}: {order_quantity} units",
                                {'urgency': urgency})
            
            # Excess inventory redistribution
            elif inventory_ratio > 0.90:
                excess_quantity = int(inventory - (self.target_level * capacity))
                
                decisions.append({
                    'type': 'REDISTRIBUTE',
                    'agent': self.name,
                    'node_id': node_id,
                    'node_code': node['code'],
                    'quantity': excess_quantity,
                    'urgency': 'LOW',
                    'reason': f"Excess inventory detected: {inventory_ratio*100:.1f}%",
                    'metadata': {
                        'current_inventory': inventory,
                        'excess_amount': excess_quantity
                    }
                })
        
        return decisions
    
    def _calculate_urgency(self, inventory_ratio: float, days_of_supply: float) -> str:
        if inventory_ratio < 0.10 or days_of_supply < 3:
            return 'CRITICAL'
        elif inventory_ratio < 0.20 or days_of_supply < 5:
            return 'HIGH'
        elif inventory_ratio < 0.30 or days_of_supply < 7:
            return 'MEDIUM'
        return 'LOW'