# License Plates

*[Screenshot placeholder showing license plate customization feature]*

Maps4FS automatically generates country-specific license plates for FS25 maps based on the map's geographic location. This feature adds authentic regional licensing to vehicles in your custom maps.

## Compatibility

- **FS25**: ✅ Fully supported
- **FS22**: ❌ Not supported

## How It Works

The system automatically:
1. **Detects country** from map coordinates using geographic lookup
2. **Applies country code** (e.g., Germany → "D", Serbia → "SRB", France → "F")
3. **Adds regional prefix** (if specified) for cities/regions within the country
4. **Generates custom license plates** combining both elements
5. **Updates map configuration** to use the customized plates
6. **Falls back gracefully** to default US plates for unsupported regions

## License Plate Format

License plates consist of two parts:

### Country Code (Automatic)
**Automatically detected** from your map's coordinates:
- Follows international vehicle registration standards
- Examples: D (Germany), SRB (Serbia), F (France), PL (Poland)
- Cannot be manually overridden

### Regional Prefix (Optional)
**Manually customizable** via UI settings:
- Represents specific regions, cities, or administrative areas
- Examples: "NS" (Novi Sad), "M" (Munich), "75" (Paris)
- 1-3 characters maximum

### Combined Result
Final license plates show: **[Country Code] [Regional Prefix]**
- Serbia, Novi Sad: `"SRB NS"`
- Germany, Munich: `"D M"`
- France, Paris: `"F 75"`
- Poland, Krakow: `"PL KRK"`

## Supported Regions

License plate generation works for European countries and specific other regions. The system automatically detects the appropriate country code based on your map's geographic location.

**For unsupported countries**: The system automatically uses the default in-game US license plates. This ensures your map works regardless of location while providing enhanced authenticity for supported regions.

## Regional Customization

You can customize the regional prefix using the **I3D Settings → License plate prefix** option in the UI.

### Regional Prefix Examples
- **Cities**: `"NS"` (Novi Sad), `"BG"` (Belgrade), `"M"` (Munich)
- **Regions**: `"75"` (Paris region), `"BY"` (Bavaria), `"SZ"` (Salzburg)
- **Custom**: Any 1-3 character identifier for your specific area

### Configuration
- **Access via**: I3D Settings → License plate prefix
- **Length**: 1-3 characters maximum (letters or numbers)
- **Case**: Automatically converted to uppercase
- **Optional**: Leave empty for country code only

## Technical Details

### Map Configuration

License plates are configured in your map's `map.xml` file:

```xml
<licensePlates filename="map/licensePlates/licensePlatesPL.xml" />
```

### Customization Files

If you want to manually customize or edit license plates:

1. **Navigate to**: `map/licensePlates/licensePlatesPL.xml`
2. **Edit the configuration** for custom layouts, colors, or positioning
3. **Modify textures** in the same directory for visual customization

### File Structure
```
map/
├── map.xml                              # References license plates
└── licensePlates/
    ├── licensePlatesPL.xml             # License plate configuration
    ├── licensePlatesPL.i3d             # 3D model definition
    └── licensePlates_diffuse.png       # Generated texture
```

## US License Plates

**Note**: US license plates use completely different formats and layouts compared to European standards. Due to this complexity and regional variation, US plates are not automatically generated. 

**Recommendation**: If you need specific US license plates, manually find and customize the appropriate template for your specific state/region.

## Troubleshooting

### Performance Warning (PNG Textures)
Maps4FS generates license plate textures as **PNG files**, which may trigger performance warnings in Giants Editor logs. This is expected behavior.

**For optimal performance**, convert the generated PNG to DDS format:

1. **Convert texture**: Use image editing software or DDS conversion tools
2. **Replace file**: Update `licensePlates_diffuse.png` with `licensePlates_diffuse.dds`
3. **Update reference**: Edit `licensePlatesPL.i3d` file:
   ```xml
   <!-- Change from: -->
   <File fileId="12" filename="licensePlates_diffuse.png" />
   
   <!-- To: -->
   <File fileId="12" filename="licensePlates_diffuse.dds" />
   ```

💡 **Tip**: See [DDS Conversion](dds_conversion.md) for detailed conversion instructions.

### License Plates Not Appearing
- Verify your map coordinates are within supported countries
- Check that FS25 compatibility is enabled
- Ensure the license plate prefix is 1-3 letters maximum

### Wrong Country Detected
- Double-check your map's center coordinates
- Consider manually setting the prefix via UI settings

### Custom Plates Not Working
- Check `map/licensePlates/licensePlatesPL.xml` syntax
- Ensure texture files are properly generated
- Verify `map.xml` references the correct license plate file

## Related Documentation

- [Map Structure](map_structure.md) - Understanding map file organization
- [Generation Settings](generation_settings.md) - Configuring map generation options
- [Step by Step Guide](step_by_step_guide.md) - Complete map creation workflow