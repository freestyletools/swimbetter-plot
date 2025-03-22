import io
import os
import sys
import json
from multiprocessing import Pool


import plotly.express as px
import plotly.graph_objects as go

import pandas as pd
from PIL import Image, ImageDraw, ImageFont

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <swimId>")
    exit(1)

swimId = sys.argv[1]
datadir = os.path.join("data", swimId)

imagesdir = "images"
if not os.path.exists(imagesdir):
    os.mkdir(imagesdir)
imagesdir = os.path.join(imagesdir, swimId)
if not os.path.exists(imagesdir):
    os.mkdir(imagesdir)


swimmer_name = ""
record_start_time = -2000
record_start_time = 0
color_primary = (0, 53, 47, 100)
color_good = (85, 170, 85)
color_bad = (83, 0, 6, 200)
font_color = (255, 255, 255, 200)
image_width = 1920
image_height = 1080
font_size = 30
font_size_small = 18
border_padding = 10
border_width = 1

graph_width = 500
graph_height = 300
graph_window_ms = 2000
graph_range_y = [-1, 5]
graph_dot_size = 10
graph_line_width = 2
graph_padding_x = 100

arm_graph_width = 200
arm_graph_height = 200
arm_graph_color = "rgb(255, 255, 255)"

arm_graph_side_x = 20
arm_graph_side_y = 20
arm_graph_overhead_x = 20
arm_graph_overhead_y = 270
arm_graph_head_x = 20
arm_graph_head_y = 520

arm_phase_width = 200
arm_phase_height = 300

arm_phase_side_x = 5
arm_phase_side_y = image_height - arm_phase_height


direction_size = 100
direction_scale = -8


colorscale = [f"rgb{color_bad}", f"rgb{color_good}"]
ranges = [
    [-10, -0.1], 
    [-0.1, 10], 
]

def bin_colors(value):
    for color, r in enumerate(ranges):
        if r[0] <= value < r[1]:
            return color


data = json.load(open(os.path.join(datadir, "data-lapforcetime.json")))
df = pd.DataFrame({
    "left_forward": data["left"]["forward"],
    "left_lateral": data["left"]["lateral"],
    "left_vertical": data["left"]["vertical"],
    "right_forward": data["right"]["forward"],
    "right_lateral": data["right"]["lateral"],
    "right_vertical": data["right"]["vertical"],
    "time": data["time"]
})

strokes = {
    "left": {},
    "right": {}
}

stroke_times = {
}

ranges_axis = {
    "depth_x": (1, -1),
    "depth_y": (1, -1),
    "sweep_x": (1, -1),
    "sweep_y": (1, -1)
}

def load_path_strokes(data, plot, arm, stroke=1):
    global strokes
    global stroke_times
    result = []
    for d in data:
        if not stroke in strokes[arm]:
            strokes[arm][stroke] = {}

        strokes[arm][stroke]["time"] = d["time"]
        strokes[arm][stroke][f"{plot}_x"] = d["xAxis"]
        strokes[arm][stroke][f"{plot}_y"] = d[plot]
        ranges_axis[f"{plot}_x"] = (min(ranges_axis[f"{plot}_x"][0], min(d["xAxis"])), max(ranges_axis[f"{plot}_x"][0], max(d["xAxis"])))
        ranges_axis[f"{plot}_y"] = (min(ranges_axis[f"{plot}_y"][0], min(d[plot])), max(ranges_axis[f"{plot}_y"][0], max(d[plot])))
        for time in d["time"]:
            if not time in stroke_times:
                stroke_times[time] = {}
            stroke_times[time][arm] = stroke
        stroke = stroke + 1
    return result
    

def load_path(filename, plot, stroke):
    data = json.load(open(filename))
    load_path_strokes(data["strokesLeft"], plot, "left", stroke=stroke)
    load_path_strokes(data["strokesRight"], plot, "right", stroke=stroke)


def load_stroke_phase(data, arm, stroke):
    global strokes
    global stroke_times
    result = []
    for d in data:
        if not stroke in strokes[arm]:
            strokes[arm][stroke] = {}

        strokes[arm][stroke]["glide"] = d["glide"]
        strokes[arm][stroke]["pull"] = d["pull"]
        strokes[arm][stroke]["recovery"] = d["recovery"]
        strokes[arm][stroke]["strokeRate"] = d["strokeRate"]
        stroke = stroke + 1
    return result
 
