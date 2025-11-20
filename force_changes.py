import os
import django
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'supply_chain_project.settings')
django.setup()

from agents.models import NetworkNode

print("Forcing inventory changes...")

nodes = NetworkNode.objects.all()
for node in nodes:
    old_inventory = node.current_inventory
    # Randomly change inventory by -500 to +500
    change = random.randint(-500, 500)
    node.current_inventory = max(0, min(node.current_inventory + change, node.inventory_capacity))
    node.save()
    print(f"{node.code}: {old_inventory} → {node.current_inventory} (change: {change:+d})")

print("\n✓ Changes applied! Refresh your dashboard to see the updates.")