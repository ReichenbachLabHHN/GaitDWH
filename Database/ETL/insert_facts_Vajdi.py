"""
This module contains functions to load the fact data from Vajdi dataset into a harmonized database.
"""
import os
import psycopg2
import pandas as pd
import platform
from console_progressbar import ProgressBar
from datetime import datetime

from dotenv import load_dotenv
from psycopg2 import Error
import database_id_mapping as mapping


def insert_facts():
    
    ## GLOBAL META DATA
    
    sample_rate = 100

    # define Recording.Dataset_ID
    dataset_id = 3

    # Deduce Recording.Dataset_Title
    dataset_title = mapping.get_dataset_title(dataset_id)

    # define globaly static dimension IDs
    activity_ID = 1
    ground_ID = 5
    step_event_ID = 1

    # define dictionary to later check for existing recording_ID
    recording_dictionary = {}

    try:
        # Load environment variables from .env file
        load_dotenv()

        connection = psycopg2.connect(
            user = os.getenv("DB_USER"),
            password = os.getenv("DB_PASSWORD"),
            host = os.getenv("DB_HOST"),
            port = os.getenv("DB_PORT"),
            database = os.getenv("DB_NAME")
        )

        # Create a cursor to perform database operations
        cursor = connection.cursor()

        # Define data path
        path_to_data = '../Data/03_Vajdi/gait-data/'
        
        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data))
        progress_bar = ProgressBar(total=number_of_files-1, prefix="Vajdi Progress: ", decimals=2, length=50, fill='X',
                                   zfill='-')

        # Iterate over all files
        for filename in os.listdir(path_to_data):
            
            # Print progress
            progress_bar.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1
            
            # Extract data
            data = pd.read_csv(path_to_data + filename)

            # Due to a file length difference between Linux and Windows systems, a separation is necessary
     #       if platform.system() == 'Linux':
            if True:
                # This if clause is based in two issues
                # 1) Some files have two .csv file endings (.csv.csv) instead of just one. 
                # 2) subject_ID index is (for example) counted as 1 instead of 01, causing information to be located
                # at a different point in the string after the 9th subject
                if len(filename) == 15 or len(filename) == 19:
                    # Extract information from filename
                    subject_ID = filename[4:5]
                    sensor_position_string = filename[6:8]
                    repetition = int(filename[10]) - 1
                elif len(filename) == 16 or len(filename) == 20:
                    # Extract information from filename
                    subject_ID = filename[4:6]
                    sensor_position_string = filename[7:9]
                    repetition = int(filename[11]) - 1
            else:
                print(filename)
                if len(filename) == 14 or len(filename) == 18:
                    # Extract information from filename
                    subject_ID = filename[3:4]
                    sensor_position_string = filename[5:7]
                    repetition = int(filename[9]) - 1
                elif len(filename) == 15 or len(filename) == 19:
                    # Extract information from filename
                    subject_ID = filename[3:5]
                    sensor_position_string = filename[6:8]
                    repetition = int(filename[10]) - 1

            # Convert subject_ID to global person_ID
            person_ID = mapping.get_global_person_id_vajdi(int(subject_ID))

            # Deduce sensor_location_ID and world_coordinate_system_ID from extracted sensor_position string
            if sensor_position_string == "lw":
                sensor_location_ID = 13
                world_coordinate_system_ID = 5
            elif sensor_position_string == "rp":
                sensor_location_ID = 9
                world_coordinate_system_ID = 6

            # Extract first and last timestamps in file
            first_timestamp = data.iloc[0]['loggingTime.txt.'][11:-6]
            last_timestamp = data.iloc[-1]['loggingTime.txt.'][11:-6]
            # Convert timestamps to datetime objects
            first_timestamp_date = datetime.strptime(first_timestamp, "%H:%M:%S.%f")
            last_timestamp_date = datetime.strptime(last_timestamp, "%H:%M:%S.%f")
            # Calulcate duration using datetime timestamps
            duration = int((last_timestamp_date - first_timestamp_date).total_seconds() * 1000)

            # Extract date information
            year = data.iloc[0]['loggingTime.txt.'][0:4]
            month = data.iloc[0]['loggingTime.txt.'][5:7]
            day = data.iloc[0]['loggingTime.txt.'][8:10]
            starting_time = data.iloc[0]['loggingTime.txt.'][11:16]

            # Check if recording for current subject and repetition already exists 
            if not recording_dictionary.get(tuple([subject_ID,repetition])):

                # create new Recording entry
                create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
                Dataset_ID, Dataset_Title, Repetition, Sample_Frequency)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                cursor.execute(create_add_record_query, (year, month, day, starting_time, duration, dataset_id,
                                                         dataset_title, repetition, sample_rate))
                recording_ID = cursor.fetchone()[0]
                connection.commit()

                # Update dictionary with recording_ID and first timestamp (The latter is later used to sync up
                # simultaneous sensor recordings)
                recording_dictionary.update({tuple([subject_ID, repetition]):
                                                 tuple([recording_ID, first_timestamp_date])})

            else:
                # get recording_ID from dictionary
                recording_ID = recording_dictionary.get(tuple([subject_ID, repetition]))[0]

            # Iterate over all data rows
            for row_idx in range(0, len(data)):
                
                # Extract current timestamp
                current_timestamp = data.iloc[row_idx]['loggingTime.txt.'][11:-6]
                # Convert current timestamp to datatime object
                current_timestamp_date = datetime.strptime(current_timestamp, "%H:%M:%S.%f")

                # Exclude data rows starting too early, effectively syncing up simultaneous sensor recordings
                if current_timestamp_date >= recording_dictionary.get(tuple([subject_ID, repetition]))[1]:

                    # Calculate timestamp
                    timestamp = int((current_timestamp_date - recording_dictionary.get(tuple([subject_ID,
                                                                            repetition]))[1]).total_seconds() * 1000)

                    # Define value lists
                    acc_list = [0, 0, 0]
                    gyro_list = [0, 0, 0]
                    # Fill accelerometer value lists
                    acc_list[0] = data.iloc[row_idx]['Df1.1$X']
                    acc_list[1] = data.iloc[row_idx]['Df1.1$Y']
                    acc_list[2] = data.iloc[row_idx]['Df1.1$Z']
                    # Fill gyroscope value lists
                    gyro_list[0] = data.iloc[row_idx]['gyroRotationX.rad.s.']
                    gyro_list[1] = data.iloc[row_idx]['gyroRotationY.rad.s.']
                    gyro_list[2] = data.iloc[row_idx]['gyroRotationZ.rad.s.']


                    # Write Facts to database
                    # ACCELEROMETER
                    sensor_ID = 6
                    create_add_raw_accelerometer_query = '''INSERT INTO Raw_Accelerometer (X, Y, Z, Time, Recording_ID,
                    Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                    Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(create_add_raw_accelerometer_query, (acc_list[0], acc_list[1], acc_list[2],
                    timestamp, recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                    # GYROSCOPE
                    sensor_ID = 7
                    create_add_raw_gyroscope_query = '''INSERT INTO Raw_Gyroscope (X, Y, Z, Time, Recording_ID,
                    Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                    Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(create_add_raw_gyroscope_query, (gyro_list[0], gyro_list[1], gyro_list[2],
                    timestamp, recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                            world_coordinate_system_ID, step_event_ID, ground_ID))
            
            connection.commit()


    
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL:", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()