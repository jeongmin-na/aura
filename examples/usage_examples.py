"""
Usage examples for the DLD to Cursor AI Prompt Generation System
"""

import asyncio
import json
from pathlib import Path
import requests

# Base URL for the API
BASE_URL = "http://localhost:8000"

def example_1_simple_text_processing():
    """Example 1: Process DLD from text content"""
    
    # Sample DLD content
    dld_content = """
    # 5G Base Station Implementation
    
    ## Requirements
    - Implement gNodeB functionality
    - Support N2 interface with AMF
    - Handle RRC connection management
    - Process uplink and downlink data
    
    ## Technical Specifications
    - Frequency: 3.5 GHz (n78 band)
    - Bandwidth: 100 MHz
    - MIMO: 4T4R configuration
    - Latency: <1ms for URLLC
    
    ## Implementation Notes
    - Use C++ for real-time processing
    - Implement proper error handling
    - Follow 3GPP specifications
    - Include comprehensive logging
    """
    
    # API request
    response = requests.post(
        f"{BASE_URL}/process-dld",
        json={
            "dld_content": dld_content,
            "output_format": "cursor_ai",
            "quality_threshold": 0.8,
            "include_feedback": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Processing successful!")
        print(f"Quality Score: {result['quality_score']:.2f}")
        print(f"Execution Time: {result.get('execution_time', 0):.2f}s")
        print("\n📝 Generated Prompt:")
        print(result['prompt'][:500] + "..." if len(result['prompt']) > 500 else result['prompt'])
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def example_2_file_upload():
    """Example 2: Upload DLD file and process"""
    
    # Sample DLD file path
    dld_file_path = Path("examples/sample_dld.md")
    
    if not dld_file_path.exists():
        print("❌ Sample DLD file not found. Please create examples/sample_dld.md first.")
        return
    
    # Upload file
    with open(dld_file_path, 'rb') as f:
        files = {'file': ('sample_dld.md', f, 'text/markdown')}
        data = {
            'output_format': 'cursor_ai',
            'quality_threshold': 0.85
        }
        
        response = requests.post(
            f"{BASE_URL}/upload-dld",
            files=files,
            data=data
        )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ File upload and processing successful!")
        print(f"Quality Score: {result['quality_score']:.2f}")
        
        # Save the generated prompt
        output_file = Path("output/generated_prompt.md")
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['prompt'])
        
        print(f"📄 Prompt saved to: {output_file}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def example_3_with_existing_project():
    """Example 3: Process DLD with existing project context"""
    
    dld_content = """
    # Enhanced RRC Connection Manager
    
    ## Requirements
    - Extend existing RRC implementation
    - Add support for dual connectivity
    - Implement connection release optimization
    - Add metrics collection
    
    ## Existing Code Integration
    - Build upon current RrcConnectionManager class
    - Reuse existing message handlers
    - Maintain backward compatibility
    - Follow existing coding patterns
    """
    
    # Include project path for context analysis
    response = requests.post(
        f"{BASE_URL}/process-dld",
        json={
            "dld_content": dld_content,
            "project_path": "/path/to/existing/5g/project",  # Update with actual path
            "output_format": "cursor_ai",
            "quality_threshold": 0.8
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Processing with project context successful!")
        print(f"Quality Score: {result['quality_score']:.2f}")
        
        # Show validation results
        validation = result.get('validation_results', {})
        print(f"📊 Validation Results:")
        print(f"  - Completeness: {validation.get('completeness_score', 0):.2f}")
        print(f"  - Consistency: {validation.get('consistency_score', 0):.2f}")
        
        # Show export formats
        export_formats = result.get('export_formats', {})
        print(f"📁 Available formats: {list(export_formats.keys())}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def example_4_multiple_formats():
    """Example 4: Generate multiple output formats"""
    
    dld_content = """
    # 5G Network Slice Manager
    
    ## Overview
    Implement a network slice management system for 5G core network.
    
    ## Requirements
    - Create slice instances dynamically
    - Manage slice lifecycle
    - Monitor slice performance
    - Implement SLA enforcement
    
    ## Technical Details
    - REST API for slice management
    - Integration with AMF and SMF
    - Database for slice configuration
    - Real-time monitoring dashboard
    """
    
    response = requests.post(
        f"{BASE_URL}/process-dld",
        json={
            "dld_content": dld_content,
            "output_format": "cursor_ai",
            "quality_threshold": 0.8
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        export_formats = result.get('export_formats', {})
        
        # Save different formats
        output_dir = Path("output/multi_format")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        for format_name, content in export_formats.items():
            if format_name == "structured_json":
                file_path = output_dir / f"prompt.json"
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(json.loads(content), f, indent=2, ensure_ascii=False)
            else:
                extension = ".md" if "md" in format_name else ".txt"
                file_path = output_dir / f"prompt_{format_name}{extension}"
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            print(f"📄 Saved {format_name} format to: {file_path}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def example_5_health_and_stats():
    """Example 5: Check system health and get statistics"""
    
    # Health check
    health_response = requests.get(f"{BASE_URL}/health")
    print("🏥 System Health:")
    print(json.dumps(health_response.json(), indent=2))
    
    # Knowledge base statistics
    stats_response = requests.get(f"{BASE_URL}/knowledge-stats")
    print("\n📊 Knowledge Base Statistics:")
    print(json.dumps(stats_response.json(), indent=2))

async def example_6_batch_processing():
    """Example 6: Process multiple DLD documents asynchronously"""
    
    dld_documents = [
        {
            "name": "AMF Implementation",
            "content": """
            # AMF Implementation
            ## Requirements
            - Implement 5G AMF network function
            - Support N1, N2 interfaces
            - Handle UE registration and mobility
            """
        },
        {
            "name": "SMF Implementation", 
            "content": """
            # SMF Implementation
            ## Requirements
            - Implement 5G SMF network function
            - Support N4, N7, N10, N11 interfaces
            - Handle session management
            """
        },
        {
            "name": "UPF Implementation",
            "content": """
            # UPF Implementation
            ## Requirements
            - Implement 5G UPF network function
            - Support N3, N4, N6 interfaces
            - Handle user plane traffic
            """
        }
    ]
    
    async def process_single_dld(doc):
        """Process a single DLD document"""
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{BASE_URL}/process-dld",
                json={
                    "dld_content": doc["content"],
                    "output_format": "cursor_ai",
                    "quality_threshold": 0.7
                }
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return {
                        "name": doc["name"],
                        "success": True,
                        "quality_score": result["quality_score"],
                        "prompt_length": len(result["prompt"])
                    }
                else:
                    return {
                        "name": doc["name"],
                        "success": False,
                        "error": await response.text()
                    }
    
    # Process all documents concurrently
    print("🔄 Processing multiple DLD documents...")
    tasks = [process_single_dld(doc) for doc in dld_documents]
    results = await asyncio.gather(*tasks)
    
    # Display results
    print("📊 Batch Processing Results:")
    for result in results:
        if result["success"]:
            print(f"  ✅ {result['name']}: Quality {result['quality_score']:.2f}, Length {result['prompt_length']}")
        else:
            print(f"  ❌ {result['name']}: {result['error']}")

def example_7_custom_configuration():
    """Example 7: Process with custom quality thresholds and settings"""
    
    dld_content = """
    # High-Precision 5G Timing System
    
    ## Requirements
    - Implement IEEE 1588 PTP support
    - Achieve sub-microsecond synchronization
    - Support SyncE for frequency sync
    - Handle GPS/GNSS backup timing
    
    ## Critical Performance Requirements
    - Timing accuracy: ±10ns
    - Frequency stability: ±0.002 ppm
    - Holdover capability: 4 hours
    - MTBF: >100,000 hours
    """
    
    # Use strict quality thresholds for critical systems
    response = requests.post(
        f"{BASE_URL}/process-dld",
        json={
            "dld_content": dld_content,
            "output_format": "cursor_ai",
            "quality_threshold": 0.95,  # High threshold for critical systems
            "include_feedback": True
        }
    )
    
    if response.status_code == 200:
        result = response.json()
        print("✅ High-precision system processing successful!")
        print(f"Quality Score: {result['quality_score']:.3f}")
        
        # Check if quality meets strict requirements
        if result['quality_score'] >= 0.95:
            print("🎯 Quality threshold met for critical system!")
        else:
            print("⚠️  Quality below threshold - review required")
            
        # Show detailed quality metrics
        validation = result.get('validation_results', {})
        if 'detailed_scores' in validation:
            print("📈 Detailed Quality Metrics:")
            for metric, score in validation['detailed_scores'].items():
                print(f"  - {metric}: {score:.3f}")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

def run_all_examples():
    """Run all examples in sequence"""
    
    print("🚀 DLD to Cursor AI Prompt Generation System - Usage Examples")
    print("=" * 70)
    
    examples = [
        ("Simple Text Processing", example_1_simple_text_processing),
        ("File Upload", example_2_file_upload),
        ("With Existing Project", example_3_with_existing_project),
        ("Multiple Formats", example_4_multiple_formats),
        ("Health and Stats", example_5_health_and_stats),
        ("Custom Configuration", example_7_custom_configuration),
    ]
    
    for name, func in examples:
        print(f"\n📝 Example: {name}")
        print("-" * 50)
        try:
            func()
        except Exception as e:
            print(f"❌ Error in {name}: {str(e)}")
        print()
    
    # Run async example
    print("📝 Example: Batch Processing")
    print("-" * 50)
    try:
        asyncio.run(example_6_batch_processing())
    except Exception as e:
        print(f"❌ Error in Batch Processing: {str(e)}")

if __name__ == "__main__":
    # Check if server is running
    try:
        health_response = requests.get(f"{BASE_URL}/health", timeout=5)
        if health_response.status_code == 200:
            print("🟢 Server is running")
            run_all_examples()
        else:
            print("🔴 Server returned error:", health_response.status_code)
    except requests.exceptions.ConnectionError:
        print("🔴 Server is not running. Please start the server first:")
        print("   python main.py")
        print("   or")
        print("   docker-compose up -d")
    except Exception as e:
        print(f"🔴 Error connecting to server: {str(e)}")
