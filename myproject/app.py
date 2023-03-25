import base64
import os
import pickle
import time
import warnings
import pyodbc
from flask import Flask, request, jsonify
import speech_recognition as speer
import mysql.connector
import numpy as np
import python_speech_features as mfcc
from scipy.io.wavfile import read
from sklearn import preprocessing
from sklearn.mixture import GaussianMixture
import logging

app = Flask(__name__)

logger = logging.getLogger(__name__)
# defines the the lowest-severity log message a logger will handle
logger.setLevel(logging.INFO)
# defines the format of our log messages
formatter = logging.Formatter('%(asctime)s :: %(module)s :: %(levelname)s :: %(message)s')
# define the file to which the logger will log
file_handler = logging.FileHandler('logger.log')
# setting up the format for the logger file
file_handler.setFormatter(formatter)
# adding FileHandler object to logger which would help us send logging output to disk file
logger.addHandler(file_handler)

warnings.filterwarnings("ignore")

audio_files = []
nms = []
verify_nms = []
count1812 = -1


## Demo Project
def calculate_delta(array):
    rows, cols = array.shape
    deltas = np.zeros((rows, 20))
    N = 2
    for i in range(rows):
        index = []
        j = 1
        while j <= N:
            if i - j < 0:
                first = 0
            else:
                first = i - j
            if i + j > rows - 1:
                second = rows - 1
            else:
                second = i + j
            index.append((second, first))
            j += 1
        deltas[i] = (array[index[0][0]] - array[index[0][1]] +
                     (2 * (array[index[1][0]] - array[index[1][1]]))) / 10
    return deltas


def extract_features(audio, rate):
    mfcc_feature = mfcc.mfcc(audio, rate, 0.025, 0.01,
                             20, nfft=1200, appendEnergy=True)
    mfcc_feature = preprocessing.scale(mfcc_feature)
    delta = calculate_delta(mfcc_feature)
    combined = np.hstack((mfcc_feature, delta))
    return combined


def convertToBinaryData(file):
    # Convert digital data to binary format
    with open(file, 'rb') as file:
        binaryData = file.read()

    return binaryData


def phrase_generator(Name, count1):
    try:
        language = str(request.json['language'])
        r = speer.Recognizer()
        duration = 3
        filename = "./" + Name + "-sample" + str(count1) + ".wav"
        with speer.AudioFile(filename) as source:
            # read the audio data from the default microphone
            audio_data = r.record(source, duration=duration)
            # convert speech to text
            text1 = r.recognize_google(audio_data, language=language)
            encodedText1 = base64.b64encode(bytes(text1, 'utf-8'))
            a = encodedText1.decode('ascii')
        return a;
    except:
        language = "en-US"
        r = speer.Recognizer()
        duration = 3
        filename = "./" + Name + "-sample" + str(count1) + ".wav"
        with speer.AudioFile(filename) as source:
            # read the audio data from the default microphone
            audio_data = r.record(source, duration=duration)
            # convert speech to text
            text1 = r.recognize_google(audio_data, language=language)
            encodedText1 = base64.b64encode(bytes(text1, 'utf-8'))
            a = encodedText1.decode('ascii')
        return a;


def base64_to_image(base64_str, path_to_save):
    with open(path_to_save, "wb") as fh:
        fh.write(base64.decodebytes(base64_str.encode('utf-8')))
    return path_to_save


