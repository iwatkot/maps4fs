import os

from maps4fs.generator.osm import preprocess

farmland_tags = {"landuse": ["farmland", "meadow"]}
exclude_cut_tags = {"power": ["line", "minor_line"]}
input_path = "unfixed_osm.osm"
output_path = "fixed_osm.osm"

if not os.path.isfile(input_path):
    raise FileNotFoundError(f"Input file {input_path} not found.")

preprocess(input_path, output_path, farmland_tags, exclude_cut_tags=exclude_cut_tags)
print(f"Preprocessing completed. Output saved to {output_path}.")
