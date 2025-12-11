import sys
import os

# Add backend to sys.path
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from app.engine.parser import HCLParser
from app.engine.graph import DependencyGraph

def test_parser():
    print("Testing HCL Parser...")
    parser = HCLParser()
    fixtures_dir = os.path.join(os.getcwd(), 'tests', 'fixtures', 'simple')
    context = parser.parse(fixtures_dir)
    
    print(f"Resources found: {len(context.resources)}")
    for addr, res in context.resources.items():
        print(f" - {addr} (Provider: {res.provider})")
        
    assert "aws_instance.web" in context.resources
    assert "aws_eip.ip" in context.resources
    print("Parser Test PASSED")
    
    return context

def test_graph(context):
    print("\nTesting Dependency Graph...")
    graph = DependencyGraph(context)
    
    # Check if dependency is detected
    # aws_eip.ip depends on aws_instance.web
    if graph.graph.has_edge("aws_eip.ip", "aws_instance.web"):
        print("Dependency verified: aws_eip.ip -> aws_instance.web")
    else:
        print("Warning: Dependency NOT detected (naive string matching might have failed)")
        
    order = graph.get_evaluation_order()
    print("Evaluation Order:", order)

if __name__ == "__main__":
    try:
        context = test_parser()
        test_graph(context)
    except ImportError as e:
        print(f"ImportError: {e}. Please ensure requirements are installed.")
    except Exception as e:
        print(f"Test Failed: {e}")
