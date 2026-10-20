"""
This module contains functions to load the fact data from OU-ISIR-ISD2 dataset into a harmonized database.
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
    dataset_id = 5
    # Deduce Recording.Dataset_Title
    dataset_title = mapping.get_dataset_title(dataset_id)

    # Define static attributes and dimension_IDs
    year = 2011
    month = None
    day = None
    starting_time = None
    sample_rate = 100
    step_event_ID = 1

    # Define dictionary for sensors of the same recording
    recording_dictionary = {}


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

        # Define data paths
        path_to_data_stub = '../Data/04_OU-ISIR/Inertial_Sensor_Dataset_2/'
        path_to_smartphone_data = 'Android/'
        path_to_imuz_right_data = 'IMUZLeft/'
        path_to_imuz_center_data = 'IMUZCenter/'
        path_to_imuz_left_data = 'IMUZRight/'





        # SMARTPHONE DATA
        
        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data_stub + path_to_smartphone_data))
        progress_bar_1 = ProgressBar(total=number_of_files-1, prefix="OU-ISIR-ISD2 Sensor 1/4 Progress: ", decimals=2,
                                     length=50, fill='X', zfill='-')

        # Iterate over all files
        for filename in os.listdir(path_to_data_stub + path_to_smartphone_data):

            # Print progress
            progress_bar_1.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1
            
            # Define sensor_location-specific dimension IDs
            sensor_ID = 10
            sensor_location_ID = 15
            world_coordinate_system_ID = 1

            # Extract data from file
            data = pd.read_csv(path_to_data_stub + path_to_smartphone_data + filename, skiprows=2, header=None)

            # Extract subject_ID from filename
            subject_ID = int(filename[5:11])
            # Convert subject_ID to global person_ID
            person_ID = mapping.get_global_person_id_ou_isir(subject_ID)

            # Exclude person with recordings, but no meta data (only one case)
            if not person_ID == 'Invalid ID':
                # Deduce repetition
                if filename[-5] == "2":
                    repetition = 1
                else:
                    repetition = 0

                # Calculate duration
                duration = int((float(len(data)) / sample_rate) * 1000)

                # Deduce activity_ID and ground_ID by filename
                if "SlopeUp" in filename:
                    activity_ID = 3
                    ground_ID = 2
                elif "SlopeDown" in filename:
                    activity_ID = 4
                    ground_ID = 2
                else:
                    activity_ID = 1
                    ground_ID = 1

                # Check if recording for person has already been created
                if not recording_dictionary.get(tuple([person_ID, activity_ID, repetition])):
                
                    # create new Recording entry
                    create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
                    Dataset_ID, Dataset_Title, Repetition, Sample_Frequency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                    cursor.execute(create_add_record_query, (year, month, day, starting_time, duration,
                                                             dataset_id, dataset_title, repetition, sample_rate))
                    recording_ID = cursor.fetchone()[0]
                    connection.commit()

                    # Update dictionary
                    recording_dictionary.update({tuple([person_ID, activity_ID, repetition]): recording_ID})

                else:

                    # Get recording_ID from dictionary
                    recording_ID = recording_dictionary.get(tuple([person_ID, activity_ID, repetition]))

                # Iterate over all data rows
                for row_idx in range(0, len(data)):
                    
                    # Calculate timestamp (Possible since sample frequency is 100Hz)
                    timestamp = row_idx * 10

                    # Define value lists
                    acc_list = [0, 0, 0]
                    # Fill accelerometer value lists
                    acc_list[0] = data.iloc[row_idx][3]
                    acc_list[1] = data.iloc[row_idx][4]
                    acc_list[2] = data.iloc[row_idx][5]


                    # Write Facts to database
                    # ACCELEROMETER
                    create_add_raw_accelerometer_query = '''INSERT INTO Raw_Accelerometer (X, Y, Z, Time, Recording_ID,
                    Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                    Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(create_add_raw_accelerometer_query, (acc_list[0], acc_list[1], acc_list[2],
                    timestamp, recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                connection.commit()







        # IMUZ RIGHT DATA
        
        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data_stub + path_to_imuz_right_data))
        progress_bar_2 = ProgressBar(total=number_of_files-1, prefix="OU-ISIR-ISD2 Sensor 2/4 Progress: ", decimals=2,
                                     length=50, fill='X', zfill='-')

        # Iterate over all files
        for filename in os.listdir(path_to_data_stub + path_to_imuz_right_data):

            # Print progress
            progress_bar_2.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1

            # Define sensor_location-specific dimension IDs
            sensor_location_ID = 12
            world_coordinate_system_ID = 7
            
            # Extract data from file
            data = pd.read_csv(path_to_data_stub + path_to_imuz_right_data + filename, skiprows=2, header=None)

            # Extract subject_ID from filename
            subject_ID = int(filename[5:11])
            # Convert subject_ID to global person_ID
            person_ID = mapping.get_global_person_id_ou_isir(subject_ID)

            # Exclude person with recordings, but no meta data (only one case)
            if not person_ID == 'Invalid ID':
                # Deduce repetition
                if filename[-5] == "2":
                    repetition = 1
                else:
                    repetition = 0

                # Calulate duration
                duration = int((float(len(data)) / sample_rate) * 1000)

                # Deduce activity_ID and ground_ID by filename
                if "SlopeUp" in filename:
                    activity_ID = 3
                    ground_ID = 2
                elif "SlopeDown" in filename:
                    activity_ID = 4
                    ground_ID = 2
                else:
                    activity_ID = 1
                    ground_ID = 1

                # Check if recording for person has already been created
                if not recording_dictionary.get(tuple([person_ID, activity_ID, repetition])):
                
                    # create new Recording entry
                    create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
                    Dataset_ID, Dataset_Title, Repetition, Sample_Frequency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                    cursor.execute(create_add_record_query, (year, month, day, starting_time, duration,
                                                             dataset_id, dataset_title, repetition, sample_rate))
                    recording_ID = cursor.fetchone()[0]
                    connection.commit()

                    # Update dictionary
                    recording_dictionary.update({tuple([person_ID, activity_ID, repetition]): recording_ID})

                else:
                    # Get recording_ID from dictionary
                    recording_ID = recording_dictionary.get(tuple([person_ID, activity_ID, repetition]))

                # Iterate over all data rows
                for row_idx in range(0, len(data)):
                    
                    # Calculate timestamp (Possible since sample frequency is 100Hz)
                    timestamp = row_idx * 10

                    # Define values lists
                    acc_list = [0, 0, 0]
                    gyro_list = [0, 0, 0]
                    # Fill accelerometer value lists
                    acc_list[0] = data.iloc[row_idx][3]
                    acc_list[1] = data.iloc[row_idx][4]
                    acc_list[2] = data.iloc[row_idx][5]
                    # Fill gyroscope value lists
                    gyro_list[0] = data.iloc[row_idx][0]
                    gyro_list[1] = data.iloc[row_idx][1]
                    gyro_list[2] = data.iloc[row_idx][2]


                    # Write Facts to database
                    # ACCELEROMETER
                    sensor_ID = 8
                    create_add_raw_accelerometer_query = '''INSERT INTO Raw_Accelerometer (X, Y, Z, Time, Recording_ID,
                    Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                    Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(create_add_raw_accelerometer_query, (acc_list[0], acc_list[1], acc_list[2],
                    timestamp, recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                    # GYROSCOPE
                    sensor_ID = 9
                    create_add_raw_gyroscope_query = '''INSERT INTO Raw_Gyroscope (X, Y, Z, Time, Recording_ID,
                    Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                    Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(create_add_raw_gyroscope_query, (gyro_list[0], gyro_list[1], gyro_list[2],
                    timestamp, recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                connection.commit()








        # IMUZ Center DATA
        
        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data_stub + path_to_imuz_center_data))
        progress_bar_3 = ProgressBar(total=number_of_files-1, prefix="OU-ISIR-ISD2 Sensor 3/4 Progress: ", decimals=2,
                                     length=50, fill='X', zfill='-')

        for filename in os.listdir(path_to_data_stub + path_to_imuz_center_data):

            # Print progress
            progress_bar_3.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1

            # Define sensor_location-specific dimension IDs
            sensor_location_ID = 14
            world_coordinate_system_ID = 8

            # Extract data
            data = pd.read_csv(path_to_data_stub + path_to_imuz_center_data + filename, skiprows=2, header=None)

            # Extract subject_ID from filename
            subject_ID = int(filename[5:11])
            # Convert subject_ID to global person_ID
            person_ID = mapping.get_global_person_id_ou_isir(subject_ID)

            # Exclude person with recordings, but no meta data (only one case)
            if not person_ID == 'Invalid ID':
                # Deduce repetition
                if filename[-5] == "2":
                    repetition = 1
                else:
                    repetition = 0

                # Calulate duration
                duration = int((float(len(data)) / sample_rate) * 1000)

                # Deduce activity_ID and ground_ID by filename
                if "SlopeUp" in filename:
                    activity_ID = 3
                    ground_ID = 2
                elif "SlopeDown" in filename:
                    activity_ID = 4
                    ground_ID = 2
                else:
                    activity_ID = 1
                    ground_ID = 1

                # Check if recording for person has already been created
                if not recording_dictionary.get(tuple([person_ID, activity_ID, repetition])):
                
                    # create new Recording entry
                    create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
                    Dataset_ID, Dataset_Title, Repetition, Sample_Frequency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                    cursor.execute(create_add_record_query, (year, month, day, starting_time, duration,
                                                             dataset_id, dataset_title, repetition, sample_rate))
                    recording_ID = cursor.fetchone()[0]
                    connection.commit()

                    # Update dictionary
                    recording_dictionary.update({tuple([person_ID, activity_ID, repetition]): recording_ID})

                else:
                    # Get recording_ID from dictionary
                    recording_ID = recording_dictionary.get(tuple([person_ID, activity_ID, repetition]))

                # Iterate over all data rows
                for row_idx in range(0, len(data)):
                    
                    # Calculate timestamp (Possible since sample frequency is 100Hz)
                    timestamp = row_idx * 10

                    # Define values lists
                    acc_list = [0, 0, 0]
                    gyro_list = [0, 0, 0]
                    # Fill accelerometer value lists
                    acc_list[0] = data.iloc[row_idx][3]
                    acc_list[1] = data.iloc[row_idx][4]
                    acc_list[2] = data.iloc[row_idx][5]
                    # Fill gyroscope value lists
                    gyro_list[0] = data.iloc[row_idx][0]
                    gyro_list[1] = data.iloc[row_idx][1]
                    gyro_list[2] = data.iloc[row_idx][2]


                    # Write Facts to database
                    # ACCELEROMETER
                    sensor_ID = 8
                    create_add_raw_accelerometer_query = '''INSERT INTO Raw_Accelerometer (X, Y, Z, Time, Recording_ID,
                    Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                    Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(create_add_raw_accelerometer_query, (acc_list[0], acc_list[1], acc_list[2],
                    timestamp, recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                    # GYROSCOPE
                    sensor_ID = 9
                    create_add_raw_gyroscope_query = '''INSERT INTO Raw_Gyroscope (X, Y, Z, Time, Recording_ID,
                    Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                    Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(create_add_raw_gyroscope_query, (gyro_list[0], gyro_list[1], gyro_list[2],
                    timestamp, recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                connection.commit()







        # IMUZ Left DATA
        
        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data_stub + path_to_imuz_left_data))
        progress_bar_4 = ProgressBar(total=number_of_files-1, prefix="OU-ISIR-ISD2 Sensor 4/4 Progress: ", decimals=2,
                                     length=50, fill='X', zfill='-')

        # Iterate over all files
        for filename in os.listdir(path_to_data_stub + path_to_imuz_left_data):

            # Print progress
            progress_bar_4.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1

            # Define sensor_location-specific dimension IDs
            sensor_location_ID = 16
            world_coordinate_system_ID = 9

            # Extract data
            data = pd.read_csv(path_to_data_stub + path_to_imuz_left_data + filename, skiprows=2, header=None)

            # Extract subject_ID from filename
            subject_ID = int(filename[5:11])
            # Convert subject_ID to global person_ID
            person_ID = mapping.get_global_person_id_ou_isir(subject_ID)

            # Exclude person with recordings, but no meta data (only one case)
            if not person_ID == 'Invalid ID':
                # Deduce repetition
                if filename[-5] == "2":
                    repetition = 1
                else:
                    repetition = 0

                # Calulate duration
                duration = int((float(len(data)) / sample_rate) * 1000)

                # Deduce activity_ID and ground_ID by filename
                if "SlopeUp" in filename:
                    activity_ID = 3
                    ground_ID = 2
                elif "SlopeDown" in filename:
                    activity_ID = 4
                    ground_ID = 2
                else:
                    activity_ID = 1
                    ground_ID = 1

                # Check if recording for person has already been created
                if not recording_dictionary.get(tuple([person_ID, activity_ID, repetition])):
                
                    # create new Recording entry
                    create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
                    Dataset_ID, Dataset_Title, Repetition, Sample_Frequency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                    cursor.execute(create_add_record_query, (year, month, day, starting_time, duration,
                                                             dataset_id, dataset_title, repetition, sample_rate))
                    recording_ID = cursor.fetchone()[0]
                    connection.commit()

                    # Update dictionary
                    recording_dictionary.update({tuple([person_ID, activity_ID, repetition]): recording_ID})

                else:
                    # Get recording_ID from dictionary
                    recording_ID = recording_dictionary.get(tuple([person_ID, activity_ID, repetition]))

                # Iterate over all data rows
                for row_idx in range(0, len(data)):

                    # Calculate timestamp (Possible since sample frequency is 100Hz)
                    timestamp = row_idx * 10

                    # Define values lists
                    acc_list = [0, 0, 0]
                    gyro_list = [0, 0, 0]
                    # Fill accelerometer value lists
                    acc_list[0] = data.iloc[row_idx][3]
                    acc_list[1] = data.iloc[row_idx][4]
                    acc_list[2] = data.iloc[row_idx][5]
                    # Fill gyroscope value lists
                    gyro_list[0] = data.iloc[row_idx][0]
                    gyro_list[1] = data.iloc[row_idx][1]
                    gyro_list[2] = data.iloc[row_idx][2]


                    # Write Facts to database
                    # ACCELEROMETER
                    sensor_ID = 8
                    create_add_raw_accelerometer_query = '''INSERT INTO Raw_Accelerometer (X, Y, Z, Time, Recording_ID,
                    Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                    Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                    cursor.execute(create_add_raw_accelerometer_query, (acc_list[0], acc_list[1], acc_list[2],
                    timestamp, recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                    # GYROSCOPE
                    sensor_ID = 9
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