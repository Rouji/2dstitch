# 2D Stitch
Stitches multiple 2D images into one large one. And does so somewhat quickly. Mainly because of the following constraints:  
- Consecutive input images have to overlap
- This does *only* translation. *No* scaling or rotation or anything else. 

My usecase for this is stitching together screenshots. Like scrolling a webpage that doesn't fit on screen at once.  
Also works fine with screen recordings! (as long as you convert all the frames to images)

# Example
```bash
wf-recorder -g "$(slurp)" -r 5 -F format=rgb24 -x rgb24 -p preset=slow -p tune=animation -c libx264rgb -f example.mp4

mkdir img
ffmpeg -i example.mp4 img/%06d.png

find img/ -type f | sort | xargs python3 -m 2dstitch example.png
```
