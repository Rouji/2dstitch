from sys import argv
import cv2
import numpy as np
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import cpu_count
from dataclasses import dataclass


orb = cv2.ORB_create()
bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)

@dataclass(frozen=True)
class Vec2D:
    x: int
    y: int
    def __add__(self, o):
        return Vec2D(self.x + o.x, self.y + o.y)
    def __sub__(self, o):
        return Vec2D(self.x - o.x, self.y - o.y)
    def __neg__(self):
        return Vec2D(-self.x, -self.y)

@dataclass
class ImageInfo:
    path: str
    pos: Vec2D
    size: Vec2D

def find_offset(prev_img, next_img) -> Vec2D:
    prev_key, prev_desc = orb.detectAndCompute(prev_img, None)
    next_key, next_desc = orb.detectAndCompute(next_img, None)

    matches = sorted(
        bf.match(prev_desc, next_desc),
        key=lambda x: x.distance
    )

    prev_matched_key = np.float32([prev_key[match.queryIdx].pt for match in matches]).reshape(-1, 1, 2)
    next_matched_key = np.float32([next_key[match.trainIdx].pt for match in matches]).reshape(-1, 1, 2)

    transform = cv2.estimateAffinePartial2D(next_matched_key, prev_matched_key, cv2.RANSAC)

    return Vec2D(int(round(transform[0][0][2])), int(round(transform[0][1][2])))

output_path = argv[1]
input_image_paths = argv[2:]
input_image_info: dict[str, ImageInfo] = dict()

print('matching consecutive images')

with ThreadPoolExecutor(cpu_count()) as exe:
    def map_offsets(paths: tuple[str ,str]) -> tuple[ImageInfo, ImageInfo, Vec2D]:
        prev_path, next_path = paths
        prev_img = cv2.imread(prev_path, cv2.IMREAD_GRAYSCALE)
        next_img = cv2.imread(next_path, cv2.IMREAD_GRAYSCALE)
        prev_info = ImageInfo(prev_path, Vec2D(0,0), Vec2D(prev_img.shape[1], prev_img.shape[0]))
        next_info = ImageInfo(next_path, Vec2D(0,0), Vec2D(next_img.shape[1], next_img.shape[0]))
        input_image_info[prev_path] = prev_info
        input_image_info[next_path] = next_info
        offset = find_offset(prev_img, next_img)
        print(f'{prev_info.path} -> {next_info.path}: {offset.x}, {offset.y}')
        return prev_info, next_info, offset

    offsets = exe.map(map_offsets, zip(input_image_paths, input_image_paths[1:]))


print('sorting results')
for _, next_info, offset in offsets:
    input_image_info[next_info.path].pos = offset

img_info_sorted: list[ImageInfo] = [input_image_info[path] for path in input_image_paths]

print('calculating absolute positions')
cumulative = Vec2D(0, 0)
for img in img_info_sorted[1:]:
    cumulative += img.pos
    img.pos = cumulative

#move top-left-most to 0,0
pos_min = Vec2D(
    min(img_info_sorted, key=lambda i: i.pos.x).pos.x,
    min(img_info_sorted, key=lambda i: i.pos.y).pos.y
)

for img in img_info_sorted:
    img.pos -= pos_min

res_max_x = max(img_info_sorted, key=lambda i: i.pos.x + i.size.x)
res_max_y = max(img_info_sorted, key=lambda i: i.pos.y + i.size.y)
resolution = Vec2D(res_max_x.pos.x + res_max_x.size.x, res_max_y.pos.y + res_max_y.size.y)

print(f'creating output image at {resolution.x}x{resolution.y}px')
output_img = np.zeros((resolution.y, resolution.x, 3), dtype=np.uint8)

print('copying input images into output')
for img_info in img_info_sorted:
    img = cv2.imread(img_info.path)
    output_img[img_info.pos.y:img_info.pos.y+img_info.size.y, img_info.pos.x:img_info.pos.x+img_info.size.x] = img

print(f'writing output to file: {output_path}')
cv2.imwrite(output_path, output_img, [cv2.IMWRITE_PNG_COMPRESSION, 9])