def load_phase(filename, stroke):
    data = json.load(open(filename))
    load_stroke_phase(data["strokesLeft"], "left", stroke=stroke)
    load_stroke_phase(data["strokesRight"], "right", stroke=stroke)


for lap in range(1, 3):
    stroke = len(strokes["left"].keys())+1
    load_path(os.path.join(datadir, f"data-pathdepth-{lap}.json"), "depth", stroke=stroke)
    load_path(os.path.join(datadir, f"data-pathsweep-{lap}.json"), "sweep", stroke=stroke)
    load_phase(os.path.join(datadir, f"data-strokephase-{lap}.json"), stroke=stroke)


last_time = max(df["time"]) + graph_window_ms/2
#last_time = 5000
now = record_start_time
#now = 19000
#now = 7000

def draw_font_box(draw, font, text, x, y, anchor="mm", fill=True):
    left, top, right, bottom = font.getbbox(text, anchor="mm")
    left = left + x - border_padding
    right = right + x + border_padding
    top = top + y - border_padding
    bottom = bottom + y + border_padding
    if fill:
        draw.rounded_rectangle([(left, top), (right, bottom)], radius=10, fill=color_primary, width=border_width)
    draw.text((x, y), text, font_color, font=font, anchor=anchor)


def draw_direction_box(draw, x, y, lateral, vertical):
    box_x = x - direction_size / 2
    box_y = y - direction_size / 2

    draw.rounded_rectangle([(box_x, box_y), (box_x + direction_size, box_y + direction_size)], radius=10, fill=color_primary, width=border_width)
    draw.text((x, y - direction_size / 2 - font_size_small/2), "Up", font_color, font=font_small, anchor="mb")
    draw.text((x, y + direction_size / 2 + font_size_small/2), "Down", font_color, font=font_small, anchor="mt")
    draw.text((x - direction_size /2 - font_size_small/2, y), "Out", font_color, font=font_small, anchor="rm")
    draw.text((x + direction_size /2 + font_size_small/2, y), "In", font_color, font=font_small, anchor="lm")
    draw.line([(x, y), (x+ (lateral/direction_scale) * direction_size, y+ (vertical/direction_scale) * direction_size)], fill=font_color, width=1)

def create_arm_phase(now, arm, align):
    now = round(now / 10) * 10
    result = Image.new('RGBA', (arm_phase_width, arm_phase_height), color_primary)
    draw = ImageDraw.Draw(result)
    if align=="left":
        x = 0
        anchor = "lt"
    elif align=="right":
        x = arm_phase_width
        anchor = "rt"
    stroke = stroke_times.get(now, {}).get(arm)
    if not stroke:
        return result

    glide = strokes[arm][stroke]["glide"] / 1000
    pull = strokes[arm][stroke]["pull"] / 1000
    recovery = strokes[arm][stroke]["recovery"] / 1000
    rate = strokes[arm][stroke]["strokeRate"]

    time_in_stroke = (now - strokes[arm][stroke]["time"][0]) / 1000
    glide_color = font_color
    pull_color = font_color
    recovery_color = font_color
    if time_in_stroke < glide:
        glide_color = (255,0,0)
    elif time_in_stroke < glide + pull:
        pull_color = (255,0,0)
    elif time_in_stroke < glide + pull + recovery:
        recovery_color = (255,0,0)

    draw.text((x, 0), "Glide (s)", glide_color, font=font_small, anchor=anchor)
    draw.text((x, 75), "Pull (s)", pull_color, font=font_small, anchor=anchor)
    draw.text((x, 150), "Recovery (s)", recovery_color, font=font_small, anchor=anchor)
    draw.text((x, 225), "Rate (str/min)", font_color, font=font_small, anchor=anchor)


    draw.text((x, 1.5*font_size_small), f"{glide:.02f}", font_color, font=font, anchor=anchor)
    draw.text((x, 75 + 1.5*font_size_small), f"{pull:0.2f}", font_color, font=font, anchor=anchor)
    draw.text((x, 150 + 1.5*font_size_small), f"{recovery:0.2f}", font_color, font=font, anchor=anchor)
    draw.text((x, 225 + 1.5*font_size_small), f"{rate:0.1f}", font_color, font=font, anchor=anchor)
    return result


