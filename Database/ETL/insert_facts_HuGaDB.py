"""
This module contains functions to load the fact data from HuGaDB into a harmonized database.
"""
import os
import psycopg2
from dotenv import load_dotenv
from psycopg2 import Error
from console_progressbar import ProgressBar
import HuGaDB_extract_data_from_file as edff
import database_id_mapping as mapping

def insert_facts():

    ## GLOBAL META DATA

    # Define Recording.Dataset_ID
    dataset_id = 0

    # Deduce Recording.Dataset_Title
    dataset_title = mapping.get_dataset_title(dataset_id)


    # Define static attributes and identifier
    year = 2016
    sample_rate = 56.35
    step_event_ID = 1


    ## Connect to database
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
        path_to_data = '../Data/00_HuGaDB/HuGaDB_v2/'
        
        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data))
        progress_bar = ProgressBar(total=number_of_files-1, prefix="HuGaDB Progress: ", decimals=2, length=50,
                                   fill='X', zfill='-')

        # Iterate over all files
        for filename in os.listdir(path_to_data):
            # Print progress
            progress_bar.print_progress_bar(counter)
            # Increase progress counter
            counter = counter + 1

            # Extract data
            data = edff.extract_data(path_to_data + filename)
            # Calculate duration
            duration = int((len(data)/sample_rate) * 1000)
            # Extract repetition from filename
            repetition = int(filename[-6:-4])
            # Extract header for later use
            header_line = edff.extract_header(path_to_data + filename)
            header = header_line.split()
            # Extract date context information
            date = edff.extract_date(path_to_data + filename)
            month = date[:2]
            day = date[3:5]
            starting_time = date[6:].replace('-', ':')

            # Create new Recording entry
            create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration, Dataset_ID,
            Dataset_Title, Repetition, Sample_Frequency) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING Recording_ID'''
            # Execute code to add Raw_Accelerometer table entry
            cursor.execute(create_add_record_query, (year, month, day, starting_time, duration, dataset_id,
                                                     dataset_title, repetition, sample_rate))
            recording_ID = cursor.fetchone()[0]
            connection.commit()

            # Extract person_ID
            local_person_ID = int(edff.extract_person_ID(path_to_data + filename))
            global_person_ID = mapping.get_global_person_id_hugadb(local_person_ID)

            # Iterate over all data rows
            for index, row in enumerate(data):
                # Extract activity
                local_activity_ID = int(row[-1])
                global_activity_ID = mapping.get_global_activity_id_hugadb(local_activity_ID)
                # Deduce Ground_ID by activity
                ground_ID = mapping.get_ground_id_by_activity_id_hugabd(global_activity_ID)
                # Calculate timestamp
                timestamp = int((index / sample_rate) * 1000)

                # Define accelerometer value lists for all sensor locations
                acc_lf_list = [0, 0, 0]
                acc_rf_list = [0, 0, 0]
                acc_ls_list = [0, 0, 0]
                acc_rs_list = [0, 0, 0]
                acc_lt_list = [0, 0, 0]
                acc_rt_list = [0, 0, 0]
                # Define gyroscope value lists for all sensor locations
                gyro_lf_list = [0, 0, 0]
                gyro_rf_list = [0, 0, 0]
                gyro_ls_list = [0, 0, 0]
                gyro_rs_list = [0, 0, 0]
                gyro_lt_list = [0, 0, 0]
                gyro_rt_list = [0, 0, 0]

                # Iterate over all columns
                for idx, column in enumerate(row):
                    # Split column header for further analysis
                    column_header = header[idx].split('_')
                    # Check by sensor type (column header prefix)
                    if column_header[0] == "acc":
                        # Check by sensor location (column header center)
                        if column_header[1] == "rf":
                            # Check by sensor axis (column header suffix)
                            if column_header[2] == "x":
                                acc_lf_list[0] = column
                            elif column_header[2] == "y":
                                acc_lf_list[1] = column
                            elif column_header[2] == "z":
                                acc_lf_list[2] = column
                        elif column_header[1] == "lf":
                            if column_header[2] == "x":
                                acc_rf_list[0] = column
                            elif column_header[2] == "y":
                                acc_rf_list[1] = column
                            elif column_header[2] == "z":
                                acc_rf_list[2] = column
                        elif column_header[1] == "rs":
                            if column_header[2] == "x":
                                acc_ls_list[0] = column
                            elif column_header[2] == "y":
                                acc_ls_list[1] = column
                            elif column_header[2] == "z":
                                acc_ls_list[2] = column
                        elif column_header[1] == "ls":
                            if column_header[2] == "x":
                                acc_rs_list[0] = column
                            elif column_header[2] == "y":
                                acc_rs_list[1] = column
                            elif column_header[2] == "z":
                                acc_rs_list[2] = column
                        elif column_header[1] == "rt":
                            if column_header[2] == "x":
                                acc_lt_list[0] = column
                            elif column_header[2] == "y":
                                acc_lt_list[1] = column
                            elif column_header[2] == "z":
                                acc_lt_list[2] = column
                        elif column_header[1] == "lt":
                            if column_header[2] == "x":
                                acc_rt_list[0] = column
                            elif column_header[2] == "y":
                                acc_rt_list[1] = column
                            elif column_header[2] == "z":
                                acc_rt_list[2] = column
                    elif column_header[0] == "gyro":
                        if column_header[1] == "rf":
                            if column_header[2] == "x":
                                gyro_lf_list[0] = column
                            elif column_header[2] == "y":
                                gyro_lf_list[1] = column
                            elif column_header[2] == "z":
                                gyro_lf_list[2] = column
                        elif column_header[1] == "lf":
                            if column_header[2] == "x":
                                gyro_rf_list[0] = column
                            elif column_header[2] == "y":
                                gyro_rf_list[1] = column
                            elif column_header[2] == "z":
                                gyro_rf_list[2] = column
                        elif column_header[1] == "rs":
                            if column_header[2] == "x":
                                gyro_ls_list[0] = column
                            elif column_header[2] == "y":
                                gyro_ls_list[1] = column
                            elif column_header[2] == "z":
                                gyro_ls_list[2] = column
                        elif column_header[1] == "ls":
                            if column_header[2] == "x":
                                gyro_rs_list[0] = column
                            elif column_header[2] == "y":
                                gyro_rs_list[1] = column
                            elif column_header[2] == "z":
                                gyro_rs_list[2] = column
                        elif column_header[1] == "rt":
                            if column_header[2] == "x":
                                gyro_lt_list[0] = column
                            elif column_header[2] == "y":
                                gyro_lt_list[1] = column
                            elif column_header[2] == "z":
                                gyro_lt_list[2] = column
                        elif column_header[1] == "lt":
                            if column_header[2] == "x":
                                gyro_rt_list[0] = column
                            elif column_header[2] == "y":
                                gyro_rt_list[1] = column
                            elif column_header[2] == "z":
                                gyro_rt_list[2] = column
                    elif column_header[0] == "EMG":
                        if column_header[1] == "r":
                            emg_l = column
                        elif column_header[1] == "l":
                            emg_r = column
                    
                    
                # Write row data to database
        
                # Accelerometer
                sensor_ID = 1
                # create Raw_Accelerometer query
                create_add_raw_accelerometer_query = '''INSERT INTO Raw_Accelerometer (X, Y, Z, Time, Recording_ID,
                Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID,
                Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

                # acc_lf_list
                sensor_location_ID = 1
                world_coordinate_system_ID = 2
                # execute code to add Raw_Accelerometer table entry
                cursor.execute(create_add_raw_accelerometer_query, (acc_lf_list[0], acc_lf_list[1], acc_lf_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))

                # acc_rf_list
                sensor_location_ID = 2
                world_coordinate_system_ID = 2
                # execute code to add Raw_Accelerometer table entry
                cursor.execute(create_add_raw_accelerometer_query, (acc_rf_list[0], acc_rf_list[1], acc_rf_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                # acc_ls_list
                sensor_location_ID = 3
                world_coordinate_system_ID = 1
                # execute code to add Raw_Accelerometer table entry
                cursor.execute(create_add_raw_accelerometer_query, (acc_ls_list[0], acc_ls_list[1], acc_ls_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                # acc_rs_list
                sensor_location_ID = 4
                world_coordinate_system_ID = 1
                # execute code to add Raw_Accelerometer table entry
                cursor.execute(create_add_raw_accelerometer_query, (acc_rs_list[0], acc_rs_list[1], acc_rs_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                # acc_lt_list
                sensor_location_ID = 5
                world_coordinate_system_ID = 1
                # execute code to add Raw_Accelerometer table entry
                cursor.execute(create_add_raw_accelerometer_query, (acc_lt_list[0], acc_lt_list[1], acc_lt_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                # acc_rt_list
                sensor_location_ID = 6
                world_coordinate_system_ID = 1
                # execute code to add Raw_Accelerometer table entry
                cursor.execute(create_add_raw_accelerometer_query, (acc_rt_list[0], acc_rt_list[1], acc_rt_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                

                # Gyroscope
                sensor_ID = 2
                # create Raw_Gyroscope query
                create_add_raw_gyroscope_query = '''INSERT INTO Raw_Gyroscope (X, Y, Z, Time, Recording_ID, Person_ID,
                Sensor_ID, Activity_ID, Sensor_Location_ID, World_Coordinate_System_ID, Step_Event_ID, Ground_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                
                # gyro_lf_list
                sensor_location_ID = 1
                world_coordinate_system_ID = 2
                # execute code to add Raw_Gyroscope table entry
                cursor.execute(create_add_raw_gyroscope_query, (gyro_lf_list[0], gyro_lf_list[1], gyro_lf_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                # gyro_rf_list
                sensor_location_ID = 2
                world_coordinate_system_ID = 2
                # execute code to add Raw_Gyroscope table entry
                cursor.execute(create_add_raw_gyroscope_query, (gyro_rf_list[0], gyro_rf_list[1], gyro_rf_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                # gyro_ls_list
                sensor_location_ID = 3
                world_coordinate_system_ID = 1
                # execute code to add Raw_Gyroscope table entry
                cursor.execute(create_add_raw_gyroscope_query, (gyro_ls_list[0], gyro_ls_list[1], gyro_ls_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                # gyro_rs_list
                sensor_location_ID = 4
                world_coordinate_system_ID = 1
                # execute code to add Raw_Gyroscope table entry
                cursor.execute(create_add_raw_gyroscope_query, (gyro_rs_list[0], gyro_rs_list[1], gyro_rs_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                # gyro_lt_list
                sensor_location_ID = 5
                world_coordinate_system_ID = 1
                # execute code to add Raw_Gyroscope table entry
                cursor.execute(create_add_raw_gyroscope_query, (gyro_lt_list[0], gyro_lt_list[1], gyro_lt_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                
                # gyro_rt_list
                sensor_location_ID = 6
                world_coordinate_system_ID = 1
                # execute code to add Raw_Gyroscope table entry
                cursor.execute(create_add_raw_gyroscope_query, (gyro_rt_list[0], gyro_rt_list[1], gyro_rt_list[2],
                timestamp, recording_ID, global_person_ID, sensor_ID, global_activity_ID, sensor_location_ID,
                                                                world_coordinate_system_ID, step_event_ID, ground_ID))
                

                # EMG
                sensor_ID = 3
                # create Raw_EMG query
                create_add_raw_emg_query = '''INSERT INTO Raw_EMG (R, L, Time, Recording_ID, Person_ID, Sensor_ID,
                Activity_ID, Sensor_Location_ID, Step_Event_ID, Ground_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

                # EMG_r
                sensor_location_ID = 7
                # execute code to add Raw_EMG table entry
                cursor.execute(create_add_raw_emg_query, (emg_r, emg_l, timestamp, recording_ID, global_person_ID,
                                        sensor_ID, global_activity_ID, sensor_location_ID, step_event_ID, ground_ID))
                
                # EMG_l
                sensor_location_ID = 8
                # execute code to add Raw_EMG table entry
                cursor.execute(create_add_raw_emg_query, (emg_r, emg_l, timestamp, recording_ID, global_person_ID,
                                        sensor_ID, global_activity_ID, sensor_location_ID, step_event_ID, ground_ID))
            
            connection.commit()
                
            


    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL:", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()