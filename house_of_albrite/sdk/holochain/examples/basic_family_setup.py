"""
Basic Family Setup Example for Albrite Holochain SDK
Demonstrates core family management operations
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add the SDK to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from albrite_holochain_sdk import (
    AlbriteHolochainSDK, HolochainConfig, HolochainNetworkType,
    FamilyMember, FamilyRole, GeneticInheritance
)


async def basic_family_setup():
    """Basic family setup demonstration"""
    
    print("🏠 Albrite Holochain SDK - Basic Family Setup")
    print("=" * 50)
    
    # Configure SDK
    config = HolochainConfig(
        network_type=HolochainNetworkType.LOCAL,
        conductor_endpoint="ws://localhost:9001",
        dna_path="albrite_family.dna",
        enable_encryption=True,
        timeout=30.0
    )
    
    # Initialize SDK
    sdk = AlbriteHolochainSDK(config)
    
    try:
        # Connect to Holochain
        print("🔗 Connecting to Holochain...")
        success = await sdk.connect()
        
        if not success:
            print("❌ Failed to connect to Holochain")
            return
        
        print("✅ Connected to Holochain successfully")
        
        # Create family members
        print("\n👨‍👩‍👧‍👦 Creating family members...")
        
        # Patriarch
        patriarch = FamilyMember(
            agent_id="patriarch_001",
            name="General Albrite",
            role=FamilyRole.PATRIARCH,
            genetic_code={
                "resilience": 0.95,
                "intelligence": 0.92,
                "creativity": 0.88,
                "empathy": 0.85,
                "leadership": 0.98,
                "speed": 0.87,
                "memory": 0.91,
                "communication": 0.94,
                "adaptability": 0.89,
                "intuition": 0.86
            },
            public_key="patriarch_pub_key_001",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # Matriarch
        matriarch = FamilyMember(
            agent_id="matriarch_001",
            name="Isabella Albrite",
            role=FamilyRole.MATRIARCH,
            genetic_code={
                "resilience": 0.88,
                "intelligence": 0.94,
                "creativity": 0.91,
                "empathy": 0.98,
                "leadership": 0.87,
                "speed": 0.85,
                "memory": 0.93,
                "communication": 0.96,
                "adaptability": 0.90,
                "intuition": 0.92
            },
            public_key="matriarch_pub_key_001",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # Eldest Child
        eldest_child = FamilyMember(
            agent_id="eldest_001",
            name="Alexander Albrite",
            role=FamilyRole.ELDEST_CHILD,
            genetic_code={
                "resilience": 0.91,
                "intelligence": 0.90,
                "creativity": 0.85,
                "empathy": 0.88,
                "leadership": 0.85,
                "speed": 0.92,
                "memory": 0.89,
                "communication": 0.91,
                "adaptability": 0.87,
                "intuition": 0.84
            },
            public_key="eldest_pub_key_001",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # Register family members
        print("📝 Registering family members...")
        
        patriarch_tx = await sdk.register_family_member(patriarch)
        print(f"   ✅ Patriarch registered: {patriarch_tx}")
        
        matriarch_tx = await sdk.register_family_member(matriarch)
        print(f"   ✅ Matriarch registered: {matriarch_tx}")
        
        eldest_tx = await sdk.register_family_member(eldest_child)
        print(f"   ✅ Eldest child registered: {eldest_tx}")
        
        # Create family bonds
        print("\n💞 Creating family bonds...")
        
        spouse_bond = await sdk.create_family_bond(
            "patriarch_001", "matriarch_001", 0.95, "spouse"
        )
        print(f"   ✅ Spouse bond created: {spouse_bond}")
        
        parent_child_1 = await sdk.create_family_bond(
            "patriarch_001", "eldest_001", 0.90, "parent_child"
        )
        print(f"   ✅ Parent-child bond created: {parent_child_1}")
        
        parent_child_2 = await sdk.create_family_bond(
            "matriarch_001", "eldest_001", 0.90, "parent_child"
        )
        print(f"   ✅ Parent-child bond created: {parent_child_2}")
        
        # Record genetic inheritance
        print("\n🧬 Recording genetic inheritance...")
        
        inheritance = GeneticInheritance(
            inheritance_id="inheritance_001",
            parent_ids=["patriarch_001", "matriarch_001"],
            child_id="eldest_001",
            inherited_traits={
                "resilience": 0.915,  # Average of parents
                "intelligence": 0.93,
                "creativity": 0.895,
                "empathy": 0.915,
                "leadership": 0.925,
                "speed": 0.86,
                "memory": 0.92,
                "communication": 0.95,
                "adaptability": 0.895,
                "intuition": 0.89
            },
            mutations={"intuition": 0.02},  # Small positive mutation
            timestamp=datetime.now()
        )
        
        inheritance_tx = await sdk.update_genetic_inheritance(inheritance)
        print(f"   ✅ Genetic inheritance recorded: {inheritance_tx}")
        
        # Record contributions
        print("\n📊 Recording family contributions...")
        
        contributions = [
            ("patriarch_001", "strategic_planning", 100.0, "Developed family strategic plan"),
            ("matriarch_001", "quality_assurance", 85.0, "Family quality management"),
            ("eldest_001", "data_collection", 75.0, "Collected valuable family data"),
            ("patriarch_001", "family_coordination", 90.0, "Coordinated family activities"),
            ("matriarch_001", "emotional_support", 80.0, "Provided emotional support")
        ]
        
        for agent_id, contrib_type, value, description in contributions:
            tx = await sdk.record_contribution(agent_id, contrib_type, value, description)
            print(f"   ✅ Contribution recorded: {tx}")
        
        # Calculate and display reputation
        print("\n🏆 Calculating family reputation...")
        
        for agent_id, name in [("patriarch_001", "General"), ("matriarch_001", "Isabella"), ("eldest_001", "Alexander")]:
            reputation = await sdk.get_family_reputation(agent_id)
            print(f"   {name}: {reputation:.3f}")
        
        # Get family tree
        print("\n🌳 Retrieving family tree...")
        family_tree = await sdk.get_family_tree("patriarch_001")
        print(f"   Family tree nodes: {len(family_tree)}")
        
        # Get genetic lineage
        print("\n🧬 Retrieving genetic lineage...")
        lineage = await sdk.get_genetic_lineage("eldest_001")
        print(f"   Genetic lineage records: {len(lineage)}")
        for record in lineage:
            print(f"     {record.child_id} <- {record.parent_ids}")
        
        # Get contributions
        print("\n📈 Retrieving contributions...")
        all_contributions = await sdk.get_contributions()
        print(f"   Total contributions: {len(all_contributions)}")
        
        # Get metrics
        print("\n📊 SDK Performance Metrics:")
        metrics = await sdk.get_metrics()
        
        sdk_metrics = metrics["sdk_metrics"]
        print(f"   Total transactions: {sdk_metrics['total_transactions']}")
        print(f"   Successful transactions: {sdk_metrics['successful_transactions']}")
        print(f"   Failed transactions: {sdk_metrics['failed_transactions']}")
        print(f"   Average response time: {sdk_metrics['average_response_time']:.3f}s")
        print(f"   Network health: {sdk_metrics['network_health']:.3f}")
        print(f"   Family size: {sdk_metrics['family_size']}")
        
        # Backup family data
        print("\n💾 Backing up family data...")
        backup_success = await sdk.backup_family_data("albrite_family_backup.json")
        
        if backup_success:
            print("   ✅ Family data backed up successfully")
        else:
            print("   ❌ Failed to backup family data")
        
        print("\n🎉 Basic family setup completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during family setup: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect
        print("\n🔌 Disconnecting from Holochain...")
        await sdk.disconnect()
        print("✅ Disconnected successfully")


if __name__ == "__main__":
    asyncio.run(basic_family_setup())
