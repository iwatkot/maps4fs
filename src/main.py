import cv2
import numpy as np

import src.globals as g
import src.maps as m
import src.weights as weights

# MAP = m.Map((36.62727651766688, 31.76728757384754), g.MAP_SIZE[0] / 2)
MAP = m.Map((58.5209, 31.2775), g.MAP_SIZE[0] / 2)


def process_img(image_path: str):
    img = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
    g.console.log(f"Shape of {image_path}: {img.shape}. Type: {img.dtype}")
    for element in MAP.elements():
        # Convert two lists of X and Y to list of pairs of X and Y
        pairs = list(zip(element[0], element[1]))
        polygon = np.array(pairs, dtype=np.int32).reshape((-1, 1, 2))
        cv2.fillPoly(img, [polygon], color=255)
    cv2.imwrite(image_path, img)


path = weights.Textures.asphalt.get_random_path()
process_img(path)

# shutil.make_archive(g.MOD_SAVE_PATH, "zip", g.OUTPUT_DIR)
# g.console.log(f"Archive created: {g.MOD_SAVE_PATH}.")

# shutil.copyfile(g.MOD_SAVE_PATH + ".zip", g.game_mod_path)
# g.console.log(f"Mod file copied to game directory: {g.game_mod_path}")
