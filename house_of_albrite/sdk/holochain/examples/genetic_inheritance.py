"""
Genetic Inheritance Example for Albrite Holochain SDK
Demonstrates advanced genetic trait inheritance and evolution
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# Add the SDK to path
import sys
sys.path.append(str(Path(__file__).parent.parent))

from albrite_holochain_sdk import (
    AlbriteHolochainSDK, HolochainConfig, HolochainNetworkType,
    FamilyMember, FamilyRole, GeneticInheritance
)


def calculate_genetic_inheritance(parent1_genes, parent2_genes, mutation_rate=0.1):
    """Calculate genetic inheritance from two parents"""
    inherited_genes = {}
    mutations = {}
    
    for trait in parent1_genes:
        # Average of parents' genes
        base_value = (parent1_genes[trait] + parent2_genes[trait]) / 2
        
        # Apply mutation
        if random.random() < mutation_rate:
            mutation_strength = random.uniform(-0.05, 0.05)
            mutated_value = max(0.0, min(1.0, base_value + mutation_strength))
            mutations[trait] = mutation_strength
            inherited_genes[trait] = mutated_value
        else:
            inherited_genes[trait] = base_value
    
    return inherited_genes, mutations


def simulate_trait_evolution(generations, base_genes):
    """Simulate genetic trait evolution over generations"""
    evolution_history = []
    current_genes = base_genes.copy()
    
    for generation in range(generations):
        # Apply environmental pressures
        environmental_factors = {
            "resilience": 1.02,    # Environment favors resilience
            "intelligence": 1.01,   # Slight pressure for intelligence
            "adaptability": 1.03,   # Strong pressure for adaptability
            "communication": 1.015, # Moderate pressure for communication
            "leadership": 1.005     # Slight pressure for leadership
        }
        
        evolved_genes = {}
        for trait, value in current_genes.items():
            factor = environmental_factors.get(trait, 1.0)
            evolved_value = max(0.0, min(1.0, value * factor))
            evolved_genes[trait] = evolved_value
        
        evolution_history.append({
            "generation": generation + 1,
            "genes": evolved_genes.copy(),
            "average_fitness": sum(evolved_genes.values()) / len(evolved_genes)
        })
        
        current_genes = evolved_genes
    
    return evolution_history


async def genetic_inheritance_example():
    """Genetic inheritance demonstration"""
    
    print("🧬 Albrite Holochain SDK - Genetic Inheritance Example")
    print("=" * 58)
    
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
        
        # Create founding family members with strong genetic traits
        print("\n👨‍👩‍👧‍👦 Creating founding family members...")
        
        # Patriarch - Strong in leadership and resilience
        patriarch_genes = {
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
        }
        
        patriarch = FamilyMember(
            agent_id="patriarch_gen001",
            name="General Albrite",
            role=FamilyRole.PATRIARCH,
            genetic_code=patriarch_genes,
            public_key="patriarch_gen_pub_key",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # Matriarch - Strong in empathy and intelligence
        matriarch_genes = {
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
        }
        
        matriarch = FamilyMember(
            agent_id="matriarch_gen001",
            name="Isabella Albrite",
            role=FamilyRole.MATRIARCH,
            genetic_code=matriarch_genes,
            public_key="matriarch_gen_pub_key",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # Register founding members
        patriarch_tx = await sdk.register_family_member(patriarch)
        print(f"   ✅ Patriarch registered: {patriarch_tx}")
        
        matriarch_tx = await sdk.register_family_member(matriarch)
        print(f"   ✅ Matriarch registered: {matriarch_tx}")
        
        # Create family bond
        bond_tx = await sdk.create_family_bond(
            "patriarch_gen001", "matriarch_gen001", 0.95, "spouse"
        )
        print(f"   ✅ Family bond created: {bond_tx}")
        
        # Simulate multiple generations of offspring
        print("\n👶 Simulating genetic inheritance across generations...")
        
        generations = []
        current_parents = [("patriarch_gen001", "matriarch_gen001")]
        current_genes = [patriarch_genes, matriarch_genes]
        
        for generation in range(1, 4):  # Create 3 generations
            print(f"\n   📅 Generation {generation}:")
            
            # Create 2-3 children per generation
            num_children = random.randint(2, 3)
            generation_children = []
            
            for child_num in range(num_children):
                # Calculate genetic inheritance
                inherited_genes, mutations = calculate_genetic_inheritance(
                    current_genes[0], current_genes[1], mutation_rate=0.15
                )
                
                # Create child
                child_id = f"gen{generation}_child{child_num + 1}"
                child_name = f"Albrite Gen{generation}.{child_num + 1}"
                child_role = FamilyRole.ELDEST_CHILD if child_num == 0 else FamilyRole.YOUNGER_CHILD
                
                child = FamilyMember(
                    agent_id=child_id,
                    name=child_name,
                    role=child_role,
                    genetic_code=inherited_genes,
                    public_key=f"{child_id}_pub_key",
                    created_at=datetime.now(),
                    last_active=datetime.now()
                )
                
                # Register child
                child_tx = await sdk.register_family_member(child)
                print(f"      👶 {child_name} registered: {child_tx}")
                
                # Record genetic inheritance
                inheritance = GeneticInheritance(
                    inheritance_id=f"inheritance_{generation}_{child_num + 1}",
                    parent_ids=current_parents,
                    child_id=child_id,
                    inherited_traits=inherited_genes,
                    mutations=mutations,
                    timestamp=datetime.now()
                )
                
                inheritance_tx = await sdk.update_genetic_inheritance(inheritance)
                print(f"      🧬 Genetic inheritance recorded: {inheritance_tx}")
                
                # Create family bonds
                for parent_id in current_parents:
                    bond_tx = await sdk.create_family_bond(
                        parent_id, child_id, 0.85, "parent_child"
                    )
                    print(f"      💞 Parent-child bond created: {bond_tx}")
                
                generation_children.append((child_id, inherited_genes))
                
                # Display genetic traits
                avg_trait_value = sum(inherited_genes.values()) / len(inherited_genes)
                print(f"         📊 Average trait value: {avg_trait_value:.3f}")
                print(f"         🧬 Mutations: {len(mutations)} traits")
                
                if mutations:
                    mutated_traits = list(mutations.keys())
                    print(f"         🔄 Mutated traits: {', '.join(mutated_traits)}")
            
            generations.append(generation_children)
            
            # For next generation, use the best performing children as parents
            if generation < 3:  # Don't create parents for last generation
                # Sort by average trait value and take top 2
                generation_children.sort(key=lambda x: sum(x[1].values()) / len(x[1]), reverse=True)
                current_parents = [generation_children[0][0], generation_children[1][0]]
                current_genes = [generation_children[0][1], generation_children[1][1]]
        
        # Analyze genetic evolution
        print("\n📈 Analyzing genetic evolution across generations...")
        
        all_genes = [patriarch_genes, matriarch_genes]
        for generation_children in generations:
            for _, genes in generation_children:
                all_genes.append(genes)
        
        # Calculate trait averages per generation
        generation_averages = []
        for i in range(0, len(all_genes), 2):
            if i + 1 < len(all_genes):
                avg = {
                    trait: (all_genes[i][trait] + all_genes[i + 1][trait]) / 2
                    for trait in all_genes[i]
                }
                generation_averages.append(avg)
        
        print("\n   📊 Trait Evolution by Generation:")
        print("   Generation | Resilience | Intelligence | Creativity | Empathy | Leadership | Speed | Memory | Communication | Adaptability | Intuition")
        print("   " + "-" * 95)
        
        for i, avg in enumerate(generation_averages):
            gen_num = i + 1
            print(f"   {gen_num:10d} | {avg['resilience']:11.3f} | {avg['intelligence']:11.3f} | {avg['creativity']:9.3f} | {avg['empathy']:7.3f} | {avg['leadership']:9.3f} | {avg['speed']:5.3f} | {avg['memory']:6.3f} | {avg['communication']:11.3f} | {avg['adaptability']:11.3f} | {avg['intuition']:9.3f}")
        
        # Simulate long-term evolution
        print("\n🔬 Simulating long-term genetic evolution...")
        
        # Use the best genes from last generation as base
        best_genes = max([genes for _, genes in generations[-1]], 
                        key=lambda g: sum(g.values()) / len(g))
        
        evolution_history = simulate_trait_evolution(10, best_genes)
        
        print("\n   📈 Evolution Over 10 Generations:")
        print("   Generation | Average Fitness")
        print("   " + "-" * 25)
        
        for record in evolution_history:
            print(f"   {record['generation']:10d} | {record['average_fitness']:15.3f}")
        
        # Identify genetic improvements
        print("\n🧬 Genetic Improvements Identified:")
        
        founding_avg = sum(patriarch_genes.values()) / len(patriarch_genes)
        final_avg = evolution_history[-1]["average_fitness"]
        improvement = ((final_avg - founding_avg) / founding_avg) * 100
        
        print(f"   📊 Founding generation average: {founding_avg:.3f}")
        print(f"   📊 Final generation average: {final_avg:.3f}")
        print(f"   📈 Overall improvement: {improvement:.1f}%")
        
        # Record genetic research contributions
        print("\n📝 Recording genetic research contributions...")
        
        research_contributions = [
            ("patriarch_gen001", "genetic_research", 150.0, "Led genetic inheritance research program"),
            ("matriarch_gen001", "trait_analysis", 120.0, "Analyzed trait evolution patterns"),
            ("gen1_child1", "mutation_study", 80.0, "Contributed to mutation analysis"),
            ("gen2_child1", "evolution_modeling", 100.0, "Participated in evolution modeling")
        ]
        
        for agent_id, contrib_type, value, description in research_contributions:
            tx = await sdk.record_contribution(agent_id, contrib_type, value, description)
            print(f"   ✅ Research contribution recorded: {tx}")
        
        # Get genetic lineage for a descendant
        print("\n🌳 Retrieving genetic lineage...")
        
        if len(generations) >= 2:
            last_generation_child = generations[-1][0][0]  # First child of last generation
            lineage = await sdk.get_genetic_lineage(last_generation_child)
            
            print(f"   🧬 Genetic lineage for {last_generation_child}:")
            for record in lineage:
                parents_str = " + ".join(record.parent_ids)
                print(f"      {record.child_id} <- ({parents_str})")
                if record.mutations:
                    mutated_traits = list(record.mutations.keys())
                    print(f"         🔄 Mutations: {', '.join(mutated_traits)}")
        
        # Calculate family genetic diversity
        print("\n🌈 Calculating family genetic diversity...")
        
        all_trait_values = {}
        for trait in patriarch_genes:
            all_trait_values[trait] = [genes[trait] for genes in all_genes]
        
        diversity_metrics = {}
        for trait, values in all_trait_values.items():
            mean_val = sum(values) / len(values)
            variance = sum((x - mean_val) ** 2 for x in values) / len(values)
            std_dev = variance ** 0.5
            diversity_metrics[trait] = {
                "mean": mean_val,
                "std_dev": std_dev,
                "range": max(values) - min(values)
            }
        
        print("   📊 Genetic Diversity Metrics:")
        print("   Trait       | Mean   | Std Dev | Range")
        print("   " + "-" * 40)
        
        for trait, metrics in diversity_metrics.items():
            print(f"   {trait:11s} | {metrics['mean']:6.3f} | {metrics['std_dev']:7.3f} | {metrics['range']:5.3f}")
        
        # Get final metrics
        print("\n📊 Final SDK Metrics:")
        metrics = await sdk.get_metrics()
        
        sdk_metrics = metrics["sdk_metrics"]
        print(f"   Total transactions: {sdk_metrics['total_transactions']}")
        print(f"   Successful transactions: {sdk_metrics['successful_transactions']}")
        print(f"   Average response time: {sdk_metrics['average_response_time']:.3f}s")
        print(f"   Family size: {sdk_metrics['family_size']}")
        
        # Backup genetic data
        print("\n💾 Backing up genetic family data...")
        backup_success = await sdk.backup_family_data("genetic_family_backup.json")
        
        if backup_success:
            print("   ✅ Genetic family data backed up successfully")
        else:
            print("   ❌ Failed to backup genetic family data")
        
        print("\n🎉 Genetic inheritance example completed successfully!")
        print(f"🧬 Created {len(generations)} generations with {sum(len(g) for g in generations)} family members")
        print(f"📈 Achieved {improvement:.1f}% genetic improvement over founding generation")
        
    except Exception as e:
        print(f"❌ Error during genetic inheritance demo: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Disconnect
        print("\n🔌 Disconnecting from Holochain...")
        await sdk.disconnect()
        print("✅ Disconnected successfully")


async def advanced_genetic_features():
    """Demonstrate advanced genetic features"""
    
    print("\n🔬 Advanced Genetic Features Demo")
    print("=" * 35)
    
    config = HolochainConfig(
        network_type=HolochainNetworkType.LOCAL,
        conductor_endpoint="ws://localhost:9001",
        dna_path="albrite_family.dna"
    )
    
    sdk = AlbriteHolochainSDK(config)
    
    try:
        await sdk.connect()
        
        # Demonstrate genetic trait specialization
        print("\n🎯 Demonstrating genetic trait specialization...")
        
        # Create specialized genetic profiles
        specialist_profiles = {
            "military_specialist": {
                "resilience": 0.98, "leadership": 0.95, "speed": 0.92,
                "intelligence": 0.88, "creativity": 0.75, "empathy": 0.70,
                "memory": 0.85, "communication": 0.90, "adaptability": 0.93, "intuition": 0.87
            },
            "research_scientist": {
                "intelligence": 0.98, "creativity": 0.96, "memory": 0.95,
                "adaptability": 0.88, "curiosity": 0.94, "analysis": 0.97,
                "resilience": 0.75, "leadership": 0.70, "speed": 0.80, "empathy": 0.85
            },
            "diplomat": {
                "empathy": 0.98, "communication": 0.97, "leadership": 0.90,
                "intelligence": 0.88, "creativity": 0.85, "adaptability": 0.92,
                "resilience": 0.80, "speed": 0.75, "memory": 0.85, "intuition": 0.91
            }
        }
        
        for specialization, traits in specialist_profiles.items():
            avg_fitness = sum(traits.values()) / len(traits)
            print(f"   🎯 {specialization.replace('_', ' ').title()}: {avg_fitness:.3f} average fitness")
        
        print("\n🔬 Advanced genetic features demonstrated successfully!")
        
    except Exception as e:
        print(f"❌ Error in advanced genetic demo: {e}")
    finally:
        await sdk.disconnect()


if __name__ == "__main__":
    # Run basic genetic inheritance example
    asyncio.run(genetic_inheritance_example())
    
    # Run advanced features demo
    asyncio.run(advanced_genetic_features())
