"""
This module contains functions to load the fact data from OU-ISIR-SAID database into a harmonized database.
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

    # define Recording.Database_ID
    database_id = 6

    # Deduce Recording.Database_Title
    database_title = mapping.get_dataset_title(database_id)

    # Define static attributes and dimension IDs
    year = 2011
    month = None
    day = None
    starting_time = None
    sample_rate = 100
    repetition = 0
    event_ID = None
    event_title = None

    # define a dictionary for common recordings between sensors
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
        path_to_data_stub = '../Data/04_OU-ISIR/Similar_Action_Inertial_Dataset/'
        path_to_imuz_right_data = 'LeftSensor/'
        path_to_imuz_center_data = 'CenterSensor/'
        path_to_imuz_left_data = 'RightSensor/'



        # IMUZ RIGHT DATA
        
        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data_stub + path_to_imuz_right_data))
        progress_bar_1 = ProgressBar(total=number_of_files-1, prefix="OU-ISIR-SAID Sensor 1/3 Progress: ", decimals=2,
                                     length=50, fill='X', zfill='-')

        # Iterate over all files
        for filename in os.listdir(path_to_data_stub + path_to_imuz_right_data):

            # Print progress
            progress_bar_1.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1

            # Define sensor_location-specific dimension IDs
            sensor_location_ID = 12
            world_coordinate_system_ID = 7

            # Extract data
            data = pd.read_csv(path_to_data_stub + path_to_imuz_right_data + filename, delimiter="\t", skiprows=2,
                               header=None)

            # Extract subject_ID from filename
            subject_ID = int(filename[5:11])
            # Convert subject_ID to global person_ID
            person_ID = mapping.get_global_person_id_ou_isir(subject_ID)

            # Exclude person with recordings, but no meta data (only one case)
            if not person_ID == 'Invalid ID':

                # Calulate duration
                duration = int((float(len(data)) / sample_rate) * 1000)

                # Check if recording for person has already been created
                if not recording_dictionary.get(person_ID):
                
                    # create new Recording entry
                    create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
                    Database_ID, Database_Title, Repetition, Sample_Frequency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                    cursor.execute(create_add_record_query, (year, month, day, starting_time, duration,
                                                             database_id, database_title, repetition, sample_rate))
                    recording_ID = cursor.fetchone()[0]
                    connection.commit()

                    # Update dictionary
                    recording_dictionary.update({person_ID: recording_ID})

                else:
                    # Get recording_ID from dictionary
                    recording_ID = recording_dictionary.get(person_ID)

                # Init step number variable
                old_step_number = 0

                # Iterate over all data rows
                for row_idx in range(0, len(data)):

                    # Extract local activity_label from data column
                    activity_label = int(data.iloc[row_idx][6])
                    # Convert local activity_label to global activity_ID
                    activity_ID = mapping.get_global_activity_id_ou_isir(activity_label)
                    # Deduce ground_ID from activity_ID
                    ground_ID = mapping.get_ground_id_by_activity_id_ou_isir(activity_ID)

                    # Extract step label from data column
                    step_label = int(data.iloc[row_idx][7])
                    # Calculate step number (Step label counts up twice every cycle, once for each leg. Step number
                    # therfore only increases every second step_label.)
                    step_number = step_label//2
                    # Handle invalid step labels
                    if step_label == -1:
                        step_label = None
                        # Check if Step_Event already exists
                        cursor.execute('''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID IS NULL AND
                        Ground_Truth_Step_Number IS NULL''')
                        step_event_ID = cursor.fetchone()
                    else:
                        # Check if a new step has begun, if so, add a ground_truth_event for the data row
                        if step_number - old_step_number == 1:
                            event_ID = 3
                            event_title = mapping.get_ground_truth_event_title(event_ID)
                            # Check if Step_Event already exists
                            cursor.execute('''SELECT Step_Event_ID FROM Step_Event WHERE
                            Ground_Truth_Event_ID = 3 AND Ground_Truth_Step_Number = %s''', (step_number,))
                            step_event_ID = cursor.fetchone()
                        else:
                            event_ID = None
                            event_title = None
                            # Check if Step_Event already exists
                            cursor.execute('''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID
                            IS NULL AND Ground_Truth_Step_Number = %s''', (step_number,))
                            step_event_ID = cursor.fetchone()
                        # Update the old step number 
                        old_step_number = step_number

                    # If Step_Event does not exist, create a new one
                    if not step_event_ID:
                        create_add_step_event_query = '''INSERT INTO Step_Event (Ground_Truth_Event_ID,
                        Ground_Truth_Event_Title, Ground_Truth_Step_Number) VALUES (%s, %s, %s)
                        RETURNING Step_Event_ID'''
                        cursor.execute(create_add_step_event_query, (event_ID, event_title, step_number))
                        step_event_ID = cursor.fetchone()[0]
                        connection.commit()
                    else:
                        # Use previously found Step_Event 
                        step_event_ID = step_event_ID[0]
            
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








        # IMUZ CENTER DATA
        
        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data_stub + path_to_imuz_center_data))
        progress_bar_2 = ProgressBar(total=number_of_files-1, prefix="OU-ISIR-SAID Sensor 2/3 Progress: ", decimals=2,
                                     length=50, fill='X', zfill='-')

        # Iterate over all files
        for filename in os.listdir(path_to_data_stub + path_to_imuz_center_data):

            # Print progress
            progress_bar_2.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1

            # Define sensor_location-specific dimension IDs
            sensor_location_ID = 14
            world_coordinate_system_ID = 8

            # Extract data
            data = pd.read_csv(path_to_data_stub + path_to_imuz_center_data + filename, delimiter="\t", skiprows=2,
                               header=None)

            # Extract subject_ID from filename
            subject_ID = int(filename[5:11])
            # Convert subject_ID to global person_ID
            person_ID = mapping.get_global_person_id_ou_isir(subject_ID)

            # Exclude person with recordings, but no meta data (only one case)
            if not person_ID == 'Invalid ID':

                # Calulate duration
                duration = int((float(len(data)) / sample_rate) * 1000)
                
                # Check if recording for person has already been created
                if not recording_dictionary.get(person_ID):
                
                    # create new Recording entry
                    create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
                    Database_ID, Database_Title, Repetition, Sample_Frequency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                    cursor.execute(create_add_record_query, (year, month, day, starting_time, duration,
                                                             database_id, database_title, repetition, sample_rate))
                    recording_ID = cursor.fetchone()[0]
                    connection.commit()

                    # Update dictionary
                    recording_dictionary.update({person_ID: recording_ID})

                else:
                    # Get recording_ID from dictionary
                    recording_ID = recording_dictionary.get(person_ID)

                # Init step number variable
                old_step_number = 0

                # Iterate over all data rows
                for row_idx in range(0, len(data)):
    
                    # Extract local activity_label from data column
                    activity_label = int(data.iloc[row_idx][6])
                    # Convert local activity_label to global activity_ID
                    activity_ID = mapping.get_global_activity_id_ou_isir(activity_label)
                    # Deduce ground_ID from activity_ID
                    ground_ID = mapping.get_ground_id_by_activity_id_ou_isir(activity_ID)

                    # Extract step label from data column
                    step_label = int(data.iloc[row_idx][7])
                    # Calculate step number (Step label counts up twice every cycle, once for each leg. Step number
                    # therfore only increases every second step_label.)
                    step_number = step_label//2
                    # Handle invalid step labels
                    if step_label == -1:
                        step_label = None
                        # Check if Step_Event already exists
                        cursor.execute('''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID IS NULL AND
                        Ground_Truth_Step_Number IS NULL''')
                        step_event_ID = cursor.fetchone()
                    else:
                        # Check if a new step has begun, if so, add a ground_truth_event for the data row
                        if step_number - old_step_number == 1:
                            event_ID = 3
                            event_title = mapping.get_ground_truth_event_title(event_ID)
                            # Check if Step_Event already exists
                            cursor.execute('''SELECT Step_Event_ID FROM Step_Event WHERE
                            Ground_Truth_Event_ID = 3 AND Ground_Truth_Step_Number = %s''', (step_number,))
                            step_event_ID = cursor.fetchone()
                        else:
                            event_ID = None
                            event_title = None
                            # Check if Step_Event already exists
                            cursor.execute('''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID
                            IS NULL AND Ground_Truth_Step_Number = %s''', (step_number,))
                            step_event_ID = cursor.fetchone()
                        # Update the old step number
                        old_step_number = step_number

                    # If Step_Event does not exist, create a new one
                    if not step_event_ID:
                        create_add_step_event_query = '''INSERT INTO Step_Event (Ground_Truth_Event_ID,
                        Ground_Truth_Event_Title, Ground_Truth_Step_Number)
                        VALUES (%s, %s, %s) RETURNING Step_Event_ID'''
                        cursor.execute(create_add_step_event_query, (event_ID, event_title, step_number))
                        step_event_ID = cursor.fetchone()[0]
                        connection.commit()
                    else:
                        # Use previously found Step_Event 
                        step_event_ID = step_event_ID[0]

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







        # IMUZ LEFT DATA
        
        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data_stub + path_to_imuz_left_data))
        progress_bar_3 = ProgressBar(total=number_of_files-1, prefix="OU-ISIR-SAID Sensor 3/3 Progress: ", decimals=2,
                                     length=50, fill='X', zfill='-')

        # Iterate over all files
        for filename in os.listdir(path_to_data_stub + path_to_imuz_left_data):

            # Print progess
            progress_bar_3.print_progress_bar(counter)
            # Increase progress counter     
            counter = counter + 1

            # Define sensor_location-specific dimension IDs
            sensor_location_ID = 16
            world_coordinate_system_ID = 9

            # Extract data
            data = pd.read_csv(path_to_data_stub + path_to_imuz_left_data + filename, delimiter="\t", skiprows=2,
                               header=None)

            # Extract subject_ID from filename
            subject_ID = int(filename[5:11])
            # Convert subject_ID to global person_ID
            person_ID = mapping.get_global_person_id_ou_isir(subject_ID)

            # Exclude person with recordings, but no meta data (only one case)
            if not person_ID == 'Invalid ID':
                
                # Calulate duration
                duration = int((float(len(data)) / sample_rate) * 1000)
                
                # Check if recording for person has already been created
                if not recording_dictionary.get(person_ID):
                
                    # create new Recording entry
                    create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
                    Database_ID, Database_Title, Repetition, Sample_Frequency)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                    cursor.execute(create_add_record_query, (year, month, day, starting_time, duration,
                                                             database_id, database_title, repetition, sample_rate))
                    recording_ID = cursor.fetchone()[0]
                    connection.commit()

                    # Update dictionary
                    recording_dictionary.update({person_ID: recording_ID})

                else:
                    # Get recording_ID from dictionary
                    recording_ID = recording_dictionary.get(person_ID)

                # Init step number variable
                old_step_number = 0

                # Iterate over all data rows
                for row_idx in range(0, len(data)):
    
                    # Extract local activity_label from data column
                    activity_label = int(data.iloc[row_idx][6])
                    # Convert local activity_label to global activity_ID
                    activity_ID = mapping.get_global_activity_id_ou_isir(activity_label)
                    # Deduce ground_ID from activity_ID
                    ground_ID = mapping.get_ground_id_by_activity_id_ou_isir(activity_ID)

                    # Extract step label from data column
                    step_label = int(data.iloc[row_idx][7])
                    # Calculate step number (Step label counts up twice every cycle, once for each leg. Step number
                    # therfore only increases every second step_label.)
                    step_number = step_label//2
                    # Handle invalid step labels
                    if step_label == -1:
                        step_label = None
                        # Check if Step_Event already exists
                        cursor.execute('''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID IS NULL AND
                        Ground_Truth_Step_Number IS NULL''')
                        step_event_ID = cursor.fetchone()
                    else:
                        # Check if a new step has begun, if so, add a ground_truth_event for the data row
                        if step_number - old_step_number == 1:
                            event_ID = 3
                            event_title = mapping.get_ground_truth_event_title(event_ID)
                            # Check if Step_Event already exists
                            cursor.execute('''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID = 3 AND
                            Ground_Truth_Step_Number = %s''', (step_number,))
                            step_event_ID = cursor.fetchone()
                        else:
                            event_ID = None
                            event_title = None
                            # Check if Step_Event already exists
                            cursor.execute('''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID
                            IS NULL AND Ground_Truth_Step_Number = %s''', (step_number,))
                            step_event_ID = cursor.fetchone()
                        # Update the old step number
                        old_step_number = step_number

                    # If Step_Event does not exist, create a new one
                    if not step_event_ID:
                        create_add_step_event_query = '''INSERT INTO Step_Event (Ground_Truth_Event_ID,
                        Ground_Truth_Event_Title, Ground_Truth_Step_Number)
                        VALUES (%s, %s, %s) RETURNING Step_Event_ID'''
                        cursor.execute(create_add_step_event_query, (event_ID, event_title, step_number))
                        step_event_ID = cursor.fetchone()[0]
                        connection.commit()
                    else:
                        # Use previously found Step_Event 
                        step_event_ID = step_event_ID[0]

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