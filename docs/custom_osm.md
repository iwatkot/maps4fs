## How to create a custom OSM file

📹 Check out the video version of this tutorial.

<a href="https://www.youtube.com/watch?v=duTXvkIiECY" target="_blank"><img src="https://github.com/user-attachments/assets/8e130247-57f2-4d0a-9a9a-a13fa847c0d8"/></a>

If you don't want to bother yourself editing the public version of the OSM data, deal with the community and so on, you can easily create your own OSM file and do there whatever you want. Here is a step-by-step guide on how to do it.

1. Download the JOSM editor from the [official website](https://josm.openstreetmap.de/) or directly from the [Windows Store](https://apps.microsoft.com/detail/xpfcg1gv0wwgzx) with one click.

2. Create a new layer (Ctrl + N).

3. Add imagery to see the map (Ctrl + Shift + N). You can use any map provider you want, in this example I'm using Bing.

![Add imagery](https://github.com/user-attachments/assets/8b6f0a68-821f-42d4-aff7-fda56485c175)

4. Download the OSM data: **File** -> **Download data** (Ctrl + Shift + Down).

![Download OSM data](https://github.com/user-attachments/assets/35b78426-73f8-4332-94dc-952510e025f1)

5. Draw the area of your ROI (region of interest). You don't need precision here, just ensure that it's large enough to cover the area you want to work with.  
After selecting the area, click **Download**.  
If you see the error message "Download area too large", download it in parts.

![Draw the area](https://github.com/user-attachments/assets/ba033f1a-adcb-4215-9852-4f01dfe1e4ef)

6. Now you should see all the data from the selected area.

7. You need to remove all the relations, otherwise the file can not be read by the `osmnx` library. To do it, go to the **Relations** tab, select everything and delete it.

![Remove relations](https://github.com/user-attachments/assets/65e1ef68-fdc2-4117-8032-2429cbaeb574)

8. Pay attention to the fact, that removing relations may lead to some areas to disappear, which was not defined separately from another objects. You can't do anything with it; if you miss something, you'll need to add it manually.

9. You can start editing your map. You can add new objects, remove existing ones, change their properties, etc. And there will be no one to tell you that you're doing something wrong or reverse your changes.

10. Pay attention to the fact that if you simply delete the object it will result a broken OSM file. Instead of simply removing something, you need to **Purge** it. To see this option, you need to enable the **Expert mode** in the settings.

![Enable expert mode](https://github.com/user-attachments/assets/eaee73df-76bb-48db-be6b-d4ddb7c5ea7c)

11. After it, you will see the **Purge** option in the **Edit** menu. Use it to remove the object properly.

![Purge object](https://github.com/user-attachments/assets/75c90888-cf6d-437b-906f-89b029350044)

12. Save the file: **File** -> **Save as** (Ctrl + Shift + S).  
Now, you can use this file in the generator.  
Friendly reminder: save your file in some safe place, so you won't lose your changes. It's also recommended to use version control systems like Git to track your changes, so you can easily revert them if something goes wrong.

## Troubleshooting
If your custom OSM file is not working, throws errors or outputs a blank map try the following approach:
1. Open your OSM file in any text editor.
2. Search for ```action='delete'```. If there are any occurences, the file cannot be handled properly. Delete all elements that contain the action delete attribute and save the file.

Actions which could lead to this issue:
- **Deleting elements**. Workaround: Use **Purge** instead of **Delete** to completely remove them from the OSM file.
- **Combine Way** (shortcut "C") when combining two or more ways (e.g. roads) together. No workaround for now. You have to manually delete the marked elements from the OSM file.
