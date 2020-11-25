# RedCraft plugin updater

RedCraft plugin updater is Python tool to download all your plugins and server engine updates from the following sources:

- SpigotMC.org (Supports premium resources if you log in)
- Jenkins CI build servers
- GitHub releases
- Direct download

## Setup the project

First, you'll need [CloudProxy](https://github.com/NoahCardoza/CloudProxy) installed and running.

If you're running Linux, macOS, BSD or WSL, it should be as easy as running `./setup.sh`. Make sure you have Python 3 and virtualenv installed (`pip3 install virtualenv`).

Otherwise, create and activate a virtualenv (optional, usually by running `python3 -m venv env` and `source env/bin/activate`), and install requirements using `pip install -r requirements.txt`.

## Config

To set your credentials and preferences, copy `.env.example` to `.env` and edit the values as you want.
Also, all the plugins we want to keep updated need to be in a `.json` file. You can use the `test_plugins.json` file as a template.

## How it works

You just have to run `python redcraft_plugin_updated.py <template_file.json>`, for example `python redcraft_plugin_updated.py test_plugins.json`

## Limitations

Currently, this project does not support 2FA on Spigot's website. I'm not sure how hard or easy it would be to add 2FA support, feel free to fork it and add this feature if you feel like it.

## Copyright warning

If you fork this project, make sure to NEVER include any plugin or resource in your repo as this could be a copyright violation.
This project should only include the files to browse sources and not their contents.
