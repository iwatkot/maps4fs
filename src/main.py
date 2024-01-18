import shutil

import cv2

import src.globals as g
import src.weights as weights

asphalt_weights = list(filter(lambda f: "asphalt" in f, g.weights_files))
g.console.log(f"Found {len(asphalt_weights)} asphalt weight files.")

top_left = (200, 200)
bottom_right = (1800, 1800)

for w in asphalt_weights:
    img = cv2.imread(w, cv2.IMREAD_UNCHANGED)
    g.console.log(f"Shape of {w}: {img.shape}. Type: {img.dtype}")
    img[top_left[0] : bottom_right[0], top_left[1] : bottom_right[1]] = 255
    cv2.imwrite(w, img)

shutil.make_archive(g.MOD_SAVE_PATH, "zip", g.OUTPUT_DIR)
g.console.log(f"Archive created: {g.MOD_SAVE_PATH}.")

shutil.copyfile(g.MOD_SAVE_PATH + ".zip", g.game_mod_path)
g.console.log(f"Mod file copied to game directory: {g.game_mod_path}")
