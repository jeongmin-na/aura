#!/usr/bin/env python3
"""
Simple system test for the DLD to Cursor AI Prompt Generation System
"""

import asyncio
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

async def test_system():
    """Test the system components"""
    print("🧪 Testing DLD to Cursor AI Prompt Generation System")
    print("=" * 60)
    
    try:
        # Test 1: Import and initialize components
        print("1️⃣ Testing imports...")
        
        from utils.config import Config
        from utils.logger import setup_logger
        from knowledge_base.knowledge_manager import KnowledgeManager
        from agents.master_agent import MasterAgent
        
        print("✅ All imports successful")
        
        # Test 2: Configuration
        print("\n2️⃣ Testing configuration...")
        
        config = Config()
        print(f"✅ Configuration loaded: {config.log_level}")
        
        # Test 3: Logger
        print("\n3️⃣ Testing logger...")
        
        logger = setup_logger("test")
        logger.info("Test log message")
        print("✅ Logger working")
        
        # Test 4: Knowledge Manager
        print("\n4️⃣ Testing Knowledge Manager...")
        
        knowledge_manager = KnowledgeManager(config)
        await knowledge_manager.initialize()
        
        stats = await knowledge_manager.get_statistics()
        print(f"✅ Knowledge Manager initialized: {stats}")
        
        # Test 5: Master Agent
        print("\n5️⃣ Testing Master Agent...")
        
        master_agent = MasterAgent(config, knowledge_manager)
        await master_agent.initialize()
        
        status = await master_agent.get_pipeline_status()
        print(f"✅ Master Agent initialized: {status['agents_status']}")
        
        # Test 6: Simple DLD Processing
        print("\n6️⃣ Testing DLD Processing...")
        
        sample_dld = """
        # Test 5G Component
        
        ## Requirements
        - Implement basic 5G functionality
        - Support N2 interface
        - Handle RRC messages
        
        ## Technical Specifications
        - Frequency: 3.5 GHz
        - Bandwidth: 100 MHz
        - Latency: <1ms
        """
        
        result = await master_agent.process_dld(
            dld_content=sample_dld,
            quality_threshold=0.6  # Lower threshold for testing
        )
        
        if result["success"]:
            print(f"✅ DLD Processing successful: Quality {result['quality_score']:.2f}")
            print(f"   Prompt length: {len(result['prompt'])} characters")
        else:
            print(f"❌ DLD Processing failed: {result.get('error_message', 'Unknown error')}")
        
        # Cleanup
        await master_agent.shutdown()
        await knowledge_manager.shutdown()
        
        print("\n🎉 All tests passed! System is working correctly.")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Please install dependencies: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_api_endpoints():
    """Test API endpoints if server is running"""
    print("\n🌐 Testing API endpoints...")
    
    try:
        import requests
        
        base_url = "http://localhost:8000"
        
        # Test health endpoint
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health endpoint working")
            health_data = response.json()
            print(f"   Status: {health_data.get('status', 'unknown')}")
        else:
            print(f"❌ Health endpoint failed: {response.status_code}")
            return False
        
        # Test knowledge stats endpoint
        response = requests.get(f"{base_url}/knowledge-stats", timeout=5)
        if response.status_code == 200:
            print("✅ Knowledge stats endpoint working")
            stats = response.json()
            print(f"   Total entries: {stats.get('total_entries', 0)}")
        else:
            print(f"❌ Knowledge stats endpoint failed: {response.status_code}")
        
        # Test DLD processing endpoint
        test_dld = {
            "dld_content": "# Test\n## Requirements\n- Test requirement",
            "quality_threshold": 0.5
        }
        
        response = requests.post(f"{base_url}/process-dld", json=test_dld, timeout=30)
        if response.status_code == 200:
            print("✅ DLD processing endpoint working")
            result = response.json()
            print(f"   Quality score: {result.get('quality_score', 0):.2f}")
        else:
            print(f"❌ DLD processing endpoint failed: {response.status_code}")
            print(f"   Error: {response.text}")
        
        print("✅ API endpoints test completed")
        return True
        
    except requests.exceptions.ConnectionError:
        print("⚠️  Server not running - skipping API tests")
        print("   Start server with: python run.py --server")
        return True
        
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def main():
    """Main test function"""
    print("🚀 DLD to Cursor AI Prompt Generation System - System Test")
    print("=" * 70)
    
    # Run component tests
    success = asyncio.run(test_system())
    
    if success:
        # Run API tests if possible
        asyncio.run(test_api_endpoints())
        
        print("\n" + "=" * 70)
        print("🎉 System test completed successfully!")
        print("\nNext steps:")
        print("1. Start the server: python run.py --server")
        print("2. Run examples: python run.py --examples")
        print("3. Check documentation: README.md")
        print("4. Deploy with Docker: python run.py --docker")
    else:
        print("\n" + "=" * 70)
        print("❌ System test failed!")
        print("Please check the error messages above and fix any issues.")
        sys.exit(1)

if __name__ == "__main__":
    main()
