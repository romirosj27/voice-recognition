# voice-recognition

This is a project for voice recognition, which enables users to verify their identity by speaking.
Currently, the project employs Flask API to communicate with users, while testing is carried out via Post Man.
The main function of this project involves building a GMM (Gaussian Mixture Model) from an audio file, detecting a
distinct phrase spoken by the user during the audio, and storing this information in a database. To verify the
user, the code calculates a score by comparing the GMM model obtained from the database and the one generated for
the audio file used for verification. If the score meets a specific threshold, the user is considered verified.
This is a rudimentary project, and as my knowledge of AI/ML advances, I plan to enhance it further.
