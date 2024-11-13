[h1]MAPS4FS[/h1]
[h2]Generate Farming Simulator 25 map from real world data[/h2]

You can find the latest release, documentation and examples on the [url=https://github.com/iwatkot/maps4fs]GitHub repository[/url].

[h3]Disclaimer[/h3]

[i]
The main goal of this project is to generate map templates, based on real-world data, for the Farming Simulator. It's important to mention that [b]templates are not maps[/b]. As a template you'll receive an empty map, where the terrain is shaped according to real-world data and textures are showing different types of terrain and objects (e.g. roads, fields, forests, buildings) with correct shapes and scales. So it's like a blueprint for a map. You don't need to bother with terrain shaping and object placement, you can start creating your map right away. If you thought that you could just run this tool and get a playable map, then I'm sorry to disappoint you. But if you are a map maker, then this tool will save you a lot of time.
[/i]


[h3]Overview[/h3]

So, if you're new to map making, here's a quick overview of the process:
[olist]
[*] Generate a map template using this tool.
[*] Download the Giants Editor from the official [url=https://gdn.giants-software.com/downloads.php]Giants Developer Network[/url].
[*] Open the map template in the Giants Editor.
[*] Now you can start creating your map (adding roads, fields, buildings, etc.).
[/olist]

[h2]How-To-Run[/h2]

You'll find detailed instructions on how to run the project below. But if you prefer video tutorials, here's one for you.
https://www.youtube.com/watch?v=ujwWKHVKsw8

[b]🗺️ Supported map sizes:** 2x2, 4x4, 8x8, 16x16 km.[/b]

[h3]Option 1: Use the web application[/h3]
In this case you don't need to install anything, just open the link and in a coiple of clicks your map template will be ready.

[olist]
[*] Open the [url=https://maps4fs.streamlit.app]MAPS4FS StreamLit[/url] web application.
[*] Fill in the required fields and click on the [b]Generate[/b] button.
[*] When the map is generated click on the [b]Download[/b] button to get the map.
[/olist]

[h3]Option 2: Use the Docker container[/h3]
This approach is for advanced users who want fastet generation and don't mind to copy-paste one commands in the terminal.

[olist]
[*] Install [url=https://docs.docker.com/get-docker/]Docker[/url] for your OS.
[*] Run the following command in your terminal: [code]docker run -d -p 8501:8501 iwatkot/maps4fs[/code]
[*] Open your browser and go to [url]http://localhost:8501[/url].
[*] Fill in the required fields and click on the [b]Generate[/b] button.
[*] When the map is generated click on the [b]Download[/b] button to get the map.
[/olist]

[h2]Settings[/h2]
There are some additional settings (you can ignore them and use the default values):
[b]Maximum Height[/b] - the maximum height of the terrain in meters. Select smaller values for plain-like maps and bigger values for mountainous maps. You may need to experiment with this value to get the desired result.
[b]Blur Seed[/b] - the seed for the blur algorithm. The default value is 5, which means 5 meters. The bigger the value, the smoother the map will be. The smaller the value, the more detailed the map will be. Keep in mind that for some regions, where terrain is bumpy, disabling the blur algorithm may lead to a very rough map. So, I recommend leaving this value as it is.

[h2]Bugs and Feature Requests[/h2]
If you find a bug or have a feature request, please create an issue in the [url=https://github.com/iwatkot/maps4fs/issues]GitHub repository[/url] or contact me directly in Telegram: [url=https://t.me/iwatkot]@iwatkot[/url].

[i]Happy map making![/i]

[i]If you need some additonal information or if you're developer and want to use this tool as a Python package, please visit the [url=https://github.com/iwatkot/maps4fs]repository page[/url]. You'll find more details on how this tool works and have an opportunity to collaborate in project development even without programming skills just by suggesting new features or reporting bugs.[/i]