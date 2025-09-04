# Procedural Generation Integration

This guide demonstrates how to combine Maps4FS with Giants Editor's Procedural Generator to create realistic terrain features including textures, foliage, trees, and other 3D objects based on real-world geographic data.

## Overview

The procedural generation workflow leverages publicly available geographic information to automatically place and distribute map elements, creating more authentic and detailed environments with minimal manual effort.

**Key Benefits:**
- Automated texture placement based on real terrain data
- Realistic foliage and tree distribution
- Reduced manual editing time
- Geographic accuracy in object placement

## Prerequisites & Installation

### Step 1: Download PG Scripts
1. Navigate to the [FS25 Procedural Generation GitLab repository](https://gitlab.com/fs25_guides/fs25_proceduralgeneration/-/tree/main/PG_Scripts)
2. Click the **Code Button** → **Download ZIP**

![Download Scripts](https://github.com/user-attachments/assets/b698eb06-cdbf-484f-b458-10cfd0297ea0)

### Step 2: Install Scripts
1. Extract the downloaded ZIP file
2. Navigate to your Farming Simulator 25 installation directory
3. Copy the `.lua` files to: `Farming Simulator 25\data\maps\proceduralPlacements\`

**⚠️ Important:** The `.lua` files must be placed directly in the `proceduralPlacements` folder, not in a subfolder.

![Unzip Scripts](https://github.com/user-attachments/assets/74246b9d-a871-4ea6-aca3-67d50bdfbec0)

## Implementation Workflow

### Step 3: Prepare Your Map
1. **Generate your map** using Maps4FS following standard procedures
2. **Open the map** in Giants Editor
3. **Remove the Trees group object** to prevent conflicts with procedural generation

![Remove Trees](https://github.com/user-attachments/assets/96ffa017-f32a-49ac-aa9d-ea89cc3397f3)

### Step 4: Configure Procedural Placement
1. Open **Window → Procedural Placement...**
2. Navigate to the **Rule** tab
3. **Save your map** before proceeding (critical step to prevent data loss)
4. Click **Place Objects** to begin generation

![Place Objects](https://github.com/user-attachments/assets/6754cc83-1af2-4df0-a0f7-0494d80c1e7d)

**⚠️ Processing Note:** Large rulesets may take several minutes to complete. The editor will appear unresponsive during generation - this is normal behavior.

### Step 5: Review and Iterate
After generation completes, you can:
- **Fine-tune rulesets** and masks for optimal results
- **Re-run generation** with modified parameters
- **Use results as a foundation** for detailed manual editing

![Result](https://github.com/user-attachments/assets/04274220-42de-442a-b218-4792804948ca)

## Advanced Customization

### Modifying Texture Rules
**Purpose:** Adjust which textures are applied to specific terrain areas

1. Open **Window → Procedural Placement...** → **Rule** tab
2. Select the target rule (e.g., `T_Forests`)
3. **Add layers:** Use the **Add Object** button
4. **Remove layers:** Click the **X** buttons next to unwanted layers
5. Apply changes with **Place Objects**

![Change Texture](https://github.com/user-attachments/assets/a447c080-6950-432a-aaab-91fc40c46124)

### Adjusting Field Boundaries
**Purpose:** Control field size and padding for realistic agricultural layouts

1. Open **Window → Procedural Placement...** → **Rule** tab
2. Select the field rule (e.g., `F_Acres`)
3. **Adjust boundaries:**
   - **Increase `borderIn`**: Shrinks field area (more padding)
   - **Increase `borderOut`**: Expands field area (less padding)
4. **Update related rules:** Modify corresponding texture rules (e.g., `T_Acres`)
5. Apply changes with **Place Objects**

![Change Padding](https://github.com/user-attachments/assets/2b9206ab-cf03-432a-a2c2-65892f2ba851)

### Creating Custom I3D Object References
**Purpose:** Add custom objects (trees, buildings, decorations) to procedural generation

#### Step 1: Register New Objects
1. Open **Window → Procedural Placement...** → **Objects** tab
2. Click **Add i3d reference**
3. **Browse and select** your target object

**Resource Location:** Default game trees are located in `Farming Simulator 25\data\maps\trees`

4. **Assign a descriptive name** for easy identification

![Create Object](https://github.com/user-attachments/assets/84ad0106-94a0-48f9-b94d-9687070ae504)

#### Step 2: Create Placement Rules
1. Navigate to the **Rules** tab
2. Click **Add Rule**
3. Enter a descriptive rule name (e.g., `R_Grasslands`)
4. Select **PG_Mask_Fill.lua** from the script dropdown

![Select Script](https://github.com/user-attachments/assets/30ef7c41-3606-4ed5-a73a-4f9ba29b973c)

#### Step 3: Configure Rule Parameters
1. **Object Min Distance:** Set minimum spacing between objects
2. **genMaskName:** Specify the target mask (e.g., `Grasslands`)
3. **Add Object:** Select your previously created object reference
4. Click **Apply** to save configuration
5. Click **Place Objects** to execute the rule

![Create Object Rule](https://github.com/user-attachments/assets/20f989f1-e4ee-4453-9752-ce43dd4f00ee)

## Ruleset Architecture

### Rule Naming Conventions
Understanding the default ruleset structure helps optimize your procedural generation workflow:

**Prefix Classifications:**
- **MaskName** → Loads and links masks with `genMaskName` parameters
- **T_** → Texture filling operations for terrain surfaces
- **F_** → Foliage placement and distribution
- **Clear_** → Object removal operations within specified masks
- **R_** → I3D reference object placement (trees, structures)
- **Subtract_** → Layer subtraction operations for mask refinement

### Processing Order
**Rules execute in hierarchical order:**
1. **Mask Loading** → Initialize geographic data layers
2. **Mask Operations** → Process and refine data layers
3. **Texturing** → Apply surface materials
4. **Foliage** → Place vegetation elements
5. **References** → Position 3D objects

## Performance Optimization

### Strategy 1: Selective Rule Execution
**For iterative development and testing:**

1. Click **Disable Main Rules** to deactivate all rules
2. **Manually activate** only the rules you want to test
3. Press **Apply** for each selected rule
4. Execute with **Place Objects**

**Restoration:** Use **Enable Main Rules** or restart Giants Editor to reactivate all rules.

### Strategy 2: Manage Reset Operations
**The default `ClearAll` rule provides a complete reset but significantly impacts performance.**

- **During development:** Disable for faster iteration
- **For final generation:** Re-enable for complete clean slate

## Configuration Integration

### Generating Custom Masks
**Create procedural masks directly from Maps4FS geographic data:**

```json
{
  "name": "concrete",
  "count": 2,
  "tags": { "building": true },
  "procedural": ["PG_buildings"]
}
```

This configuration generates `data/masks/PG_buildings.png` based on geographic areas tagged as buildings.

### Multi-Mask Generation
**Generate multiple mask variations from single geographic data:**

```json
{
  "name": "grassDirtPatchy",
  "count": 2,
  "tags": { "landuse": "meadow" },
  "procedural": ["PG_meadows", "PG_grasslands"]
}
```

This creates both `PG_meadows` and `PG_grasslands` masks from meadow-tagged areas, enabling varied terrain treatment options.