@app.route("/adduser", methods=['POST'])
def record_audio_train():
    time.sleep(3)
    try:
        global audio_files
        nm = request.json['name']
        Name = str(nm)
        nms.append(Name)
        logger.info(f"The request from {Name} has been received for registration")

        duration = 3
        phrase = []
        scores = []

        phrase_count = 0
        phrase_detection = True
        Success = False
        voice_detection = True
        count1 = 0
        img_b64_str = request.json['voice']
        if img_b64_str == "":
            return "Please enter a valid audio file"

        audio_files.append(img_b64_str)

        if not len(audio_files) >= 3:
            # time.sleep(5)
            # print(Name)
            return "One Audio file inserted, please insert a total of three audio files"
        else:
            result1 = all(i == nms[0] for i in nms)
            if result1:
                img_path = base64_to_image(audio_files[0], './' + Name + "-sample" + str(0) + ".wav")
                img_path = base64_to_image(audio_files[1], './' + Name + "-sample" + str(1) + ".wav")
                img_path = base64_to_image(audio_files[2], './' + Name + "-sample" + str(2) + ".wav")
                nms.clear()
                audio_files.clear()
            else:
                nms.clear()
                audio_files.clear()
                time.sleep(3)

                return "please try again after few seconds"
            for count in range(3):
                OUTPUT_FILENAME = Name + "-sample" + str(count) + ".wav"
                source = "./"
                dest = "./"
                train_file = "./training_set_addition.txt"
                count = 1
                features = np.asarray(())
            for i in range(3):
                path = Name + "-sample" + str(i) + ".wav"
                sr, audio = read(source + path)
                vector = extract_features(audio, sr)
                if features.size == 0:
                    features = vector
                else:
                    features = np.vstack((features, vector))
                if count == 1:
                    gmm = GaussianMixture(
                        n_components=6, max_iter=200, covariance_type='diag', n_init=3)
                    gmm.fit(features)
                    # dumping the trained gaussian model
                    picklefile = Name + ".gmm"
                    pickle.dump(gmm, open(dest + picklefile, 'wb'))
                    features = np.asarray(())
                    count = 0
                    z = "./" + Name + ".gmm"
                    count = count + 1
                    gmmFile = convertToBinaryData(z)
                scores.append(verify_reg_model())
                if phrase_count <= 2:
                    phrase.append(phrase_generator(Name, phrase_count))
                    phrase_count = phrase_count + 1
                if (len(scores) == 3):
                    if (all(i >= -20 for i in scores)):
                        if len(phrase) == 3:
                            result = all(i == phrase[0] for i in phrase)
                            if result:
                                cnxn = pyodbc.connect('DRIVER={SQL Server};Server=localhost\SQLEXPRESS;Database=development;Trusted_Connection=True;')
                                cursor = cnxn.cursor()
                                audioFile = convertToBinaryData('./' + OUTPUT_FILENAME)

                                # phrase_generator(Name, count1)
                                try:
                                    cursor.execute(
                                        '''INSERT INTO VoiceRecords(Username,Gmm_Model,Audio,Phrases) VALUES(?, ?, ?,?)''',
                                        (Name, gmmFile, audioFile, phrase_generator(Name, count1)))
                                    # Convert data into tuple format
                                    cursor.commit()
                                    Success = True
                                    cursor.close()
                                    count1 = count1 + 1
                                except pyodbc.Error as e:
                                    logger.info("Error message:", e)
                                    if os.path.exists(Name + "-sample" + str(0) + ".wav"):
                                        os.remove(Name + "-sample" + str(0) + ".wav")
                                        os.remove(Name + "-sample" + str(1) + ".wav")
                                        os.remove(Name + "-sample" + str(2) + ".wav")
                                    if os.path.exists(Name + ".gmm"):
                                        os.remove(Name + ".gmm")
                                    return "Error message:", e
                            else:
                                phrase_detection = False
                    else:
                        voice_detection = False
        if os.path.exists(Name + "-sample" + str(0) + ".wav"):
            os.remove(Name + "-sample" + str(0) + ".wav")
            os.remove(Name + "-sample" + str(1) + ".wav")
            os.remove(Name + "-sample" + str(2) + ".wav")
        if os.path.exists(Name + ".gmm"):
            os.remove(Name + ".gmm")

        if os.path.exists("training_set_addition.txt"):
            os.remove("training_set_addition.txt")
        if Success == True:
            logger.info(Name + " has been added successfully")
            return Name + " has been added successfully"
        if (phrase_detection == False):
            logger.info("Incorrect phrase, please try again")
            return "Incorrect phrase, please try again"
        if (voice_detection == False):
            logger.info(
                "The user's voice varies or invalid phrases, Please try again with correct user's voice and phrases")
            return "The user's voice varies or invalid phrases, Please try again with correct user's voice and phrases"
    except Exception as e:
        logger.info("The error is :  {}".format(str(e)))
        if os.path.exists(Name + "-sample" + str(0) + ".wav"):
            os.remove(Name + "-sample" + str(0) + ".wav")
            os.remove(Name + "-sample" + str(1) + ".wav")
            os.remove(Name + "-sample" + str(2) + ".wav")
        if os.path.exists(Name + ".gmm"):
            os.remove(Name + ".gmm")
        try:
            if os.path.exists("training_set_addition.txt"):
                os.remove("training_set_addition.txt")

            return "The error is :  {}".format(str(e))
        except:
            return "The error is :  {}".format(str(e))


