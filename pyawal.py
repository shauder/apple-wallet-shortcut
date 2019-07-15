import re
import mimetypes
import urllib.request
import os, sys, getopt
import shutil
import base64
from flask import (
    Flask,
    redirect,
    request,
    render_template
)
from wallet.models import Pass, Barcode, StoreCard

# Create the application instance
app = Flask(__name__, template_folder="templates", static_url_path='')

# Create a URL route in our application for "/"
@app.route('/')
def home():
    return redirect("https://www.icloud.com/shortcuts/02a14e2324eb46fea473e9bc7485bffa", code=302)

@app.route('/bark')
def bark():
    return redirect("https://www.icloud.com/shortcuts/f5448973270340ca86e9f0b2471e44f4", code=302)

@app.route('/api/apple/barcode/<barcode>', methods=['GET', 'POST'])
def gen_apple_wallet(barcode):
    content = request.get_json(silent=True)
    simplename = re.sub('[^a-zA-Z0-9]', '', content["name"]).lower()

    if os.path.exists("/app/static/passes/" + simplename + "/" + barcode):
        shutil.rmtree("/app/static/passes/" + simplename + "/" + barcode)

    if os.path.exists("/app/static/passes/" + simplename):
        os.mkdir("/app/static/passes/" + simplename + "/" + barcode)
    else:
        os.mkdir("/app/static/passes/" + simplename)
        os.mkdir("/app/static/passes/" + simplename + "/" + barcode)

    if len(barcode) > 7:
        urllib.request.urlretrieve("http://barcodes4.me/barcode/c39/" + barcode + ".png?resolution=1", "/app/static/passes/" + simplename + "/" + barcode + "/strip.png")
    else:
        urllib.request.urlretrieve("http://barcodes4.me/barcode/c39/" + barcode + ".png?resolution=2", "/app/static/passes/" + simplename + "/" + barcode + "/strip.png")

    cardInfo = StoreCard()
    cardInfo.addHeaderField('barcode', barcode, 'Account Number')

    cardInfo.addBackField('name',content["name"],'Name: ')
    cardInfo.addBackField('description',content["description"],'Description: ')
    cardInfo.addBackField('credit','https://wallet.shane.app','Created By: ')

    organizationName = content["name"]
    passTypeIdentifier = os.environ.get('PASS_TYPE_IDENT')
    teamIdentifier = os.environ.get('TEAM_IDENT')
    passfile = Pass(cardInfo, \
    passTypeIdentifier=passTypeIdentifier, \
    organizationName=organizationName, \
    teamIdentifier=teamIdentifier)

    passfile.logoText = content["name"]
    passfile.description = content["description"]
    passfile.labelColor = content["label_color"]
    passfile.backgroundColor = content["background_color"]
    passfile.foregroundColor = content["foreground_color"]
    passfile.serialNumber = os.environ.get('PASS_TYPE_IDENT') + '.' + simplename + '.' + barcode
    passfile.barcode = Barcode(message = barcode)

    imgdata_icon = open("/app/static/passes/" + simplename + "/" + barcode + "/icon.png", "wb")
    imgdata_logo = open("/app/static/passes/" + simplename + "/" + barcode + "/logo.png", "wb")
    imgdata_icon.write(base64.b64decode(str(content["icon"])))
    imgdata_logo.write(base64.b64decode(str(content["logo"])))
    imgdata_icon.close()
    imgdata_logo.close()

    passfile.addFile('icon.png', open('/app/static/passes/' + simplename + '/' + barcode + '/icon.png', 'rb'))
    passfile.addFile('logo.png', open('/app/static/passes/' + simplename + '/' + barcode + '/logo.png', 'rb'))
    passfile.addFile('strip.png', open('/app/static/passes/' + simplename + '/' + barcode + '/strip.png', 'rb'))

    if content["location"]:
        passfile.locations = [{"latitude" : float(content["latitude"]), "longitude" : float(content["longitude"]), "relevantText" : content["relevant_text"]}]

    passfile.create('/app/crts/certificate.pem', '/app/crts/key.pem', '/app/crts/wwdr.pem', os.environ.get('PASS_PASSWORD'), '/app/static/passes/' + simplename + '/' + barcode + '/pass.pkpass')
    return os.environ.get('RETURN_ADDRESS').replace('"', '') + "/passes/" + simplename  + "/" + barcode + "/pass.pkpass"
    #return app.send_static_file("passes/" + simplename  + "/" + barcode + "/pass.pkpass")

def main():
    mimetypes.add_type('application/vnd.apple.pkpass', '.pkpass')
    app.run(host='0.0.0.0', port=5002, debug=False)

# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    main()
