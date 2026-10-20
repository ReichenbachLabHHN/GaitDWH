"""
This module contains functions to load the fact data from McGill dataset into a harmonized database.
"""
import os
import psycopg2
import numpy as np
import pandas as pd
from console_progressbar import ProgressBar
from dotenv import load_dotenv
from psycopg2 import Error
import database_id_mapping as mapping


def insert_facts():

    ## GLOBAL META DATA

    # define Recording.Dataset_ID
    dataset_id = 1

    # Deduce Recording.Dataset_Title
    dataset_title = mapping.get_dataset_title(dataset_id)

    # define globaly static dimension IDs & attributes
    activity_ID = 1
    ground_ID = 5
    step_event_ID = 1
    sample_rate = 30

    try:
        # Load environment variables from .env file
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

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
        path_to_data = '../Data/004_McGill/gait-dataset/'
        path_to_subject_information = '../Data/004_McGill/SubjectInformation.csv'

        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data))
        progress_bar = ProgressBar(total=number_of_files-1, prefix="McGill Progress: ", decimals=2, length=50,
                                   fill='X', zfill='-')

        # Iterate over all files
        for filename in os.listdir(path_to_data):

            # Print progress
            progress_bar.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1

            # Extract data
            data = np.genfromtxt(path_to_data + filename, delimiter='\t', skip_header=1)

            # Calculate duration (Last entry timestamp - First entry timestamp)
            duration = int(data[-1][0]) - int(data[0][0])

            # Extract local person ID from filename
            local_person_ID = int(filename[1:4])
            # Convert local to global person_ID
            global_person_ID = mapping.get_global_person_id_mcgill(local_person_ID)

            # Extract repetition from filename
            repetition = int(filename[7:8]) - 1

            # Extract subject information
            subject_information = pd.read_csv(path_to_subject_information)
            person_data = subject_information.loc[local_person_ID - 1]

            # Extract specific subject information from correct column depending on repetition
            if repetition == 0:
                date = person_data['Date']
                raw_starting_time = str(person_data['Time'])
                pocket = person_data['Pocket']
            elif repetition == 1:
                date = person_data['Date.1']
                raw_starting_time = str(person_data['Time.1'])
                pocket = person_data['Pocket.1']

            # Extract date information
            year = int(date[6:])
            month = int(date[3:5])
            day = int(date[:2])
            starting_time = raw_starting_time[:5]
            
            # create new Recording entry
            create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
            Dataset_ID, Dataset_Title, Repetition, Sample_Frequency)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
            cursor.execute(create_add_record_query, (year, month, day, starting_time, duration, dataset_id,
                                                     dataset_title, repetition, sample_rate))
            recording_ID = cursor.fetchone()[0]
            connection.commit()

            # Deduce sensor_location_ID
            if pocket == "R":
                sensor_location_ID = 9
            elif pocket == "R Back":
                sensor_location_ID = 10
            elif pocket == "L":
                sensor_location_ID = 11

            # Iterate over all data rows
            for index, row in enumerate(data):
                # Calculate timestamp
                timestamp = int((data[index,0] - data[0][0]))

                # Define value lists
                acc_list = [0, 0, 0]
                mag_list = [0, 0, 0]
                # Fill accelerometer value lists
                acc_list[0] = row[1]
                acc_list[1] = row[2]
                acc_list[2] = row[3]
                # Fill magnetometer value lists
                mag_list[0] = row[6]
                mag_list[1] = row[7]
                mag_list[2] = row[8]

                # Deduce world_coordinate_system_ID
                if sensor_location_ID == 9 or sensor_location_ID == 11:
                    world_coordinate_system_ID = 3
                elif sensor_location_ID == 10:
                    world_coordinate_system_ID = 4    

                # Write Facts to database
                # ACCELEROMETER
                sensor_ID = 4
                create_add_raw_accelerometer_query = '''INSERT INTO Raw_Accelerometer (X, Y, Z, Time, Recording_ID,
                Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID,
                Step_Event_ID, Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                cursor.execute(create_add_raw_accelerometer_query, (acc_list[0], acc_list[1], acc_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                # MAGNETOMETER
                sensor_ID = 5
                create_add_raw_magnetometer_query = '''INSERT INTO Raw_Magnetometer (X, Y, Z, Time, Recording_ID,
                Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                cursor.execute(create_add_raw_magnetometer_query, (mag_list[0], mag_list[1], mag_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
            
            connection.commit()
        

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL:", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()