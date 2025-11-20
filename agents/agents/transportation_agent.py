from .base_agent import BaseAgent
from typing import Dict, List, Any
import math

class TransportationAgent(BaseAgent):
    """Agent responsible for transportation optimization"""
    
    def __init__(self):
        super().__init__("TransportationOptimizer", priority=2)
        self.cost_per_mile = 2.5
        self.cost_per_unit = 0.5
    
    def make_decision(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not self.validate_state(state, ['nodes', 'inventory_decisions']):
            return []
        
        decisions = []
        nodes = state['nodes']
        inventory_decisions = state['inventory_decisions']
        
        # Process reorder decisions
        reorder_decisions = [d for d in inventory_decisions if d['type'] == 'REORDER']
        
        for reorder in reorder_decisions:
            dest_node = next((n for n in nodes if n['id'] == reorder['node_id']), None)
            if not dest_node:
                continue
            
            # Find best source node
            best_route = self._find_optimal_route(
                dest_node,
                reorder['quantity'],
                nodes,
                reorder['urgency']
            )
            
            if best_route:
                decisions.append({
                    'type': 'TRANSPORT',
                    'agent': self.name,
                    'from_node_id': best_route['source_id'],
                    'from_node_code': best_route['source_code'],
                    'to_node_id': dest_node['id'],
                    'to_node_code': dest_node['code'],
                    'quantity': reorder['quantity'],
                    'estimated_cost': best_route['cost'],
                    'distance': best_route['distance'],
                    'urgency': reorder['urgency'],
                    'reason': f"Optimal route: {best_route['source_code']} → {dest_node['code']}",
                    'metadata': {
                        'transit_time': best_route['transit_time'],
                        'cost_breakdown': best_route['cost_breakdown']
                    }
                })
        
        return decisions
    
    def _find_optimal_route(self, dest_node: Dict, quantity: int, 
                           all_nodes: List[Dict], urgency: str) -> Dict:
        """Find the optimal source node and route"""
        best_route = None
        lowest_cost = float('inf')
        
        for source_node in all_nodes:
            if (source_node['id'] == dest_node['id'] or 
                not source_node.get('is_active', True) or
                source_node['current_inventory'] < quantity):
                continue
            
            distance = self._calculate_distance(
                source_node['latitude'], source_node['longitude'],
                dest_node['latitude'], dest_node['longitude']
            )
            
            transport_cost = distance * self.cost_per_mile
            handling_cost = quantity * self.cost_per_unit
            total_cost = transport_cost + handling_cost
            
            if urgency == 'CRITICAL':
                total_cost *= 1.5
            elif urgency == 'HIGH':
                total_cost *= 1.2
            
            if total_cost < lowest_cost:
                lowest_cost = total_cost
                transit_time = self._estimate_transit_time(distance, urgency)
                
                best_route = {
                    'source_id': source_node['id'],
                    'source_code': source_node['code'],
                    'distance': distance,
                    'cost': total_cost,
                    'transit_time': transit_time,
                    'cost_breakdown': {
                        'transport': transport_cost,
                        'handling': handling_cost
                    }
                }
        
        return best_route
    
    def _calculate_distance(self, lat1: float, lon1: float, 
                          lat2: float, lon2: float) -> float:
        """Calculate haversine distance between two points in miles"""
        R = 3959  # Earth radius in miles
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat / 2) ** 2 + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _estimate_transit_time(self, distance: float, urgency: str) -> int:
        """Estimate transit time in hours"""
        base_speed = 50
        
        if urgency == 'CRITICAL':
            base_speed = 65
        elif urgency == 'HIGH':
            base_speed = 55
        
        return int(distance / base_speed)