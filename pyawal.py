import re
import mimetypes
import os
import barcode
import base64
from io import BytesIO
from PIL import Image
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

    app_debug = content.get('debug', False)

    if app_debug:
        print(pass_name)
        print(pass_description)
        print(pass_icon)
        print(pass_logo)
        print(pass_location)
        print(pass_latitude)
        print(pass_longitude)
        print(pass_relevant_text)
        print(pass_foreground_color)
        print(pass_background_color)
        print(pass_label_color)

    simplename = re.sub('[^a-zA-Z0-9]', '', pass_name).lower()

    pass_buffer = BytesIO()
    AW_C39 = barcode.get_barcode_class('Code39')
    AW_C39(barcode_input, writer=ImageWriter(), add_checksum=False).render({'font_size': 0, 'dpi': 300}).save(pass_buffer, format='PNG')
    pass_barcode = base64.b64encode(pass_buffer.getvalue())

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

    passfile.addFile('icon.png', BytesIO(base64.b64decode(str(pass_icon))))
    passfile.addFile('logo.png', BytesIO(base64.b64decode(str(pass_logo))))
    passfile.addFile('strip.png', BytesIO(base64.b64decode(pass_barcode)))
    
    passfile.create('crts/certificate.pem', 'crts/key.pem', 'crts/wwdr.pem', pass_passcode, 'passes/' + simplename + '_' + barcode_input + '.pkpass')

    return return_url.replace('"', '') + '/api/v1/' + simplename  + '/' + barcode_input

@app.route('/api/v1/<get_simplename>/<get_barcode>', methods=['POST', 'GET'])
def get_apple_wallet(get_simplename, get_barcode):
    return send_file('passes/' + get_simplename + '_' + get_barcode + '.pkpass', mimetype='application/vnd.apple.pkpass')

def main():
    mimetypes.add_type('application/vnd.apple.pkpass', '.pkpass')
    app.run(host='0.0.0.0', port=app_port, debug=False)

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    main()
