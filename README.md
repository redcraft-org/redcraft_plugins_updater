# RedCraftSpigotMCUpdater

RedCraftSpigotMCUpdater is Python 3 tool to download all watched plugins and their updates from SpigotMC.org and keep an up to date folder with latest plugins versions, very useful when ran as root.

## Setup the project

If you're running a UNIX based system, it should be as easy as running `./setup.sh`. Make sure you have Python 3 and virtualenv installed (`pip3 install virtualenv`).

Otherwise, create and activate a virtualenv (optional, usually by running `python3 -m venv env` and `source env/bin/activate`), and install requirements using `pip install -r requirements.txt`.

## Config

To set your credentials and preferences, copy `.env.example` to `.env` and edit the values as you want.

## Limitations

Currently, this project does not support 2FA. I'm not sure how hard or easy it would be to add 2FA support, feel free to fork it and add this feature if you feel like it.

## Copyright warning

If you fork this project, make sure to NEVER include any Spigot plugin in your repo as this could be a copyright violation. This project alone should only include the files to browse SpigotMC and not its contents.
