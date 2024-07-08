# Voice Recognition

This repository contains a Flask-based voice recognition application that uses various machine learning techniques to train and verify voice models. The application supports user registration through voice samples and performs voice verification to authenticate users. The project leverages Gaussian Mixture Models (GMM) for voice recognition and integrates with SQL databases to store and retrieve user data.

# Features
- User Registration: Users can register by providing three audio samples. These samples are used to train a GMM model for the user.
- Voice Verification: Registered users can verify their identity by providing a voice sample, which is compared against the stored GMM model.
- Phrase Generation: The application generates and encodes phrases using Google Speech Recognition API.
- Feature Extraction: MFCC (Mel Frequency Cepstral Coefficients) features are extracted from audio files to train and verify models.
- Logging: Comprehensive logging is implemented to track application events and errors.
- Database Integration: Uses SQL Server and MySQL to store user data, voice models, and verification records.

# Technologies Used
- Flask: Web framework for building the API.
- SpeechRecognition (speer): Library for recognizing speech using various APIs and Google Web Speech API.
- Python Speech Features (mfcc): Library for extracting MFCC features from audio files.
- Scikit-learn: Machine learning library used for training GMM models.
- MySQL & PyODBC: Libraries for database connectivity and operations.
- Logging: Python's built-in logging module for logging application events.

# API Endpoints
- /adduser: Endpoint to register a new user with voice samples.
- /verifyuser: Endpoint to verify a user's identity with a voice sample.

# Usage
Registering a User:

Send a POST request to /adduser with the user's name and three base64-encoded audio files.
The application will train a GMM model and store it in the database.

Verifying a User:

Send a POST request to /verifyuser with the user's name and a base64-encoded audio file.
The application will verify the voice sample against the stored GMM model and return the verification result.