def write_to_file(binary_code, file_name):
    # Convert binary to a proper file and store in memory
    with open(file_name, 'wb') as file:
        file.write(binary_code)


# If this error comes when running verify model TypeError: a bytes-like object is required, not 'NoneType'
# this means there is a null value in the DB in the Gmm_Model column delete these value before running the code.
def verify_reg_model():
    source = "./"
    modelpath = "./"
    # test_file = "./training_set_addition.txt"
    # file_paths = open(test_file, 'r')
    gmm_files = [os.path.join(modelpath, fname) for fname in
                 os.listdir(modelpath) if fname.endswith('.gmm')]
    # Load the Gaussian gender Models
    models = [pickle.load(open(fname, 'rb')) for fname in gmm_files]
    total_sample = 0.0
    # Read the test directory and get the list of test audio files
    nm = request.json['name']
    Name = str(nm)
    for i in range(3):
        path = Name + "-sample" + str(i) + ".wav"
        # path = path.strip()
        total_sample += 1.0
        sr, audio = read(source + path)
        vector = extract_features(audio, sr)
        log_likelihood = np.zeros(len(models))
        for i in range(len(models)):
            gmm = models[i]  # checking with each model one by one
            scores = np.array(gmm.score(vector))
            log_likelihood[i] = scores.sum()
        score = gmm.score(vector)
        if score >= -20.0:
            return score
        else:
            return score


def record_audio_test(b):
    valid = False
    img_b64_str = request.json['voice']
    img_path = base64_to_image(img_b64_str, "./" + b + "-sample.wav")
    OUTPUT_FILENAME = "sample.wav"
    r = speer.Recognizer()
    duration = 3
    cnxn_str = ('Server=localhost\SQLEXPRESS;Database=development;Trusted_Connection=True;')
    cursor = pyodbc.connect(cnxn_str)
    record12 = b
    cursor.execute('SELECT Phrases FROM Voice_Recognition WHERE Username= %s;', (b,))
    record1 = cursor.fetchone()
    cursor.commit()
    try:
        language = str(request.json['language'])
        r = speer.Recognizer()
        duration = 3
        filename = "./" + b + "-sample.wav"
        with speer.AudioFile(filename) as source:
            # read the audio data from the default microphone
            audio_data = r.record(source, duration=duration)
            # convert speech to text
            text1 = r.recognize_google(audio_data, language=language)
            encodedText1 = base64.b64encode(bytes(text1, 'utf-8'))
            a = encodedText1.decode('ascii')
    # return a;
    except:
        r = speer.Recognizer()
        duration = 3
        filename = "./" + b + "-sample.wav"
        with speer.AudioFile(filename) as source:
            # read the audio data from the default microphone
            audio_data = r.record(source, duration=duration)
            # convert speech to text
            text1 = r.recognize_google(audio_data)
            encodedText1 = base64.b64encode(bytes(text1, 'utf-8'))
            a = encodedText1.decode('ascii')
    # return a;
    if a == record1[0]:
        valid = True
        return valid
    else:
        return valid


def write_to_file(binary_code, file_name):
    # Convert binary to a proper file and store in memory
    try:
        with open(file_name, 'wb') as file:
            file.write(binary_code)
    except:
        with open(file_name, 'wb') as file:
            file.write(binary_code)


