from .base_agent import BaseAgent
from typing import Dict, List, Any
from collections import defaultdict, deque
import numpy as np

class DemandForecastAgent(BaseAgent):
    """Agent responsible for demand forecasting"""
    
    def __init__(self):
        super().__init__("DemandForecaster", priority=1)
        self.historical_data = defaultdict(lambda: deque(maxlen=30))
    
    def make_decision(self, state: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_state(state, ['nodes', 'demands']):
            return {}
        
        forecasts = {}
        nodes = state['nodes']
        current_demands = state['demands']
        
        for node in nodes:
            node_id = node['id']
            current_demand = current_demands.get(node_id, 0)
            
            self.historical_data[node_id].append(current_demand)
            forecast = self._generate_forecast(node_id, node)
            forecasts[node_id] = forecast
        
        return {
            'type': 'FORECAST',
            'agent': self.name,
            'forecasts': forecasts
        }
    
    def _generate_forecast(self, node_id: str, node: Dict) -> int:
        """Generate demand forecast"""
        history = list(self.historical_data[node_id])
        
        if len(history) < 3:
            return int(np.mean(history)) if history else 0
        
        ma_forecast = np.mean(history[-7:]) if len(history) >= 7 else np.mean(history)
        
        weights = np.exp(np.linspace(-1, 0, len(history[-7:])))
        weights /= weights.sum()
        wma_forecast = np.average(history[-7:], weights=weights) if len(history) >= 7 else ma_forecast
        
        trend = 0
        if len(history) >= 7:
            x = np.arange(len(history))
            y = np.array(history)
            trend = np.polyfit(x, y, 1)[0]
        
        base_forecast = (ma_forecast * 0.4 + wma_forecast * 0.6)
        trend_adjustment = trend * 3
        
        node_type_multiplier = {
            'STORE': 1.1,
            'DC': 1.05,
            'WH': 1.0,
            'SUPPLIER': 0.95
        }.get(node.get('node_type', 'WH'), 1.0)
        
        final_forecast = (base_forecast + trend_adjustment) * node_type_multiplier
        
        return max(0, int(final_forecast))