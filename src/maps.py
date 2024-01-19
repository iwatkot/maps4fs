import osmnx as ox

import src.globals as g


class Map(metaclass=g.Singleton):
    def __init__(self, coordinates: tuple[float, float], distance: int):
        # lat, lon = coordinates
        g.console.log(f"Fetching map data for coordinates: {coordinates}...")
        self.coordinates = coordinates
        self.distance = distance
        self.bbox = ox.utils_geo.bbox_from_point(self.coordinates, dist=self.distance)
        self._get_parameters()

    def _get_parameters(self):
        north, south, east, west = ox.utils_geo.bbox_from_point(
            self.coordinates, dist=self.distance, project_utm=True
        )
        self.minimum_x = west
        self.minimum_y = south
        g.console.log(f"Map minimum coordinates (XxY): {self.minimum_x} x {self.minimum_y}.")
        g.console.log(f"Map maximum coordinates (XxY): {east} x {north}.")

        self.easting = self.minimum_x < 500000
        self.northing = self.minimum_y < 10000000
        g.console.log(f"Map is in {'east' if self.easting else 'west'} of central meridian.")
        g.console.log(f"Map is in {'north' if self.northing else 'south'} hemisphere.")

        self.height = abs(north - south)
        self.width = abs(east - west)
        g.console.log(f"Map dimensions (HxW): {self.height} x {self.width}.")

        self.height_coef = self.height / (self.distance * 2)
        self.width_coef = self.width / (self.distance * 2)
        g.console.log(f"Map coefficients (HxW): {self.height_coef} x {self.width_coef}.")

    def get_relative_x(self, x: float) -> int:
        if self.easting:
            raw_x = x - self.minimum_x
        else:
            raw_x = self.minimum_x - x
        return int(raw_x * self.height_coef)

    def get_relative_y(self, y: float) -> int:
        if self.northing:
            raw_y = y - self.minimum_y
        else:
            raw_y = self.minimum_y - y
        return self.height - int(raw_y * self.width_coef)

    def elements(self, object_type: str = "building"):
        objects = ox.features_from_bbox(*self.bbox, tags={object_type: True})
        objects_utm = ox.project_gdf(objects, to_latlong=False)
        g.console.log(f"Fetched {len(objects_utm)} {object_type}s.")
        for index, obj in objects_utm.iterrows():
            try:
                xs, ys = obj["geometry"].exterior.coords.xy
                xs = [int(self.get_relative_x(x)) for x in xs.tolist()]
                ys = [int(self.get_relative_y(y)) for y in ys.tolist()]
                yield xs, ys
            except AttributeError:
                pass
