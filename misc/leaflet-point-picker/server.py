#!/usr/bin/env python
# coding: utf-8
import argparse
import glob
import json
import os
from flask import Flask, render_template, jsonify, send_file
app = Flask(__name__)

parser = argparse.ArgumentParser(
    description='Point Cloud Point Picker Server')
parser.add_argument('products', type=str,
                    help='directory name for rasterized asset of products')

args = parser.parse_args()

def product_list():
    prod_paths = glob.glob(os.path.join(args.products, '**'))
    products = []
    for prod_path in prod_paths:
        lasfiles = glob.glob(os.path.join(prod_path, '*.[lL][aA][sS].json'))
        print(lasfiles)
        if len(lasfiles) == 0:
            # skip if empty for las files
            continue
        prod_id = os.path.basename(prod_path)
        products.append({
            'id': prod_id,
            'path': prod_path,
        })
    return products

def product_info(id):
    try:
        with open(os.path.join(args.products, str(id), 'info.json')) as f:
            prod_info = json.load(f)
    except:
        prod_info = {
            'name': str(id),
            'client_name': None,
        }
    return prod_info

def product_area(id):
    with open(os.path.join(args.products, str(id), 'area.json')) as f:
        prod_area = json.load(f)
    return prod_area

def product_pcdimg(id, img_path):
    return os.path.join(args.products, str(id), img_path)

@app.route('/')
@app.route('/product')
def products():
    # generate product list
    prod_list = product_list()
    products = []
    for prod in prod_list:
        prod_info = product_info(prod['id'])
        products.append({
            'href': '/product/{}/pointpicker'.format(prod['id']),
            'caption': '{}({})'.format(prod_info['name'], prod_info['client_name'])
        })

    var = {}
    var['products'] = products
    return render_template('products.html', var=var)


@app.route('/product/<prod_id>/pointpicker')
def pointpicker(prod_id):
    var = {
        'id': prod_id
    }
    return render_template('pointpicker.html', var=var)

@app.route('/product/<prod_id>/info')
def info(prod_id):
    prod_info = product_info(prod_id)
    return jsonify(prod_info)

@app.route('/product/<prod_id>/area')
def area(prod_id):
    prod_area = product_area(prod_id)
    return jsonify(prod_area)

@app.route('/product/<prod_id>/pcdimg/<img_path>')
def pcdimg(prod_id, img_path):
    filepath = product_pcdimg(prod_id, img_path)
    return send_file(filepath, mimetype='image/png')


if __name__ == '__main__':
    app.config.update({'DEBUG': True })
    app.config.update({'JSON_AS_ASCII': False})
    app.run(host='0.0.0.0')
