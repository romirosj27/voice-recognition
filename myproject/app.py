import base64
import os
import pickle
import time
import warnings
import pyodbc
from flask import Flask, request
import speech_recognition as speer
import numpy as np
import python_speech_features as mfcc
from scipy.io.wavfile import read
from sklearn import preprocessing
from sklearn.mixture import GaussianMixture
import logging

# REMARKS
# This is a project for voice recognition, which enables users to verify their identity by speaking.
# Currently, the project employs Flask API to communicate with users, while testing is carried out via Post Man.
# The main function of this project involves building a GMM (Gaussian Mixture Model) from an audio file, detecting a
# distinct phrase spoken by the user during the audio, and storing this information in a database. To verify the
# user, the code calculates a score by comparing the GMM model obtained from the database and the one generated for
# the audio file used for verification. If the score meets a specific threshold, the user is considered verified.
# This is a rudimentary project, and as my knowledge of AI/ML advances, I plan to enhance it further.
# ENDREMARKS
# HISTORY
# 05/03/21 Romiro Johnson Created
# 02/04/23 Romiro Johnson Refactored the code
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
cnxn = pyodbc.connect('DRIVER={SQL Server};Server=localhost\SQLEXPRESS;Database=development;Trusted_Connection=True;')
cursor = cnxn.cursor()

warnings.filterwarnings("ignore")

audio_files = []
list_of_usernames = []  # This list is created to check if the username is the same for all the three times
verify_nms = []
count1812 = -1


# This function is utilized to collect the pertinent information from the received audio file and store it in the
# database.
@app.route("/adduser", methods=['POST'])
def record_audio_train():
    time.sleep(3)
    try:
        global audio_files
        received_username = str(request.json['name'])
        list_of_usernames.append(received_username)
        logger.info(f"The request from {received_username} has been received for registration")

        phrase = []
        scores = []

        phrase_count = 0

        count1 = 0
        img_b64_str = request.json['voice']

        if img_b64_str == "":
            return "Please enter a valid audio file"

        if (check_if_user_exists(received_username) == False):
            logger.info("User already exists")
            return "User already exists";

        audio_files.append(img_b64_str)

        if not len(audio_files) >= 3:
            return "One Audio file inserted, please insert a total of three audio files"
        else:
            result1 = all(i == list_of_usernames[0] for i in list_of_usernames)
            if result1:
                base64_to_image(audio_files[0], './' + received_username + "-sample" + str(0) + ".wav")
                base64_to_image(audio_files[1], './' + received_username + "-sample" + str(1) + ".wav")
                base64_to_image(audio_files[2], './' + received_username + "-sample" + str(2) + ".wav")
                list_of_usernames.clear()
                audio_files.clear()
            else:
                # This is done to avoid simultaneous transactions
                list_of_usernames.clear()
                audio_files.clear()
                time.sleep(3)
                return "please try again after few seconds"
            for count in range(3):
                OUTPUT_FILENAME = received_username + "-sample" + str(count) + ".wav"
                source = "./"
                dest = "./"
                count = 1
                features = np.asarray(())
            for i in range(3):
                path = received_username + "-sample" + str(i) + ".wav"
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
                    picklefile = received_username + ".gmm"
                    pickle.dump(gmm, open(dest + picklefile, 'wb'))
                    features = np.asarray(())
                    count = 0
                    z = "./" + received_username + ".gmm"
                    count = count + 1
                    gmmFile = convertToBinaryData(z)
                scores.append(verify_reg_model())
                if phrase_count <= 2:
                    phrase.append(phrase_generator(received_username, phrase_count))
                    phrase_count = phrase_count + 1
                if (all(i >= -20 for i in scores)):
                    result = all(i == phrase[0] for i in phrase)
                    if result:
                        audioFile = convertToBinaryData('./' + OUTPUT_FILENAME)
                        # phrase_generator(Name, count1)
                        try:
                            cursor.execute(
                                '''INSERT INTO VoiceRecords(Username,Gmm_Model,Audio,Phrases) VALUES(?, ?, ?,?)''',
                                (received_username, gmmFile, audioFile, phrase_generator(received_username, count1)))
                            # Convert data into tuple format
                            cursor.commit()
                            count1 = count1 + 1
                        except pyodbc.Error as e:
                            logger.info("Error message:", e)
                            delete_files(received_username)
                            return "Error message:", e
                    else:
                        logger.info("Incorrect phrase, please try again")
                        return "Incorrect phrase, please try again"
                else:
                    logger.info(
                        "The user's voice varies or invalid phrases, Please try again with correct user's voice and "
                        "phrases")
                    return "The user's voice varies or invalid phrases, Please try again with correct user's voice " \
                           "and phrases "
        delete_files(received_username)
        logger.info(received_username + " has been added successfully")
        return received_username + " has been added successfully"
    except Exception as e:
        logger.info("The error is :  {}".format(str(e)))
        delete_files(received_username)
        try:
            delete_files(received_username);
            return "The error is :  {}".format(str(e))
        except:
            return "The error is :  {}".format(str(e))


