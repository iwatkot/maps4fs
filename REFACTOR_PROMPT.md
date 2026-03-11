maps4fs started as a small script and during development became a really big one with a lot of legacy crap, extra files saving and so on
cmponents were designed as separate one but soon it become obvious that is not possible in many scenarios
so im saving some info_layer data in jsons, read them with next components and so on

which is not cool, hard to debug and all of that

and i came to conclusion that the only way is to completely rewrite it

also i have scripts for qgis feature that deprecated like 1 year ago and still in codebase

im saving a lot of duplicate files for dem and so on, then read them in various places and so on
texture component is my nightmare because i designed it to work exlusively with geometry and now need other tags and blah blah blah

editing of i3d (xmls) using ET is a nightmare
all those find findall with checks for None everywhere is a freaking mess, so im thinking about the wrapper

so, what we need to do now

1. make an MD file with clear steps

2. first we update our tests, lowering number of cases, but making them MUCH MORE different, so we can try to test our refactoring easily in automated way
and the test themselves should check MUCH MORE because basically they are check if generation did not crash, and some basic checks, while it's a lot of other things.

3. then we check settings, like DEMSettings and all this stuff, making sure that it will be 100% compatible with refactor. we also check schemas (texture, trees, grle, buildings), and TRYING to make it compatible, if we need to change something - it's not a problem. let's change it.

4. we don't care about signatures, like constructor and all of that, so we can change everything we want, to make it look simple and straightforward. we dont care about backward compatibility in the meaning of method names, it's signartures and so on. because mostly the core feature is map.generate(), all other things are not uimportant. and buildings of settings of course.

5. we save all this steps with clear insructions in MD file like REFACTOR_PLAN.md

6. then we analyze all the code base, and thinking about the most simple way in the meaning of code to organize this mess. the goal is to move helper functions, classes away from main source and make sure that main code uses simple, clean functions to achieve the goal, the shorter the final code the better.

7. we consider moving texture handler to a separate module that probably will become separate library, that essentially designed to draw OSM data.

8. we consider if this makes sense to make the library async or not. only if it makes sense, we considering it and adding it into suggestions, if not - we skip this part.
9. we check what the ACTUAL files being used, e.g. as far as i remember i generate sveral types of water, but i only using line surface and water resources (they also should be named correctly: polygon-based-water and polyline-based-water). if we see that the actual files (appliciable mostly for meshes) are not being injected into the map itself, we consider removing it from the codebase, because it just adds extra complexity and confusion.
10. we shoud be careful, since some files like overview.dds are not like added to the map, but the map itself still uses it.

11. we deprecating the FS22 game and the generator starting from version 3.0 will only support FS25. HOWEVER!!! We must built everything that way, that when the new game (e.g. FS28) will be released, we can easily add support for it without changing the codebase drastically. So we need to make sure that the code is flexible enough to accommodate future changes in the game versions without requiring a complete overhaul. It mostly applied to working with list of files, their names, and especially structure in the i3d (xml) files. Some parts such as schemas already built to achive that, but the code right now in many places targets directly to specific places in i3d (xml) files without a way to customize it. So in our final suggestion we completely remove FS22 from the game, but we remember about future games.

12. we do not change the code during this step, we save all our consideration in md where listed all the classes, suggested structure and how the things will work in a separate md file REFACTOR_SUGGESTIONS.md.

13. We stop at this step, and we'll discuss the suggestions and after it we'll move to the next steps.