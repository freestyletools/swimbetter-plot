Warning, this is a work in progress! More information can be found [here](https://freestyletools.github.io/)

1. Copy `settings.py-dist` to `settings.py` and enter your [EO SwimBETTER smart paddles](https://www.eolab.com/swimbetter) credentials

2. Create the python venv:

```
python3 -m venv .venv
.venv/bin/pip3 install -r requirements.txt
```

3. Export the data from swimbeter:

```
.venv/bin/python3 export-data.py
```

The data is stored in data/*swimId*

4. Create the overlay images:

```
.venv/bin/python3 plot.py data/<swimId>
```

The images are stored in images/*swimId*

5. Create the overlay video:

```
cd images/<swimId>
ffmpeg -framerate 60 -pattern_type glob -i '*.png' -c:v prores -pix_fmt yuva444p10le overlay.mov
```

6. Use images/*swimId*/overlay.mov in any video edit software and put the overlay on top of the camera. You'll need to manually align the camera video with the overlay.






