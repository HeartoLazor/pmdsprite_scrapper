# Pokemon Mystery Dungeon SpriteCollab Scraper
A _very rough and non optimized_ Python web scraper built with Selenium that extracts Pokémon sprite variation data from the PMD Sprite Collab website (https://sprites.pmdcollab.org/). The tool automatically populates a CSV file with information about variation paths, pokemon variation name, and generate the minimal variant flags intended to be used with https://www.nexusmods.com/stardewvalley/mods/39038?tab=description.

This scrapper generates a pokemon_selenium.csv, that expects to have the information of the number and the pokemon in the first two columns.
The data columns filled by the scrapper are:
  **variations_paths:** Directory paths to sprite variations (semicolon-separated)
  **variation_types:** Names of each variation type (semicolon-separated)
  **minimal_variants:** Binary flags indicating minimal variants (semicolon-separated 1/0 values)

# Example Output:
input pokemon_data.csv with this information in bold:
**number,name,generation**,variations_paths,variation_types,minimal_variants
**0001,Bulbasaur,1**,0001/;0001/0001/;0001/0000/0001/;0001/0001/0001/,Normal;Altcolor;Shiny;Altcolor Shiny,1;1;1;1
**0002,Ivysaur,1**,0002/;0002/0001/;0002/0000/0001/,Normal;Altcolor;Shiny,1;1;1
...

Output pokemon_selenium.csv with this information in bold updated:
number,name,generation,**variations_paths,variation_types,minimal_variants**
0001,Bulbasaur,1,**0001/;0001/0001/;0001/0000/0001/;0001/0001/0001/,Normal;Altcolor;Shiny;Altcolor Shiny,1;1;1;1**
0002,Ivysaur,1,**0002/;0002/0001/;0002/0000/0001/,Normal;Altcolor;Shiny,1;1;1**
...

# Installation
Prerequisites:

Python 3.7+
Chrome/Chromium browser

Install required python packages:

pip install selenium csv tqdm

# Usage
Full scrapping:

python pmdresource_scrapper.py

If you only need to update/generate the minimal_variants column without re-scraping:

python pmdresource_scrapper.py --minimal-only

this column is used to configure which variant is enabled for the Stardew Mod generation with the minimal variants flag. Doesn't overwrite if a configuration for that variation is already found, if not creates an entry with 1 (enabled).

# Configuration
Modify these constants in the script to customize behavior:

INPUT_POKEMON_CSV = "pokemon_data.csv"      # Input CSV file

OUT_POKEMON_CSV = "pokemon_selenium.csv"    # Output CSV file

POKEMON_RANGE_START = 1                     # First Pokémon to process

POKEMON_RANGE_END = 1025                    # Last Pokémon to process

RESTART_AFTER = 1                           # Restart browser after N Pokémon, recommended 1 to avoid scrapping errors.
