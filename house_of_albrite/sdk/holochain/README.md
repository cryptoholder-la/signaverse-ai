# Albrite Holochain SDK

## Overview

The Albrite Holochain SDK provides enterprise-grade integration between the Albrite Family-Based Agent Architecture and Holochain's distributed coordination system. This SDK enables genetic family systems to operate on a decentralized, tamper-resistant network with full cryptographic security and consensus mechanisms.

## Features

### 🧬 Genetic Family Integration
- **Genetic Inheritance Tracking**: Record and verify genetic trait inheritance between family members
- **Family Bond Management**: Create and maintain family relationships with strength metrics
- **Reputation System**: Calculate and track family member reputation based on contributions
- **Consensus Mechanisms**: Family-based decision making with voting systems

### 🔒 Security & Privacy
- **Cryptographic Signing**: All transactions signed with agent keys
- **Encrypted Communication**: Optional end-to-end encryption for sensitive data
- **Access Control**: Role-based permissions for family operations
- **Tamper Resistance**: Immutable ledger of all family activities

### 📊 Performance & Monitoring
- **Real-time Metrics**: Track transaction success rates, response times, network health
- **Event Handling**: Comprehensive event system for real-time updates
- **Backup & Restore**: Complete family data backup and restoration capabilities
- **Network Status**: Monitor Holochain network health and connectivity

### 🚀 Advanced Features
- **Multi-Network Support**: Local, staging, production, and custom networks
- **Async Operations**: Full asyncio support for high-performance operations
- **Flexible Configuration**: Extensive configuration options for all use cases
- **Error Handling**: Robust error handling with automatic retries

## Quick Start

### Installation

```bash
# Install dependencies
pip install aiohttp websockets

# Copy SDK to your project
cp house_of_albrite/sdk/holochain/albrite_holochain_sdk.py your_project/
```

### Basic Usage

```python
import asyncio
from albrite_holochain_sdk import create_albrite_holochain_sdk, FamilyMember, FamilyRole

async def main():
    # Create SDK instance
    sdk = await create_albrite_holochain_sdk(
        network_type="local",
        dna_path="path/to/albrite_family.dna"
    )
    
    try:
        # Register family member
        member = FamilyMember(
            agent_id="agent_001",
            name="Albrite Agent",
            role=FamilyRole.PATRIARCH,
            genetic_code={
                "resilience": 0.95,
                "intelligence": 0.92,
                "leadership": 0.98
            },
            public_key="agent_public_key",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        await sdk.register_family_member(member)
        print("Family member registered successfully!")
        
    finally:
        await sdk.disconnect()

asyncio.run(main())
```

## API Reference

### Core Classes

#### `AlbriteHolochainSDK`
Main SDK class for Holochain integration.

```python
class AlbriteHolochainSDK:
    def __init__(self, config: HolochainConfig = None)
    async def connect(self) -> bool
    async def disconnect(self)
    async def get_metrics(self) -> Dict[str, Any]
```

#### `HolochainConfig`
Configuration for Holochain connection.

```python
@dataclass
class HolochainConfig:
    network_type: HolochainNetworkType = LOCAL
    conductor_endpoint: str = "ws://localhost:9001"
    admin_port: int = 9001
    app_interface_port: int = 9002
    dna_path: Optional[str] = None
    agent_key: Optional[str] = None
    log_level: HolochainLogLevel = INFO
    max_retries: int = 3
    timeout: float = 30.0
    enable_encryption: bool = True
    enable_persistence: bool = True
```

#### `FamilyMember`
Represents a family member in the Holochain network.

```python
@dataclass
class FamilyMember:
    agent_id: str
    name: str
    role: FamilyRole
    genetic_code: Dict[str, float]
    public_key: str
    created_at: datetime
    last_active: datetime
    reputation_score: float = 0.0
    family_bonds: List[str] = field(default_factory=list)
    contributions: List[Dict[str, Any]] = field(default_factory=list)
```

### Family Management

#### Register Family Member
```python
async def register_family_member(self, member: FamilyMember) -> str:
    """Register a family member in Holochain"""
```

#### Create Family Bond
```python
async def create_family_bond(self, agent_id_1: str, agent_id_2: str, 
                           bond_strength: float, bond_type: str = "family") -> str:
    """Create family bond between two agents"""
```

#### Record Contribution
```python
async def record_contribution(self, agent_id: str, contribution_type: str, 
                           value: float, description: str) -> str:
    """Record agent contribution in family ledger"""
```

#### Update Genetic Inheritance
```python
async def update_genetic_inheritance(self, inheritance: GeneticInheritance) -> str:
    """Record genetic inheritance in Holochain"""
```

### Query Methods

#### Get Family Member
```python
async def get_family_member(self, agent_id: str) -> Optional[FamilyMember]:
    """Get family member by ID"""
```

