## Farmlands

It's a pretty simple component of the map, but it's also one of the most important. If you do not define the farmlands InfoLayer in Giants Editor, you will not be able to buy any land in the game. But, lucky for us, it's simple and straightforward to set up.  
➡️ The generator automatically draws farmlands and adds them to the `farmlands.xml` file. But, if you need to adjust them, you can do it manually.

### Setting up the Farmlands InfoLayer

In the Giants Editor enable the `Terrain Info Layer Paint Mode` tool [1], then select the **farmlands** in the **Info Layer** selector [2]. Now you can choose the actual farmland number [3] and paint it on the map.  
Remember, that if you did not paint some region by any farmland, it will not be possible to buy it in game. You can left those for regions that are not supposed to be bought by the player (city, forest, etc.).  

![Drawing farmlands in the Giants Editor](https://github.com/user-attachments/assets/f16f172d-6a6c-4026-97a1-a1f59149a62c)

After painting the farmlands and saving the file, you need to edit the `config/farmlands.xml` file to match the farmlands you painted in the editor.

### Editing the farmlands.xml
You'll find the `farmlands.xml` file in the `config` directory of your map. Open it in a text editor and add the farmlands you painted in the editor. The file should look like this:

```xml
    <farmlands infoLayer="farmlands" pricePerHa="60000">
        <farmland id="1" priceScale="1" npcName="FORESTER" />
        <farmland id="2" priceScale="1" npcName="GRANDPA" />
    </farmlands>
```

So, the keys here are kinda obvious, if you want to change the global price for the lands, you can do it in the `pricePerHa` attribute. The `farmland` tag contains the information about the lands. The `id` attribute is the ID of the land, the `priceScale` is the multiplier for the price of the land, and the `npcName` is the name of the NPC who owns the land.  

After drawing the farmlands in the Giants Editor and editing the `farmlands.xml` file, you should be able to buy the lands in the game.