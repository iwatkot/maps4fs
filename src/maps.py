import osmnx as ox
import shapely.coords

ox.projection.project_gdf


lat, lon = (36.62727651766688, 31.76728757384754)
dist = 40
north, south, east, west = ox.utils_geo.bbox_from_point((lat, lon), dist=dist)

buildings = ox.features_from_bbox(north, south, east, west, tags={"building": True})
buildings_utm = ox.project_gdf(buildings, to_latlong=False)

for index, building in buildings_utm.iterrows():
    geometry: shapely.geometry = building["geometry"]
    # print(geometry.exterior.coords.xy)
    xs, ys = geometry.exterior.coords.xy
    xs = xs.tolist()
    ys = ys.tolist()
    print(xs)
    print(ys)
