# How to use Maps4FS effectively

The main goal of Maps4FS is to minimize the time spent on creating the map in the sections that can be fully or partially automated. So you can focus on the most important part of the map - the content, while not worrying about the technical details of the map creation. Therefore, we need to split the map creation into two parts: the part that can be considered as assets and the part that does not have any actual value (non-asset).  
By non-asset, we mean the part that does not require any time to create - the part that is created automatically by the Maps4FS. And by asset, we mean the part that will be done manually and will require time to create.  
So, the main advice is simple: do not do anything manually until you are completely satisfied with the results of the automatic generation of the map. Let's talk about the details of this process.

## Preparation

### OSM Data
First of all, you need to understand that the data comes from the OpenStreetMap (OSM), so if in your region of interest the OSM data is not sufficient or not precise enough, you will need to improve it. While you can work with a public version of the OSM data right in the browser, I strongly recommend using the [custom OSM](008_customosm.md) approach. In this case, you can edit the data in any way you want, and it will always be available for you without dealing with the guidelines and restrictions of the OSM.

### Generation info
You will probably generate your map a lot of times before you are satisfied with the results. So, to ensure that you will always generate the map for the same place, size, and rotation, remember to save the `generation_info.json` file, which contains all the required parameters to reproduce the same results (excluding the changes you made). Learn more about the generation info in the [Generation Info](https://github.com/iwatkot/maps4fs?tab=readme-ov-file#generation-info) section of the README.  
If you generate the map with the same parameters, all the other assets you made will be compatible with those changes in most cases, so you will be able to replace only one specific part if needed.

## Non-asset part
So, if you edited your OSM data and it looks more or less like you want it, you can start the automatic generation of the map.  
I would recommend the following pipeline:
1. Generate the map and open it in the Giants Editor.
2. Check if non-asset parts look fine, like roads, fields, farmlands, etc.
3. Do not edit anything manually until you are completely satisfied with the results of the automatic generation.
4. If something seems off, just save the `generation_info.json` and move everything else to the trash bin. It costs you nothing; you did not spend any time on it, so you can just start over. Now, you can repeat steps 1-3 until you are satisfied with the results.
5. Once you are satisfied with the non-asset parts, you can start working on the asset parts manually.

## Asset part
To value the time you spend on creating the map, do not start working manually on anything until you've checked everything in the non-asset part.  
Once you are satisfied with the non-asset parts, you can start working on the asset parts manually. First of all, check the background terrain and water meshes, the satellite images for them, and all other things that were generated automatically. If something is wrong with them, go back to the non-asset part and repeat steps 1-3.  
And if it's all fine, now you can actually spend your time on creating the map.