def delete_files(Name):
    if os.path.exists(Name + "-sample" + str(0) + ".wav"):
        os.remove(Name + "-sample" + str(0) + ".wav")
        os.remove(Name + "-sample" + str(1) + ".wav")
        os.remove(Name + "-sample" + str(2) + ".wav")
    if os.path.exists(Name + ".gmm"):
        os.remove(Name + ".gmm")
    if os.path.exists("training_set_addition.txt"):
        os.remove("training_set_addition.txt")


# This function is used to verify the users according to the audio file provided
@app.route("/verifyuser", methods=['POST'])
def verify_model():
    try:
        a = 0
        cnxn = pyodbc.connect(
            'DRIVER={SQL Server};Server=localhost\SQLEXPRESS;Database=development;Trusted_Connection=True;')
        cur = cnxn.cursor()
        nm = request.json['name']
        Name = str(nm)
        verify_nms.append(Name)
        result1 = all(i == verify_nms[0] for i in verify_nms)
        if result1:
            if len(verify_nms) >= 2:
                verify_nms.clear()
            logger.info(f"The request from {Name} has been received for verification")
            try:
                cur.execute('''SELECT Username, Gmm_Model FROM VoiceRecords WHERE Username= ?;''', (Name,))
                record1 = cur.fetchall()
            except pyodbc.Error as ex:
                sqlstate = ex.args[1]
                print(sqlstate)
                logger.info(sqlstate)

            for row in record1:
                verify_nms.clear()
                write_to_file(row[1], "./" + row[0] + ".gmm")

            source = "./"
            modelpath = "./"
            test_file = "./testing_set_addition.txt"
            gmm_files = [os.path.join(modelpath, fname) for fname in
                         os.listdir(modelpath) if fname.endswith('.gmm')]
            # Load the Gaussian mixture models
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
            if (verify_users_voice_and_phrase(Name) == False):
                logger.info(
                    "The user's voice varies or invalid phrases, Please try again with correct user's voice and phrases")
                delete_files(Name)
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
                delete_files(Name)
            except:
                delete_files(Name)
                return "please try again after few seconds"

            return calculate_score(Name, score)
        else:
            time.sleep(3)
            verify_nms.clear()
            return "please try again after few seconds"
    except Exception as e:
        logger.info("The error is :  {}".format(str(e)))
        delete_files(Name)
        try:
            delete_files(Name)
            verify_nms.clear()
            return "The error is :  {}".format(str(e))
        except:
            delete_files(Name)
            verify_nms.clear()

            return "The error is :  {}".format(str(e))


# This function classifies the score.
def calculate_score(Name, score):
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


# This function checks if the name provided already exists in the database
def check_if_user_exists(Name):
    cursor.execute('''SELECT Count(Username) FROM VoiceRecords WHERE Username= ?;''', (Name,))
    rowcount = cursor.fetchall()[0]
    if rowcount[0] == 0:
        return True
    else:
        return False


# This function is used to check if the phrase in the database matches the phrase said in the voice recording
def verify_users_voice_and_phrase(userName):
    valid = False
    img_b64_str = request.json['voice']
    base64_to_image(img_b64_str, "./" + userName + "-sample.wav")
    # OUTPUT_FILENAME = "sample.wav"
    # r = speer.Recognizer()
    # duration = 3
    # record12 = userName
    cursor.execute('SELECT Phrases FROM VoiceRecords WHERE Username = ?;', (userName,))
    record1 = cursor.fetchone()
    cursor.commit()
    try:
        language = str(request.json['language'])
        r = speer.Recognizer()
        duration = 3
        filename = "./" + userName + "-sample.wav"
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
        filename = "./" + userName + "-sample.wav"
        with speer.AudioFile(filename) as source:
            # read the audio data from the default microphone
            audio_data = r.record(source, duration=duration)
            # convert speech to text
            text1 = r.recognize_google(audio_data)
            encodedText1 = base64.b64encode(bytes(text1, 'utf-8'))
            a = encodedText1.decode('ascii')
    if a == record1[0]:
        valid = True
        return valid
    else:
        return valid


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
        return a
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
        return a


def base64_to_image(base64_str, path_to_save):
    with open(path_to_save, "wb") as fh:
        fh.write(base64.decodebytes(base64_str.encode('utf-8')))
    return path_to_save


def write_to_file(binary_code, file_name):
    # Convert binary to a proper file and store in memory
    with open(file_name, 'wb') as file:
        file.write(binary_code)


# This function is used to generate a score
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


def write_to_file(binary_code, file_name):
    # Convert binary to a proper file and store in memory
    try:
        with open(file_name, 'wb') as file:
            file.write(binary_code)
    except:
        with open(file_name, 'wb') as file:
            file.write(binary_code)


if __name__ == "__main__":
    app.run(debug=True, threaded=True)
