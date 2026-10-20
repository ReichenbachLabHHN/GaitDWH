"""
Feature extraction pipeline.
This module contains functions to process the accelerometer data and extract several features.
"""
import os
import statistics
import psycopg2
import numpy as np
import math
from dotenv import load_dotenv
from psycopg2 import Error
from scipy.signal import find_peaks
from scipy.stats.stats import pearsonr
from scipy.fft import fft, fftfreq
from console_progressbar import ProgressBar
import gait_toolbox
import matplotlib.pyplot as plt
from Database.ETL import database_id_mapping as mapping, create_postgres_db


def extract_gait_features():
    """
    Feature Extraction pipeline.
    """
    ## SETTINGS
    # Load environment variables from .env file
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

    activities_list = os.getenv("ACTIVITIES_LIST", "").split(",")
    activities_list = [int(x) for x in activities_list]  # convert each to int
    feature_frames_list = os.getenv("FEATURE_FRAMES_LIST", "").split(",")
    feature_frames_list = [int(x) for x in feature_frames_list]
    resample_target_sample_rate = int(os.getenv("RESAMPLE_TARGET_SAMPLE_RATE"))
    moving_average_filter_window_size = int(os.getenv("MOVING_AVERAGE_FILTER_WINDOW_SIZE"))
    fourier_coefficient_amount = int(os.getenv("FOURIER_COEFFICIENT_AMOUNT"))
    correlation_flag_threshold = float(os.getenv("CORRELATION_FLAG_THRESHOLD"))
    normalize_target_cycle_length = 200
    
    try:

        connection = psycopg2.connect(
            user = os.getenv("DB_USER"),
            password = os.getenv("DB_PASSWORD"),
            host = os.getenv("DB_HOST"),
            port = os.getenv("DB_PORT"),
            database = os.getenv("DB_NAME")
        )

        # Create a cursor to perform database operations
        cursor = connection.cursor()

        # Clean database feature tables
        create_postgres_db.clean_db(connection, cursor, features_only=True)
        create_postgres_db.create_feature_tables(connection, cursor)
        create_postgres_db.create_feature_indices(connection, cursor)
        for feature_frame in feature_frames_list:
            create_postgres_db.drop_statistical_measure_tables(feature_frame, connection, cursor)
            create_postgres_db.create_statistical_measure_feature_table(feature_frame, connection, cursor)
            create_postgres_db.create_statistical_measure_tables_indices(feature_frame, connection, cursor)

        # Retrieve all recording_IDs
        query = '''SELECT Recording_ID FROM Recording'''
        cursor.execute(query)
        recording_IDs = cursor.fetchall()

        # Number of recordings that completed the full processing pipelin
        counter = 0

        # Counts all recordings that were processed to some extent, including those that were skipped before completion
        total_counter = 0
        # counter for  total amount of recordings no gait cycle could be extracted from
        skip_no_gait_cycles_extracted = 0
        # counter for  total amount of recordings no frequency peaks could be detected in
        skip_no_frequency_peaks_counter = 0
        # counter for  total amount of recordings that did not contain any walking data
        # note this becomes useless/needs to e altered if other than walking data is being analyzed
        # (activities list in the .envs file)
        skip_no_walking_counter = 0

        # Progress Bar
        progress_bar = ProgressBar(total=len(recording_IDs), prefix="Preprocessing + Feature Extraction Progress: ",
                                   decimals=2, length=50, fill='X', zfill='-')

        # Recording loop
        for recording_ID_tuple in recording_IDs:

            recording_ID = recording_ID_tuple[0]

            # Increase progress counter
            counter+=1

            # Debug statement for manual adjustment of start point
            if recording_ID >= 0:
                # Retrieve sample rate
                query = '''SELECT Sample_Frequency FROM Recording WHERE Recording_ID = %s'''
                cursor.execute(query, (recording_ID,))
                sample_rate = cursor.fetchone()[0]

                # Retrieve relevant sensor_location_IDs
                query = '''SELECT DISTINCT Sensor_Location_ID FROM Raw_Accelerometer WHERE Recording_ID = %s'''
                cursor.execute(query, (recording_ID,))
                sensor_location_IDs = cursor.fetchall()

                # Sensor_location loop
                for sensor_location_ID in sensor_location_IDs:
                    # Retrieve body_side_ID from sensor_location_ID
                    query = '''SELECT Body_Side_ID FROM Sensor_Location WHERE Sensor_Location_ID = %s'''
                    cursor.execute(query, (sensor_location_ID,))
                    body_side_ID = cursor.fetchone()[0]
                    
                    if body_side_ID == 1:
                        centered = True
                    else:
                        centered = False
                    
                    # Retrieve accelerometer data
                    query = '''SELECT * FROM Raw_Accelerometer WHERE Recording_ID = %s AND Sensor_Location_ID = %s
                    ORDER BY Time'''
                    cursor.execute(query, (recording_ID, sensor_location_ID))
                    accelerometer_data = cursor.fetchall()
                    
                    # Check for empty data
                    if len(accelerometer_data) == 0:
                        skip_no_walking_counter+=1
                        total_counter+=1
                        continue
                    
                    # Transform accelerometer data to numpy array
                    accelerometer_data_array = np.array(accelerometer_data)
                    
                    # Loop by wanted activity
                    for activity_ID in activities_list:
                    
                        # Isolate all samples of activity with the current activity type in the recording and add them
                        # to a common list
                        accelerometer_activity_array = np.array([accelerometer_row for accelerometer_row
                                                in accelerometer_data_array if accelerometer_row[8] == activity_ID])
                        accelerometer_data_array = accelerometer_activity_array

                        # The list might now contain concatenated segments of independent walking sample sequences
                        ## Split up the independent walking sequences
                        # Define result list for the split segments (several accelerometer_segments)
                        accelerometer_segments_list = []
                        # Define list for a continous walking segment (can be several rows)
                        accelerometer_segment = []
                        # Calculate time per sample
                        milliseconds_per_sample = 1000/sample_rate
                        # Initilize variable for later use
                        old_timestamp = None
                        old_pk = None
                        # Iterate through all samples
                        for accelerometer_row in accelerometer_data_array:
                            # Extract the current timestamp from the sample
                            current_timestamp = accelerometer_row[4]
                            # Extract the current primary key from the sample
                            current_pk = accelerometer_row[0]
                            # Called when old_timestamp is in its initilized state
                            # (once, at the start [or twice if recording starts with walking activity])
                            if not old_timestamp:
                                # Checks if the current timestamp starts at recording time 0, which is not the case if
                                # the overall recording started with non-walking activity
                                if not current_timestamp == 0:
                                    # old_timestamp is set as the timestamp of the sample before the current one
                                    old_timestamp = current_timestamp - milliseconds_per_sample
                                    # old_pk is set as the primary key of the sample before the current one
                                    old_pk = current_pk - 1
                                else:
                                    # If the current sample is the first in the recording, it can just be added to
                                    # the current segment list
                                    accelerometer_segment.append(accelerometer_row)
                                    # Continue with next sample ("if not timestamp" is then entered again,
                                    # but current_timestamp cannot be 0, and old_timestamp is therefor set)
                                    continue
                            # Checks if the current sample follows the previous (old) one directly, either timewise
                            # or primary key wise
                            if ((current_timestamp-old_timestamp)/milliseconds_per_sample < 2
                                    or old_pk == current_pk - 1):
                                # If the current sample follows right after the previous one, it is added to
                                # the current segment list
                                accelerometer_segment.append(accelerometer_row)
                            else:
                                # Since there is a time gap between the current and previous samples,
                                # it is not a continuous segment.
                                # The current segment is therefore added to the list of segments,
                                # and the current sample is a added to a new segment list.
                                accelerometer_segments_list.append(accelerometer_segment)
                                accelerometer_segment = []
                                accelerometer_segment.append(accelerometer_row)
                            # The old timestamp is set to the current one
                            old_timestamp = current_timestamp
                            # The old primary key is set to the current one
                            old_pk = current_pk
                        # If all samples belong to a single, long walking segment, add the segment
                        # to the list of segments
                        if not accelerometer_segment == []:
                            accelerometer_segments_list.append(accelerometer_segment)

                        segment_number = -1
                        # Iterate over all segments in the list of walking activity segments
                        for accelerometer_segment in accelerometer_segments_list:
                            segment_number+=1
                            # Skip too small segments
                            if not len(accelerometer_segment) > 3*sample_rate:
                                continue
                            
                            # Convert segement to numpy array
                            accelerometer_segment = np.array(accelerometer_segment)
                        
                            # Remove primary keys
                            accelerometer_data_array = accelerometer_segment[:, 1:]
                            
                            # Rotate data
                            accelerometer_data_array = _rotate_data(accelerometer_data_array, cursor)

                            # Upsample data and write to database
                            accelerometer_data_array, pre_accelerometer_primary_keys = (
                                _upsample_data(accelerometer_data_array, sample_rate, resample_target_sample_rate,
                                        segment_number, connection, cursor, return_primary_keys=True))
                            #the new sample rate
                            resampled_sample_rate = resample_target_sample_rate

                            # Extract jerk vector
                            jerk_vector = _extract_jerk_vector(accelerometer_data_array,
                                                moving_average_filter_window_size, segment_number, connection, cursor)

                            # Extract fourier coefficients and write them to the database
                            _extract_fourier_coefficients(jerk_vector, fourier_coefficient_amount,
                                                resampled_sample_rate, connection, cursor)

                            # Extract dominant peaks, minima, and non_dominant_peaks
                            dominant_peaks, minima, non_dominant_peaks, step_frequency =(gait_toolbox.
                                        detect_extrema_events(jerk_vector, resampled_sample_rate, centered, plot=False))

                            # Skip recording if no frequency peaks could be detected
                            if isinstance(dominant_peaks, np.ndarray):
                                dominant_peaks = dominant_peaks.tolist()
                            if not dominant_peaks:
                                skip_no_frequency_peaks_counter += 1
                                total_counter += 1
                                continue


                            # Extract gait_cycles and write them to the database
                            gait_cycles = _extract_gait_cycles(jerk_vector, minima, centered, 4,
                                                               segment_number, connection, cursor)
                            # Skip recording if no gait cycles could be extracted
                            if len(gait_cycles) == 0:
                                skip_no_gait_cycles_extracted+=1
                                total_counter+=1
                                continue

                            # Normalize gait cycles
                            normalized_gait_cycles = _normalize_gait_cycles(gait_cycles, normalize_target_cycle_length)

                            # Write normalized_gait_cycles to Database
                            _write_normalized_gait_cycles_to_database(normalized_gait_cycles, None, None,
                                                                      segment_number, connection, cursor)

                            # Write extrema events to Step_Event table
                            _write_extrema_events_to_database(accelerometer_data_array, pre_accelerometer_primary_keys,
                                                    jerk_vector, dominant_peaks, non_dominant_peaks, minima, centered,
                                                              connection, cursor)

                            total_counter+=1
                        if len(accelerometer_segments_list) > 0:
                            # Retrieve all uniform gait cycles of the current recording and sensor location
                            gait_cycle_query = '''SELECT * FROM Feature_Uniform_Accelerometer_Gait_Cycle
                                            WHERE Recording_Id = %s AND Sensor_Location_Id = %s and Activity_Id = %s'''

                            input_list = [recording_ID, sensor_location_ID, activity_ID]
                            input_list = [input for input in input_list if not input == None]
                            input_tuple = tuple(input_list)
                            cursor.execute(gait_cycle_query, input_tuple)
                            uniform_gait_cycles = cursor.fetchall()

                            if len(uniform_gait_cycles) == 0:
                                continue

                            mean_gait_cycle = _calculate_mean_gait_cycle(uniform_gait_cycles)

                            mean_gait_cycle = np.array(mean_gait_cycle)

                            _write_mean_gait_cycle_to_database(mean_gait_cycle, len(uniform_gait_cycles),
                                                                   normalized_gait_cycles[0], connection, cursor)

                            # Calculate correlations to mean cycle
                            gait_cycle_correlations_to_mean_cycle = _calculate_gait_cycle_correlations_to_mean_cycle(
                                uniform_gait_cycles, mean_gait_cycle)

                            # Calculate correlation flags
                            gait_cycle_correlation_flags = _calculate_gait_cycle_correlation_flags(
                                gait_cycle_correlations_to_mean_cycle, correlation_flag_threshold)

                            # Write normalized_gait_cycles to Database, this is done to update the entries with
                            # the correlation to the mean cycle
                            _write_normalized_gait_cycles_to_database(uniform_gait_cycles,
                                                                        gait_cycle_correlations_to_mean_cycle,
                                                                        gait_cycle_correlation_flags, segment_number,
                                                                        connection, cursor)

                            # Retrieve all uniform gait cycles of the current recording and sensor location of
                            # high enough quality
                            gait_cycle_query = '''SELECT * FROM Feature_Uniform_Accelerometer_Gait_Cycle
                                                    WHERE Recording_Id = %s AND Sensor_Location_Id = %s
                                                    AND Activity_Id = %s AND Correlation_To_Mean_Recording > %s'''

                            input_list = [recording_ID, sensor_location_ID, activity_ID, correlation_flag_threshold]
                            input_list = [input for input in input_list if not input == None]
                            input_tuple = tuple(input_list)
                            cursor.execute(gait_cycle_query, input_tuple)
                            uniform_gait_cycles = cursor.fetchall()

                            for feature_frame in feature_frames_list:
                                # Calculate features for each frame and write them to database
                                _extract_statistical_measure_feature(uniform_gait_cycles, feature_frame,
                                                                     connection, cursor)
            # Print progress
            progress_bar.print_progress_bar(counter)

        # Optional Statistics
        print("Extracted features of " + str(counter) + " recordings.")
        print("Total records including sensor locations: " + str(total_counter))
        print("Skipped sensor locations due to missing gait cycles: " + str(skip_no_gait_cycles_extracted))
        print("Skipped sensor locations due to missing frequency peak: " + str(skip_no_frequency_peaks_counter))
        print("Skipped sensor locations due to missing walking activity content: " + str(skip_no_walking_counter))

        _calculate_correlations_of_mean_gait_cycles_within_a_person(connection, cursor)
        _calculate_correlations_of_mean_gait_cycles_within_a_dataset(connection, cursor)
            
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()


