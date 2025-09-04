# Farmland System Architecture

## Overview: Property Ownership Framework

Farmlands define the **property ownership and economic structure** of your map, establishing purchasable land parcels that players can acquire to expand their agricultural operations. Unlike fields (which are cultivation areas), farmlands represent the underlying property boundaries that control access, ownership, and economic progression.

**Critical Function**: Without properly configured farmlands, players cannot purchase land in-game, effectively breaking the economic progression system that drives long-term gameplay engagement.

**System Relationship**: Farmlands serve as containers for fields, buildings, and other assets, with ownership of the farmland granting access to all contained elements.

## Automated Farmland Generation

### Maps4FS Integration

**Automated Creation**: Maps4FS automatically analyzes geographic data and generates logical farmland boundaries based on real-world property patterns, agricultural zones, and terrain features.

**Output Generation**:
- **Visual Mapping**: Farmland boundaries painted in the terrain info layer
- **Configuration File**: Complete `farmlands.xml` with economic parameters
- **Geographic Logic**: Boundaries reflect realistic property divisions and land use patterns

**Quality Assurance**: Generated farmlands undergo validation to ensure appropriate sizing, logical boundaries, and economic balance for progressive gameplay.

## Technical Implementation

### Info Layer System

**Core Requirement**: Farmlands must be defined in Giants Editor's terrain info layer system to function in-game.

**Technical Structure**:
- **Layer Type**: `farmlands` info layer in terrain system
- **Data Format**: Indexed color mapping where each farmland ID corresponds to a specific color value
- **Boundary Definition**: Painted regions define exact ownership boundaries for each property

### Giants Editor Configuration

**Farmland Painting Workflow**:

![Farmlands Configuration in Giants Editor](https://github.com/user-attachments/assets/f16f172d-6a6c-4026-97a1-a1f59149a62c)

1. **Enable Paint Mode**: Activate `Terrain Info Layer Paint Mode` [1]
2. **Select Layer**: Choose **farmlands** from Info Layer selector [2]  
3. **Choose Farmland ID**: Select specific farmland number [3] for painting
4. **Paint Boundaries**: Apply farmland designation to desired map regions
5. **Validate Coverage**: Ensure all purchasable areas are properly designated

**Strategic Considerations**:
- **Unpainted Regions**: Areas without farmland designation remain unpurchasable (suitable for cities, protected forests, water bodies)
- **Boundary Precision**: Accurate painting ensures clear property lines and prevents ownership conflicts
- **Economic Zones**: Consider grouping related agricultural areas into logical property units

## Economic Configuration

### Farmlands.xml Structure

**File Location**: `config/farmlands.xml` within your map directory

**Complete Configuration Example**:
```xml
<farmlands infoLayer="farmlands" pricePerHa="60000">
    <farmland id="1" priceScale="1.0" npcName="FORESTER" />
    <farmland id="2" priceScale="1.5" npcName="GRANDPA" />
    <farmland id="3" priceScale="0.8" npcName="NEIGHBOR" />
    <farmland id="4" priceScale="2.0" npcName="CORPORATION" />
</farmlands>
```

### Economic Parameters

**Global Settings**:
- **`pricePerHa`**: Base price per hectare (default: €60,000)
- **`infoLayer`**: References the terrain info layer name (must be "farmlands")

**Individual Farmland Properties**:
- **`id`**: Unique identifier matching the painted info layer value
- **`priceScale`**: Price multiplier for this specific farmland (1.0 = base price)
- **`npcName`**: Current owner identifier for narrative and economic context

### Strategic Pricing Framework

**Price Scale Guidelines**:
- **Premium Locations** (1.5-2.5×): Properties with high-value fields, optimal terrain, or strategic positioning
- **Standard Properties** (0.8-1.2×): Typical agricultural land with average characteristics
- **Starter Areas** (0.5-0.8×): Entry-level properties for new players
- **Specialty Zones** (1.0-3.0×): Unique properties with specific characteristics (forests, industrial access)

**Economic Balance Considerations**:
- **Progressive Acquisition**: Design farmland prices to support logical expansion patterns
- **Geographic Value**: Reflect real-world property value factors (location, terrain quality, infrastructure access)
- **Gameplay Pacing**: Balance affordability with progression challenge

## Advanced Farmland Design

### Strategic Property Division

**Optimal Farmland Sizing**:
- **Starter Properties**: 10-25 hectares for initial player acquisition
- **Mid-Game Expansion**: 25-75 hectares for established operations
- **Large-Scale Operations**: 75+ hectares for advanced agricultural enterprises

**Boundary Logic**:
- **Natural Divisions**: Use rivers, roads, or terrain features as logical property lines
- **Field Integration**: Ensure farmland boundaries encompass complete field units
- **Infrastructure Access**: Include necessary roads and utility access within property boundaries

### Economic Progression Design

**Tiered Property System**:
1. **Entry Level**: Affordable properties near starting location with basic infrastructure
2. **Expansion Phase**: Mid-tier properties offering specialized opportunities (forestry, livestock)
3. **Premium Acquisitions**: High-value properties with optimal conditions and strategic advantages
4. **Elite Holdings**: Luxury properties representing end-game agricultural empires

**Owner Integration**:
- **Narrative Context**: NPC names should reflect local culture and farming traditions
- **Economic Relationships**: Consider how existing owners might interact with player progression
- **Selling Motivation**: Implied reasons why properties become available for purchase

## Quality Assurance & Validation

### Testing Procedures

**Functionality Verification**:
1. **Load Map**: Test map loading and farmland layer recognition
2. **Purchase Testing**: Verify all painted farmlands are purchasable in-game
3. **Boundary Accuracy**: Confirm property lines match intended boundaries
4. **Economic Balance**: Test progression pacing and affordability curves

**Common Issues & Solutions**:
- **Unpurchasable Land**: Verify info layer painting and XML configuration alignment
- **Boundary Conflicts**: Check for overlapping or gap issues in painted regions
- **Economic Imbalance**: Adjust price scales based on gameplay testing results

### Professional Workflow

**Comprehensive Farmland Development**:
1. **Generate Base Structure**: Use Maps4FS automated generation as foundation
2. **Analyze Geographic Logic**: Review boundaries for real-world property patterns
3. **Optimize Economic Structure**: Balance pricing for progressive gameplay
4. **Refine Boundaries**: Adjust property lines for optimal field integration and logical divisions
5. **Validate Implementation**: Comprehensive testing of purchase mechanics and economic progression

**Strategic Outcome**: Well-designed farmland systems create engaging economic progression that reflects realistic property acquisition while providing clear goals and meaningful expansion opportunities for players at all skill levels.