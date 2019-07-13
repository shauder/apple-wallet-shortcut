import re
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
    return redirect("https://www.icloud.com/shortcuts/1de2bda171f3470f9fb94a6cb68dabdd", code=302)

@app.route('/bark')
def bark():
    return redirect("https://www.icloud.com/shortcuts/f5448973270340ca86e9f0b2471e44f4", code=302)

@app.route('/api/apple/barcode/<barcode>', methods=['GET', 'POST'])
def gen_apple_wallet(barcode):
    content = request.get_json(silent=True)
    urllib.request.urlretrieve("http://barcodes4.me/barcode/c39/" + barcode + ".png", "strip.png")
    simplename = re.sub('[^a-zA-Z0-9]', '', content["name"]).lower()

    cardInfo = StoreCard()
    cardInfo.addHeaderField('barcode', barcode, 'Account Number')

    cardInfo.addBackField('name',content["name"],'Name: ')
    cardInfo.addBackField('description',content["description"],'Description: ')
    cardInfo.addBackField('credit','https://wallet.shane.app','Created By: ')

    organizationName = content["name"]
    passTypeIdentifier = pass_type_ident
    teamIdentifier = team_ident
    passfile = Pass(cardInfo, \
    passTypeIdentifier=passTypeIdentifier, \
    organizationName=organizationName, \
    teamIdentifier=teamIdentifier)

    passfile.logoText = content["name"]
    passfile.description = content["description"]
    passfile.labelColor = content["label_color"]
    passfile.backgroundColor = content["background_color"]
    passfile.foregroundColor = content["foreground_color"]
    passfile.serialNumber = pass_type_ident + '.' + simplename + '.' + barcode
    passfile.barcode = Barcode(message = barcode)

    imgdata_icon = open("icon.png", "wb")
    imgdata_logo = open("logo.png", "wb")
    imgdata_icon.write(base64.b64decode(str(content["icon"])))
    imgdata_logo.write(base64.b64decode(str(content["logo"])))
    imgdata_icon.close()
    imgdata_logo.close()

    passfile.addFile('icon.png', open('icon.png', 'rb'))
    passfile.addFile('logo.png', open('logo.png', 'rb'))
    passfile.addFile('strip.png', open('strip.png', 'rb'))

    if content["location"]:
        passfile.locations = [{"latitude" : float(content["latitude"]), "longitude" : float(content["longitude"]), "relevantText" : content["relevant_text"]}]

    if os.path.exists("/data/passes/" + simplename + "/" + barcode):
        shutil.rmtree("/data/passes/" + simplename + "/" + barcode)

    if os.path.exists("/data/passes/" + simplename):
        os.mkdir("/data/passes/" + simplename + "/" + barcode)
    else:
        os.mkdir("/data/passes/" + simplename)
        os.mkdir("/data/passes/" + simplename + "/" + barcode)

    passfile.create('/data/crts/certificate.pem', '/data/crts/key.pem', '/data/crts/wwdr.pem', pass_password, '/data/passes/' + simplename + '/' + barcode + '/pass.pkpass')
    return return_address + simplename  + "/" + barcode + "/pass.pkpass"


def main(argv):
    global pass_type_ident
    global team_ident
    global pass_password
    global return_address
    try:
        opts, args = getopt.getopt(argv,"hi:o:p:r:",["pass=","team=","ident=","return="])
    except getopt.GetoptError:
        print ('pyawal.py -p <pass_type_ident> -t <team_ident> -p <pass_password>')
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            print ('pyawal.py -i <pass_type_ident> -t <team_ident> -p <pass_password>')
            sys.exit()
        elif opt in ("-i", "--ident"):
            pass_type_ident = arg
        elif opt in ("-t", "--team"):
            team_ident = arg
        elif opt in ("-p", "--pass"):
            pass_password = arg
        elif opt in ("-r", "--return"):
            return_address = arg
    app.run(host='0.0.0.0', port=5001, debug=True)
    
# If we're running in stand alone mode, run the application
if __name__ == '__main__':
    main(sys.argv[1:])
