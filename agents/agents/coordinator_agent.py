from .base_agent import BaseAgent
from .inventory_agent import InventoryAgent
from .transportation_agent import TransportationAgent
from .service_level_agent import ServiceLevelAgent
from .demand_forecast_agent import DemandForecastAgent
from typing import Dict, Any

class CoordinatorAgent(BaseAgent):
    """Orchestrates all agents"""
    
    def __init__(self):
        super().__init__("Coordinator", priority=0)
        self.agents = {
            'demand_forecast': DemandForecastAgent(),
            'inventory': InventoryAgent(),
            'transportation': TransportationAgent(),
            'service_level': ServiceLevelAgent()
        }
    
    def make_decision(self, state: Dict[str, Any]) -> Dict[str, Any]:
        results = {
            'forecasts': {},
            'inventory_decisions': [],
            'transport_decisions': [],
            'service_alerts': [],
            'logs': []
        }
        
        try:
            # Phase 1: Demand Forecasting
            forecast_result = self.agents['demand_forecast'].make_decision(state)
            results['forecasts'] = forecast_result.get('forecasts', {})
            results['logs'].append({'agent': 'demand_forecast', 'message': 'Forecasts generated'})
            
            state['forecasts'] = results['forecasts']
            
            # Phase 2: Inventory Management
            results['inventory_decisions'] = self.agents['inventory'].make_decision(state)
            results['logs'].append({'agent': 'inventory', 'message': f"{len(results['inventory_decisions'])} decisions"})
            
            state['inventory_decisions'] = results['inventory_decisions']
            
            # Phase 3: Transportation Optimization
            results['transport_decisions'] = self.agents['transportation'].make_decision(state)
            results['logs'].append({'agent': 'transportation', 'message': f"{len(results['transport_decisions'])} transports"})
            
            state['transport_decisions'] = results['transport_decisions']
            
            # Phase 4: Service Level Monitoring
            results['service_alerts'] = self.agents['service_level'].make_decision(state)
            results['logs'].append({'agent': 'service_level', 'message': f"{len(results['service_alerts'])} alerts"})
            
        except Exception as e:
            self.logger.error(f"Error in coordination: {str(e)}", exc_info=True)
        
        return results