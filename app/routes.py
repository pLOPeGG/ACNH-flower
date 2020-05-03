import json

from flask import render_template, request

from app import app
from flower import main

app.flower_db = main.get_flowerpedia_db()

@app.route("/", methods=["GET"])
@app.route("/index", methods=["GET"])
def index():
    flower_types = [
        {"name": str(f_type).strip("_").capitalize()} for f_type in main.Flower.flowertypes
    ]
    
    flower_colors = [
        {"name": str(f_color)} for f_color in main.Flower.flowercolors
    ]
    
    return render_template("form.html", title="Home", flower_types=flower_types, flower_colors=flower_colors)

@app.route("/results", methods=["POST"])
def result_page():
    form = request.form
    
    tgt_type = getattr(main.Flower, form["tgt_type"])
    tgt_color = getattr(main.Flower, form["tgt_color"])
    seed = True if "seed" in form else False
    island = True if "island" in form else False
    
    tgt = main.uget(main.flower_info, _type=tgt_type, _color=tgt_color)
    if len(tgt) == 0:
        return "This target does not exist"
    
    flowerpedia = app.flower_db[(tgt_type, seed, island)]
    best_flower = max(tgt, key=lambda x: flowerpedia[x].total_prob)
    
    path = main.ancestors(best_flower, flowerpedia)
    
    return f"{tgt_type=} {tgt_color=} {seed=} {island=} {json.dumps(path)}"






