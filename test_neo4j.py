from whats_eat.app.env_loader import load_env
from neo4j import GraphDatabase
import os
import ssl
import certifi

# Disable SSL certificate verification (for development only)
ssl._create_default_https_context = ssl._create_unverified_context

load_env()

# Get credentials
uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USER')
pwd = os.getenv('NEO4J_PASSWORD')

print(f'Connecting to {uri}...')

# Connect and test
driver = GraphDatabase.driver(uri, auth=(user, pwd))
with driver.session() as session:
    # Test query
    result = session.run('MATCH (n) RETURN count(n) as count')
    print(f'Node count: {result.single()["count"]}')
    print('Connected successfully!')
    
    # Test write
    print('Testing write...')
    result = session.run(
        'CREATE (n:Test {name: $name}) RETURN n',
        name='test_node'
    )
    print('Write test passed!')
    
    # Cleanup
    session.run(
        'MATCH (n:Test {name: $name}) DELETE n',
        name='test_node'
    )

driver.close()
print('All tests completed!')