import generate

# TODO: Make it possible to change the map size.
DISTANCE = 1024
DEFAULT_COORDS1 = (58.5209, 31.2775)
DEFAULT_COORDS2 = (36.62728038014358, 31.767259155479046)
DEFAULT_COORDS3 = (36.64024, 31.77443)
DEFAULT_COORDS4 = (58.480506039472864, 30.81793196704757)

# parser = ap.ArgumentParser(
#     description="Generate a map for Farming Simulator 22 using OpenStreetMap."
# )
# parser.add_argument("lat", type=float, help="Latitude of the center of the map (e.g. 58.5209)")
# parser.add_argument("lon", type=float, help="Longitude of the center of the map (e.g. 31.2775)")

# args = parser.parse_args()

# gm = generate.Map((args.lat, args.lon), DISTANCE)
gm = generate.Map(DEFAULT_COORDS4, DISTANCE)
