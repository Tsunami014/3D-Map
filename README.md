# ASE Assessment 1
## Overview
This project aims to provide users with an overview of a city, specifically for finding where in a city they would like to live. The program will accomplish this through displaying desirable factors of a city of the users choosing; including elevation, roads, greenery, water features and points of interest, in addition to the price of an apartment and the amount of money the government has. These desirable factors will help users decide how suited to the city they will be, in addition to how much they want to live there. This could be a new feature for a real estate website or software.
## Features
 - Displays a 3D map of the chosen location, with information such as greenery, roads, POIs, water features, etc.
    - You can move around in the 3D environment with the keyboard
 - Displays government money and housing prices
## APIs used
 - [Openstreetmap](nominatim.openstreetmap.org) for the recognition of place names
 - [Nextzen](nextzen.org) for the map and heightmap data
 - [WorldBank](worldbank.org) for the total money data
 - [DataWrapper](https://www.datawrapper.de/) for the apartment price data
## How to install
Ensure you have a version of python3 and it has pip, then run `pip install requirements.txt`.
## How to run
Type in the terminal `python3 main.py` in this directory or double click on the file in the file explorer.

**THERE ARE 2 FILES**:
 - `main.py` is the one with 3D which is recommended
 - `mainold.py` is the one in 2D which is still cool if you want to have a look, but this file *is not* the main project file.
### Controls
CONTROLS:
 - Arrow keys; move
 - , or . keys; zoom in/out
 - ESC; quit
 - `*`If you get lost, press 'r' to go back to the map
 - `*`If you need help, press 'h'

DISPLAY:
 - Green; land
 - Blue; water
 - Brown; land use
 - Yellow lines; roads
 - Red dots; Points Of Interest
 - Black line; country outline

`*`main.py only

