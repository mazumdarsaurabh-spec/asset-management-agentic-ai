# views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from django.db.models import Sum
from django.utils import timezone
from .models import NetworkNode, Demand, AgentDecision
from .serializers import NetworkNodeSerializer, DemandSerializer, AgentDecisionSerializer
from .agents.coordinator_agent import CoordinatorAgent
import random
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import traceback

class NetworkNodeViewSet(viewsets.ModelViewSet):
    queryset = NetworkNode.objects.all()
    serializer_class = NetworkNodeSerializer

    @csrf_exempt
    @action(detail=False, methods=['post'])
    def initialize_network(self, request):
        """Initialize network with sample nodes"""
        nodes_data = [
            {'name': 'Distribution Center 1', 'code': 'DC1', 'node_type': 'DC',
             'latitude': 40.7128, 'longitude': -74.0060, 'inventory_capacity': 10000, 'current_inventory': 5000},
            {'name': 'Distribution Center 2', 'code': 'DC2', 'node_type': 'DC',
             'latitude': 34.0522, 'longitude': -118.2437, 'inventory_capacity': 10000, 'current_inventory': 4500},
            {'name': 'Warehouse 1', 'code': 'WH1', 'node_type': 'WH',
             'latitude': 41.8781, 'longitude': -87.6298, 'inventory_capacity': 15000, 'current_inventory': 8000},
            {'name': 'Warehouse 2', 'code': 'WH2', 'node_type': 'WH',
             'latitude': 29.7604, 'longitude': -95.3698, 'inventory_capacity': 15000, 'current_inventory': 7500},
            {'name': 'Store 1', 'code': 'STORE1', 'node_type': 'STORE',
             'latitude': 41.4993, 'longitude': -81.6944, 'inventory_capacity': 2000, 'current_inventory': 500},
            {'name': 'Store 2', 'code': 'STORE2', 'node_type': 'STORE',
             'latitude': 33.4484, 'longitude': -112.0740, 'inventory_capacity': 2000, 'current_inventory': 600},
            {'name': 'Store 3', 'code': 'STORE3', 'node_type': 'STORE',
             'latitude': 47.6062, 'longitude': -122.3321, 'inventory_capacity': 2000, 'current_inventory': 450},
        ]

        created_nodes = []
        updated_nodes = []

        try:
            for node_data in nodes_data:
                node, created = NetworkNode.objects.get_or_create(
                    code=node_data['code'],
                    defaults=node_data
                )

                if not created:
                    # Node exists, update it instead
                    for key, value in node_data.items():
                        if key != 'code':  # Don't update the unique code
                            setattr(node, key, value)
                    node.save()
                    updated_nodes.append(node)
                else:
                    created_nodes.append(node)

            all_nodes = created_nodes + updated_nodes
            serializer = self.get_serializer(all_nodes, many=True)

            message = f'Network ready! '
            if created_nodes:
                message += f'Created {len(created_nodes)} new nodes. '
            if updated_nodes:
                message += f'Updated {len(updated_nodes)} existing nodes.'

            return Response({
                'status': 'success',
                'message': message,
                'created': len(created_nodes),
                'updated': len(updated_nodes),
                'total': len(all_nodes),
                'nodes': serializer.data
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            traceback.print_exc()
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def network_summary(self, request):
        """Get network summary statistics"""
        nodes = NetworkNode.objects.filter(is_active=True)

        summary = {
            'total_nodes': nodes.count(),
            'total_capacity': nodes.aggregate(Sum('inventory_capacity'))['inventory_capacity__sum'] or 0,
            'total_inventory': nodes.aggregate(Sum('current_inventory'))['current_inventory__sum'] or 0,
            'by_type': {}
        }

        for node_type, _ in NetworkNode.NODE_TYPES:
            type_nodes = nodes.filter(node_type=node_type)
            summary['by_type'][node_type] = {
                'count': type_nodes.count(),
                'total_inventory': type_nodes.aggregate(Sum('current_inventory'))['current_inventory__sum'] or 0,
                'total_capacity': type_nodes.aggregate(Sum('inventory_capacity'))['inventory_capacity__sum'] or 0
            }

        summary['utilization_rate'] = (summary['total_inventory'] / summary['total_capacity'] * 100) if summary['total_capacity'] > 0 else 0

        # Optionally include cost summary if you compute & store them server-side
        # summary['total_transport_cost'] = ...
        # summary['total_service_level_cost'] = ...

        return Response(summary)

    @action(detail=False, methods=['post'])
    def reset_network(self, request):
        """Delete all nodes and reinitialize"""
        try:
            # Delete all existing nodes
            deleted_count = NetworkNode.objects.all().delete()[0]

            # Reinitialize
            return self.initialize_network(request)

        except Exception as e:
            traceback.print_exc()
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AgentDecisionViewSet(viewsets.ModelViewSet):
    queryset = AgentDecision.objects.all()
    serializer_class = AgentDecisionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()

        agent_name = self.request.query_params.get('agent', None)
        if agent_name:
            queryset = queryset.filter(agent_name=agent_name)

        decision_type = self.request.query_params.get('type', None)
        if decision_type:
            queryset = queryset.filter(decision_type=decision_type)

        urgency = self.request.query_params.get('urgency', None)
        if urgency:
            queryset = queryset.filter(urgency=urgency)

        return queryset.order_by('-created_at')

    @csrf_exempt
    @action(detail=False, methods=['post'])
    def run_agent_cycle(self, request):
        """Execute one cycle of agent decision-making"""
        try:
            nodes = NetworkNode.objects.filter(is_active=True)

            if nodes.count() == 0:
                return Response({
                    'status': 'error',
                    'message': 'No nodes found. Please initialize network first.'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Generate demands
            demands = self._generate_demands(nodes)

            # Prepare state for agents
            state = {
                'nodes': [
                    {
                        'id': str(node.id),
                        'code': node.code,
                        'name': node.name,
                        'node_type': node.node_type,
                        'current_inventory': node.current_inventory,
                        'inventory_capacity': node.inventory_capacity,
                        'latitude': node.latitude,
                        'longitude': node.longitude,
                        'is_active': node.is_active
                    } for node in nodes
                ],
                'demands': demands
            }

            # Run coordinator agent
            coordinator = CoordinatorAgent()
            results = coordinator.make_decision(state)

            # --- Compute totals here so frontend gets them ---
            # Total transport cost: sum estimated_cost fields on transport_decisions
            total_transport_cost = 0
            for td in results.get('transport_decisions', []):
                # estimated_cost could be number or string; coerce safely
                try:
                    total_transport_cost += float(td.get('estimated_cost', 0) or 0)
                except Exception:
                    total_transport_cost += 0

            # Service level cost: a simple heuristic based on alert urgency (customize as needed)
            URGENCY_COST = {
                'CRITICAL': 500.0,
                'HIGH': 200.0,
                'MEDIUM': 50.0,
                'LOW': 10.0
            }
            total_service_level_cost = 0
            for alert in results.get('service_alerts', []):
                urgency = alert.get('urgency', 'MEDIUM')
                total_service_level_cost += URGENCY_COST.get(urgency.upper(), 50.0)

            # Save decisions in DB
            saved_decisions = self._save_decisions(results)

            # Execute transport decisions (update inventories)
            self._execute_transport_decisions(results.get('transport_decisions', []))

            return Response({
                'status': 'success',
                'results': {
                    'inventory_decisions': len(results.get('inventory_decisions', [])),
                    'transport_decisions': len(results.get('transport_decisions', [])),
                    'service_alerts': len(results.get('service_alerts', [])),
                    'total_transport_cost': round(total_transport_cost, 2),
                    'total_service_level_cost': round(total_service_level_cost, 2),
                    'logs': results.get('logs', []),
                },
                'saved_decisions': len(saved_decisions),
                'decisions': AgentDecisionSerializer(saved_decisions, many=True).data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            traceback.print_exc()
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_demands(self, nodes):
        """Generate random demands for nodes"""
        demands = {}
        today = timezone.now().date()

        for node in nodes:
            if node.node_type == 'STORE':
                demand_qty = random.randint(100, 300)
            elif node.node_type == 'DC':
                demand_qty = random.randint(50, 200)
            else:
                demand_qty = random.randint(30, 150)

            demands[str(node.id)] = demand_qty

            # Save to database
            Demand.objects.create(
                node=node,
                quantity=demand_qty,
                period=today
            )

        return demands

    def _save_decisions(self, results):
        """Save agent decisions to database"""
        saved_decisions = []

        # Save inventory decisions
        for decision in results.get('inventory_decisions', []):
            node = NetworkNode.objects.get(id=decision['node_id'])

            agent_decision = AgentDecision.objects.create(
                agent_name=decision.get('agent', 'ReorderAgent'),
                decision_type=decision.get('type', 'REORDER'),
                urgency=decision.get('urgency', 'MEDIUM'),
                destination_node=node,
                quantity=decision.get('quantity'),
                reason=decision.get('reason', '')
            )
            saved_decisions.append(agent_decision)

        # Save transport decisions
        for decision in results.get('transport_decisions', []):
            from_node = NetworkNode.objects.get(id=decision['from_node_id'])
            to_node = NetworkNode.objects.get(id=decision['to_node_id'])

            agent_decision = AgentDecision.objects.create(
                agent_name=decision.get('agent', 'TransportPlanner'),
                decision_type=decision.get('type', 'TRANSPORT'),
                urgency=decision.get('urgency', 'MEDIUM'),
                source_node=from_node,
                destination_node=to_node,
                quantity=decision.get('quantity'),
                estimated_cost=decision.get('estimated_cost'),
                reason=decision.get('reason', '')
            )
            saved_decisions.append(agent_decision)

        # Save service alerts
        for alert in results.get('service_alerts', []):
            node = NetworkNode.objects.get(id=alert['node_id'])

            agent_decision = AgentDecision.objects.create(
                agent_name=alert.get('agent', 'MonitorAgent'),
                decision_type=alert.get('type', 'SERVICE_ALERT'),
                urgency=alert.get('urgency', 'MEDIUM'),
                destination_node=node,
                reason=alert.get('reason', '')
            )
            saved_decisions.append(agent_decision)

        return saved_decisions

    def _execute_transport_decisions(self, transport_decisions):
        """Execute transportation decisions and update inventory"""
        for decision in transport_decisions:
            try:
                from_node = NetworkNode.objects.get(id=decision['from_node_id'])
                to_node = NetworkNode.objects.get(id=decision['to_node_id'])
                quantity = int(decision.get('quantity', 0))

                if from_node.current_inventory >= quantity:
                    from_node.current_inventory -= quantity
                    to_node.current_inventory = min(
                        to_node.current_inventory + quantity,
                        to_node.inventory_capacity
                    )

                    from_node.save()
                    to_node.save()

            except Exception as e:
                # log and continue
                print(f"Error executing transport decision: {str(e)}")
                continue


class DemandViewSet(viewsets.ModelViewSet):
    queryset = Demand.objects.all()
    serializer_class = DemandSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        node_id = self.request.query_params.get('node', None)
        if node_id:
            queryset = queryset.filter(node_id=node_id)
        return queryset.order_by('-timestamp')


def dashboard_view(request):
    """Render the React dashboard"""
    return render(request, 'dashboard.html')


def demo_dashboard_view(request):
    return render(request, 'demo_dashboard.html')


def live_demo_view(request):
    return render(request, 'live_demo.html')


@api_view(['POST'])
def simulate_auto_changes(request):
    nodes = NetworkNode.objects.all()
    for node in nodes:
        # Randomly adjust current inventory (+/- 10% or fixed -500..+500)
        change = random.randint(-500, 500)
        node.current_inventory = max(0, min(node.inventory_capacity, node.current_inventory + change))
        node.save()
    return Response({"status": "auto simulation complete"})
