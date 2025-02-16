## Frequently Asked Questions about Docker

📹 Learn how to install Docker and launch the tool locally in the video tutorial.  

[![YouTube tutorial](https://github.com/user-attachments/assets/c86ee51f-d787-4ffe-9da9-6c8d938b05ac)](https://youtu.be/1AHGIxTxSBM)


In this section, you will find anwers to the most frequently asked questions about usage of the Docker version of the app. Most of those questions are not related to the app, but to the Docker itself. Please, before asking a question, or opening an issue, check if the answer is already here. Thank you!


### I can't install/launch Docker, it says something about Virtualization, what should I do?

Refer to the Docker documentation, specifically [System requirements](https://docs.docker.com/desktop/setup/install/windows-install/#system-requirements). It's very well explained there.
Complete step by step tutorial can be found [here](https://docs.docker.com/desktop/troubleshoot-and-support/troubleshoot/topics/#virtualization).

### I can't launch Docker, it says something about WSL, what should I do?

By default, Docker Desktop for Windows uses the WSL 2 backend. And it's probably is not installed on your system. So, there two ways to fix it: install the WSL 2 backend, or switch to the Hyper-V backend.

#### Install WSL 2 backend

Check out the [official documentation](https://docs.docker.com/desktop/setup/install/windows-install/#system-requirements) of Docker, it contains all the needed links and instructions. Here's also a [tutorial](https://learn.microsoft.com/en-us/windows/wsl/install) from Microsoft.

#### Switch to Hyper-V backend

You can also switch to the Hyper-V backend, which is easier to set up. Note, that Hyper-V should be enabled on your system (check the previous question).

➡️ Note, that Hyper-V is not available on Home editions of Windows, in that case you should use the WSL 2 backend.

To do it, go to the Docker Desktop, open the **Settings**, then **General**, and switch to the Hyper-V backend. Then restart the Docker Desktop.

![Disable WSL](https://github.com/user-attachments/assets/9a4032c0-b265-49c7-8cbb-b0884e030713)

### It looks like I can not upgrade the software, why?

When working with Docker you should remember that you're working with containers. And when you running a new container, if you already downloaded the image before, it will be used from the cache. So, in that case you'll always get the old version of the software. To get the new version, you should remove the old container and image, and then run the new one.
To do it, go to the Docker Desktop, open the **Containers** tab, select all containers, click **Stop**, then **Remove**. Then go to the **Images** tab and do the same. After that, you can run the new container.

### It looks like the app crashes in Docker, why?

Probably, it's because of the Docker Exit Code 137, which meants OOM (Out of Memory). You can increase the memory limit for the Docker Desktop in the settings if you're using Hyper-V backend. If you're using WSL backend, you can increase the memory limit in the [WSL Settings](https://learn.microsoft.com/en-us/answers/questions/1296124/how-to-increase-memory-and-cpu-limits-for-wsl2-win).

To do it, go to the Docker Desktop, open the **Settings**, then **Resources**, and increase the memory limit. Then restart the Docker Desktop.  
Note, that depending on the settings of generation (the map size, resize factors and so on), the app may work with images of enormous sizes, which require a lot of memory. For example, when you downloading the satellite images for a 4 km map, the resulting image is 20K x 20K pixels, which is 400 megapixels. And it requires a lot of memory to process it. And also, when generating mesh for backgrpound terrain, the app uses a lot of memory too. If your machine can't handle it, con sider lowering the generation settings.

![Increase memory limit](https://github.com/user-attachments/assets/c0101e93-0377-4515-aece-210522aa0aa5)

### I keep getting Unauthorized error when trying to execute docker run command, what should I do?

The maps4fs Docker image is public and doesn't require any authentication. If you're getting the Unauthorized error, it's probably because of the broken Docker credentials. To fix it, simply log out from your Docker account in the Docker Desktop app (the button on the right top corner), then try to run the command again.

### I have an error in the Docker (local) version of the app, how to know what's wrong?

If you are using local (Docker) version of the app, open terminal and execute:

```bash
docker logs maps4fs
```

And see the output. It will contain the error message, which will help you to understand what's wrong. If you can't understand the error message, ask for help in our Discord server.