import re
import mimetypes
import json
import urllib.request
import os, sys, getopt
import shutil
import base64
import barcode
from barcode import Code39
from barcode.writer import ImageWriter
from flask import (
    Flask,
    redirect,
    request,
    render_template,
    send_file
)
from wallet.models import Pass, Barcode, StoreCard

GENERIC_PASS_URL = 'https://www.icloud.com/shortcuts/3b57bb037e114d85b6ef2b16a89c03a4'
BARK_PASS_URL = 'https://www.icloud.com/shortcuts/6fabf0a510044e799da7620757c6c3d6'

pass_type_id = os.environ.get('PASS_TYPE_IDENT')
team_id = os.environ.get('TEAM_IDENT')
pass_passcode = os.environ.get('PASS_PASSWORD')
prd_address = os.environ.get('PRD_ADDRESS')
dev_address = os.environ.get('DEV_ADDRESS')

if os.environ.get('PRODUCTION'):
    develop = False
    address = prd_address
    app_port = '5002'
    return_url = address
else:
    develop = True
    address = dev_address
    app_port = '5002'
    return_url = address + ':' + app_port

# Create the application instance
app = Flask(__name__, template_folder='templates', static_url_path='')

# Create a URL route in our application for '/'
@app.route('/')
def home():
    return redirect(GENERIC_PASS_URL, code=302)

@app.route('/bark')
def bark():
    return redirect(BARK_PASS_URL, code=302)

@app.route('/api/apple/barcode/<barcode_input>', methods=['POST', 'GET'])
def legacy_gen_apple_wallet(barcode_input):
    return gen_apple_wallet(barcode_input)

@app.route('/api/v1/c39/<barcode_input>', methods=['POST', 'GET'])
def gen_apple_wallet(barcode_input):
    if request.is_json:
        content = request.get_json(silent=False)
    else:
        content = { 'name': 'Membership Card' }

    pass_name = content.get('name', 'Membership Card')
    pass_description = content.get('description', 'My membership card C39 pass')
    pass_icon = content.get('icon', 'iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAYAAADhAJiYAAAAsElEQVRYhe3TQQ6CMBBAUTgEp9AjmBiPwy10p8dyRcJF7A7XbL4bYoyh0xLoFHR+0hWEecmUorC2HFACF8CRPjfMKiXQVQHy3U0CPTOAOgn0btbuI4qaZSADGchAawJpZqCfBZ0Tn2kg70sLtVlQn2FlvQRq0a+VQDvgoYhxwD602wqoifg7IvN9pwaq8G0LNFUze6CB/gHUAIfhNDlBd+A08vz4CdMAjUJ8sOQgK3cvu8yLjMfMIIsAAAAASUVORK5CYII=')
    pass_logo = content.get('logo', 'iVBORw0KGgoAAAANSUhEUgAAACQAAAAkCAQAAABLCVATAAAAhklEQVR4Ae2RsQmEQBBFn0VYxV0JB8eVYxeanWUZLdiIm2lsMoogOIjIjibqvpc/Zvjcn4QCjwTqKUhQ/BGjJYrOHGpRyGQoMnl+KIZiyOIjQ3mY15i/N7/Wo6gRozWKF40p43mDJiXTZ2+YL8xI2UU2XBNDjs+oOxaq+DHzxZlCKrKMPY8BIe3BAqhXRQ8AAAAASUVORK5CYII=')
    pass_location = content.get('location', False)
    pass_latitude = content.get('latitude', '0')
    pass_longitude = content.get('longitude', '0')
    pass_relevant_text = content.get('relevant_text', 'A pass is available for use here')
    pass_foreground_color = content.get('foreground_color', 'rgb(0,0,0)')
    pass_background_color = content.get('background_color', 'rgb(37,170,225)')
    pass_label_color = content.get('label_color', 'rgb(241,92,34)')

    # print(pass_name)
    # print(pass_description)
    # print(pass_icon)
    # print(pass_logo)
    # print(pass_location)
    # print(pass_latitude)
    # print(pass_longitude)
    # print(pass_relevant_text)
    # print(pass_foreground_color)
    # print(pass_background_color)
    # print(pass_label_color)

    simplename = re.sub('[^a-zA-Z0-9]', '', pass_name).lower()

    if os.path.exists('static/passes/' + simplename + '/' + barcode_input):
        shutil.rmtree('static/passes/' + simplename + '/' + barcode_input)

    if os.path.exists('static/passes/' + simplename):
        os.mkdir('static/passes/' + simplename + '/' + barcode_input)
    else:
        os.mkdir('static/passes/' + simplename)
        os.mkdir('static/passes/' + simplename + '/' + barcode_input)

    imgdata_icon = open('static/passes/' + simplename + '/' + barcode_input + '/icon.png', 'wb')
    imgdata_icon.write(base64.b64decode(str(pass_icon)))
    imgdata_icon.close()

    imgdata_logo = open('static/passes/' + simplename + '/' + barcode_input + '/logo.png', 'wb')
    imgdata_logo.write(base64.b64decode(str(pass_logo)))
    imgdata_logo.close()

    AW_C39 = barcode.get_barcode_class('Code39')
    c39 = AW_C39(barcode_input, writer=ImageWriter(), add_checksum=False)
    fullname = c39.save('static/passes/' + simplename + '/' + barcode_input + '/strip', {'font_size': 0, 'dpi': 300})

    cardInfo = StoreCard()
    cardInfo.addHeaderField('barcode', barcode_input, 'Account Number')

    cardInfo.addBackField('name', pass_name, 'Name: ')
    cardInfo.addBackField('description', pass_description, 'Description: ')
    cardInfo.addBackField('credit', address, 'Created By: ')

    passfile = Pass(cardInfo, \
    passTypeIdentifier=pass_type_id, \
    organizationName=pass_name, \
    teamIdentifier=team_id)

    passfile.logoText = pass_name
    passfile.description = pass_description
    passfile.serialNumber = pass_type_id + '.' + simplename + '.' + barcode_input
    passfile.barcode = ''
    passfile.foregroundColor = pass_foreground_color
    passfile.backgroundColor = pass_background_color
    passfile.labelColor = pass_label_color

    if pass_location:
        passfile.locations = [{'latitude' : float(pass_latitude), 'longitude' : float(pass_longitude), 'relevantText' : pass_relevant_text}]

    passfile.addFile('icon.png', open('static/passes/' + simplename + '/' + barcode_input + '/icon.png', 'rb'))
    passfile.addFile('logo.png', open('static/passes/' + simplename + '/' + barcode_input + '/logo.png', 'rb'))
    passfile.addFile('strip.png', open('static/passes/' + simplename + '/' + barcode_input + '/strip.png', 'rb'))

    passfile.create('crts/certificate.pem', 'crts/key.pem', 'crts/wwdr.pem', pass_passcode, 'static/passes/' + simplename + '/' + barcode_input + '/pass.pkpass')

    return return_url.replace('"', '') + '/api/v1/' + simplename  + '/' + barcode_input

@app.route('/api/v1/<get_simplename>/<get_barcode>', methods=['POST', 'GET'])
def get_apple_wallet(get_simplename, get_barcode):
    return send_file('static/passes/' + get_simplename + '/' + get_barcode + '/pass.pkpass', mimetype='application/vnd.apple.pkpass')

def main():
    mimetypes.add_type('application/vnd.apple.pkpass', '.pkpass')
    app.run(host='0.0.0.0', port=app_port, debug=False)

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    main()
