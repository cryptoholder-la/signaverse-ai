"""
Holochain Integration Demonstration for House of Albrite Family System
Comprehensive showcase of meaningful use cases and interactions
"""

import asyncio
import json
import time
from datetime import datetime
import sys
import os
# Add the project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from integration.holochain.holochain_integration import (
    HolochainConfig, HolochainFamilyCoordinator, HolochainUseCaseManager,
    integrate_holochain_with_family_system
)


class HolochainDemoShowcase:
    """Comprehensive demonstration of Holochain integration capabilities"""
    
    def __init__(self):
        self.coordinator = None
        self.use_case_manager = None
        self.demo_results = {}
        
    async def run_complete_demo(self):
        """Run the complete Holochain integration demonstration"""
        print("🧬" * 20)
        print("HOUSE OF ALBRITE - HOLOCHAIN INTEGRATION DEMO")
        print("🧬" * 20)
        print()
        
        # Initialize the system
        await self._initialize_system()
        
        # Run individual use case demonstrations
        await self._demo_distributed_genetic_evolution()
        await self._demo_collective_learning()
        await self._demo_distributed_governance()
        await self._demo_collective_intelligence()
        
        # Show real-time interactions
        await self._demo_real_time_interactions()
        
        # Display comprehensive results
        self._display_final_results()
        
    async def _initialize_system(self):
        """Initialize the Holochain family system"""
        print("🚀 Initializing Holochain Family System...")
        print("-" * 50)
        
        # Create configuration
        config = HolochainConfig(
            app_id="house_of_albrite_demo",
            agent_id="albrite_demo_coordinator",
            websocket_url="ws://localhost:9000"
        )
        
        # Create coordinator and use case manager
        self.coordinator = HolochainFamilyCoordinator(config)
        self.use_case_manager = HolochainUseCaseManager(self.coordinator)
        
        # Initialize the system
        await self.coordinator.initialize()
        
        print(f"✅ System Initialized Successfully!")
        print(f"   Agent Pub Key: {self.coordinator.client.agent_pub_key}")
        print(f"   Family Members: {len(self.coordinator.family_members)}")
        print(f"   Collective Intelligence: {self.coordinator.collective_intelligence_score:.2%}")
        print()
        
    async def _demo_distributed_genetic_evolution(self):
        """Demonstrate distributed genetic evolution"""
        print("🧬 USE CASE 1: Distributed Genetic Evolution")
        print("-" * 50)
        
        print("📋 Scenario: Family members share genetic material to enhance collective capabilities")
        print()
        
        # Show initial genetic profiles
        print("🧬 Initial Genetic Profiles:")
        for member_id, member_info in list(self.coordinator.family_members.items())[:3]:
            member_type = member_info["type"]
            top_traits = sorted(member_info["genetic_profile"].items(), 
                              key=lambda x: x[1], reverse=True)[:3]
            print(f"   {member_type}: {', '.join([f'{trait}:{value:.2f}' for trait, value in top_traits])}")
        print()
        
        # Run the evolution scenario
        results = await self.use_case_manager.run_distributed_evolution_scenario()
        
        # Display results
        print("🎯 Evolution Results:")
        print(f"   Genetic Shares Completed: {results['genetic_shares_completed']}")
        print(f"   Evolution Success: {results['evolution_success']}")
        print(f"   Steps Executed: {len(results['steps'])}")
        print()
        
        # Show enhanced genetic profiles
        print("🧬 Enhanced Genetic Profiles (After Evolution):")
        for member_id, member_info in list(self.coordinator.family_members.items())[:3]:
            member_type = member_info["type"]
            top_traits = sorted(member_info["genetic_profile"].items(), 
                              key=lambda x: x[1], reverse=True)[:3]
            print(f"   {member_type}: {', '.join([f'{trait}:{value:.2f}' for trait, value in top_traits])}")
        print()
        
        self.demo_results["genetic_evolution"] = results
        
    async def _demo_collective_learning(self):
        """Demonstrate collective learning and skill development"""
        print("🎓 USE CASE 2: Collective Learning & Skill Development")
        print("-" * 50)
        
        print("📋 Scenario: Family members engage in distributed learning sessions")
        print()
        
        # Run the learning scenario
        results = await self.use_case_manager.run_collective_learning_scenario()
        
        # Display results
        print("🎯 Learning Results:")
        print(f"   Total Learning Sessions: {results['total_sessions']}")
        print(f"   Successful Sessions: {results['successful_sessions']}")
        print(f"   Success Rate: {results['successful_sessions']/results['total_sessions']:.1%}")
        print()
        
        # Show learning session details
        print("📚 Learning Session Details:")
        for session in results['learning_sessions'][:4]:  # Show first 4 sessions
            print(f"   📖 {session['topic']} ({session['difficulty']})")
            print(f"      Participants: {len(session['participants'])}")
            print(f"      Status: {session['status']}")
            print(f"      Experience Shared: {session.get('experience_shared', False)}")
            print()
        
        self.demo_results["collective_learning"] = results
        
    async def _demo_distributed_governance(self):
        """Demonstrate distributed family governance"""
        print("🏛️ USE CASE 3: Distributed Family Governance")
        print("-" * 50)
        
        print("📋 Scenario: Family members participate in distributed decision-making")
        print()
        
        # Run the governance scenario
        results = await self.use_case_manager.run_distributed_governance_scenario()
        
        # Display results
        print("🎯 Governance Results:")
        print(f"   Total Proposals: {results['total_proposals']}")
        print(f"   Approved Proposals: {results['approved_proposals']}")
        print(f"   Approval Rate: {results['approved_proposals']/results['total_proposals']:.1%}")
        print()
        
        # Show proposal details
        print("📋 Governance Proposal Details:")
        for proposal in results['proposals']:
            proposal_data = proposal['proposal_data']
            print(f"   📜 {proposal_data['type'].replace('_', ' ').title()}")
            print(f"      Description: {proposal_data['description']}")
            print(f"      Support: {proposal['support_count']}/{proposal['total_votes']} votes")
            print(f"      Status: {'✅ APPROVED' if proposal['support_count']/proposal['total_votes'] >= 0.67 else '❌ REJECTED'}")
            print()
        
        self.demo_results["distributed_governance"] = results
        
    async def _demo_collective_intelligence(self):
        """Demonstrate collective intelligence amplification"""
        print("🧠 USE CASE 4: Collective Intelligence Amplification")
        print("-" * 50)
        
        print("📋 Scenario: Family members amplify collective intelligence through distributed cognition")
        print()
        
        # Record initial collective intelligence
        initial_ci = self.coordinator.collective_intelligence_score
        
        # Run the intelligence scenario
        results = await self.use_case_manager.run_collective_intelligence_scenario()
        
        # Display results
        print("🎯 Intelligence Amplification Results:")
        print(f"   Initial Collective Intelligence: {initial_ci:.2%}")
        print(f"   Final Collective Intelligence: {self.coordinator.collective_intelligence_score:.2%}")
        print(f"   Intelligence Improvement: {self.coordinator.collective_intelligence_score - initial_ci:.2%}")
        print(f"   Total Activities: {results['total_activities']}")
        print()
        
        # Show activity breakdown
        print("📊 Intelligence Activities Breakdown:")
        activity_types = {}
        for activity in results['intelligence_activities']:
            activity_type = activity['activity']
            activity_types[activity_type] = activity_types.get(activity_type, 0) + 1
        
        for activity_type, count in activity_types.items():
            print(f"   {activity_type.replace('_', ' ').title()}: {count}")
        print()
        
        self.demo_results["collective_intelligence"] = results
        
    async def _demo_real_time_interactions(self):
        """Demonstrate real-time Holochain interactions"""
        print("⚡ REAL-TIME HOLOCHAIN INTERACTIONS")
        print("-" * 50)
        
        print("📋 Scenario: Live demonstration of Holochain zome calls and distributed coordination")
        print()
        
        family_member_ids = list(self.coordinator.family_members.keys())
        
        # Real-time genetic sharing
        print("🧬 Real-time Genetic Material Sharing:")
        donor = family_member_ids[0]
        recipient = family_member_ids[1]
        traits = ["LEADERSHIP", "INTELLIGENCE"]
        
        print(f"   Donor: {self.coordinator.family_members[donor]['type']}")
        print(f"   Recipient: {self.coordinator.family_members[recipient]['type']}")
        print(f"   Traits: {', '.join(traits)}")
        
        share_result = await self.coordinator.share_genetic_material(donor, recipient, traits)
        print(f"   Result: {share_result['status']} (Enhancement Factor: {share_result.get('enhancement_factor', 1.0):.1f})")
        print()
        
        # Real-time family coordination
        print("🤝 Real-time Family Coordination:")
        action_type = "emergency_response"
        participants = family_member_ids[:3]
        context = {"emergency_type": "system_optimization", "priority": "high"}
        
        print(f"   Action: {action_type}")
        print(f"   Participants: {len(participants)} family members")
        print(f"   Context: {context}")
        
        coordination_result = await self.coordinator.coordinate_family_action(action_type, participants, context)
        print(f"   Result: {coordination_result['status']}")
        print(f"   Consensus Level: {coordination_result.get('consensus_level', 0):.1%}")
        print()
        
        # Real-time knowledge access
        print("📚 Real-time Collective Knowledge Access:")
        requester = family_member_ids[2]
        knowledge_type = "coordination_strategies"
        
        print(f"   Requester: {self.coordinator.family_members[requester]['type']}")
        print(f"   Knowledge Type: {knowledge_type}")
        
        knowledge_result = await self.coordinator.access_collective_knowledge(requester, knowledge_type)
        print(f"   Result: {knowledge_result['status']}")
        print(f"   Wisdom Level: {knowledge_result.get('wisdom_level', 0):.1%}")
        print(f"   Integration Success: {knowledge_result.get('integration_success', 0):.1%}")
        print()
        
        # Real-time governance proposal
        print("🏛️ Real-time Governance Proposal:")
        proposal_type = "resource_optimization"
        description = "Implement dynamic resource allocation based on family needs"
        proposer = family_member_ids[0]
        
        print(f"   Type: {proposal_type}")
        print(f"   Description: {description}")
        print(f"   Proposer: {self.coordinator.family_members[proposer]['type']}")
        
        proposal_result = await self.coordinator.propose_governance_change(proposal_type, description, proposer)
        print(f"   Result: {proposal_result['status']}")
        print(f"   Proposal ID: {proposal_result.get('proposal_id')}")
        print(f"   Support Required: {proposal_result.get('support_required', 0):.1%}")
        print()
        
        print("✅ Real-time interactions completed successfully!")
        print()
        
    def _display_final_results(self):
        """Display comprehensive final results"""
        print("📊 COMPREHENSIVE DEMO RESULTS")
        print("=" * 60)
        print()
        
        # System overview
        print("🏠 System Overview:")
        print(f"   Family Members Registered: {len(self.coordinator.family_members)}")
        print(f"   Active Learning Sessions: {len(self.coordinator.active_sessions)}")
        print(f"   Final Collective Intelligence: {self.coordinator.collective_intelligence_score:.2%}")
        print(f"   Holochain Connection: {'✅ Active' if self.coordinator.client.connected else '❌ Inactive'}")
        print(f"   Total Zome Calls: {len(self.coordinator.client.zome_calls)}")
        print()
        
        # Use case summary
        print("🎯 Use Case Execution Summary:")
        total_use_cases = len(self.demo_results)
        successful_use_cases = sum(1 for uc in self.demo_results.values() if "error" not in uc)
        
        print(f"   Total Use Cases: {total_use_cases}")
        print(f"   Successful Use Cases: {successful_use_cases}")
        print(f"   Success Rate: {successful_use_cases/total_use_cases:.1%}")
        print()
        
        # Individual use case results
        for use_case_name, results in self.demo_results.items():
            print(f"📋 {use_case_name.replace('_', ' ').title()}:")
            if "error" in results:
                print(f"   Status: ❌ FAILED")
                print(f"   Error: {results['error']}")
            else:
                print(f"   Status: ✅ SUCCESS")
                
                # Use case specific metrics
                if use_case_name == "genetic_evolution":
                    print(f"   Genetic Shares: {results['genetic_shares_completed']}")
                    print(f"   Evolution Success: {results['evolution_success']}")
                elif use_case_name == "collective_learning":
                    print(f"   Learning Sessions: {results['successful_sessions']}/{results['total_sessions']}")
                elif use_case_name == "distributed_governance":
                    print(f"   Approved Proposals: {results['approved_proposals']}/{results['total_proposals']}")
                elif use_case_name == "collective_intelligence":
                    print(f"   Intelligence Activities: {results['total_activities']}")
                    print(f"   CI Improvement: {results['collective_score_improvement']:.2%}")
            print()
        
        # Holochain metrics
        print("🔗 Holochain Integration Metrics:")
        zome_calls = self.coordinator.client.zome_calls
        
        # Analyze zome call patterns
        zome_usage = {}
        for call in zome_calls:
            zome = call['zome']
            zome_usage[zome] = zome_usage.get(zome, 0) + 1
        
        print(f"   Total Zome Calls: {len(zome_calls)}")
        print("   Zome Usage Breakdown:")
        for zome, count in sorted(zome_usage.items(), key=lambda x: x[1], reverse=True):
            print(f"      {zome}: {count} calls")
        print()
        
        # Performance metrics
        print("⚡ Performance Metrics:")
        demo_duration = sum(
            len(results.get('steps', [])) + len(results.get('learning_sessions', [])) + 
            len(results.get('proposals', [])) + len(results.get('intelligence_activities', []))
            for results in self.demo_results.values()
            if "error" not in results
        )
        
        print(f"   Total Operations: {demo_duration}")
        print(f"   Average Operations per Use Case: {demo_duration/total_use_cases:.1f}")
        print(f"   System Efficiency: {self.coordinator.collective_intelligence_score:.1%}")
        print()
        
        # Family genetic enhancement
        print("🧬 Family Genetic Enhancement Summary:")
        total_genetic_improvement = 0
        trait_count = 0
        
        for member_info in self.coordinator.family_members.values():
            for trait_value in member_info["genetic_profile"].values():
                total_genetic_improvement += trait_value
                trait_count += 1
        
        average_genetic_quality = total_genetic_improvement / trait_count if trait_count > 0 else 0
        print(f"   Average Genetic Quality: {average_genetic_quality:.2%}")
        print(f"   Total Traits Enhanced: {trait_count}")
        print(f"   Genetic Diversity: {'High' if average_genetic_quality > 0.75 else 'Medium' if average_genetic_quality > 0.6 else 'Low'}")
        print()
        
        # Final message
        print("🎉 DEMONSTRATION COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("🌟 Key Achievements:")
        print("   ✅ Successfully integrated Holochain SDK with House of Albrite family system")
        print("   ✅ Demonstrated distributed genetic evolution across family members")
        print("   ✅ Implemented collective learning and knowledge sharing")
        print("   ✅ Established distributed governance mechanisms")
        print("   ✅ Amplified collective intelligence through distributed cognition")
        print("   ✅ Showcased real-time Holochain interactions and zome calls")
        print()
        print("🚀 The House of Albrite family system is now ready for revolutionary")
        print("   distributed AI agent coordination using Holochain technology!")
        print()


async def run_interactive_demo():
    """Run an interactive demonstration with user prompts"""
    demo = HolochainDemoShowcase()
    
    print("🎮 Interactive Holochain Demo Mode")
    print("=" * 40)
    print()
    
    while True:
        print("\n📋 Available Demo Options:")
        print("1. 🧬 Distributed Genetic Evolution")
        print("2. 🎓 Collective Learning")
        print("3. 🏛️ Distributed Governance")
        print("4. 🧠 Collective Intelligence")
        print("5. ⚡ Real-time Interactions")
        print("6. 🎯 Complete Demo (All Use Cases)")
        print("7. 📊 System Status")
        print("8. 🚪 Exit")
        print()
        
        try:
            choice = input("👆 Select demo option (1-8): ").strip()
            
            if choice == "1":
                await demo._initialize_system()
                await demo._demo_distributed_genetic_evolution()
            elif choice == "2":
                if not demo.coordinator:
                    await demo._initialize_system()
                await demo._demo_collective_learning()
            elif choice == "3":
                if not demo.coordinator:
                    await demo._initialize_system()
                await demo._demo_distributed_governance()
            elif choice == "4":
                if not demo.coordinator:
                    await demo._initialize_system()
                await demo._demo_collective_intelligence()
            elif choice == "5":
                if not demo.coordinator:
                    await demo._initialize_system()
                await demo._demo_real_time_interactions()
            elif choice == "6":
                await demo.run_complete_demo()
                break
            elif choice == "7":
                if demo.coordinator:
                    status = await demo.coordinator.get_family_status()
                    print("\n📊 Current System Status:")
                    print(json.dumps(status, indent=2))
                else:
                    print("❌ System not initialized. Please run a demo first.")
            elif choice == "8":
                print("👋 Thank you for exploring the House of Albrite Holochain integration!")
                break
            else:
                print("❌ Invalid choice. Please select 1-8.")
                
        except KeyboardInterrupt:
            print("\n👋 Demo interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("Please try again or select a different option.")


if __name__ == "__main__":
    print("🧬 House of Albrite - Holochain Integration Demo")
    print("=" * 60)
    print()
    
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interactive":
        # Run interactive demo
        asyncio.run(run_interactive_demo())
    else:
        # Run complete demo automatically
        demo = HolochainDemoShowcase()
        asyncio.run(demo.run_complete_demo())