# If this error comes when running verify model TypeError: a bytes-like object is required, not 'NoneType'
# this means there is a null value in the DB in the Gmm_Model column delete these value before running the code.
@app.route("/verifyuser", methods=['POST'])
def verify_model():
    try:
        a = 0
        connection = mysql.connector.connect(host='localhost:5000',
                                             user='admin',
                                             password='test123$')
        cur = connection.cursor(buffered=True)
        nm = request.json['name']
        Name = str(nm)
        verify_nms.append(Name)
        result1 = all(i == verify_nms[0] for i in verify_nms)
        if result1:
            if len(verify_nms) >= 2:
                verify_nms.clear()
            logger.info(f"The request from {Name} has been received for verification")

            cur.execute('SELECT Username, Gmm_Model FROM Voice_Regocnition WHERE Username= %s;', (Name,))
            record1 = cur.fetchall()
            for row in record1:
                verify_nms.clear()
                write_to_file(row[1], "./" + row[0] + ".gmm")
            # print(row[0] +" DB")

            source = "./"
            modelpath = "./"
            test_file = "./testing_set_addition.txt"
            gmm_files = [os.path.join(modelpath, fname) for fname in
                         os.listdir(modelpath) if fname.endswith('.gmm')]
            # Load the Gaussian gender Models
            models = [pickle.load(open(fname, 'rb')) for fname in gmm_files]
            speakers = [fname.split("/")[-1].split(".gmm")[0] for fname
                        in gmm_files]

            username = False
            for i, j in enumerate(speakers):
                if j == Name:
                    a = i
                    username = True
            if username == False:
                if os.path.exists("testing_set_addition.txt"):
                    os.remove("testing_set_addition.txt")
                if os.path.exists(Name + "-sample.wav"):
                    os.remove(Name + "-sample.wav")
                if os.path.exists(Name + ".gmm"):
                    os.remove(Name + ".gmm")
                logger.info(Name + " Doesn't Exist. Please verify with correct username")
                return Name + " Doesn't Exist. Please verify with correct username"
            if (record_audio_test(Name) == False):
                logger.info(
                    "The user's voice varies or invalid phrases, Please try again with correct user's voice and phrases")
                if os.path.exists("testing_set_addition.txt"):
                    os.remove("testing_set_addition.txt")
                if os.path.exists(Name + "-sample.wav"):
                    os.remove(Name + "-sample.wav")
                if os.path.exists(Name + ".gmm"):
                    os.remove(Name + ".gmm")

                return "The user's voice varies or invalid phrases, Please try again with correct user's voice and phrases"
            # Read the test directory and get the list of test audio files
            try:
                for i in range(1):
                    path = "./" + Name + "-sample.wav"
                    sr, audio = read(source + path)
                    vector = extract_features(audio, sr)
                    gmm = models[a]

                    score = gmm.score(vector)
                # file_paths.close()
                if os.path.exists("testing_set_addition.txt"):
                    os.remove("testing_set_addition.txt")
                if os.path.exists(Name + "-sample.wav"):
                    os.remove(Name + "-sample.wav")
                if os.path.exists(Name + ".gmm"):
                    os.remove(Name + ".gmm")
            except:
                if os.path.exists(Name + "-sample.wav"):
                    os.remove(Name + "-sample.wav")
                if os.path.exists(Name + ".gmm"):
                    os.remove(Name + ".gmm")
                return "please try again after few seconds"

            if score >= -20.0:
                logger.info(Name + " has been verified")
                return "Score: " + str(score.sum()) + "\nUsers voice verified " + "Accuracy 95%" + "\nPhrase is valid"
            elif score >= -22.0:
                logger.info(Name + " has been verified")
                return "Score: " + str(score.sum()) + "\nUsers voice verified " + "Accuracy 90%" + "\nPhrase is valid"
            elif score >= -23.0:
                logger.info(Name + " has been verified")
                return "Score: " + str(score.sum()) + "\nUsers voice verified " + "Accuracy 80%" + "\nPhrase is valid"
            elif score >= -24.0:
                logger.info(Name + " has been verified")
                return "Score: " + str(score.sum()) + "\nUsers voice verified " + "Accuracy 70%" + "\nPhrase is valid"
            elif score >= -25.0:
                logger.info(Name + " has been verified")
                return "Score: " + str(score.sum()) + "\nUsers voice verified " + "Accuracy 60%" + "\nPhrase is valid"
            else:
                logger.info(Name + "has not been verified")
                return "Score: " + str(score.sum()) + "\nPlease try again, unable to verify users voice"
        else:
            time.sleep(3)
            verify_nms.clear()
            return "please try again after few seconds"
    except Exception as e:
        logger.info("The error is :  {}".format(str(e)))
        if os.path.exists(Name + "-sample.wav"):
            os.remove(Name + "-sample.wav")
        if os.path.exists(Name + ".gmm"):
            os.remove(Name + ".gmm")
        try:
            if os.path.exists("testing_set_addition.txt"):
                os.remove("testing_set_addition.txt")
            verify_nms.clear()
            return "The error is :  {}".format(str(e))
        except:
            if os.path.exists("testing_set_addition.txt"):
                os.remove("testing_set_addition.txt")
            verify_nms.clear()

            return "The error is :  {}".format(str(e))


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
