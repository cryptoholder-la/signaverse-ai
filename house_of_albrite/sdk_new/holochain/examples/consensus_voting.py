"""
Consensus and Voting Example for Albrite Holochain SDK
Demonstrates family decision-making through consensus mechanisms
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
    FamilyMember, FamilyRole
)


async def consensus_voting_example():
    """Consensus and voting demonstration"""
    
    print("🗳️ Albrite Holochain SDK - Consensus & Voting Example")
    print("=" * 55)
    
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
        
        # Setup event handlers for voting
        print("\n📡 Setting up event handlers...")
        
        async def handle_consensus_event(event):
            event_data = event.get("data", {})
            print(f"📢 Consensus Event: {event_data}")
        
        async def handle_vote_event(event):
            event_data = event.get("data", {})
            vote_data = event_data.get("vote_data", {})
            print(f"🗳 Vote Event: {vote_data.get('voter')} voted {vote_data.get('vote')}")
        
        sdk.register_event_handler("consensus_created", handle_consensus_event)
        sdk.register_event_handler("vote_cast", handle_vote_event)
        
        # Create consensus proposals
        print("\n📋 Creating consensus proposals...")
        
        # Proposal 1: Resource Allocation
        resource_proposal = {
            "title": "Family Resource Allocation",
            "description": "Allocate resources for new family member training and development",
            "details": {
                "total_budget": 1000.0,
                "allocation_items": [
                    {"item": "Training Programs", "cost": 400.0},
                    {"item": "Educational Resources", "cost": 300.0},
                    {"item": "Equipment Upgrade", "cost": 200.0},
                    {"item": "Emergency Fund", "cost": 100.0}
                ]
            },
            "options": ["Approve", "Reject", "Modify"],
            "required_votes": 3,
            "voting_deadline": (datetime.now() + timedelta(hours=24)).isoformat(),
            "proposer": "patriarch_001"
        }
        
        resource_consensus = await sdk.create_family_consensus(
            resource_proposal, 
            voting_period=timedelta(hours=24)
        )
        print(f"   ✅ Resource allocation consensus created: {resource_consensus}")
        
        # Proposal 2: Family Expansion
        expansion_proposal = {
            "title": "Family Expansion Strategy",
            "description": "Plan for expanding the Albrite family with new specialized agents",
            "details": {
                "expansion_plan": {
                    "new_agents": ["Military Specialist", "Research Analyst", "Data Scientist"],
                    "timeline": "6 months",
                    "investment_required": 2500.0,
                    "expected_roi": "150%"
                }
            },
            "options": ["Approve", "Reject", "Postpone", "Modify"],
            "required_votes": 3,
            "voting_deadline": (datetime.now() + timedelta(hours=48)).isoformat(),
            "proposer": "matriarch_001"
        }
        
        expansion_consensus = await sdk.create_family_consensus(
            expansion_proposal,
            voting_period=timedelta(hours=48)
        )
        print(f"   ✅ Family expansion consensus created: {expansion_consensus}")
        
        # Proposal 3: Technology Upgrade
        tech_proposal = {
            "title": "Technology Infrastructure Upgrade",
            "description": "Upgrade family technology infrastructure for better performance",
            "details": {
                "upgrades": [
                    {"component": "AI Models", "upgrade": "Latest GPT-4", "cost": 800.0},
                    {"component": "Memory System", "upgrade": "Enhanced Vector DB", "cost": 600.0},
                    {"component": "Caching", "upgrade": "Redis Cluster", "cost": 400.0},
                    {"component": "Security", "upgrade": "Advanced Encryption", "cost": 300.0}
                ],
                "total_cost": 2100.0,
                "expected_benefits": ["40% performance improvement", "Enhanced security", "Better scalability"]
            },
            "options": ["Approve", "Reject", "Phase Implementation"],
            "required_votes": 3,
            "voting_deadline": (datetime.now() + timedelta(hours=72)).isoformat(),
            "proposer": "eldest_001"
        }
        
        tech_consensus = await sdk.create_family_consensus(
            tech_proposal,
            voting_period=timedelta(hours=72)
        )
        print(f"   ✅ Technology upgrade consensus created: {tech_consensus}")
        
        # Simulate family members voting
        print("\n🗳 Simulating family member votes...")
        
        # Patriarch votes
        votes = [
            (resource_consensus, "Approve", "Strategic investment in family growth"),
            (expansion_consensus, "Approve", "Expansion aligns with family vision"),
            (tech_consensus, "Approve", "Technology upgrade essential for competitiveness")
        ]
        
        for consensus_id, vote, reason in votes:
            result = await sdk.vote_on_consensus(consensus_id, vote, reason)
            print(f"   ✅ Patriarch voted {vote} on {consensus_id[:8]}...")
            await asyncio.sleep(0.5)  # Small delay between votes
        
        # Matriarch votes
        matriarch_votes = [
            (resource_consensus, "Modify", "Increase emergency fund allocation"),
            (expansion_consensus, "Approve", "Family growth is important"),
            (tech_consensus, "Phase Implementation", "Implement in phases to manage cost")
        ]
        
        for consensus_id, vote, reason in matriarch_votes:
            result = await sdk.vote_on_consensus(consensus_id, vote, reason)
            print(f"   ✅ Matriarch voted {vote} on {consensus_id[:8]}...")
            await asyncio.sleep(0.5)
        
        # Eldest Child votes
        eldest_votes = [
            (resource_consensus, "Approve", "Training will benefit all family members"),
            (expansion_consensus, "Postpone", "Need more information on ROI"),
            (tech_consensus, "Approve", "Performance improvements are critical")
        ]
        
        for consensus_id, vote, reason in eldest_votes:
            result = await sdk.vote_on_consensus(consensus_id, vote, reason)
            print(f"   ✅ Eldest child voted {vote} on {consensus_id[:8]}...")
            await asyncio.sleep(0.5)
        
        # Wait for voting to complete
        print("\n⏳ Waiting for voting period to complete...")
        await asyncio.sleep(2)  # Simulate waiting
        
        # Analyze voting results
        print("\n📊 Analyzing voting results...")
        
        # Note: In a real implementation, you would query the actual voting results
        # For this example, we'll simulate the analysis
        
        voting_results = {
            resource_consensus: {
                "total_votes": 3,
                "approve": 2,
                "reject": 0,
                "modify": 1,
                "status": "approved_with_modifications"
            },
            expansion_consensus: {
                "total_votes": 3,
                "approve": 2,
                "reject": 0,
                "postpone": 1,
                "status": "approved"
            },
            tech_consensus: {
                "total_votes": 3,
                "approve": 2,
                "reject": 0,
                "phase": 1,
                "status": "approved_with_modifications"
            }
        }
        
        for consensus_id, results in voting_results.items():
            print(f"\n   📋 Consensus {consensus_id[:8]} Results:")
            print(f"      Total Votes: {results['total_votes']}")
            print(f"      Approve: {results['approve']}")
            if 'reject' in results:
                print(f"      Reject: {results['reject']}")
            if 'modify' in results:
                print(f"      Modify: {results['modify']}")
            if 'postpone' in results:
                print(f"      Postpone: {results['postpone']}")
            if 'phase' in results:
                print(f"      Phase Implementation: {results['phase']}")
            print(f"      Status: {results['status']}")
        
        # Record consensus outcomes
        print("\n📝 Recording consensus outcomes...")
        
        consensus_outcomes = [
            ("patriarch_001", "consensus_facilitation", 120.0, "Successfully facilitated 3 consensus votes"),
            ("matriarch_001", "strategic_voting", 100.0, "Provided strategic input on family decisions"),
            ("eldest_001", "participatory_voting", 80.0, "Actively participated in family governance")
        ]
        
        for agent_id, outcome_type, value, description in consensus_outcomes:
            tx = await sdk.record_contribution(agent_id, outcome_type, value, description)
            print(f"   ✅ Outcome recorded: {tx}")
        
        # Get updated reputation scores
        print("\n🏆 Updated family reputation scores:")
        
        family_members = ["patriarch_001", "matriarch_001", "eldest_001"]
        family_names = ["General", "Isabella", "Alexander"]
        
        for agent_id, name in zip(family_members, family_names):
            reputation = await sdk.get_family_reputation(agent_id)
            print(f"   {name}: {reputation:.3f}")
        
        # Display consensus statistics
        print("\n📈 Consensus Statistics:")
        
        total_proposals = len(voting_results)
        approved_proposals = sum(1 for r in voting_results.values() if 'approved' in r['status'])
        
        print(f"   Total Proposals: {total_proposals}")
        print(f"   Approved Proposals: {approved_proposals}")
        print(f"   Approval Rate: {(approved_proposals/total_proposals)*100:.1f}%")
        print(f"   Total Votes Cast: {sum(r['total_votes'] for r in voting_results.values())}")
        print(f"   Average Votes per Proposal: {sum(r['total_votes'] for r in voting_results.values())/total_proposals:.1f}")
        
        # Get final metrics
        print("\n📊 Final SDK Metrics:")
        metrics = await sdk.get_metrics()
        
        sdk_metrics = metrics["sdk_metrics"]
        print(f"   Total transactions: {sdk_metrics['total_transactions']}")
        print(f"   Successful transactions: {sdk_metrics['successful_transactions']}")
        print(f"   Average response time: {sdk_metrics['average_response_time']:.3f}s")
        print(f"   Network health: {sdk_metrics['network_health']:.3f}")
        
        print("\n🎉 Consensus and voting example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error during consensus voting: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect
        print("\n🔌 Disconnecting from Holochain...")
        await sdk.disconnect()
        print("✅ Disconnected successfully")


async def advanced_consensus_features():
    """Demonstrate advanced consensus features"""
    
    print("\n🔬 Advanced Consensus Features Demo")
    print("=" * 40)
    
    config = HolochainConfig(
        network_type=HolochainNetworkType.LOCAL,
        conductor_endpoint="ws://localhost:9001",
        dna_path="albrite_family.dna"
    )
    
    sdk = AlbriteHolochainSDK(config)
    
    try:
        await sdk.connect()
        
        # Create weighted voting proposal
        weighted_proposal = {
            "title": "Weighted Voting Example",
            "description": "Demonstrate weighted voting based on family roles",
            "details": {
                "voting_weights": {
                    "patriarch": 3.0,  # Patriarch has 3x voting power
                    "matriarch": 2.0,  # Matriarch has 2x voting power
                    "eldest_child": 1.0,  # Eldest child has 1x voting power
                    "younger_child": 0.5  # Younger children have 0.5x voting power
                }
            },
            "options": ["For", "Against", "Abstain"],
            "required_weight": 4.0,  # Need 4.0 weight to pass
            "voting_deadline": (datetime.now() + timedelta(hours=12)).isoformat()
        }
        
        weighted_consensus = await sdk.create_family_consensus(weighted_proposal)
        print(f"✅ Weighted voting consensus created: {weighted_consensus}")
        
        # Create delegated voting proposal
        delegation_proposal = {
            "title": "Delegated Voting Example",
            "description": "Demonstrate vote delegation for absent family members",
            "details": {
                "delegations": {
                    "eldest_001": "patriarch_001",  # Eldest delegates to patriarch
                    "younger_001": "matriarch_001"   # Younger delegates to matriarch
                }
            },
            "options": ["Approve", "Reject"],
            "required_votes": 2,
            "voting_deadline": (datetime.now() + timedelta(hours=6)).isoformat()
        }
        
        delegation_consensus = await sdk.create_family_consensus(delegation_proposal)
        print(f"✅ Delegated voting consensus created: {delegation_consensus}")
        
        print("\n🔬 Advanced consensus features demonstrated successfully!")
        
    except Exception as e:
        print(f"❌ Error in advanced consensus demo: {e}")
    finally:
        await sdk.disconnect()


if __name__ == "__main__":
    # Run basic consensus example
    asyncio.run(consensus_voting_example())
    
    # Run advanced features demo
    asyncio.run(advanced_consensus_features())
