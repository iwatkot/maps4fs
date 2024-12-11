## Fields

I guess you know what a field is. It's where we actually grow and harvest our crops. Important note: it's not mandatory to add fields in Giants Editor, since it's possible for player to create a field in game. But it would be much more convenient to create fields while working in your mod.  
And the coolest thing: the generator already created everything for you! Just one click and all the fields will be shown on the map.

### Where the fields come from?

Before we dive into details, let's talk about the source of the fields. The data for adding everything to your map (including fields) comes from the [OpenStreetMap](https://www.openstreetmap.org/). So, it may happen that something is missing or incorrect. In this case, it's recommended to go to OSM by yourself and fix the issue. It's very simple, and you can do it without any special knowledge. You'll find more information about it in the [FAQ](https://github.com/iwatkot/maps4fs/blob/main/docs/FAQ.md) section of the docs.

### How to add fields to the map?
The generator will automatically create all the required nodes in the `map.i3d` file, so you need only to open the map in Giants Editor, go to **Scripts** -> **Shared scripts** -> **Map** -> **Farmland fields** -> **Field toolkit** and click on the **Repaint all fields** button.  
After it all the fields should appear on the map. Note: due to different geometries in OSM data, some fields may not appear if they were defined as multipolygons. In this case, you need to create them manually.  

![PolygonPoints](https://github.com/user-attachments/assets/ae49761d-aee5-4879-9531-b4522ac55cc2)

To add a new field click on the **Create field** button in the toolkit. A new field will appear at the center of **fields** TransformGroup. Now all you need to do is place the **PolygonPoints** on the correct positions on the map, and after it click on the **Repaint selected field** button.