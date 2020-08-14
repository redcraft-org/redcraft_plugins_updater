# RedCraftSpigotMCUpdater

RedCraftSpigotMCUpdater is Python 3 tool to download all watched plugins and their updates from [SpigotMC.org](https://spigotmc.org) and keep an up to date folder with latest plugins versions, very useful when ran as root.

## Setup the project

First, you'll need [CloudProxy](https://github.com/NoahCardoza/CloudProxy) installed and running.

If you're running Linux, macOS, BSD or WSL, it should be as easy as running `./setup.sh`. Make sure you have Python 3 and virtualenv installed (`pip3 install virtualenv`).

Otherwise, create and activate a virtualenv (optional, usually by running `python3 -m venv env` and `source env/bin/activate`), and install requirements using `pip install -r requirements.txt`.

## Config

To set your credentials and preferences, copy `.env.example` to `.env` and edit the values as you want.

## How it works

When you run `redcraft_spigotmc_updater.py`, it will log in on [SpigotMC.org](https://spigotmc.org) using [cloudscraper](https://github.com/VeNoMouS/cloudscraper), escalate the CloudFlare tokens with [CloudProxy](https://github.com/NoahCardoza/CloudProxy), and then check your watched plugins and download them in the output folder specified in the config.

## Limitations

Currently, this project does not support 2FA. I'm not sure how hard or easy it would be to add 2FA support, feel free to fork it and add this feature if you feel like it.

## Copyright warning

If you fork this project, make sure to NEVER include any Spigot plugin in your repo as this could be a copyright violation. This project alone should only include the files to browse SpigotMC and not its contents.
