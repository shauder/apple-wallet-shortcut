import re
import mimetypes
import os
import barcode
import base64
import requests
from urllib.parse import unquote_plus
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

GENERIC_PASS_URL = 'https://www.icloud.com/shortcuts/70e4911a049045eea3cfd32d3d9908e6'

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

@app.route('/api/v1/ip', methods=['POST', 'GET'])
def get_ext_ip():
    return requests.get('https://checkip.amazonaws.com').text.strip()

@app.route('/api/v1/<barcode_type>/<barcode_input>', methods=['POST', 'GET'])
def gen_apple_wallet(barcode_type, barcode_input):

    if request.method == 'POST':
        if request.is_json:
            content = request.get_json(silent=False)
        else:
            content = { 'name': 'Membership Card' }

    elif request.method == 'GET':
        if request.is_json:
            content = request.get_json(silent=False)
        else:
            content = request.args

    else:
        return 'Bad request.'

    pass_name = decode_input(content.get('name', 'Membership Card'))
    pass_description = decode_input(content.get('description', 'My membership card ' + barcode_type + ' pass'))
    pass_header_text = decode_input(content.get('header_text'))
    pass_header_value = decode_input(content.get('header_value'))
    pass_primary_text = decode_input(content.get('primary_text'))
    pass_primary_value = decode_input(content.get('primary_value'))
    pass_icon = decode_input(content.get('icon', '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'))
    pass_logo = decode_input(content.get('logo', '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'))
    pass_location = decode_input(content.get('location', False))
    pass_latitude = decode_input(content.get('latitude', '0'))
    pass_longitude = decode_input(content.get('longitude', '0'))
    pass_relevant_text = decode_input(content.get('relevant_text', 'A pass is available for use here'))
    pass_foreground_color = decode_input(content.get('foreground_color', 'rgb(0,0,0)'))
    pass_background_color = decode_input(content.get('background_color', 'rgb(37,170,225)'))
    pass_label_color = decode_input(content.get('label_color', 'rgb(241,92,34)'))

    pass_debug = content.get('debug', False)

    if pass_debug:
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

    if barcode_type.upper() == 'C39':
        if len(barcode_input) < 44:
            pass_barcode_buffer = BytesIO()
            AW_C39 = barcode.get_barcode_class('Code39')
            AW_C39(barcode_input, writer=ImageWriter(), add_checksum=False).render({'font_size': 0, 'dpi': 300}).save(pass_barcode_buffer, format='PNG')
            pass_barcode = base64.b64encode(pass_barcode_buffer.getvalue())
        else:
            return 'Bad Code39 code.'
    elif barcode_type.upper() == 'C128':
        if len(barcode_input) < 129:
            pass_barcode_buffer = BytesIO()
            AW_C128 = barcode.get_barcode_class('Code128')
            AW_C128(barcode_input, writer=ImageWriter()).render({'font_size': 0, 'dpi': 300}).save(pass_barcode_buffer, format='PNG')
            pass_barcode = base64.b64encode(pass_barcode_buffer.getvalue())
        else:
            return 'Bad Code128 code.'
    elif barcode_type.upper() == 'EAN13':
        barcode_input = re.sub("\D", "", barcode_input)
        if len(barcode_input) == 13:
            pass_barcode_buffer = BytesIO()
            AW_EAN13 = barcode.get_barcode_class('EAN13')
            AW_EAN13(barcode_input, writer=ImageWriter()).render({'font_size': 0, 'dpi': 300}).save(pass_barcode_buffer, format='PNG')
            pass_barcode = base64.b64encode(pass_barcode_buffer.getvalue())
        else:
            return 'Bad EAN13 code.'
    elif barcode_type.upper() == 'EAN8':
        barcode_input = re.sub("\D", "", barcode_input)
        if len(barcode_input) == 8:
            pass_barcode_buffer = BytesIO()
            AW_EAN8 = barcode.get_barcode_class('EAN8')
            AW_EAN8(barcode_input, writer=ImageWriter()).render({'font_size': 0, 'dpi': 300}).save(pass_barcode_buffer, format='PNG')
            pass_barcode = base64.b64encode(pass_barcode_buffer.getvalue())
        else:
            return 'Bad EAN8 code.'
    elif barcode_type.upper() == 'JAN':
        barcode_input = re.sub("\D", "", barcode_input)
        if ( barcode_input[0:2] == '45' or barcode_input[0:2] == '49' ) and len(barcode_input) == 13:
            pass_barcode_buffer = BytesIO()
            AW_JAN = barcode.get_barcode_class('JAN')
            AW_JAN(barcode_input, writer=ImageWriter()).render({'font_size': 0, 'dpi': 300}).save(pass_barcode_buffer, format='PNG')
            pass_barcode = base64.b64encode(pass_barcode_buffer.getvalue())
        else:
            return 'Bad JAN code.'
    elif barcode_type.upper() == 'ISBN13':
        barcode_input = re.sub("\D", "", barcode_input)
        if ( barcode_input[0:3] == '978' or barcode_input[0:3] == '979' ) and len(barcode_input) == 13:
            pass_barcode_buffer = BytesIO()
            AW_ISBN13 = barcode.get_barcode_class('ISBN13')
            AW_ISBN13(barcode_input, writer=ImageWriter()).render({'font_size': 0, 'dpi': 300}).save(pass_barcode_buffer, format='PNG')
            pass_barcode = base64.b64encode(pass_barcode_buffer.getvalue())
        else:
            return 'Bad ISBN13 code.'
    elif barcode_type.upper() == 'ISBN10':
        barcode_input = re.sub("\D", "", barcode_input)
        if len(barcode_input) == 10:
            pass_barcode_buffer = BytesIO()
            AW_ISBN10= barcode.get_barcode_class('ISBN10')
            AW_ISBN10(barcode_input, writer=ImageWriter()).render({'font_size': 0, 'dpi': 300}).save(pass_barcode_buffer, format='PNG')
            pass_barcode = base64.b64encode(pass_barcode_buffer.getvalue())
        else:
            return 'Bad ISBN10 code.'
    elif barcode_type.upper() == 'ISSN':
        barcode_input = re.sub("\D", "", barcode_input)
        if len(barcode_input) == 8:
            pass_barcode_buffer = BytesIO()
            AW_ISSN= barcode.get_barcode_class('ISSN')
            AW_ISSN(barcode_input, writer=ImageWriter()).render({'font_size': 0, 'dpi': 300}).save(pass_barcode_buffer, format='PNG')
            pass_barcode = base64.b64encode(pass_barcode_buffer.getvalue())
        else:
            return 'Bad ISSN code.'
    elif barcode_type.upper() == 'NOCODE':
        pass_barcode = None
    else:
        return 'No valid barcode type passed with the request, try again.'

    cardInfo = StoreCard()

    if not barcode_type.upper() == 'NOCODE' and not pass_header_text and not pass_header_value:
        pass_header_text = 'Account Number'
        pass_header_value = barcode_input

    if pass_header_text and pass_header_value:
        cardInfo.addHeaderField('header_field', pass_header_value, pass_header_text)

    if barcode_type.upper() == 'NOCODE' and pass_primary_value and pass_primary_text:
        cardInfo.addPrimaryField('primary_field', pass_primary_value, pass_primary_text)

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

    if not barcode_type.upper() == 'NOCODE':
        passfile.addFile('strip.png', BytesIO(base64.b64decode(pass_barcode)))

    pass_encoded = base64.b64encode(passfile.create('crts/certificate.pem', 'crts/key.pem', 'crts/wwdr.pem', pass_passcode).getvalue())

    return send_file(BytesIO(base64.b64decode(pass_encoded)), mimetype='application/vnd.apple.pkpass', as_attachment=True, attachment_filename='pass.pkpass')

def decode_input(input_text):
    if input_text:
        if '%2B' in input_text or '%3D' in input_text or '%2F' in input_text:
            return unquote_plus(input_text)
        else:
            return input_text

def main():
    mimetypes.add_type('application/vnd.apple.pkpass', '.pkpass')
    app.run(host='0.0.0.0', port=app_port, debug=False)

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    main()
