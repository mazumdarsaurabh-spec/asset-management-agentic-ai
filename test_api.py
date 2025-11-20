import requests
import json

BASE_URL = "http://localhost:8000"

def test_endpoints():
    print("=" * 60)
    print("Testing Supply Chain API Endpoints")
    print("=" * 60)
    
    endpoints = [
        ('GET', '/api/', 'API Root'),
        ('GET', '/api/nodes/', 'List Nodes'),
        ('GET', '/api/decisions/', 'List Decisions'),
        ('GET', '/api/nodes/network_summary/', 'Network Summary'),
        ('POST', '/api/nodes/initialize_network/', 'Initialize Network'),
    ]
    
    for method, endpoint, description in endpoints:
        url = BASE_URL + endpoint
        print(f"\n{description}:")
        print(f"  {method} {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)
            
            print(f"  Status: {response.status_code}")
            
            if response.status_code == 200:
                print("  ✓ SUCCESS")
            elif response.status_code == 201:
                print("  ✓ CREATED")
            elif response.status_code == 404:
                print("  ✗ NOT FOUND - Check URL configuration")
            else:
                print(f"  ⚠ Response: {response.status_code}")
                
        except requests.exceptions.ConnectionError:
            print("  ✗ CONNECTION ERROR - Is the server running?")
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_endpoints()