#### Get Family Tree
```python
async def get_family_tree(self, root_agent_id: str = None) -> Dict[str, Any]:
    """Get complete family tree"""
```

#### Get Genetic Lineage
```python
async def get_genetic_lineage(self, agent_id: str) -> List[GeneticInheritance]:
    """Get genetic lineage for an agent"""
```

#### Get Contributions
```python
async def get_contributions(self, agent_id: str = None, 
                         start_time: datetime = None, 
                         end_time: datetime = None) -> List[Dict[str, Any]]:
    """Get contributions with optional filters"""
```

### Advanced Features

#### Create Family Consensus
```python
async def create_family_consensus(self, proposal: Dict[str, Any], 
                              voting_period: timedelta = timedelta(hours=24)) -> str:
    """Create family consensus proposal"""
```

#### Vote on Consensus
```python
async def vote_on_consensus(self, consensus_id: str, vote: str, 
                          reason: str = None) -> str:
    """Vote on family consensus proposal"""
```

#### Get Family Reputation
```python
async def get_family_reputation(self, agent_id: str) -> float:
    """Calculate family member reputation based on contributions and interactions"""
```

### Utility Methods

#### Backup Family Data
```python
async def backup_family_data(self, backup_path: str) -> bool:
    """Backup all family data to file"""
```

#### Restore Family Data
```python
async def restore_family_data(self, backup_path: str) -> bool:
    """Restore family data from backup file"""
```

## Configuration

### Network Types

```python
class HolochainNetworkType(Enum):
    LOCAL = "local"           # Local development network
    STAGING = "staging"       # Staging network for testing
    PRODUCTION = "production"  # Production network
    CUSTOM = "custom"         # Custom network configuration
```

### Family Roles

```python
class FamilyRole(Enum):
    PATRIARCH = "patriarch"           # Head of household
    MATRIARCH = "matriarch"           # Quality guardian
    ELDEST_CHILD = "eldest_child"     # Primary provider
    YOUNGER_CHILD = "younger_child"   # Supporting members
    MILITARY_COMMANDER = "military_commander"  # Military defense
```

### Logging Levels

```python
class HolochainLogLevel(Enum):
    DEBUG = "debug"    # Detailed debugging information
    INFO = "info"      # General information messages
    WARN = "warn"      # Warning messages
    ERROR = "error"    # Error messages only
```

## Examples

### Complete Family Setup

```python
import asyncio
from datetime import datetime
from albrite_holochain_sdk import (
    create_albrite_holochain_sdk, FamilyMember, FamilyRole,
    GeneticInheritance, HolochainNetworkType
)

async def setup_family():
    # Initialize SDK
    sdk = await create_albrite_holochain_sdk(
        network_type=HolochainNetworkType.LOCAL,
        dna_path="albrite_family.dna"
    )
    
    try:
        # Create patriarch
        patriarch = FamilyMember(
            agent_id="patriarch_001",
            name="General Albrite",
            role=FamilyRole.PATRIARCH,
            genetic_code={
                "resilience": 0.95, "intelligence": 0.92, "creativity": 0.88,
                "empathy": 0.85, "leadership": 0.98, "speed": 0.87,
                "memory": 0.91, "communication": 0.94, "adaptability": 0.89,
                "intuition": 0.86
            },
            public_key="patriarch_pub_key",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # Create matriarch
        matriarch = FamilyMember(
            agent_id="matriarch_001",
            name="Isabella Albrite",
            role=FamilyRole.MATRIARCH,
            genetic_code={
                "resilience": 0.88, "intelligence": 0.94, "creativity": 0.91,
                "empathy": 0.98, "leadership": 0.87, "speed": 0.85,
                "memory": 0.93, "communication": 0.96, "adaptability": 0.90,
                "intuition": 0.92
            },
            public_key="matriarch_pub_key",
            created_at=datetime.now(),
            last_active=datetime.now()
        )
        
        # Register family members
        await sdk.register_family_member(patriarch)
        await sdk.register_family_member(matriarch)
        
        # Create family bond
        await sdk.create_family_bond("patriarch_001", "matriarch_001", 0.95, "spouse")
        
        # Record genetic inheritance for child
        inheritance = GeneticInheritance(
            inheritance_id="inheritance_001",
            parent_ids=["patriarch_001", "matriarch_001"],
            child_id="child_001",
            inherited_traits={
                "resilience": 0.915, "intelligence": 0.93, "creativity": 0.895,
                "empathy": 0.915, "leadership": 0.925, "speed": 0.86,
                "memory": 0.92, "communication": 0.95, "adaptability": 0.895,
                "intuition": 0.89
            },
            mutations={"intuition": 0.02},  # Small mutation
            timestamp=datetime.now()
        )
        
        await sdk.update_genetic_inheritance(inheritance)
        
        # Record contributions
        await sdk.record_contribution("patriarch_001", "strategic_planning", 100.0, "Family strategic planning")
        await sdk.record_contribution("matriarch_001", "quality_assurance", 85.0, "Family quality management")
        
        # Get family reputation
        patriarch_rep = await sdk.get_family_reputation("patriarch_001")
        matriarch_rep = await sdk.get_family_reputation("matriarch_001")
        
        print(f"Patriarch reputation: {patriarch_rep}")
        print(f"Matriarch reputation: {matriarch_rep}")
        
        # Get family tree
        family_tree = await sdk.get_family_tree("patriarch_001")
        print(f"Family tree: {family_tree}")
        
        # Get metrics
        metrics = await sdk.get_metrics()
        print(f"SDK metrics: {metrics}")
        
        # Backup family data
        await sdk.backup_family_data("albrite_family_backup.json")
        
    finally:
        await sdk.disconnect()

asyncio.run(setup_family())
```