## Private Functions --------------------------------
# Note: Most of these functions preprocess the data and then call the basic functions in gait_toolbox.py. 
# The Results are then further processed or written to the database.
def _rotate_data(input_data, cursor):
    """
    Rotate the data from its coordinate system to the world coordinate system.
    Each recording has its owm coordinate system, calculated from the combination of the internal coordinate sytem of
    the used sensor and the way the sensor is placed on the body.

    Args:
        input_data:
            The data to be rotated.
        cursor:
            Cursor to perform database operations

    Returns:
        rotated_accelerometer_sample_list (list):
            The rotated data.
        """
    # Iterate through all data points
    rotated_accelerometer_sample_list = []

    # Get World_Coordinate_System_ID from accelerometer_data
    world_coordinate_system_ID = input_data[0][9]

    # Retrieve rotation matrices by Wold_Coordinate_System_ID
    query = '''SELECT Rotation_To_World_Coordinate_System FROM World_Coordinate_System
                WHERE World_Coordinate_System_ID = %s'''
    cursor.execute(query, (world_coordinate_system_ID,))
    rotation_to_world_coordinate_system_string = cursor.fetchone()[0]

    for accelerometer_sample in input_data:
        # Apply rotation
        rotated_accelerometer_sample = gait_toolbox.apply_rotation_matrix(accelerometer_sample,
                                                                          rotation_to_world_coordinate_system_string)
        # Remove World_Coordinate_System column
        rotated_accelerometer_sample = np.delete(rotated_accelerometer_sample, 9, 0)
        rotated_accelerometer_sample_list.append(rotated_accelerometer_sample)
    return rotated_accelerometer_sample_list

