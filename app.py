import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory,flash 
from werkzeug.utils import secure_filename
import cv2
import numpy as np

UPLOAD_FOLDER ='static/uploads/'
DOWNLOAD_FOLDER = 'static/downloads/'
ALLOWED_EXTENSIONS = {'jpg', 'png','.jpeg'}
app = Flask(__name__, static_url_path="/static")


# APP CONFIGURATIONS
app.config['SECRET_KEY'] = 'opencv'  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
# limit upload size upto 6mb
app.config['MAX_CONTENT_LENGTH'] = 6 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        paper_type = request.form.get('scanner')
        if 'file' not in request.files:
            flash('No file attached in request')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            flash('No file selected')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            # filename = secure_filename(file.filename)
            filename = "image.png"
            file.save(os.path.join(UPLOAD_FOLDER, filename))
            area = calculate(os.path.join(UPLOAD_FOLDER, filename), filename, paper_type)
            data={
                "area": area,
                "processed_img":'static/downloads/'+filename,
                "uploaded_img":'static/uploads/'+filename
            }
            return render_template("index.html",data=data)  
    return render_template('index.html')
    

def calculate(path, filename, paper_type):
    # variable
    Paper_width_inch = 0
    Paper_height_inch = 0
    thresh = 200

    if str(paper_type) == "A6":
        Paper_width_inch = 4+1/8
        Paper_height_inch = 5+7/8
    elif str(paper_type) == "A5":
        Paper_width_inch = 5+7/8
        Paper_height_inch = 8+1/4
    elif str(paper_type) == "A4":
        Paper_width_inch = 8+1/4
        Paper_height_inch = 11+3/4
    elif str(paper_type) == "A3":
        Paper_width_inch = 11+3/4
        Paper_height_inch = 16+1/2
    elif str(paper_type) == "A2":
        Paper_width_inch = 16+1/2
        Paper_height_inch = 23+3/8
    else:
        Paper_width_inch = 23+3/8
        Paper_height_inch = 33+1/8

    # read image
    plant_colors = cv2.imread(path)

    # get dimension
    dimensions = plant_colors.shape
    width_px = dimensions[1]
    height_px = dimensions[0]

    # get DPI
    DPI_w = round(width_px / Paper_width_inch)
    DPI_h = round(height_px / Paper_height_inch)

    # find area to crop 0.2cm in area
    ymin = round(DPI_h/2.54*0.2)
    xmin = round(DPI_w/2.54*0.2)
    ymax = height_px - ymin
    xmax = width_px - xmin
    print("y:", ymin, ymax)
    print("x:", xmin, xmax)

    # crop image
    crop_plant_colors = plant_colors[ymin:ymax, xmin:xmax]

    # get glay image
    plant_grayImage = cv2.cvtColor(crop_plant_colors, cv2.COLOR_BGR2GRAY)

    # get invert black white image
    blackAndWhiteImage = cv2.threshold(
        plant_grayImage, thresh, 255, cv2.THRESH_BINARY)[1]

    # count area
    number_of_black_pix = np.sum(blackAndWhiteImage == 0)
    area = (number_of_black_pix * 2.54 * 2.54)/(DPI_w*DPI_h)

    # RESULT
    cv2.imwrite(f"{DOWNLOAD_FOLDER}{filename}",blackAndWhiteImage)
    return area

if __name__ == '__main__':
    app.run()