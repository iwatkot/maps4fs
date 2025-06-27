# Contributing to Maps4FS Ecosystem

<p align="center">
    <a href="#Maps4FS-Ecosystem-Overview">Maps4FS Ecosystem Overview</a> •
    <a href="#Reporting-Issues">Reporting Issues</a> •
    <a href="#How-to-Contribute">How to Contribute</a><br>
    <a href="#Code-style">Code style</a> •
    <a href="#Submitting-a-Pull-Request">Submitting a Pull Request</a> •
    <a href="#Code-of-Conduct">Code of Conduct</a>
</p>

## Maps4FS Ecosystem Overview

Thank you for your interest in contributing to the Maps4FS!  
It's important to note that the Maps4FS project consists of multiple repositories, each with its own specific focus.  
Here's a brief overview of the repositories and their purposes:
- [Maps4FS](https://github.com/iwatkot/maps4fs): The main repository that contains the core functionality and Python package for Maps4FS.
- [Maps4FSUI](https://github.com/iwatkot/maps4fsui): The repository for the Maps4FS Web UI, currently based on a [Streamlit](https://streamlit.io/) app. If you adding some new features to the main repository, you **must** test it with the UI as well, and, if necessary, update the UI code too.
- [Maps4FSAPI](https://github.com/iwatkot/maps4fsapi): The repository for the Maps4FS API, which provides a RESTful interface to interact with the Maps4FS. When adding new features to the main repository, ensure the backward compatibility with the API. If necessary, update the API code to reflect any changes made in the main repository.
- 🔒 [Maps4FSStats](https://github.com/iwatkot/maps4fsstats): The repository contains CI/CD API for deployment in production, collecting user statistics and all other 3rd party services integration: Nginx, MetaBase, MongoDB, Portainer.
- [Maps4FSBot](https://github.com/iwatkot/maps4fsbot): The repository contains the Discord bot for Maps4FS, which mostly used to avoid spamming in the Discord server and also provides API keys for the Public API.

## Reporting Issues
If you encounter any issues while using Maps4FS, please follow these steps to report them:
1. **Check Existing Issues**: Before creating a new issue, please check the [existing issues](https://github.com/iwatkot/maps4fs/issues) to see if your issue has already been reported.
2. **Create a New Issue**: If your issue is not listed, you can create a new issue by clicking on the "New issue" button in the [Issues tab](https://github.com/iwatkot/maps4fs/issues).
3. **Provide Detailed Information**: When creating a new issue, please provide as much detail as possible, including:
- Coordinates of the central point of the map  
- Map size  
- Map rotation  
- Map output size  
- Any additional settings if where enabled  
- Error message if any  
- Screenshots if possible  
- Any additional information that you think might be useful  

This will help me understand the issue better and provide a quicker resolution.

## How to Contribute

ℹ️ You'll need to install [Git](https://git-scm.com/) and [Python](https://www.python.org/downloads/) (version 3.11 or higher) on your machine to contribute to the Maps4FS project. You also must have a GitHub account to fork the repository and submit pull requests.  
ℹ️ It's recommended to use [Visual Studio Code](https://code.visualstudio.com/) as your code editor, since the repository already contains a `.vscode` directory with the recommended settings, and launch configurations for debugging.

1. **Fork the Repository**: Start by [forking the repository](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo) you want to contribute to. This creates a copy of the repository under your GitHub account.
2. **Clone Your Fork**: Clone your forked repository to your local machine using the command:

```bash
git clone <your_forked_repository_url>
```

3. **Create a New Branch**: Before making any changes, create a new branch for your feature or bug fix:

```bash
git checkout -b feature/your-feature-name
```

4. **Prepare a virtual environment**: It's recommended to use a virtual environment to manage dependencies. The repository already contains ready-to-use scripts in the `dev` directory. You can use the following command to create a virtual environment and install dependencies:

```bash
sh dev/create_venv.sh # For Linux/MacOS
dev\create_venv.ps1 # For Windows
```

Dependencies will be installed from the `dev/requirements.txt` file.

ℹ️ When working with the Maps4FSUI repository, you'll need to put the `data` directory from the main Maps4FS repository into the root `maps4fsui` directory. You can do this by running the following command:

5. **Make Your Changes**: Now, you can make your changes in the codebase. Ensure that your code follows the project's coding standards and conventions.

6. **Use the demo.py script**: The `demo.py` script is provided to help you test your changes. If you're using VSCode, you can simply select the `demo.py` launch configuration and run it.  

If you're using the terminal, you can run the script with the following command:

```bash
python demo.py
```

7. ⚠️ **Run MyPy**: The project relies on the static type checker [MyPy](https://mypy.readthedocs.io/en/stable/).  
   Before submitting a pull request, ensure that your code passes MyPy checks. You can run MyPy with the following command:

```bash
mypy maps4fs # Or othjer corresponding directory (maps4fsui, maps4fsapi, etc.)
```

ℹ️ The automatic checks will also be performed by the CI/CD pipeline, but it's a good practice to run them locally before submitting a pull request.

8. ⚠️ **Run Pylint**: The project uses [Pylint](https://pylint.pycqa.org/en/latest/) for code quality checks.  
   Before submitting a pull request, ensure that your code passes Pylint checks. You can run Pylint with the following command:

```bash
pylint maps4fs # Or other corresponding directory (maps4fsui, maps4fsapi, etc.)
```

ℹ️ The automatic checks will also be performed by the CI/CD pipeline, but it's a good practice to run them locally before submitting a pull request.

9. ⚠️ **Run PyTest**: The project uses [PyTest](https://docs.pytest.org/en/stable/) for automated testing. 
   Before submitting a pull request, ensure that your code passes all tests. You can run the tests with the following command:

```bash
pytest maps4fs # Or other corresponding directory (maps4fsui, maps4fsapi, etc.)
```

ℹ️ The automatic tests will also be performed by the CI/CD pipeline, but it's a good practice to run them locally before submitting a pull request.

10. **Optional: Use a symlink**: If you're working with the Maps4FSUI or Maps4fSAPI repositories and in the same time you may need to make changes in the main Maps4FS repository, you can use a symlink to avoid additional steps and make your development process smoother.  

You'll find the [`dev/create_symlink.sh`](https://github.com/iwatkot/maps4fsapi/blob/main/dev/create_symlink.sh) script in the `dev` directory of the Maps4FSAPI repository.  

This script creates a symlink to the main Maps4FS repository in the `maps4fsapi` directory, allowing you to work with both repositories simultaneously without needing to copy files back and forth.

## Code style
The Maps4FS project follows the [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide for Python code.  
Please ensure that your code adheres to these guidelines and is properly formatted. Remember to run Pylint and MyPy to check for any style violations before submitting your pull request.  
All methods, functions and classes must have type hints (including generic types) and docstrings in [Google style](https://google.github.io/styleguide/pyguide.html#38-comments-and-docstrings).  

If those requirements are not met, your pull request will not be accepted.

## Submitting a Pull Request
Once you have made your changes and tested them, you can submit a [pull request](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) to the repository.

## Code of Conduct
By participating in this project, you agree to abide by the [Code of Conduct](CODE_OF_CONDUCT.md).