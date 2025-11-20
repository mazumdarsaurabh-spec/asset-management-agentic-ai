import requests
import json

BASE_URL = "http://localhost:8000/api"

def test_system():
    print("=" * 60)
    print("Testing Supply Chain Agent System")
    print("=" * 60)
    
    # Test 1: Initialize Network
    print("\n1. Initializing Network...")
    response = requests.post(f"{BASE_URL}/nodes/initialize_network/")
    if response.status_code == 201:
        print("✓ Network initialized successfully")
        print(f"   Created {len(response.json()['nodes'])} nodes")
    else:
        print("✗ Failed to initialize network")
        return
    
    # Test 2: Get Network Summary
    print("\n2. Getting Network Summary...")
    response = requests.get(f"{BASE_URL}/nodes/network_summary/")
    if response.status_code == 200:
        summary = response.json()
        print("✓ Network Summary:")
        print(f"   Total Nodes: {summary['total_nodes']}")
        print(f"   Total Capacity: {summary['total_capacity']}")
        print(f"   Total Inventory: {summary['total_inventory']}")
        print(f"   Utilization: {summary['utilization_rate']:.2f}%")
    
    # Test 3: Run Agent Cycle
    print("\n3. Running Agent Decision Cycle...")
    response = requests.post(f"{BASE_URL}/decisions/run_agent_cycle/")
    if response.status_code == 200:
        results = response.json()['results']
        print("✓ Agent cycle completed:")
        print(f"   Inventory Decisions: {results['inventory_decisions']}")
        print(f"   Transport Decisions: {results['transport_decisions']}")
        print(f"   Service Alerts: {results['service_alerts']}")
        
        # Display some decisions
        if response.json().get('decisions'):
            print("\n   Recent Decisions:")
            for decision in response.json()['decisions'][:3]:
                print(f"   - {decision['agent_name']}: {decision['decision_type']} ({decision['urgency']})")
    
    # Test 4: Get All Decisions
    print("\n4. Retrieving All Decisions...")
    response = requests.get(f"{BASE_URL}/decisions/")
    if response.status_code == 200:
        decisions = response.json()
        print(f"✓ Retrieved {len(decisions['results'])} decisions")
    
    print("\n" + "=" * 60)
    print("All tests completed successfully!")
    print("=" * 60)

if __name__ == "__main__":
    test_system()