def create_arm_graph(now, arm, plot):
    now = round(now / 10) * 10
    result = Image.new('RGBA', (arm_graph_width, arm_graph_height + font_size_small*2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(result)
    draw.text((arm_graph_width / 2, font_size_small), plot, font_color, font=font_small, anchor="mb")
    fig = go.Figure()
    stroke = stroke_times.get(now, {}).get(arm)
    if not stroke:
        return result

    if plot == "Side On":
        x = strokes[arm][stroke]["depth_x"]
        y = strokes[arm][stroke]["depth_y"]
        range_x = ranges_axis["depth_x"]
        range_y = ranges_axis["depth_y"]
        force_x = -(df[f"{arm}_forward"][now / 10] / 8)
        force_y = (df[f"{arm}_vertical"][now / 10] / 8)
    if plot == "Overhead":
        x = strokes[arm][stroke]["sweep_y"]
        y = strokes[arm][stroke]["sweep_x"]
        range_x = ranges_axis["sweep_y"]
        range_y = ranges_axis["sweep_x"]
        force_x = (df[f"{arm}_lateral"][now / 10] / 8)
        if arm == "left":
            force_x = -force_x
        force_y = -(df[f"{arm}_forward"][now / 10] / 8)
    if plot == "Head On":
        x = strokes[arm][stroke]["sweep_y"]
        y = strokes[arm][stroke]["depth_y"]
        range_x = ranges_axis["sweep_y"]
        range_y = ranges_axis["depth_y"]
        force_x = (df[f"{arm}_lateral"][now / 10] / 8)
        if arm == "left":
            force_x = -force_x
        force_y = (df[f"{arm}_vertical"][now / 10] / 8)
        
    r = [min(range_x[0], range_y[0]), max(range_x[1], range_y[1])]
    fig.add_trace(go.Scatter(x=x, y=y, line=dict(width=graph_line_width), marker=dict(color="white")))
    if now in strokes[arm][stroke]["time"]:
        index = strokes[arm][stroke]["time"].index(now)
        fig.add_trace(go.Scatter(
            x=[x[index]],
            y=[y[index]],
            mode="markers",
            marker=dict(
                color=["rgba(255,0,0,1)"],
                size=graph_dot_size,
            )
        ))
        fig.add_trace(go.Scatter(x=[x[index], x[index] + force_x], y=[y[index], y[index] + force_y], line=dict(width=graph_line_width*2), marker=dict(color="red")))
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)',
    })
    fig.update_layout(showlegend=False)
    fig.update_xaxes(visible=False, range=[-1, 1])
    fig.update_yaxes(visible=False, range=[-1, 1])
    fig.update_layout(width=arm_graph_width, height=arm_graph_height, margin=dict(l=0, r=0, t=0, b=0))
    graph = fig.to_image(format="png")
    img = Image.open(io.BytesIO(graph))
    draw = ImageDraw.Draw(img)
    draw.line([(arm_graph_width/2, 0), (arm_graph_width/2, arm_graph_height)], fill=font_color, width=1)
    draw.line([(0, arm_graph_height/2), (arm_graph_width, arm_graph_height/2)], fill=font_color, width=1)
    result.paste(img, (0, font_size_small*2))
    return result
 
def create_graph(x, y, now, last_time):
    fig = go.Figure()
    color_cluster = list(map(bin_colors, y))
    fig.add_trace(go.Scatter(x=x, y=y, mode='markers', marker=dict(color=color_cluster, colorscale=colorscale), line=dict(width=graph_line_width)))
    if now >= 0 and now < (last_time - graph_window_ms/2):
        fig.add_trace(go.Scatter(
            x=[x[int(now / 10)]],
            y=[y[int(now / 10)]],
            mode="markers",
            marker=dict(
                color=["rgba(255,0,0,1)"],
                size=graph_dot_size,
            )
        ))
    fig.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)', #f'rgba{color_primary}',
    })
    fig.update_layout(showlegend=False)
    fig.update_xaxes(visible=False, range=[now - graph_window_ms/2, now + graph_window_ms/2])
    fig.update_yaxes(visible=False)
    fig.update_layout(width=graph_width, height=graph_height, margin=dict(l=0, r=0, t=0, b=0))
    graph = fig.to_image(format="png")
    img = Image.open(io.BytesIO(graph))
    mask = Image.new('RGBA', (graph_width, graph_height), (255, 255, 255, 0))
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([(0, 0), (graph_width, graph_height)], radius=10, fill=(255, 255, 255, 255), width=border_width)
    return (img, mask)
    


