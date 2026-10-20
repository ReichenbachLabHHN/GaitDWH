"""
This module contains functions to load the fact data from A Database of Human Gait Performance into a harmonized
database.
"""
import os
import psycopg2
import pandas as pd
from console_progressbar import ProgressBar
from dotenv import load_dotenv
from psycopg2 import Error
import database_id_mapping as mapping


def insert_facts():

    ## GLOBAL META DATA

    # Define Recording.Dataset_ID
    dataset_id = 7

    # Deduce Recording.Dataset_Title
    dataset_title = mapping.get_dataset_title(dataset_id)

    # Define globaly static dimension IDs
    step_event_ID = 1

    year = None
    month = None
    day = None
    starting_time = None

    sample_rate = 100

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

        # Define directory path to data
        path_to_subjects_subfolders = '../Data/009_A_database_for_human_gait/subjects/'

        # Define variable for later use
        old_trial_number = 1
        
        # Progress Bar
        counter = 0
        progress_bar = ProgressBar(total=30-1, prefix="A database of human gait Progress: ", decimals=2, length=50, fill='X', zfill='-')

        # Iterate over all subjects
        for subject in os.listdir(path_to_subjects_subfolders):

            # Print progress
            progress_bar.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1

            # Get global person_ID
            subject_ID = int(subject)
            person_ID = mapping.get_global_person_id_a_database_for_human_gait(subject_ID)

            # Iterate over all files
            for index, filename in enumerate(sorted(os.listdir(path_to_subjects_subfolders + subject + '/'))):

                # Exclude non-data files
                if "mtb" not in filename and "lock" not in filename:
                    # Extract trial number from filename
                    if "-" in filename[0:2]:
                        new_trial_number = int(filename[0:1])
                    else:
                        new_trial_number = int(filename[0:2])

                    # Exclude recordings with trial numbers 1-3, since they are calibration recordings
                    if new_trial_number not in range(1,4):
                        # Read data
                        data = pd.read_csv(path_to_subjects_subfolders + subject + '/' + filename, skiprows=1,
                                           header=None)
                        # Check if trial number changed
                        if new_trial_number != old_trial_number:
                            # Overwrite old trial number for next check
                            old_trial_number = new_trial_number
                            # Calculate duration
                            duration = int((len(data) / sample_rate) * 1000)
                            # Get repetition
                            repetition = mapping.get_repetition_by_trial_number(new_trial_number)
                            # Create new Record entry
                            create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time,
                                Duration, Dataset_ID, Dataset_Title, Repetition, Sample_Frequency)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                            # Execute code to add Raw_Accelerometer table entry
                            cursor.execute(create_add_record_query, (year, month, day, starting_time,duration,
                                                            dataset_id, dataset_title, repetition, sample_rate))
                            recording_ID = cursor.fetchone()[0]
                            connection.commit()
                        # Get Activity_ID and Ground_ID
                        activity_ID = mapping.get_activity_id_by_trial_number(new_trial_number)
                        ground_ID = mapping.get_ground_id_by_trial_number(new_trial_number)
                        # Get sensor_location_code from filename
                        sensor_location_code = filename[-10:-8]
                        # Get Sensor_Location_ID
                        sensor_location_ID =(
                            mapping.get_sensor_location_id_by_sensor_location_code(sensor_location_code))

                        # Iterate over all data rows
                        for row_idx in range(0, len(data)):
                            # Exclude rows with no data (Accidential row additions from the data source)
                            if not data.iloc[row_idx][2] == ' ':
                                # Deduce timestamp (Possible since sample frequency is 100Hz)
                                timestamp = row_idx * 10
                                # Create value lists
                                acc_list = [0, 0, 0]
                                gyro_list = [0, 0, 0]
                                mag_list = [0, 0, 0]
                                # Fill accelerometer value list
                                acc_list[0] = data.iloc[row_idx][2]
                                acc_list[1] = data.iloc[row_idx][3]
                                acc_list[2] = data.iloc[row_idx][4]
                                # Fill gyroscope value list
                                gyro_list[0] = data.iloc[row_idx][8]
                                gyro_list[1] = data.iloc[row_idx][9]
                                gyro_list[2] = data.iloc[row_idx][10]
                                # Fill magnetometer value list
                                mag_list[0] = data.iloc[row_idx][11]
                                mag_list[1] = data.iloc[row_idx][12]
                                mag_list[2] = data.iloc[row_idx][13]

                                # Deduce world coordinate system from sensor location
                                # range(22,26) are IDs 22, 23, 24 and 25
                                if sensor_location_ID in range(22, 26):
                                    world_coordinate_system_ID = 10
                                elif sensor_location_ID == 26:
                                    world_coordinate_system_ID = 1
                                elif sensor_location_ID == 17:
                                    world_coordinate_system_ID = 11

                                # ACCELEROMETER
                                sensor_ID = 11
                                create_add_raw_accelerometer_query = '''INSERT INTO Raw_Accelerometer (X, Y, Z, Time,
                                Recording_ID, Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID,
                                World_Coordinate_System_ID, Step_Event_ID, Ground_ID)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                                # execute code to add Raw_Accelerometer table entry
                                cursor.execute(create_add_raw_accelerometer_query, (acc_list[0], acc_list[1],
                                acc_list[2], timestamp, recording_ID, person_ID, sensor_ID, activity_ID,
                                sensor_location_ID, world_coordinate_system_ID, step_event_ID, ground_ID))
                                

                                # GYROSCOPE
                                sensor_ID = 12
                                create_add_raw_gyroscope_query = '''INSERT INTO Raw_Gyroscope (X, Y, Z, Time,
                                Recording_ID, Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID,
                                World_Coordinate_System_ID, Step_Event_ID, Ground_ID)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                                # execute code to add Raw_Gyroscope table entry
                                cursor.execute(create_add_raw_gyroscope_query, (gyro_list[0], gyro_list[1],
                                gyro_list[2], timestamp, recording_ID, person_ID, sensor_ID, activity_ID,
                                sensor_location_ID, world_coordinate_system_ID, step_event_ID, ground_ID))
                                

                                # MAGNETOMETER
                                sensor_ID = 13
                                create_add_raw_magnetometer_query = '''INSERT INTO Raw_Magnetometer (X, Y, Z, Time,
                                Recording_ID, Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID,
                                World_Coordinate_System_ID, Step_Event_ID, Ground_ID)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                                # execute code to add Raw_Magnetometer table entry
                                cursor.execute(create_add_raw_magnetometer_query, (mag_list[0], mag_list[1],
                                mag_list[2], timestamp, recording_ID, person_ID, sensor_ID, activity_ID,
                                sensor_location_ID, world_coordinate_system_ID, step_event_ID, ground_ID))
                                
                        connection.commit()




    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL:", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()