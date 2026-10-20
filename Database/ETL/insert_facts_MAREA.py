"""
This module contains functions to load the fact data from MAREA dataset into the harmonized database.
"""
import os
import psycopg2
import numpy as np
import pandas as pd
import scipy.io
from console_progressbar import ProgressBar
from dotenv import load_dotenv
from psycopg2 import Error
import Database.ETL.database_id_mapping as mapping


def insert_facts():
    
    ## GLOBAL META DATA

    # define Recording.Dataset_ID
    dataset_id = 2

    # Deduce Recording.Dataset_Title
    dataset_title = mapping.get_dataset_title(dataset_id)

    # define globaly static dimension IDs and attributes
    repetition = 0
    sensor_ID = 14

    sample_rate = 128
    year = None
    month = None
    day = None
    starting_time = None

    # define dictionary to later add multiple sensors to the same recording
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
        path_to_data = '../Data/02_MAREA/Subject_Data_txt_format/'
        path_to_activity_timestamps = '../Data/02_MAREA/Activity_Timings/'
        
        # Get ground truth array for later use
        ground_truth_array = _get_ground_truth_array()

        # Progress Bar
        counter = 0
        number_of_files = len(os.listdir(path_to_data))
        progress_bar = ProgressBar(total=number_of_files-1, prefix="MAREA Progress: ", decimals=2, length=50, fill='X',
                                   zfill='-')

        # Extract activity timestamps from csv files
        indoor_activity_timestamps = pd.read_csv(path_to_activity_timestamps + 'Indoor_Experiment_Timings.txt',
                                                 header=None)
        outdoor_activity_timestamps = pd.read_csv(path_to_activity_timestamps + 'Outdoor_Experiment_Timings.txt',
                                                  header=None)

        # Iterate over all files
        for filename in os.listdir(path_to_data):

            # Display progress bar update
            progress_bar.print_progress_bar(counter)
            # Count up progress
            counter = counter + 1

            # Read data
            data = pd.read_csv(path_to_data + filename)
            
            # Extract subject_ID from file name, length varies due to 1) subject_ID being
            # either single- or double-digit, 2) sensor location string
            if len(filename) == 11 or len(filename) == 14:
                subject_ID = filename[3:4]
            elif len(filename) == 12 or len(filename) == 15:
                subject_ID = filename[3:5]
            # Get global person_ID by local subject_ID
            person_ID = mapping.get_global_person_id_marea(int(subject_ID))

            # Define sensor_location_ID and world_coordinate_system_ID depending
            # on sensor location string in the file name
            if "LF" in filename:
                sensor_location_ID = 21
                world_coordinate_system_ID = 12
            elif "RF" in filename:
                sensor_location_ID = 20
                world_coordinate_system_ID = 13
            elif "Waist" in filename:
                sensor_location_ID = 19
                world_coordinate_system_ID = 4
            elif "Wrist" in filename:
                sensor_location_ID = 18
                world_coordinate_system_ID = 12

            # Calculate signal length
            duration = int(len(data)/sample_rate) * 1000

            # Since every subject only has one big recording, check if the subject already had a recording_ID created
            # and if not, create it and add it to a dictionary.
            if not recording_dictionary.get(int(subject_ID)):
                # create Recording entry
                # SQL query to add the recording
                create_add_record_query = '''INSERT INTO Recording (Year, Month, Day, Starting_Time, Duration,
                Dataset_ID, Dataset_Title, Repetition, Sample_Frequency)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING Recording_ID'''
                cursor.execute(create_add_record_query, (year, month, day, starting_time, duration, dataset_id,
                                                         dataset_title, repetition, sample_rate))
                recording_ID = cursor.fetchone()[0]
                connection.commit()
                # Update the dictionary with the created recording_ID
                recording_dictionary.update({int(subject_ID): recording_ID})
            # Else, use the recording_ID in the dictionary
            else:
                recording_ID = recording_dictionary[int(subject_ID)]

            # Detect outdoor recordings by subject_ID and extract the corresponding activity samples
            if int(subject_ID) > 11:
                outdoor_activity_sample_stamps_for_subject = (
                                                        outdoor_activity_timestamps.iloc)[int(subject_ID) % 11 - 1, :]
            else:
                indoor_activity_sample_stamps_for_subject = (
                                                        indoor_activity_timestamps.iloc)[int(subject_ID) % 11 - 1, :]
            
            # Add step counter for the ground truth later on
            step_number = 0

            # Iterate through every data row
            for row_idx in range(0, len(data)):
                # For outdoor recordings
                if int(subject_ID) > 11:
                    # Define ground_ID
                    ground_ID = 6
                    # Outdoor Walk
                    if row_idx < outdoor_activity_sample_stamps_for_subject[1]:
                        activity_ID = 1
                        ground_truth_column = 5
                    # Outdoor Run
                    else:
                        activity_ID = 15
                        ground_truth_column = 6
                # For indoor recordings
                else:
                    # Indoor Treadmill Walk Flat
                    if row_idx < indoor_activity_sample_stamps_for_subject[1]:
                        ground_ID = 12
                        activity_ID = 1
                        ground_truth_column = 0
                    # Indoor Treadmill Run
                    elif row_idx < indoor_activity_sample_stamps_for_subject[2]:
                        ground_ID = 12
                        activity_ID = 15
                        ground_truth_column = 2
                    # Exclude signal points in non-activity areas
                    elif row_idx < indoor_activity_sample_stamps_for_subject[3]:
                        continue
                    # Indoor Treadmill Walk Slope
                    elif row_idx < indoor_activity_sample_stamps_for_subject[4]:
                        ground_ID = 13
                        activity_ID = 1
                        ground_truth_column = 1
                    # Exclude signal points in non-activity areas
                    elif row_idx < indoor_activity_sample_stamps_for_subject[5]:
                        continue
                    # Indoor Walk
                    elif row_idx < indoor_activity_sample_stamps_for_subject[6]:
                        ground_ID = 1
                        activity_ID = 1
                        ground_truth_column = 3
                    # Indoor Run
                    else:
                        ground_ID = 1
                        activity_ID = 15
                        ground_truth_column = 4
                
                # Extracts ground truth information from ground truth array
                ground_truth_section = ground_truth_array[(int(subject_ID) % 11) - 1, ground_truth_column]
                
                # Sets step event ID to no event
                event_id = 0
                # Sets event order flag to None
                order_boolean = None
                
                # Iterates over all ground truth entries
                for ground_truth_entry in ground_truth_section:
                    # Checks if the current row index matches the ground truth occurance index
                    if row_idx == ground_truth_entry[0]:
                        # Uses the event type string to determine the Event_ID
                        event_abbreviation = ground_truth_entry[1]
                        event_id = mapping.get_ground_truth_event_id_by_abbreviation(event_abbreviation)
                        order_boolean = ground_truth_entry[2]
                        # Increases the step number if the event is a right heel strike
                        if event_id == 3:
                            step_number += 1

                # Checks if a ground truth event could not be matched
                if order_boolean == None:
                    # Check if Step_Event already exists
                    check_for_step_event_query = '''SELECT Step_Event_ID FROM Step_Event WHERE
                    Ground_Truth_Event_ID = %s AND Ground_Truth_Order_Flag IS NULL AND Ground_Truth_Step_Number = %s'''
                    cursor.execute(check_for_step_event_query, (event_id, step_number))
                    step_event_ID = cursor.fetchone()
                else:
                    # Check if Step_Event already exists
                    check_for_step_event_query = '''SELECT Step_Event_ID FROM Step_Event WHERE
                    Ground_Truth_Event_ID = %s AND Ground_Truth_Order_Flag = %s AND Ground_Truth_Step_Number = %s'''
                    cursor.execute(check_for_step_event_query, (event_id, order_boolean, step_number))
                    step_event_ID = cursor.fetchone()

                # If it doesn't exist, create a new Step_Event
                if not step_event_ID:
                    # Get ground truth event title
                    event_title = mapping.get_ground_truth_event_title(event_id)
                    # Create new Step_Event
                    create_add_step_event_query = '''INSERT INTO Step_Event (Ground_Truth_Event_ID,
                    Ground_Truth_Event_Title, Ground_Truth_Order_Flag, Ground_Truth_Step_Number)
                    VALUES (%s, %s, %s, %s) RETURNING Step_Event_ID'''
                    cursor.execute(create_add_step_event_query,
                                   (event_id, event_title, order_boolean, step_number))
                    step_event_ID = cursor.fetchone()[0]
                    connection.commit()
                
                # Calculate timestamp in milliseconds
                timestamp = int((row_idx / sample_rate) * 1000)
                
                # Create list for accelerometer axis values
                acc_list = [0, 0, 0]
                # Fill list with accelerometer axis values
                acc_list[0] = data.iloc[row_idx]['accX']
                acc_list[1] = data.iloc[row_idx]['accY']
                acc_list[2] = data.iloc[row_idx]['accZ']

                # Insert new accelerometer entry to the database
                create_add_raw_accelerometer_query = '''INSERT INTO Raw_Accelerometer
                (X, Y, Z, Time, Recording_ID, Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID,
                World_Coordinate_System_ID, Step_Event_ID, Ground_ID)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''
                cursor.execute(create_add_raw_accelerometer_query, (acc_list[0], acc_list[1], acc_list[2],
                timestamp, recording_ID, person_ID, sensor_ID, activity_ID, sensor_location_ID,
                world_coordinate_system_ID, step_event_ID, ground_ID))
            
            connection.commit()


    
    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL:", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

def _get_ground_truth_array():
    """
    Returns the MAREA ground truth in form of a numpy array with fixed activity segments and correct event order
    analysis.

    Returns:
        ground_truth_check_array (numpy array): 
            11x7 array, containing sorted lists of gait events, each list element itself being a list containing 
            1) index of occurance, 2) string of event type, 3) correct order flag
    """
    # Init return array
    ground_truth_check_array = np.zeros((11,7))
    ground_truth_check_array = np.array(ground_truth_check_array, dtype=object)
    # Define path to ground truth
    path_to_ground_truth = '../Data/02_MAREA/'
    # Load ground truth
    ground_truth_struct = scipy.io.loadmat(path_to_ground_truth + 'GroundTruth.mat')
    ground_truth = ground_truth_struct['GroundTruth']
    # Define activity column names
    column_names =\
        ["treadWalk", "treadIncline", "treadWalknRun", "indoorWalk", "indoorWalknRun", "outdoorWalk", "outdoorWalknRun"]
    # Iterate over all activity columns
    for column_index, column_name in enumerate(column_names):
        # Iterate over subject rows
        for i in range(0, 11):
            # Exclude subjects with no recordings for outdoors
            if "outdoor" in column_name and i > 8:
                ground_truth_check_array[i, column_index] = None
            else:
                # Call sub-function
                correct_order_boolean = _check_ground_truth_order(ground_truth, column_name, i)
                ground_truth_check_array[i, column_index] = correct_order_boolean
    return ground_truth_check_array






def _check_ground_truth_order(ground_truth, column_name, row_index):
    """
    Extracts ground truth information and checks it for event order for a specified column and row of the provided
    ground truth.

    Args:
        ground_truth (numpy array):
            The ground truth data to be extracted from
        column_name (string): 
            Name of the column to extract from
        row_index (int):
            Index of the row to extract from

    Returns:
        total_ground_truth_events (list):
            Sorted list of ground truth events, each list element itself being a list containing 
            1) index of occurance, 2) string of event type, 3) correct order flag
    """
    # Restricts provided ground truth to the specified column and row
    ground_truth_section = ground_truth[column_name]
    ground_truth_element = ground_truth_section[0, row_index]
    
    # Separates step event information into 4 event lists
    ground_truth_lf_hs = ground_truth_element['LF_HS'][0,0]
    ground_truth_lf_to = ground_truth_element['LF_TO'][0,0]
    ground_truth_rf_hs = ground_truth_element['RF_HS'][0,0]
    ground_truth_rf_to = ground_truth_element['RF_TO'][0,0]
    
    # Removes redundant information in Running segments
    if "nRun" in column_name:
        # Deduces the column name of the corresponding walking segment by simply removing the "nRun" part
        subtract_column_name = column_name.replace("nRun", "")
        
        # Extracts the ground truth information for the walking segment for the specified column and row
        ground_truth_subtract_section = ground_truth[subtract_column_name]
        ground_truth_subtract_element = ground_truth_subtract_section[0, row_index]
        
        # Separates walking step event information into 4 event lists
        ground_truth_subtract_lf_hs = ground_truth_subtract_element['LF_HS'][0,0]
        ground_truth_subtract_lf_to = ground_truth_subtract_element['LF_TO'][0,0]
        ground_truth_subtract_rf_hs = ground_truth_subtract_element['RF_HS'][0,0]
        ground_truth_subtract_rf_to = ground_truth_subtract_element['RF_TO'][0,0]
        
        # Calulcates the length of the walking segments
        ground_truth_subtract_lf_hs_length = len(ground_truth_subtract_lf_hs)
        ground_truth_subtract_lf_to_length = len(ground_truth_subtract_lf_to)
        ground_truth_subtract_rf_hs_length = len(ground_truth_subtract_rf_hs)
        ground_truth_subtract_rf_to_length = len(ground_truth_subtract_rf_to)
        
        # Removes the redundant walking segments from the runnning events
        ground_truth_lf_hs = ground_truth_lf_hs[ground_truth_subtract_lf_hs_length:]
        ground_truth_lf_to = ground_truth_lf_to[ground_truth_subtract_lf_to_length:]
        ground_truth_rf_hs = ground_truth_rf_hs[ground_truth_subtract_rf_hs_length:]
        ground_truth_rf_to = ground_truth_rf_to[ground_truth_subtract_rf_to_length:]
        

    # Creates a list for the new event structure 
    new_ground_truth_lf_hs = []
    # Iterates through all event entries of 1 of the 4 event lists
    for index, ground_truth_entry in enumerate(ground_truth_lf_hs):
        # Adds the event entry to the list, abiding the new structure
        new_ground_truth_lf_hs.append([ground_truth_entry, "lf_hs"])

    # Creates a list for the new event structure
    new_ground_truth_lf_to = []
    # Iterates through all event entries of 1 of the 4 event lists
    for index, ground_truth_entry in enumerate(ground_truth_lf_to):
        # Adds the event entry to the list, abiding the new structure
        new_ground_truth_lf_to.append([ground_truth_entry, "lf_to"])
    
    # Creates a list for the new event structure
    new_ground_truth_rf_hs = []
    # Iterates through all event entries of 1 of the 4 event lists
    for index, ground_truth_entry in enumerate(ground_truth_rf_hs):
        # Adds the event entry to the list, abiding the new structure
        new_ground_truth_rf_hs.append([ground_truth_entry, "rf_hs"])
    
    # Creates a list for the new event structure
    new_ground_truth_rf_to = []
    # Iterates through all event entries of 1 of the 4 event lists
    for index, ground_truth_entry in enumerate(ground_truth_rf_to):
        # Adds the event entry to the list, abiding the new structure
        new_ground_truth_rf_to.append([ground_truth_entry, "rf_to"])
    
    # Adds together all 4 new ground truth event lists
    total_ground_truth_events =(
            new_ground_truth_lf_hs + new_ground_truth_lf_to + new_ground_truth_rf_hs + new_ground_truth_rf_to)
    # Sorts new overall ground truth event list by occurance index
    total_ground_truth_events = sorted(total_ground_truth_events, key = lambda x: x[0])
    
    # Iterates over all entries of the new overall ground truth event list
    for index, ground_truth_event in enumerate(total_ground_truth_events):
        # Extracts the previous and following events for the current entry,
        # sets them None if the event is the first or last in the list
        if not index == 0:
            previous_event = total_ground_truth_events[index-1]
        else:
            previous_event = None
        if not ground_truth_event == total_ground_truth_events[-1]:
            next_event = total_ground_truth_events[index+1]
        else:
            next_event = None
        # Calls sub-function to ckeck for correct order
        correct_order_boolean = _check_ground_truth_element_order(ground_truth_event, previous_event, next_event)
        # Adds order information to the return list
        total_ground_truth_events[index] = [ground_truth_event[0], ground_truth_event[1], correct_order_boolean]
    return total_ground_truth_events
        
 


 
def _check_ground_truth_element_order(ground_truth_event, previous_event, next_event):
    """
    Checks if the provided ground truth event abides the standard gait cycle event order
    (rf_hs -> lf_to -> lf_hs -> rf_to -> rf_hs)

    Args:
        ground_truth_event (list):
            Ground truth event to be checked, containing 1) occurance index, 2) event type string.
        previous_event (list):
            Ground truth event prior to the event to be checked, containing 1) occurance index, 2) event type string.
        next_event (list):
            Ground truth event following the event to be checked, containing 1) occurance index, 2) event type string.

    Returns:
        (boolean):
            Correct order flag, True meaning correct order was abided.
    """
    current_event = ground_truth_event[1]
    if current_event == "lf_hs":
        if previous_event == None:
            if next_event[1] == "rf_to":
                return True
            else:
                return False
        elif next_event == None:
            if previous_event[1] == "lf_to":
                return True
            else:
                return False
        else:
            if previous_event[1] == "lf_to" and next_event[1] == "rf_to":
                return True
            else:
                return False
    if current_event == "lf_to":
        if previous_event == None:
            if next_event[1] == "lf_hs":
                return True
            else:
                return False
        elif next_event == None:
            if previous_event[1] == "rf_hs":
                return True
            else:
                return False
        else:
            if previous_event[1] == "rf_hs" and next_event[1] == "lf_hs":
                return True
            else:
                return False
    if current_event == "rf_hs":
        if previous_event == None:
            if next_event[1] == "lf_to":
                return True
            else:
                return False
        elif next_event == None:
            if previous_event[1] == "rf_to":
                return True
            else:
                return False
        else:
            if previous_event[1] == "rf_to" and next_event[1] == "lf_to":
                return True
            else:
                return False
    if current_event == "rf_to":
        if previous_event == None:
            if next_event[1] == "rf_hs":
                return True
            else:
                return False
        elif next_event == None:
            if previous_event[1] == "lf_hs":
                return True
            else:
                return False
        else:
            if previous_event[1] == "lf_hs" and next_event[1] == "rf_hs":
                return True
            else:
                return False
            
            

if __name__ == "__main__":
    insert_facts()