font = ImageFont.truetype("Open_Sans/static/OpenSans-Regular.ttf", font_size) 
font_small = ImageFont.truetype("Open_Sans/static/OpenSans-Regular.ttf", font_size_small) 
frame = 0

def draw_frame(now, frame):
    img = Image.new('RGBA', (image_width, image_height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    draw_font_box(draw, font, swimmer_name, image_width / 2, font_size * 2)
    
    graph_left = create_arm_graph(now, "left", "Side On")
    img.paste(graph_left, (arm_graph_side_x, arm_graph_side_y))
    graph_left = create_arm_graph(now, "left", "Overhead")
    img.paste(graph_left, (arm_graph_overhead_x, arm_graph_overhead_y))
    graph_left = create_arm_graph(now, "left", "Head On")
    img.paste(graph_left, (arm_graph_head_x, arm_graph_head_y))

    graph_right = create_arm_graph(now, "right", "Side On")
    img.paste(graph_right, (image_width - arm_graph_width - arm_graph_side_x, arm_graph_side_y))
    graph_right = create_arm_graph(now, "right", "Overhead")
    img.paste(graph_right, (image_width - arm_graph_width - arm_graph_overhead_x, arm_graph_overhead_y))
    graph_right = create_arm_graph(now, "right", "Head On")
    img.paste(graph_right, (image_width - arm_graph_width - arm_graph_head_x, arm_graph_head_y))


    draw.rounded_rectangle([(0, image_height - graph_height - font_size_small), (graph_padding_x + graph_width, image_height)], radius=10, fill=color_primary, width=border_width)
    phase_left = create_arm_phase(now, "left", align="left")
    img.paste(phase_left, (arm_phase_side_x, image_height - arm_phase_height))
    graph_left, mask = create_graph(df.time, df.left_forward, now, last_time)
    img.paste(graph_left, (graph_padding_x, image_height - graph_height), mask=graph_left) 
    draw_font_box(draw, font, "Left Hand", (graph_padding_x + graph_width)/2, image_height - graph_height + font_size, anchor="mb", fill=False)
    draw_font_box(draw, font_small, "Propulsion (force going backward)", graph_padding_x + (graph_width / 2), image_height - font_size, fill=False)

    draw.rounded_rectangle([(image_width - graph_width - graph_padding_x, image_height - graph_height - font_size_small), (image_width, image_height)], radius=10, fill=color_primary, width=border_width)
    phase_right = create_arm_phase(now, "right", align="right")
    img.paste(phase_right, (image_width - arm_phase_width - arm_phase_side_x, image_height - arm_phase_height))
    graph_right, mask = create_graph(df.time, df.right_forward, now, last_time)
    img.paste(graph_right, (image_width - graph_width - graph_padding_x, image_height - graph_height), mask=graph_right) 
    draw_font_box(draw, font, "Right Hand", image_width - (graph_padding_x + graph_width) / 2, image_height - graph_height + font_size, fill=False, anchor="mb")
    draw_font_box(draw, font_small, "Propulsion (force going backward)", image_width - graph_width - graph_padding_x + (graph_width / 2), image_height - font_size, fill=False)


    img.save(os.path.join(imagesdir, f'fig{frame:08}.png'), 'PNG')

    if frame % 10 == 0:
        print(now)
    
if True:
    work = []
    while now < last_time:
        work.append([now, frame])
        frame = frame + 1
     
        now = record_start_time + (1000 * frame) / 60
else:
    frame = 2600
    now = record_start_time + (1000 * frame) / 60
    work = [[now, frame]]

if __name__ == "__main__":
    with Pool() as p:
        p.starmap(draw_frame, work)