def _upsample_data(input_data, sample_rate, target_sample_rate, segment_number, connection, cursor,
                   return_primary_keys=False):
    """
    Resamples the input_data from a given sample rate to a target sample rate. After resampling the preprocessed
    accelerometer data is saved to the database in the "Pre_Accelerometer" table.
    Args:
        input_data:
            The data to be resampled.
        sample_rate:
            Current sampling rate of the data.
        target_sample_rate:
            The target sampling rate.
        segment_number:
            Segment number within the current recording.
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations

    Returns:
        resampled_data (list):
            The resampled data.
        pre_accelerometer_primary_key_list:
            Primary keys of the new entries created in the "Pre_Accelerometer" table.
        """
    resample_input_array = np.array(input_data)
    if not sample_rate == target_sample_rate:
        resampled_data = (gait_toolbox.resample_accelerometer_data
                          (resample_input_array, sample_rate, target_sample_rate))
    else:
        resampled_data = resample_input_array
    
    # Write each row into database 
    pre_accelerometer_primary_key_list = []
    for resampled_row in resampled_data:
        # Create Pre_Accelerometer entry
        create_add_pre_accelerometer_entry_query = '''INSERT INTO Pre_Accelerometer (X, Y, Z, Time, Recording_ID,
        Segment_Number, Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, Step_Event_ID, Ground_ID)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Pre_Accelerometer_ID'''
        # Execute code to add Pre_Accelerometer table entry
        cursor.execute(create_add_pre_accelerometer_entry_query, (resampled_row[0], resampled_row[1], resampled_row[2],
                                resampled_row[3], resampled_row[4], segment_number, resampled_row[5], resampled_row[6],
                                resampled_row[7], resampled_row[8], resampled_row[9], resampled_row[10]))
        pre_accelerometer_ID = cursor.fetchone()
        pre_accelerometer_primary_key_list.append(pre_accelerometer_ID)
    connection.commit()
    if return_primary_keys:
        return resampled_data, pre_accelerometer_primary_key_list
    else:
        return resampled_data

def _extract_jerk_vector(accelerometer_data_array, filter_window_size, segment_number, connection, cursor):
    """
    Extracts the magnitude of the jerk vector from the given accelerometer data.

    Args:
        accelerometer_data_array:
            The given accelerometer data.
        filter_window_size:
            Length of the moving average filter used to smooth the jerk vector.
        segment_number:
            Segment number within the current recording.
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations

    Returns:
        jerk_vector (list):
            The jerk vector.
        """
    # Extract jerk vector
    jerk_vector = gait_toolbox.extract_jerk_vector(accelerometer_data_array, segment_number, connection, cursor,
                                                   filter_window_size)

    # Remove Step_Event column
    jerk_vector = np.delete(jerk_vector, 7, 1)
    # Remove time column
    jerk_vector = np.delete(jerk_vector, 1, 1)

    return jerk_vector