### Event Handling

```python
async def setup_event_handlers():
    sdk = await create_albrite_holochain_sdk()
    
    # Register event handlers
    async def handle_new_transaction(event):
        print(f"New transaction: {event}")
    
    async def handle_family_update(event):
        print(f"Family updated: {event}")
    
    sdk.register_event_handler("new_transaction", handle_new_transaction)
    sdk.register_event_handler("family_update", handle_family_update)
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await sdk.disconnect()
```

### Consensus Decision Making

```python
async def family_consensus_example():
    sdk = await create_albrite_holochain_sdk()
    
    try:
        # Create consensus proposal
        proposal = {
            "title": "Family Resource Allocation",
            "description": "Allocate resources for new family member training",
            "options": ["Approve", "Reject", "Modify"],
            "required_votes": 3,
            "voting_deadline": (datetime.now() + timedelta(hours=24)).isoformat()
        }
        
        consensus_id = await sdk.create_family_consensus(proposal)
        print(f"Consensus created: {consensus_id}")
        
        # Family members vote
        await sdk.vote_on_consensus(consensus_id, "Approve", "Supports family growth")
        await sdk.vote_on_consensus(consensus_id, "Approve", "Good investment")
        await sdk.vote_on_consensus(consensus_id, "Modify", "Needs more resources")
        
    finally:
        await sdk.disconnect()
```

## Performance Metrics

The SDK tracks comprehensive performance metrics:

```python
metrics = await sdk.get_metrics()
print(metrics)
# Output:
# {
#     "sdk_metrics": {
#         "total_transactions": 150,
#         "successful_transactions": 145,
#         "failed_transactions": 5,
#         "average_response_time": 0.85,
#         "network_health": 0.98,
#         "family_size": 12
#     },
#     "network_status": {
#         "connected_peers": 8,
#         "bandwidth": "1.2 MB/s",
#         "block_height": 1234
#     },
#     "family_size": 12,
#     "active_transactions": 3,
#     "connection_status": True,
#     "uptime": 3600.0
# }
```

## Error Handling

The SDK provides comprehensive error handling:

```python
try:
    await sdk.register_family_member(member)
except Exception as e:
    print(f"Failed to register family member: {e}")
    # Handle error appropriately
```

Common error types:
- **Connection Errors**: Failed to connect to Holochain conductor
- **Authentication Errors**: Invalid agent key or credentials
- **Transaction Errors**: Failed transaction submission or validation
- **Network Errors**: Network connectivity issues

## Security Considerations

### Key Management
- Store agent keys securely
- Use hardware security modules when possible
- Rotate keys regularly

### Encryption
- Enable encryption for sensitive data
- Use strong cryptographic algorithms
- Verify message integrity

### Access Control
- Implement proper role-based access
- Regularly audit permissions
- Monitor for unauthorized access

## Troubleshooting

### Common Issues

#### Connection Failed
```bash
# Check if Holochain conductor is running
hc sandbox list

# Start conductor if not running
hc sandbox run
```

#### DNA Installation Failed
```bash
# Verify DNA file exists
ls -la path/to/albrite_family.dna

# Check DNA hash
sha256sum path/to/albrite_family.dna
```

#### Transaction Timeout
```python
# Increase timeout in configuration
config = HolochainConfig(timeout=60.0)
```

### Debug Mode

Enable debug logging:

```python
config = HolochainConfig(log_level=HolochainLogLevel.DEBUG)
sdk = AlbriteHolochainSDK(config)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This SDK is part of the Albrite AI Family project and is licensed under the same terms as the main project.

## Support

For support and questions:
- Check the documentation
- Review the examples
- Open an issue on the repository
- Contact the development team

---

**The Albrite Holochain SDK brings the power of distributed coordination to genetic family systems, enabling truly decentralized, tamper-resistant family operations on the Holochain network.**
