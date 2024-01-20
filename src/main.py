import argparse as ap

import generate

# TODO: Make it possible to change the map size.
DISTANCE = 1024
# 58.5209, 31.2775

parser = ap.ArgumentParser(
    description="Generate a map for Farming Simulator 22 using OpenStreetMap."
)
parser.add_argument("lat", type=float, help="Latitude of the center of the map (e.g. 58.5209)")
parser.add_argument("lon", type=float, help="Longitude of the center of the map (e.g. 31.2775)")

args = parser.parse_args()

gm = generate.Map((args.lat, args.lon), DISTANCE)
