from flask import Flask, request, send_file, redirect, render_template
from pymongo import MongoClient
from uuid import uuid4
from qrcode import make as create_qr
from io import BytesIO
from PIL.Image import open, Image
from PIL import ImageDraw, ImageFont
from os import environ as env

app = Flask(__name__)
mongo = MongoClient(env.get("MONGO_URI"))
db = mongo["lagerplass"]
items_table = db["items"]
boxes_table = db["boxes"]

secure = bool(env.get("SECURE"))

def better_redirect(url):
    if secure:
        return redirect("https://%s%s" % (request.headers["host"], url))


@app.route('/boxes', methods=["POST"])
def create_box():
    box_id = str(uuid4())
    boxes_table.insert_one({
        "_id": box_id,
        "location": request.args["location"],
        "items": []
    })

    return better_redirect("/boxes/%s" % box_id)


@app.route("/items", methods=["POST"])
def create_item():
    item_id = str(uuid4())
    items_table.insert_one({
        "_id": item_id,
        "category": request.args["category"],
        "name": request.args["name"]
    })
    return item_id


@app.route("/items/<string:item_id>", methods=["DELETE"])
def delete_item(item_id):
    items_table.delete_one({"_id": item_id})
    return "Ok."


@app.route("/boxes/<string:box_id>/items/<string:item_id>", methods=["DELETE"])
def remove_item_from_box(box_id, item_id):
    boxes_table.update_one({"_id": box_id}, {"$pull": {"items": item_id}})
    return "Ok."


@app.route("/boxes/<string:box_id>/qr")
def render_qr(box_id):
    qr_img = BytesIO()
    qr = create_qr("http%s://%s/boxes/%s" % (("", "s")[secure], request.headers["host"], box_id))
    qr.save(qr_img, format="png")

    qr_img.seek(0)

    image: Image = open(qr_img)
    width, height = image.size
    draw = ImageDraw.Draw(image)
    text_seat = box_id[:4]
    font = ImageFont.truetype('font.ttf', 40)
    draw.text((40, height - 45), text_seat, font=font)

    out = BytesIO()
    image.save(out, format="png")

    out.seek(0)

    return send_file(out, "image/png")


@app.route("/boxes/<string:box_id>")
def get_box_items(box_id):
    box = boxes_table.find_one({"_id": box_id})
    location = box["location"]
    items = []
    for item_id in box["items"]:
        item = items_table.find_one({"_id": item_id})
        if item:
            items.append(item)
    all_items_sorted = {}
    all_items = items_table.find()

    for item in all_items:
        if item["_id"] in box["items"]:
            continue
        if not all_items_sorted.get(item["category"]):
            all_items_sorted[item["category"]] = []
        all_items_sorted[item["category"]].append(item)

    return render_template("boxinfo.jinja2", box_id=box_id, location=location, items=items, all_items=all_items_sorted)


@app.route("/boxes/<string:box_id>/items/<string:item_id>", methods=["POST"])
def add_to_box(box_id, item_id):
    boxes_table.update_one({"_id": box_id}, {"$push": {"items": item_id}})
    return "Ok."


@app.route("/items")
def create_item_gui():
    items = items_table.find()
    return render_template("createitem.jinja2", items=items)


@app.route("/")
def render_homepage():
    all_items = items_table.find()
    categories = []
    for item in all_items:
        if item["category"] in categories:
            continue
        categories.append(item["category"])
    return render_template("homepage.jinja2", categories=categories)


@app.route("/categories/<string:category_name>")
def render_category(category_name):
    items = items_table.find({"category": category_name})
    return render_template("category.jinja2", items=items, category=category_name)


@app.route("/items/<string:item_id>")
def render_item(item_id):
    boxes = boxes_table.find({"items": item_id})
    return render_template("items.jinja2", boxes=boxes)


@app.route("/boxes/<string:box_id>", methods=["DELETE"])
def delete_box(box_id):
    boxes_table.delete_one({"_id": box_id})
    return "Ok."


@app.route("/boxes")
def render_boxes_gui():
    boxes = boxes_table.find()
    return render_template("createboxes.jinja2", boxes=boxes)


if __name__ == '__main__':
    app.run()