def _extract_fourier_coefficients(jerk_vector, coefficient_amount, sample_rate, connection, cursor):
    """
    Calculates the Fourier Coefficients from a given jerk vector.

    Args:
        jerk_vector:
            The given jerk vector.
        coefficient_amount:
            The amount of Fourier Coefficients to be calculated and saved.
        sample_rate:
            Sample rate of the data input data.
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations

    Returns:
        jerk_vector (list):
            The jerk vector.
        """
    # Transform in case of list
    jerk_vector = np.array(jerk_vector)
    # Isolate jerk values
    jerk_vector_values = jerk_vector[:, 0]
    jerk_vector_fks = jerk_vector[:, 1:]
    # Number of samples
    input_vector_length = len(jerk_vector_values)
    # Apply Fast Fourier Transform
    fourier_coefficients = fft(jerk_vector_values)

    # Sample spacing (e.g. sample rate: 120Hz
    # -> 120 samples/second -> 120 samples/unit on the frequency x axis -> 1/120 Hz/sample)
    hertz_per_sample = 1.0 / sample_rate
    # Define x-axis and remove redundancy caused by symmetry (// for floor division)
    frequency_axis = fftfreq(input_vector_length, hertz_per_sample)[0:int(input_vector_length//2)]
    # Alter Fourier Coefficients to remove symmerty redundencies and normalize y values
    fourier_coefficients = 2/input_vector_length * abs(fourier_coefficients[0:int(input_vector_length//2)])
    # Calculate sample size of one hertz
    one_hertz_sample_size = len(frequency_axis)/max(frequency_axis)
    # Define check margin to ignore on the left side to avoid fake peaks close to 0
    check_margin = int(one_hertz_sample_size//5)
    # Set check margin to 1 in case of very low input_vector_length
    if check_margin == 0:
        check_margin = 1
    # Calculate maximum value excluding the area left of the check margin
    max_value = max(fourier_coefficients[check_margin:])
    frequency_peaks = []
    value_frequency_peaks = []
    divisor = 2
    while len(frequency_peaks)<5:
        peaks, _ = find_peaks(fourier_coefficients, height=max_value/divisor, distance=3/4*one_hertz_sample_size)
        # Deduce peak frequencies from peak samples
        frequency_peaks = frequency_axis[peaks]
        value_frequency_peaks = fourier_coefficients[peaks]
        divisor+=1

    if len(fourier_coefficients) >= coefficient_amount:
        fourier_coefficients = fourier_coefficients[0:coefficient_amount]
    else:
        missing_coefficients = coefficient_amount - len(fourier_coefficients)
        for i in range(0, missing_coefficients):
            fourier_coefficients.append(np.NaN)
    fourier_coefficients_string = ','.join([str(value) for value in fourier_coefficients])
    frequency_peaks_string = ','.join([str(value) for value in frequency_peaks])
    value_frequency_peaks_string = ','.join([str(value) for value in value_frequency_peaks])
    # Calculate most frequent foreign keys  
    foreign_key_length =  len(jerk_vector_fks[0])
    foreign_key_list = []
    for i in range(0, foreign_key_length):
        frame_foreign_key_column = jerk_vector_fks[:, i]
        most_common_foreign_key = statistics.mode(frame_foreign_key_column)
        foreign_key_list.append(most_common_foreign_key)
    recording_ID = foreign_key_list[0]
    person_ID = foreign_key_list[1]
    sensor_ID = foreign_key_list[2]
    activity_ID = foreign_key_list[3]
    sensor_location_ID = foreign_key_list[4]
    ground_ID = foreign_key_list[5]
    # Create Feature_Fourier_Coefficients entry
    create_add_feature_fourier_coefficients_entry_query = '''INSERT INTO Feature_Fourier_Coefficients
    (Fourier_Coefficients, Length_Signal, Frequency_Peaks, Frequency_Peaks_Values, Recording_ID, Person_ID, Sensor_ID,
    Activity_ID, Sensor_Location_ID, Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

    # Execute code to add Feature_Fourier_Coefficients table entry
    cursor.execute(create_add_feature_fourier_coefficients_entry_query, (fourier_coefficients_string,
                            input_vector_length, frequency_peaks_string, value_frequency_peaks_string, recording_ID,
                            person_ID, sensor_ID, activity_ID, sensor_location_ID, ground_ID))
    connection.commit()

def _extract_gait_cycles(jerk_vector, minima, centered, activity_index, segment_number, connection, cursor):
    """
    Extracts Gait Cycls from a given jerk vector.

    Args:
        jerk_vector:
            The jerk vector.
        minima:
            Index of minima pairs in that jerk vector.
        centered:
            Indication whether the current data is from a centered sensor.
        activity_index:
            Type of activity performed during recording of the data.
        segment_number:
            Segment number within the current recording.
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations

    Returns:
        gait_cycles (list):
            Extracted gait cycles.
        """
    gait_cycles = gait_toolbox.extract_gait_cycles(jerk_vector, minima, centered, activity_index)
    cycle_number = 0
    # Write gait_cycles to database
    for gait_cycle in gait_cycles:
        gait_cycle_string = ','.join([str(value) for value in gait_cycle[0]])
        recording_ID = gait_cycle[1]
        person_ID = gait_cycle[2]
        sensor_ID = gait_cycle[3]
        activity_ID = gait_cycle[4]
        sensor_location_ID = gait_cycle[5]
        ground_ID = gait_cycle[6]
        minimum_index = gait_cycle[7]
        dominant_peak_index = gait_cycle[8]
        non_dominant_peak_index = gait_cycle[9]
        # Create Feature_Accelerometer_Gait_Cycle entry
        create_add_feature_accelerometer_gait_cycle_entry_query = '''INSERT INTO Feature_Accelerometer_Gait_Cycle
        (Cycle, Minimum_Index, Dominant_Peak_Index, Non_Dominant_Peak_Index, Recording_ID, Segment_Number, Cycle_Number,
        Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, Ground_ID)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,%s)'''

        # Execute code to add Feature_Accelerometer_Gait_Cycle table entry
        cursor.execute(create_add_feature_accelerometer_gait_cycle_entry_query, (gait_cycle_string, minimum_index,
                            dominant_peak_index, non_dominant_peak_index, recording_ID, segment_number, cycle_number,
                            person_ID, sensor_ID, activity_ID, sensor_location_ID, ground_ID))

        gait_cycle_values = gait_cycle[0]
        gait_cycle_values = gait_toolbox.normalize(gait_cycle_values)
        gait_cycle[0] = gait_cycle_values
        gait_cycle_string = ','.join([str(value) for value in gait_cycle_values])

        # Create Feature_Y_Normalized_Accelerometer_Gait_Cycle entry
        create_add_feature_y_normalized_accelerometer_gait_cycle_entry_query ='''INSERT INTO
        Feature_Y_Normalized_Accelerometer_Gait_Cycle (Cycle, Minimum_Index, Dominant_Peak_Index,
        Non_Dominant_Peak_Index, Recording_ID, Segment_Number, Cycle_Number, Person_ID, Sensor_ID, Activity_ID,
        Sensor_Location_ID, Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

        # Execute code to add Feature_Y_Normalized_Accelerometer_Gait_Cycle table entry
        cursor.execute(create_add_feature_y_normalized_accelerometer_gait_cycle_entry_query, (gait_cycle_string,
                                        minimum_index, dominant_peak_index, non_dominant_peak_index, recording_ID,
                                        segment_number, cycle_number, person_ID, sensor_ID, activity_ID,
                                        sensor_location_ID, ground_ID))

        cycle_number+=1

    connection.commit()
    return gait_cycles

def _normalize_gait_cycles(gait_cycles, normalize_target_cycle_length):
    """
    Normalizes the gait cycle data to a specific amount of samples.

    Args:
        gait_cycles:
            Gait cycles to be normalized.
        normalize_target_cycle_length:
            Amount of samples the gait cycles will be normalized to.
    Returns:
        normalized_gait_cycles (list):
            Normalized gait cycles.
        """
    normalized_gait_cycles = []
    for gait_cycle in gait_cycles:
        gait_cycle_values = gait_cycle[0]
        gait_cycle[7] = round(gait_cycle[7]/len(gait_cycle[0])*200)
        gait_cycle[8] = round(gait_cycle[8]/len(gait_cycle[0])*200)
        gait_cycle[9] = round(gait_cycle[9]/len(gait_cycle[0])*200)
        normalized_gait_cycle = gait_toolbox.normalize_gait_cycle_length(gait_cycle_values,
                                                                         normalize_target_cycle_length)
        gait_cycle[0] = normalized_gait_cycle
        normalized_gait_cycles.append(gait_cycle)
    return normalized_gait_cycles

def _calculate_mean_gait_cycle(gait_cycles):
    """
    Normalizes the gait cycle data to a specific amount of samples.

    Args:
        gait_cycles:
            Gait cycles from which mean will be calculated.

    Returns:
        mean_gait_cycle:
            Mean gait cycle.
        """
    gait_cycles = np.array(gait_cycles, dtype=object)
    gait_cycles_values = gait_cycles[:, 1:201]
    mean_gait_cycle = gait_toolbox.calculate_mean_gait_cycle(gait_cycles_values)
    return mean_gait_cycle

def _calculate_gait_cycle_correlations_to_mean_cycle(gait_cycles, mean_cycle):
    """
    Calculated correlation of the individual gait cycles to their mean.

    Args:
        gait_cycles:
            Individual Gait cycles.
        mean_gait_cycle:
            Mean gait cycle.

    Returns:
        correlation_list (list):
            Correlation Coefficients of the individual gait cycles to their mean.
        """
    correlation_list = []
    gait_cycles = np.array(gait_cycles, dtype=object)
    gait_cycles_values = gait_cycles[:, 1:201]
    for gait_cycle in gait_cycles_values:
        if np.all(gait_cycle == gait_cycle[0]):
            correlation = None
        else:
            correlation, _ = pearsonr(gait_cycle, mean_cycle)
        correlation_list.append(correlation)
    return correlation_list

def _calculate_gait_cycle_correlation_flags(correlations, threshold):
    """
    Checks if correlations are above a given threshold.

    Args:
        correlations (list):
            Correlations
        threshold:
            Value of the threshold against which the individual correlations will be checked.

    Returns:
        flag_list (list):
            Indications of whether the gait cycles were below of above the threshold.
        """
    flag_list = []
    for correlation in correlations:
        if not correlation:
            flag = None
        elif correlation > threshold:
            flag = True
        else:
            flag = False
        flag_list.append(flag)
    return flag_list

def _write_mean_gait_cycle_to_database(mean_gait_cycle, amount_gait_cycles, gait_cycle, connection, cursor):
    """
    Saves the mean gait cycles to the database.

    Args:
        mean_gait_cycle:
            The mean gait cycle to be saved.
        amount_gait_cycles:
            Amount of gait cycles the mean was calculated from.
        gait_cycle:
            One of the gait cycles from which the mean was calculated from, to gain information about the foreign
            keys to be saved.
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations
        """
    recording_ID = gait_cycle[1]
    person_ID = gait_cycle[2]
    sensor_ID = gait_cycle[3]
    activity_ID = gait_cycle[4]
    sensor_location_ID = gait_cycle[5]
    ground_ID = gait_cycle[6]

    # Create Feature_Mean_Accelerometer_Gait_Cycle entry
    create_add_feature_mean_accelerometer_gait_cycle_entry_query = '''INSERT INTO Feature_Mean_Accelerometer_Gait_Cycle
    ('''

    for i in range(200):
        create_add_feature_mean_accelerometer_gait_cycle_entry_query += "value_" + str(i) + ","

    create_add_feature_mean_accelerometer_gait_cycle_entry_query += '''Amount_Gait_Cycles, Recording_ID, Person_ID,
    Sensor_ID, Activity_ID, Sensor_Location_ID, Ground_ID) VALUES ('''

    for i in range(206):
        create_add_feature_mean_accelerometer_gait_cycle_entry_query += "%s, "
    create_add_feature_mean_accelerometer_gait_cycle_entry_query += "%s)"


    # Execute code to add Feature_Mean_Accelerometer_Gait_Cycle table entry
    cursor.execute(create_add_feature_mean_accelerometer_gait_cycle_entry_query, (*mean_gait_cycle, amount_gait_cycles,
                                    recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID, ground_ID))
    connection.commit()

def _write_normalized_gait_cycles_to_database(normalized_gait_cycles, correlations, flags, segment_number,
                                              connection, cursor):
    """
    Saves the normalized gait cycles to the database.

    Args:
        normalized_gait_cycles (list):
            Normalized gait cycles.
        correlations (list):
            Individual correlation coefficients to the mean gait cycle of all the current cycles.
        flags (list):
            Indication whether the current gait cycles have a correlations with the mean gait cycle above
            a given threshold.
        segment_number:
            Segment number within the current recording.
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations
        """
    if not correlations:
        cycle_number = 0
        for index, gait_cycle in enumerate(normalized_gait_cycles):
            recording_ID = gait_cycle[1]
            person_ID = gait_cycle[2]
            sensor_ID = gait_cycle[3]
            activity_ID = gait_cycle[4]
            sensor_location_ID = gait_cycle[5]
            ground_ID = gait_cycle[6]
            minimum_index = gait_cycle[7]
            dominant_peak_index = gait_cycle[8]
            non_dominant_peak_index = gait_cycle[9]

            # Create Feature_Uniform_Accelerometer_Gait_Cycle entry
            create_add_feature_uniform_accelerometer_gait_cycle_entry_query = '''INSERT INTO
            Feature_Uniform_Accelerometer_Gait_Cycle ('''

            for i in range(200):
                create_add_feature_uniform_accelerometer_gait_cycle_entry_query += "Value_" + str(i)+","

            create_add_feature_uniform_accelerometer_gait_cycle_entry_query += '''Minimum_Index, Dominant_Peak_Index,
            Non_Dominant_Peak_Index, Recording_ID, Segment_Number, Cycle_Number, Person_ID, Sensor_ID, Activity_ID,
            Sensor_Location_ID, Ground_ID) VALUES ('''

            for i in range(210):
                create_add_feature_uniform_accelerometer_gait_cycle_entry_query += "%s, "
            create_add_feature_uniform_accelerometer_gait_cycle_entry_query += "%s)"

            # Execute code to add Feature_Uniform_Accelerometer_Gait_Cycle table entry
            cursor.execute(create_add_feature_uniform_accelerometer_gait_cycle_entry_query, (*gait_cycle[0],
                                            minimum_index, dominant_peak_index, non_dominant_peak_index, recording_ID,
                                            segment_number, cycle_number, person_ID, sensor_ID, activity_ID,
                                            sensor_location_ID, ground_ID))
            cycle_number+= 1
        connection.commit()
    else:
        for index, gait_cycle in enumerate(normalized_gait_cycles):
            # Update uniform gait cycle entry with correlation information
            update_uniform_gait_cycle_query = '''UPDATE Feature_Uniform_Accelerometer_Gait_Cycle
            SET Correlation_To_Mean_Recording = %s, Usable_Flag = %s
            WHERE Feature_Uniform_Accelerometer_Gait_Cycle_ID = %s'''

            cursor.execute(update_uniform_gait_cycle_query, (correlations[index], flags[index], gait_cycle[0]))
            connection.commit()

def _write_extrema_events_to_database(accelerometer_data, pre_accelerometer_primary_keys, jerk_vector, dominant_peaks,
                                      non_dominant_peaks, minima, centered, connection, cursor):
    """
    Args:
        accelerometer_data:
            Accelerometer data to be processed.
        pre_accelerometer_primary_keys (list):
            Primary keys of the entries in the "pre-Accelerometer" table for the current accelerometer data.
        jerk_vector:
            Jerk vector, that was calculated from the accelerometer data.
        dominant_peaks:
            Index of dominant peaks.
        non_dominant_peaks:
            Index of non-dominant peaks.
        minima:
            Index of minima pairs in that jerk vector.
        centered:
            Indication whether the current data is from a centered sensor.
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations
        """
    #accelerometer data and jerk vector might differ in length because of the moving average filter
    #this needs to be taken into account when using the indices for (non)-dominant peaks and minima.
    nan_amount = (len(accelerometer_data)-len(jerk_vector))
    cycle_start_minima = []
    dominant_peaks = np.array(dominant_peaks)
    dominant_peaks = dominant_peaks + nan_amount
    minima = np.array(minima)
    minima = minima + nan_amount
    # Extract second minimum from each minima pair if sensor is not centered
    # Transform minima pairs list to single minima list
    if not centered:
        non_dominant_peaks = np.array(non_dominant_peaks)
        non_dominant_peaks = non_dominant_peaks + nan_amount
        minima_temp = []
        for minima_pair in minima:
            cycle_start_minima.append(minima_pair[1])
            minima_temp.append(minima_pair[0])
            minima_temp.append(minima_pair[1])
        minima = minima_temp
    else:
        cycle_start_minima = minima
        cycle_start_minima = cycle_start_minima[1:]
        cycle_start_minima = cycle_start_minima[::2]

    for index, accelerometer_row in enumerate(accelerometer_data):
        # Introduce variable for tracking if an event was already applied
        event_found = False
        # Introduce variable for the cycle the current row is in
        correct_cycle_index = None
        # Figure out which gait cycle the accelerometer_row belongs to
        for i, minimum in enumerate(cycle_start_minima):
            if not minimum == cycle_start_minima[-1] and minimum < cycle_start_minima[i+1]:
                if index >= minimum and index < cycle_start_minima[i+1]:
                    correct_cycle_index = i
                    break

        correct_correlation_value = None
        correct_flag = None
        # check dominant peaks
        if index in dominant_peaks:
            detected_event_ID = 1
            detected_event_title = mapping.get_detected_event_title(detected_event_ID)
            event_found = True
            current_step_event_ID = accelerometer_row[9]
            # Get info on current Step_Event
            query = '''SELECT Ground_Truth_Event_ID, Ground_Truth_Event_Title, Ground_Truth_Order_Flag,
            Ground_Truth_Step_Number FROM Step_Event WHERE Step_Event_ID = %s'''
            cursor.execute(query, (current_step_event_ID,))
            current_step_event_info = cursor.fetchone()
            # Check if Step_Event with detected events already exists
            check_for_step_event_query = '''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID = %s AND
            Ground_Truth_Order_Flag = %s AND Ground_Truth_Step_Number = %s AND Detected_Event_ID = %s AND
            Detected_Event_Reliability = %s AND Detected_Event_Reliable_Flag = %s'''
            input_list = [current_step_event_info[0], current_step_event_info[2], current_step_event_info[3],
                          detected_event_ID, correct_correlation_value, correct_flag]
            if current_step_event_info[0] == None:
                check_for_step_event_query = (check_for_step_event_query.
                     replace("Ground_Truth_Event_ID = %s", "Ground_Truth_Event_ID IS NULL"))
            if current_step_event_info[2] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Order_Flag = %s", "Ground_Truth_Order_Flag IS NULL"))
            if current_step_event_info[3] == None:
                check_for_step_event_query = (check_for_step_event_query.
                      replace("Ground_Truth_Step_Number = %s", "Ground_Truth_Step_Number IS NULL"))
            if correct_correlation_value == None:
                check_for_step_event_query = (check_for_step_event_query.
                     replace("Detected_Event_Reliability = %s", "Detected_Event_Reliability IS NULL"))
            if correct_flag == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Detected_Event_Reliable_Flag = %s", "Detected_Event_Reliable_Flag IS NULL"))
            input_list = [input for input in input_list if not input == None]
            input_tuple = tuple(input_list)
            cursor.execute(check_for_step_event_query, input_tuple)
            step_event_ID = cursor.fetchone()
            if step_event_ID:
                step_event_ID = step_event_ID[0]
            # If not, create new Step_Event entry
            else:
                create_new_step_event_query = '''INSERT INTO Step_Event (Ground_Truth_Event_ID,
                Ground_Truth_Event_Title, Ground_Truth_Order_Flag, Ground_Truth_Step_Number, Detected_Event_ID,
                Detected_Event_Title, Detected_Event_Reliability, Detected_Event_Reliable_Flag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING Step_Event_ID'''

                cursor.execute(create_new_step_event_query, (current_step_event_info[0], current_step_event_info[1],
                                                             current_step_event_info[2], current_step_event_info[3],
                                                             detected_event_ID, detected_event_title,
                                                             correct_correlation_value, correct_flag))
                step_event_ID = cursor.fetchone()[0]
            # Update accelerometer entry with new Step_Event_ID
            update_accelerometer_row_query = '''UPDATE Pre_Accelerometer SET Step_Event_ID = %s
                                                WHERE Pre_Accelerometer_ID = %s'''
            test = pre_accelerometer_primary_keys[index]
            cursor.execute(update_accelerometer_row_query, (step_event_ID, pre_accelerometer_primary_keys[index]))
            connection.commit()
        # check non_dominant_peaks if sensor is not centered
        elif not centered and index in non_dominant_peaks:
            detected_event_ID = 2
            detected_event_title = mapping.get_detected_event_title(detected_event_ID)
            event_found = True
            current_step_event_ID = accelerometer_row[9]
            # Get info on current Step_Event
            query = '''SELECT Ground_Truth_Event_ID, Ground_Truth_Event_Title, Ground_Truth_Order_Flag,
                        Ground_Truth_Step_Number FROM Step_Event WHERE Step_Event_ID = %s'''
            cursor.execute(query, (current_step_event_ID,))
            current_step_event_info = cursor.fetchone()
            # Check if Step_Event with detected events already exists
            check_for_step_event_query = '''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID = %s AND
            Ground_Truth_Order_Flag = %s AND Ground_Truth_Step_Number = %s AND Detected_Event_ID = %s AND
            Detected_Event_Reliability = %s AND Detected_Event_Reliable_Flag = %s'''

            input_list = [current_step_event_info[0], current_step_event_info[2], current_step_event_info[3],
                          detected_event_ID, correct_correlation_value, correct_flag]
            if current_step_event_info[0] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Event_ID = %s", "Ground_Truth_Event_ID IS NULL"))
            if current_step_event_info[2] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Order_Flag = %s", "Ground_Truth_Order_Flag IS NULL"))
            if current_step_event_info[3] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Step_Number = %s", "Ground_Truth_Step_Number IS NULL"))
            if correct_correlation_value == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Detected_Event_Reliability = %s", "Detected_Event_Reliability IS NULL"))
            if correct_flag == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Detected_Event_Reliable_Flag = %s", "Detected_Event_Reliable_Flag IS NULL"))
            input_list = [input for input in input_list if not input == None]
            input_tuple = tuple(input_list)
            cursor.execute(check_for_step_event_query, input_tuple)
            step_event_ID = cursor.fetchone()
            if step_event_ID:
                step_event_ID = step_event_ID[0]
            # If not, create new Step_Event entry
            else:
                create_new_step_event_query = '''INSERT INTO Step_Event (Ground_Truth_Event_ID,
                Ground_Truth_Event_Title, Ground_Truth_Order_Flag, Ground_Truth_Step_Number, Detected_Event_ID,
                Detected_Event_Title, Detected_Event_Reliability, Detected_Event_Reliable_Flag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING Step_Event_ID'''
                cursor.execute(create_new_step_event_query, (current_step_event_info[0], current_step_event_info[1],
                                            current_step_event_info[2], current_step_event_info[3], detected_event_ID,
                                            detected_event_title, correct_correlation_value, correct_flag))
                step_event_ID = cursor.fetchone()[0]
            # Update accelerometer entry with new Step_Event_ID
            update_accelerometer_row_query = '''UPDATE Pre_Accelerometer SET Step_Event_ID = %s
                                                WHERE Pre_Accelerometer_ID = %s'''
            cursor.execute(update_accelerometer_row_query, (step_event_ID, pre_accelerometer_primary_keys[index]))
            connection.commit()
        # check minima
        elif index in minima:
            detected_event_ID = 3
            detected_event_title = mapping.get_detected_event_title(detected_event_ID)
            event_found = True
            current_step_event_ID = accelerometer_row[9]
            # Get info on current Step_Event
            query = '''SELECT Ground_Truth_Event_ID, Ground_Truth_Event_Title, Ground_Truth_Order_Flag,
                        Ground_Truth_Step_Number FROM Step_Event WHERE Step_Event_ID = %s'''
            cursor.execute(query, (current_step_event_ID,))
            current_step_event_info = cursor.fetchone()
            # Check if Step_Event with detected events already exists
            check_for_step_event_query = '''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID = %s
            AND Ground_Truth_Order_Flag = %s AND Ground_Truth_Step_Number = %s AND Detected_Event_ID = %s AND
            Detected_Event_Reliability = %s AND Detected_Event_Reliable_Flag = %s'''

            input_list = [current_step_event_info[0], current_step_event_info[2], current_step_event_info[3],
                          detected_event_ID, correct_correlation_value, correct_flag]
            if current_step_event_info[0] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Event_ID = %s", "Ground_Truth_Event_ID IS NULL"))
            if current_step_event_info[2] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Order_Flag = %s", "Ground_Truth_Order_Flag IS NULL"))
            if current_step_event_info[3] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Step_Number = %s", "Ground_Truth_Step_Number IS NULL"))
            if correct_correlation_value == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Detected_Event_Reliability = %s", "Detected_Event_Reliability IS NULL"))
            if correct_flag == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Detected_Event_Reliable_Flag = %s", "Detected_Event_Reliable_Flag IS NULL"))
            input_list = [input for input in input_list if not input == None]
            input_tuple = tuple(input_list)
            cursor.execute(check_for_step_event_query, input_tuple)
            step_event_ID = cursor.fetchone()
            if step_event_ID:
                step_event_ID = step_event_ID[0]
            # If not, create new Step_Event entry
            else:
                create_new_step_event_query = '''INSERT INTO Step_Event (Ground_Truth_Event_ID,
                Ground_Truth_Event_Title, Ground_Truth_Order_Flag, Ground_Truth_Step_Number, Detected_Event_ID,
                Detected_Event_Title, Detected_Event_Reliability, Detected_Event_Reliable_Flag)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING Step_Event_ID'''

                cursor.execute(create_new_step_event_query, (current_step_event_info[0], current_step_event_info[1],
                                            current_step_event_info[2], current_step_event_info[3], detected_event_ID,
                                            detected_event_title, correct_correlation_value, correct_flag))
                step_event_ID = cursor.fetchone()[0]
            # Update accelerometer entry with new Step_Event_ID
            update_accelerometer_row_query = '''UPDATE Pre_Accelerometer SET Step_Event_ID = %s
                                                WHERE Pre_Accelerometer_ID = %s'''
            cursor.execute(update_accelerometer_row_query, (step_event_ID, pre_accelerometer_primary_keys[index]))
            connection.commit()
        elif not event_found:
            detected_event_ID = 0
            detected_event_title = mapping.get_detected_event_title(detected_event_ID)
            current_step_event_ID = accelerometer_row[9]
            # Get info on current Step_Event
            query = '''SELECT Ground_Truth_Event_ID, Ground_Truth_Event_Title, Ground_Truth_Order_Flag,
                        Ground_Truth_Step_Number FROM Step_Event WHERE Step_Event_ID = %s'''
            cursor.execute(query, (current_step_event_ID,))
            current_step_event_info = cursor.fetchone()
            # Check if Step_Event with detected events already exists
            check_for_step_event_query = '''SELECT Step_Event_ID FROM Step_Event WHERE Ground_Truth_Event_ID = %s
            AND Ground_Truth_Order_Flag = %s AND Ground_Truth_Step_Number = %s AND Detected_Event_ID = %s'''

            input_list = [current_step_event_info[0], current_step_event_info[2], current_step_event_info[3],
                          detected_event_ID]
            if current_step_event_info[0] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Event_ID = %s", "Ground_Truth_Event_ID IS NULL"))
            if current_step_event_info[2] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Order_Flag = %s", "Ground_Truth_Order_Flag IS NULL"))
            if current_step_event_info[3] == None:
                check_for_step_event_query = (check_for_step_event_query.
                    replace("Ground_Truth_Step_Number = %s", "Ground_Truth_Step_Number IS NULL"))
            input_list = [input for input in input_list if not input == None]
            input_tuple = tuple(input_list)
            cursor.execute(check_for_step_event_query, input_tuple)
            step_event_ID = cursor.fetchone()
            if step_event_ID:
                step_event_ID = step_event_ID[0]
            # If not, create new Step_Event entry
            else:
                create_new_step_event_query = '''INSERT INTO Step_Event (Ground_Truth_Event_ID,
                Ground_Truth_Event_Title, Ground_Truth_Order_Flag, Ground_Truth_Step_Number, Detected_Event_ID,
                Detected_Event_Title) VALUES (%s, %s, %s, %s, %s, %s) RETURNING Step_Event_ID'''

                cursor.execute(create_new_step_event_query, (current_step_event_info[0], current_step_event_info[1],
                                                             current_step_event_info[2], current_step_event_info[3],
                                                             detected_event_ID, detected_event_title))
                step_event_ID = cursor.fetchone()[0]
            # Update accelerometer entry with new Step_Event_ID
            update_accelerometer_row_query = '''UPDATE Pre_Accelerometer SET Step_Event_ID = %s
                                                WHERE Pre_Accelerometer_ID = %s'''
            cursor.execute(update_accelerometer_row_query, (step_event_ID, pre_accelerometer_primary_keys[index]))
            connection.commit()
def _extract_statistical_measure_feature(all_gait_cycles, feature_frame_size, connection, cursor):
    """

    Args:
        all_gait_cycles:

        feature_frame_size:

        connection:
            Database connection.
        cursor:
            Cursor to perform database operations
        """
    if len(all_gait_cycles)>feature_frame_size:
        #randmly shuffle gait cycles
        np.random.shuffle(all_gait_cycles)

        # Calculate the number of arrays of feature_frame_size you can create
        num_arrays = len(all_gait_cycles) // feature_frame_size

        # Split the original array into arrays of feature_frame_size
        cycle_array_with_feature_frame_size = np.array_split(all_gait_cycles[:num_arrays * feature_frame_size],
                                                             num_arrays)

        for index in range(0, num_arrays):
            current_gait_cycles = cycle_array_with_feature_frame_size[index]

            # Calculate features
            feature_value_M_DP = gait_toolbox.extract_feature_M_DP(current_gait_cycles)
            feature_value_SD_DP = gait_toolbox.extract_feature_SD_DP(current_gait_cycles)

            feature_value_R_M_DNP = gait_toolbox.extract_feature_R_M_DNP(current_gait_cycles)
            feature_value_R_SD_DNP = gait_toolbox.extract_feature_R_SD_DNP(current_gait_cycles)

            feature_value_M_SD_DS = gait_toolbox.extract_feature_M_SD_DS(current_gait_cycles)
            feature_value_R_M_SD_DNS = gait_toolbox.extract_feature_R_M_SD_DNS(current_gait_cycles)

            feature_value_SD_SD_DS = gait_toolbox.extract_feature_SD_SD_DS(current_gait_cycles)
            feature_value_R_SD_SD_DNS = gait_toolbox.extract_feature_R_SD_SD_DNS(current_gait_cycles)

            feature_value_R_M_SL = gait_toolbox.extract_feature_R_M_SL(current_gait_cycles)
            feature_value_R_SD_SL = gait_toolbox.extract_feature_R_SD_SL(current_gait_cycles)

            foreign_key_length = len(current_gait_cycles[0]) - 210
            foreign_key_list = []
            frame_sub_segment_fks = current_gait_cycles[:, 208:]

            frame_sub_segment_fks = np.delete(frame_sub_segment_fks, 1, 1)
            frame_sub_segment_fks = np.delete(frame_sub_segment_fks, 1, 1)

            for i in range(0, foreign_key_length):
                frame_foreign_key_column = frame_sub_segment_fks[:, i]
                most_common_foreign_key = statistics.mode(frame_foreign_key_column)
                foreign_key_list.append(most_common_foreign_key)
            recording_ID = foreign_key_list[0]
            person_ID = foreign_key_list[1]
            sensor_ID = foreign_key_list[2]
            activity_ID = foreign_key_list[3]
            sensor_location_ID = foreign_key_list[4]
            ground_ID = foreign_key_list[5]

            # Create Feature_Statistical_Measure entry
            #  create_add_feature_statistical_measure_entry_query = f'''INSERT INTO Feature_Statistical_Measure_{str(feature_frame_size)} (Feature_Value, Recording_ID, Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, Ground_ID) VALUES (%s, %s, %s, %s, %s, %s, %s)'''
            create_add_feature_statistical_measure_entry_query = f'''INSERT INTO Feature_Statistical_Measure_
            {str(feature_frame_size)} (M_DP_Value, SD_DP_Value, R_M_DNP_Value, R_SD_DNP_Value, M_SD_DS_Value,
            R_M_SD_DNS_Value, SD_SD_DS_Value, R_SD_SD_DNS_Value, R_M_SL_Value, R_SD_SL_Value, Recording_ID, Person_ID,
            Sensor_ID, Activity_ID, Sensor_Location_ID, Ground_ID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

            # Execute code to add Feature_Statistical_Measure table entry
            cursor.execute(create_add_feature_statistical_measure_entry_query, (
            feature_value_M_DP, feature_value_SD_DP, feature_value_R_M_DNP, feature_value_R_SD_DNP,
            feature_value_M_SD_DS, feature_value_R_M_SD_DNS, feature_value_SD_SD_DS, feature_value_R_SD_SD_DNS,
            feature_value_R_M_SL, feature_value_R_SD_SL, recording_ID, person_ID, sensor_ID, activity_ID,
            sensor_location_ID, ground_ID))
        connection.commit()

def _calculate_correlations_of_mean_gait_cycles_within_a_person(connection, cursor):
    """
    Calculates correlations of each gait cycle of every individual person with the mean gait cycle of that person.
    Args:
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations
        """
    print("Calculating gait cycle correlations in comparison to mean of each person.")
    # Retrieve all person_IDs
    query = '''SELECT Person_ID FROM Person'''
    cursor.execute(query)
    person_IDs = cursor.fetchall()

    counter = 0
    progress_bar = ProgressBar(total=len(person_IDs), prefix="Correlations within a Person: ", decimals=2, length=50,
                               fill='X', zfill='-')
    for person_ID_tuple in person_IDs:
        # Increase progress counter
        counter += 1

        person_ID = person_ID_tuple[0]

        # Retrieve relevant sensor_location_IDs
        query = '''SELECT DISTINCT Sensor_Location_ID FROM Feature_Uniform_Accelerometer_Gait_Cycle
                    WHERE Person_ID = %s'''
        cursor.execute(query, (person_ID,))
        sensor_location_IDs = cursor.fetchall()
        # Sensor_location loop
        for sensor_location_ID in sensor_location_IDs:
            # Retrieve all uniform gait cycles of the current recording and sensor location
            gait_cycle_query = '''SELECT * FROM Feature_Uniform_Accelerometer_Gait_Cycle WHERE Sensor_Location_Id = %s
                                    and Activity_Id = %s and Person_Id = %s'''

            input_list = [sensor_location_ID, 1, person_ID]
            input_list = [input for input in input_list if not input == None]
            input_tuple = tuple(input_list)
            cursor.execute(gait_cycle_query, input_tuple)
            uniform_gait_cycles = cursor.fetchall()

            if len(uniform_gait_cycles) == 0:
                continue

            # Calculate mean gait cycle
            mean_gait_cycle = _calculate_mean_gait_cycle(uniform_gait_cycles)

            mean_gait_cycle = np.array(mean_gait_cycle)

            #values_cycle = mean_gait_cycle
            #x = np.linspace(0, len(values_cycle) - 1, len(values_cycle))
            #plt.plot(x, values_cycle, 'b-')
            #plt.show()

            # Calculate correlations to mean cycle
            correlations = _calculate_gait_cycle_correlations_to_mean_cycle(
                uniform_gait_cycles, mean_gait_cycle)

            for index, gait_cycle in enumerate(uniform_gait_cycles):
                # Update uniform gait cycle entry with correlation information
                update_uniform_gait_cycle_query = '''UPDATE Feature_Uniform_Accelerometer_Gait_Cycle SET
                            Correlation_To_Mean_Person = %s WHERE Feature_Uniform_Accelerometer_Gait_Cycle_ID = %s'''
                cursor.execute(update_uniform_gait_cycle_query, (correlations[index], gait_cycle[0]))
                connection.commit()
        progress_bar.print_progress_bar(counter)

def _calculate_correlations_of_mean_gait_cycles_within_a_dataset(connection, cursor):
    """
    Calculates correlations of each gait cycle with the mean gait cycle of the corresponding dataset.
    Args:
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations
        """
    print("Calculating gait cycle correlations in comparison to mean of each databset.")
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))
    activities_list = os.getenv("ACTIVITIES_LIST", "").split(",")
    # Retrieve all person_IDs
    query = '''SELECT Distinct Dataset_ID FROM Recording'''
    cursor.execute(query)
    dataset_IDs = cursor.fetchall()

    counter = 0
    progress_bar = ProgressBar(total=len(dataset_IDs), prefix="Correlations within a dataset: ",
                               decimals=2, length=50, fill='X', zfill='-')
    for dataset_ID_tuple in dataset_IDs:
        # Increase progress counter
        counter += 1

        dataset_ID = dataset_ID_tuple[0]


        # Retrieve relevant sensor_location_IDs
        query = '''SELECT Distinct sensor_location_id FROM feature_uniform_accelerometer_gait_cycle
        INNER JOIN recording ON feature_uniform_accelerometer_gait_cycle.Recording_Id=recording.Recording_Id
        WHERE Dataset_Id = %s'''

        cursor.execute(query, (dataset_ID,))
        sensor_location_IDs = cursor.fetchall()
        # Sensor_location loop
        for sensor_location_ID in sensor_location_IDs:
            for activity_ID in activities_list:
                # Retrieve all uniform gait cycles of the current recording and sensor location
                gait_cycle_query = '''SELECT * FROM Feature_Uniform_Accelerometer_Gait_Cycle INNER JOIN Recording ON
                Feature_Uniform_Accelerometer_Gait_Cycle.Recording_Id=Recording.Recording_Id WHERE Sensor_Location_Id = %s
                and Activity_Id = %s and Dataset_Id = %s'''

                input_list = [sensor_location_ID, activity_ID, dataset_ID]
                input_list = [input for input in input_list if not input == None]
                input_tuple = tuple(input_list)
                cursor.execute(gait_cycle_query, input_tuple)
                uniform_gait_cycles = cursor.fetchall()

                if len(uniform_gait_cycles) == 0:
                    continue

                # Calculate mean gait cycle
                mean_gait_cycle = _calculate_mean_gait_cycle(uniform_gait_cycles)

                mean_gait_cycle = np.array(mean_gait_cycle)


                # Calculate correlations to mean cycle
                correlations = _calculate_gait_cycle_correlations_to_mean_cycle(
                    uniform_gait_cycles, mean_gait_cycle)

                for index, gait_cycle in enumerate(uniform_gait_cycles):
                    # Update uniform gait cycle entry with correlation information
                    update_uniform_gait_cycle_query = '''UPDATE Feature_Uniform_Accelerometer_Gait_Cycle SET
                    Correlation_To_Mean_Dataset = %s WHERE Feature_Uniform_Accelerometer_Gait_Cycle_ID = %s'''

                    cursor.execute(update_uniform_gait_cycle_query, (correlations[index], gait_cycle[0]))
                    connection.commit()
        progress_bar.print_progress_bar(counter)
            

if __name__ == '__main__':
    extract_gait_features()