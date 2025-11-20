# agents/coordinator_agent.py
import math
from typing import Dict, Any, List

# Simple haversine distance (km)
def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))


class CoordinatorAgent:

    def __init__(
        self,
        target_utilization: float = 0.6,
        reorder_threshold: float = 0.35,
        transfer_threshold: float = 0.8,
        per_unit_transport_cost_km: float = 0.02
    ):
        self.target_utilization = float(target_utilization)
        self.reorder_threshold = float(reorder_threshold)
        self.transfer_threshold = float(transfer_threshold)
        self.per_unit_transport_cost_km = float(per_unit_transport_cost_km)

    def make_decision(self, state: Dict[str, Any]) -> Dict[str, Any]:

        nodes = state.get('nodes', [])
        demands = state.get('demands', {})

        logs = []
        inventory_decisions = []
        transport_decisions = []
        service_alerts = []
        forecasting_alerts = []

        node_map = {n['id']: n for n in nodes}
        donors = []

        # --------------------------------------------------------------------
        # ⭐ PHASE 1: Scan nodes for shortages, surplus & forecasting alerts
        # --------------------------------------------------------------------
        for n in nodes:

            cap = max(1, n['inventory_capacity'])
            curr = n['current_inventory']
            ratio = curr / cap
            target = cap * self.target_utilization
            node_id = n['id']
            demand_est = demands.get(node_id, 150)

            # ———————— ⭐ FORECAST ALERT ————————
            if demand_est > 0:
                cycles_left = curr / demand_est

                if cycles_left < 2:
                    forecasting_alerts.append({
                        'agent': 'ForecastAgent',
                        'node_id': node_id,
                        'type': 'FORECAST_ALERT',
                        'urgency': 'HIGH',
                        'reason': f"{n['name']} will stockout in {round(cycles_left,1)} cycles"
                    })
                    logs.append(f"[FORECAST] {n['code']} risk of stockout in {round(cycles_left,1)} cycles")

            # ———————— ⭐ CRITICAL SHORTAGE ALERT ————————
            if ratio < 0.15:
                service_alerts.append({
                    'agent': 'MonitorAgent',
                    'node_id': node_id,
                    'type': 'SERVICE_ALERT',
                    'urgency': 'CRITICAL',
                    'reason': f"Inventory dangerously low ({curr}/{cap})"
                })
                logs.append(f"[ALERT] {n['code']} CRITICAL low ({curr}/{cap})")

            # ———————— ⭐ REORDER (Receiver Node) ————————
            if ratio < self.reorder_threshold:
                need = int(max(1, target - curr))
                inventory_decisions.append({
                    'agent': 'ReorderAgent',
                    'node_id': node_id,
                    'type': 'REORDER',
                    'urgency': 'HIGH' if ratio < 0.2 else 'MEDIUM',
                    'quantity': need,
                    'reason': f"Below threshold ({ratio:.2f}), need {need}"
                })
                logs.append(f"[REORDER] {n['code']} needs {need}")

            # ———————— ⭐ SURPLUS (Donor Node) ————————
            if ratio > self.transfer_threshold:
                surplus = int(curr - target)
                if surplus > 0:
                    donors.append({
                        'id': node_id,
                        'code': n['code'],
                        'name': n['name'],
                        'lat': n['latitude'],
                        'lon': n['longitude'],
                        'surplus': surplus
                    })
                    logs.append(f"[DONOR] {n['code']} surplus {surplus}")

        # --------------------------------------------------------------------
        # ⭐ PHASE 2: Transport Planning (Donor → Receiver)
        # --------------------------------------------------------------------
        receivers = [{'id': d['node_id'], 'need': d['quantity']} for d in inventory_decisions]

        for rec in receivers:
            rnode = node_map.get(rec['id'])
            if not rnode:
                continue

            need_left = rec['need']

            donors_sorted = sorted(
                donors,
                key=lambda d: haversine_km(
                    rnode['latitude'], rnode['longitude'], d['lat'], d['lon']
                )
            )

            for donor in donors_sorted:
                if need_left <= 0 or donor['surplus'] <= 0:
                    continue

                qty = min(need_left, donor['surplus'])
                distance = haversine_km(
                    rnode['latitude'], rnode['longitude'], donor['lat'], donor['lon']
                )
                cost = round(distance * qty * self.per_unit_transport_cost_km, 2)

                transport_decisions.append({
                    'agent': 'TransportPlanner',
                    'from_node_id': donor['id'],
                    'to_node_id': rec['id'],
                    'type': 'TRANSPORT',
                    'urgency': 'HIGH' if distance > 200 else 'MEDIUM',
                    'quantity': qty,
                    'estimated_cost': cost,
                    'reason': f"Move {qty} units ({distance:.1f} km, cost ${cost})"
                })

                logs.append(
                    f"[TRANSPORT] {donor['code']} → {rnode['code']} qty {qty} cost ${cost}"
                )

                donor['surplus'] -= qty
                need_left -= qty

        # --------------------------------------------------------------------
        # ⭐ PHASE 3: Cost Calculations
        # --------------------------------------------------------------------
        total_transport_cost = sum(t['estimated_cost'] for t in transport_decisions)

        urgency_cost = {
            'CRITICAL': 50,
            'HIGH': 20,
            'MEDIUM': 5,
            'LOW': 0
        }

        # includes forecast alerts + service alerts
        total_service_level_cost = sum(
            urgency_cost.get(a['urgency'], 0)
            for a in service_alerts + forecasting_alerts
        )

        # --------------------------------------------------------------------
        # ⭐ FINAL OUTPUT
        # --------------------------------------------------------------------
        results = {
            'inventory_decisions': inventory_decisions,
            'transport_decisions': transport_decisions,
            'service_alerts': service_alerts + forecasting_alerts,
            'total_transport_cost': round(total_transport_cost, 2),
            'total_service_level_cost': round(total_service_level_cost, 2),
            'logs': logs
        }

        return results
