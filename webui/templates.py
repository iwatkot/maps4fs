class Messages:
    TITLE = "maps4FS"
    MAIN_PAGE_DESCRIPTION = (
        "Generate map templates for Farming Simulator from real places.  \n"
        "💬 Join our [Discord server](https://discord.gg/Sj5QKKyE42) to get help, share your "
        "maps, or just chat.  \n"
        "🤗 If you like the project, consider supporting it on [Buy Me a Coffee](https://www.buymeacoffee.com/iwatkot0)."
    )
    MAIN_PAGE_COMMUNITY_WARNING = (
        "🚜 Hey, farmer!  \n"
        "Do you know what **Docker** is? If yes, please consider running the application "
        "locally.  \n"
        "On StreamLit community hosting the sizes of generated maps are limited "
        "to a size of maximum 4096x4096 meters, while locally you only limited by "
        "your hardware.  \n"
        "Learn more about the Docker version in the repo's "
        "[README](https://github.com/iwatkot/maps4fs?tab=readme-ov-file#option-2-docker-version).  \n"
        "Also, if you are familiar with Python, you can use the "
        "[maps4fs](https://pypi.org/project/maps4fs/) package to generate maps locally."
    )
    TERRAIN_RELOAD = (
        "ℹ️ When opening the map first time in the Giants Editor, select the **terrain** object, "
        "open the **Terrain** tab in the **Attributes** window, scroll down to the end "
        "and press the **Reload material** button.  \n"
        "Otherwise you may (and will) face some glitches."
    )
    HEIGHT_SCALE_INFO = (
        "ℹ️ Remember to adjust the ***heightScale*** parameter in the Giants Editor to a value "
        "that suits your map. Learn more about it in repo's "
        "[README](https://github.com/iwatkot/maps4fs?tab=readme-ov-file#For-advanced-users)."
    )
    AUTO_PRESET_INFO = (
        "Auto preset will automatically apply different algorithms to make terrain more "
        "realistic. It's recommended for most cases. If you want to have more control over the "
        "terrain generation, you can disable this option and change the advanced settings."
    )
    AUTO_PRESET_DISABLED = (
        "Auto preset is disabled. In this case you probably receive a full black DEM "
        "image file. But it is NOT EMPTY. Dem image value range is from 0 to 65535, "
        "while on Earth the highest point is 8848 meters. So, unless you are not "
        "working with map for Everest, you probably can't see anything on the DEM image "
        "by eye, because it is too dark. You can use the "
        "multiplier option from Advanced settings to make the terrain more pronounced."
    )
    DEM_MULTIPLIER_INFO = (
        "This multiplier can be used to make the terrain more pronounced. "
        "By default the DEM file will be exact copy of the real terrain. "
        "If you want to make it more steep, you can increase this value. "
        "Or make it smaller to make the terrain more flat."
    )
    DEM_BLUR_RADIUS_INFO = (
        "This value is used to blur the elevation map. Without blurring the terrain "
        "may look too sharp and unrealistic. By default the blur radius is set to 21 "
        "which corresponds to a 21x21 pixel kernel. You can increase this value to make "
        "the terrain more smooth. Or make it smaller to make the terrain more sharp."
    )
    DEM_PLATEAU_INFO = (
        "This value is used to make the whole map higher or lower. "
        "This value will be added to each pixel of the DEM image, making it higher."
        "It can be useful if you're working on a plain area and need to add some "
        "negative height (to make rivers, for example)."
    )
    TOOLBOX_INFO = (
        "This section contains different tools that can be helpful for modders, grouped by "
        "the component of the map they are related to.  \n"
    )
    KNOWLEDGE_INFO = (
        "Here you can find some useful information about the different aspects of map modding."
    )
    FAQ_INFO = "Here you can find answers to the most frequently asked questions."
