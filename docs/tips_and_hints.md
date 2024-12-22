## Tips and Hints

Here you'll find some useful advice for a map creation process.

### Create a Ground Colision Map

At the end of the map creation process, you need to create a ground collision map. It's a very important step because it will define where the vehicles can drive and where they can't.  
To do it, in Giants Editor go to **Scripts** -> **Shared scripts** -> **Map** -> **Create Ground Collision Map**. If you don't do this, you'll face some issues in the game.  
➡️ Any time you edit the map, you need to do it again.

### Put the objects on the terrain

After generation, the trees (or any other object) may be floating above the terrain. To fix this, you need to put them on the terrain.  
1. Select the objects in the **Scenegraph**.
2. DO NOT ❌ Select the groups of objects, you need to select EACH OBJECT. Otherwise, it won't work. To make it easier, you can select and first one, scroll down to the last one, hold **Shift** and click on the last one.

![Select objects](https://github.com/user-attachments/assets/2afbea4e-6d0c-4ee5-a3c1-ce021926c9fd)

3. Click **Scripts** -> **Shared scripts** -> **Map** -> **Terrain** -> **Place objects on terrain**.