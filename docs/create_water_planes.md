## How to create water planes

📹 Check out the video version of this tutorial.  

[![YouTube tutorial](https://github.com/iwatkot/maps4fs/releases/download/2.0.2/ep06-play.png)](https://www.youtube.com/watch?v=lZeEZ-ce3cI)  

The generator will automatically generates the obj files for the water planes, but you need to process them both in Blender and in Giants Editor for them to look correctly in the game.

1. Find the obj file in the `water` directory.
2. Import the obj file in Blender.

![Import obj file in Blender](https://github.com/user-attachments/assets/c29c7187-2cd5-45b8-ad32-e6af85430c59)

3. Ensure that imported object selected, right click anywhere and select **Set Origin** -> **Origin to Geometry**.

![Set origin to geometry](https://github.com/user-attachments/assets/e2cf16af-5d42-449a-935a-524a70643f23)

4. Press the **N** key to open the **Transform** panel and set the **Location** to **0, 0, 0** and **Rotation** to **0, 0, 0**.  
DO NOT TOUCH SCALE AND DIMENSIONS!

![Set location and rotation](https://github.com/user-attachments/assets/5489c013-2495-47c9-b422-d0d1d5b1ef9d)

5. Add an empty material to the object.

![Add empty material](https://github.com/user-attachments/assets/5923b99f-1483-4b34-98bd-4e32ba6fec5b)

6. Change the emission color to fully black.

![Emission](https://github.com/user-attachments/assets/3e3e028e-a3d8-40ce-8a00-9bc701147fbb)

![Black emission](https://github.com/user-attachments/assets/5687df82-6fe2-405d-af02-106d8c5e554b)

7. Apply the **Decimate** modifier to the object and **Shade Smooth**. You can find the example of this in the tutorial about [Background Terrain](https://github.com/iwatkot/maps4fs/blob/main/docs/create_background_terrain.md).

8. Open the **Giants Editor I3D Exporter** and set the path to the directory where the game is installed.

![Set path to the game directory](https://github.com/user-attachments/assets/971e1e13-235e-4ff3-83f1-a3f8af977c5f)

9. Go to the **Material** tab and press the **Detect Path** button.

![Detect path](https://github.com/user-attachments/assets/63fb3970-114b-4964-9032-c7ad00c5aa55)

10. Select shader **oceanShader.xml**.

![Select ocean shader](https://github.com/user-attachments/assets/8c6ddb13-cd0d-4726-96a6-4b3f2657cb57)

11. SAVE THE BLENDER FILE! Then press the **Apply** button.

![Apply](https://github.com/user-attachments/assets/4e5c53d8-73b7-4a25-b20a-b40d58477b1d)

12. Go to the **Export**, ensure that your object is selected and press the **Export selected** button.

![Export selected](https://github.com/user-attachments/assets/ba592c54-2d33-4e5b-9fe4-d03e49268d7d)

13. Open the Giants Editor and import the i3d file. It will be black, but don't worry, it's normal.  
After it, position the water plane in the correct place.

![Position the water plane](https://github.com/user-attachments/assets/c7257060-bd83-498f-a5dc-098e675540df)

14. Open the **Material Editing** window and select your water plane.

15. Change the **Variation** to **simple** and then edit values as on the screenshot.  
Those are default values for the water plane, but you can play with them to achieve the desired effect.

![Water plane values](https://github.com/user-attachments/assets/6624878c-818d-4371-bbf9-8bb6ace6589f)

16. Set **Smoothness** and **Metalness** to **1**.

17. Click on the button near the **Normal map**.

![Normal map](https://github.com/user-attachments/assets/95adc493-983a-46ae-bd20-7d1f4e998ba7)

18. Click on the **...** button and provide the path to the **water_normal.dds** file.  
It's placed in `where-the-game-is-installed/data/maps/textures/shared/water_normal.dds`.

![Water normal map](https://github.com/user-attachments/assets/515de60b-bc1a-4843-b548-2820107435af)

19. You should see the normal map in the window. Press the **OK** button.

![Normal map window](https://github.com/user-attachments/assets/bee7955f-7f6c-4d94-978c-0ab7835b9e2b)

20. Now switch to the UserAttributes tag, enter name `onCreate`, select the `Script callback`, and click Add.
After it, set the value of the Attribute to `Environment.onCreateWater`.

22. It should look like this.

![Water plane in GE](https://github.com/user-attachments/assets/b246cf85-b044-4ceb-bff4-9b32a753b143)

We're done here!
