import generate

distance = 8192
# 2048, 4096, 8192, 16384
DEFAULT_COORDS1 = (58.5209, 31.2775)
DEFAULT_COORDS2 = (36.62728038014358, 31.767259155479046)
DEFAULT_COORDS3 = (36.64024, 31.77443)
DEFAULT_COORDS4 = (58.480506039472864, 30.81793196704757)

# parser = ap.ArgumentParser(
#     description="Generate a map for Farming Simulator 22 using OpenStreetMap."
# )
# parser.add_argument("lat", type=float, help="Latitude of the center of the map (e.g. 58.5209)")
# parser.add_argument("lon", type=float, help="Longitude of the center of the map (e.g. 31.2775)")
# parser.add_argument(
#     "size", type=int,
#     help="Size of the map in meters. Must be a multiple of 2048 (e.g. 2048, 4096, 8192)"
# )
# args = parser.parse_args()
# lat = args.lat
# lon = args.lon
# size = args.size

# if not size % 2048 == 0:
#     raise ValueError("Size must be a multiple of 2048 (e.g. 2048, 4096, 8192)")
# distance = size / 2

# gm = generate.Map((args.lat, args.lon), distance)
gm = generate.Map(DEFAULT_COORDS1, distance)
