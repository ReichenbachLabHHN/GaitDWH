"""
Helper functions for processing the accelerometer data.
"""
import numpy as np
import math
import pandas as pd
import statistics
import ast
from scipy.fft import fft, fftfreq
from scipy.signal import find_peaks, argrelmin, resample
import matplotlib.pyplot as plt

## PUBLIC FUNCTIONS
def apply_rotation_matrix(data_row, rotation_matrix):
    """
    Receives an accelerometer data row and applies the provided rotation matrix to it.

    Args:
        data_row (list/numpy array): 
            The input data row which is to be transformed. 
            The first three elements must contain X, Y, and Z coordinates respectively.
            May contain additional elements.
        rotation_matrix (numpy array/string):
            The rotation matrix to be applied to the data row.

    Raises:
        Exception: 
            Is raised if the rotation matrix is neither a string nor a numpy array.

    Returns:
        data_row (numpy array):
            The transformed data row.
            If provided, additional elements are preserved.
    """
    # Turn data_row into an numpy array in case it is a list
    data_row = np.array(data_row)
    # Check for correct type of rotation_matrix input
    if isinstance(rotation_matrix, np.ndarray):
        rotation_matrix_array = rotation_matrix
    # Transform string input into numpy array form
    elif isinstance(rotation_matrix, str):
        rotation_matrix_tuple = ast.literal_eval(rotation_matrix)
        rotation_matrix_array = np.array(rotation_matrix_tuple)
    # Throw exception if input is of neither of the accepted input types
    else:
        raise Exception("rotation_matrix has to either be of np.ndarray or string type!")
    # Extract accelerometer columns from data_row input
    accelerometer_columns = data_row[0:3]
    # Apply rotation matrix to accelerometer columns
    rotated_accelerometer_columns = np.matmul(rotation_matrix_array, accelerometer_columns)
    # Overwrite accelerometer values in data_row with rotated ones
    data_row[0:3] = rotated_accelerometer_columns
    return data_row

def resample_accelerometer_data(input_data, current_sample_rate, target_sample_rate):
    """
    Resamples the provided data set to the chosen target sample rate. 
    Optionally provided additional columns are assigned to the closest corresponding point in the new data.

    Args:
        input_data (list/numpy array):
            The data set to be resampled.
            The first 4 columns must be X, Y, Z, and Timestamp respectively.
            May contain additional columns.
        current_sample_rate (float): 
            The sample rate of the provided data set.
        target_sample_rate (float): 
            The desired target sample rate to resample the data set to.

    Returns:
        return_data (numpy array):
            The resampled data set. 
            If provided, the additional columns have been applied depending on
            the closest point in the original dataset.
    """
    # Initialize return list
    return_data = []
    # Turn input_data into a numpy array in case it is a list
    input_data = np.array(input_data)
    # Isolate accelerometer values
    resample_input_data_values = input_data[:, [0, 1, 2]]
    # Isolate timestamps
    resample_input_data_time = input_data[:, 3]
    # Calculate target sample length from current and target sample rate
    target_sample_length = int(len(resample_input_data_values) / current_sample_rate * target_sample_rate)
    # Resample accelerometer data and timestamps
    resampled_data_values, resampled_data_time = resample(x=resample_input_data_values, num=target_sample_length,
                                                          t=resample_input_data_time)
    # Calculate number of columns in the input data
    input_data_column_num = len(input_data[0])
    # Iterate through all timestamps of the resampled data
    for index, timestamp in enumerate(resampled_data_time):
        # Identify correct row of resampled accelerometer values
        resampled_data_values_row = resampled_data_values[index]
        # Initialize new return row with resampled accelerometer values
        resampled_return_data_row = resampled_data_values_row
        # Append timestamp to the new return row
        resampled_return_data_row = np.append(resampled_return_data_row, timestamp)
        # Check if there are other columns to append
        if input_data_column_num > 4:
            # Initialize smallest time gap variable as infinite
            smallest_time_gap = np.inf
            previous_time_gap = np.inf
            # Iterate through all rows of the original input data
            for i, row in enumerate(input_data):
                # Calculate the time gap between the current timestamp in the resampled data sample and the
                # timestamp of the current data sample in the original data
                time_gap = abs(timestamp - row[3])
                if time_gap<previous_time_gap:
                    # Overwrite smallest time gap if time gap is smaller
                    if time_gap < smallest_time_gap:
                        smallest_time_gap = time_gap
                        smallest_time_gap_index = i
                    previous_time_gap = time_gap
                else:
                     break
            # Pick sample of the original data which is closest to the current resampled sample timewise
            smallest_time_gap_element = input_data[smallest_time_gap_index]
            # Append additional rows of the picked sample to the return row
            resampled_return_data_row = np.append(resampled_return_data_row, smallest_time_gap_element[4:])
        # Append return row to the return list
        return_data.append(resampled_return_data_row)
    return return_data

def extract_jerk_vector(data_vector, segment_number, connection, cursor, filter=True, filter_window_size=10,
                        persist = True):
    """
    Extracts a jerk vector from a provided data set.
    Optionally applies a moving average filter to the jerk vector with a chosen window size.
    Optionally persists it in the database (default True).

    Args:
        data_vector (list/numpy array): 
            The data set the jerk vector is to be extracted from.
            The first four columns need to be X, Y, Z, and Timestamp respectively.
            May contain additional columns.
        filter (bool, optional): 
            A flag deciding if a moving average filter should be applied to the jerk vector before returning it. 
            Defaults to True.
        filter_window_size (int, optional): 
            The window size for the moving average filter.
            Only relevant if the filter is applied. 
            Defaults to 10.

    Returns:
        jerk vector (numpy array):
            The extracted jerk vector.
            May be filtered and/or normalized depending on input flags.
            If provided, additional columns are preserved.
    """
    # Convert data_vector to a numpy array, in case it is a list
    data_vector = np.array(data_vector)
    # Calculate jerk data for all axes
    jerk_per_axis = _calculate_jerk(data_vector)
    # Calculate jerk vector
    jerk_vector = _calculate_jerk_vector(jerk_per_axis)

    if persist:
        for jerk_row in jerk_vector:
            #        # Create Jerk entry
            create_add_jerk_entry_query = '''INSERT INTO Raw_Jerk (Jerk_value, Time, Recording_ID, Segment_Number,
            Person_ID, Sensor_ID, Activity_ID, Sensor_Location_ID, Step_Event_ID, Ground_ID)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'''

            # Execute code to add Raw_Jerk table entry
            cursor.execute(create_add_jerk_entry_query, (jerk_row[0], jerk_row[1], jerk_row[2], segment_number,
                                        jerk_row[3], jerk_row[4], jerk_row[5], jerk_row[6], jerk_row[7], jerk_row[8]))
        connection.commit()

    if filter:
        # Filter
        jerk_vector = _apply_moving_average_filter(jerk_vector, filter_window_size)
    return jerk_vector

def detect_extrema_events(input_vector, sample_rate, centered, plot=True):
    """
    Detects extrema events (dominant peaks, minima, and non-dominant peaks), as well as the step frequency
    of the provided jerk vector.
    Optionally plots the resulting events with the jerk vector.

    Args:
        input_vector (list/numpy array):
            The provided jerk vector to detect the extrema events in.
            Must contain jerk values in first column.
        sample_rate (float):
            Sample rate of the provided jerk vector.
        centered (bool):
            A flag containing information about if the sensor used in the jerk vector's underlying recording was
            attached to the body center.
            If True, the sensor was centered. If False, it was attached to either the left or the right body side.
        plot (bool, optional): 
            A flag deciding if the extrema events should be plotted after their detection. 
            The plot includes the original jerk vector.
            Defaults to False.

    Returns:
        (tuple): 
            dominant_peaks (list):
                A list of all detected dominant peaks.
                Returns None if the jerk vector's frequency peak could not be detected.
            minima (list):
                A list of all detected minima.
                Returns a list of minima pairs if the sensor is not centered. Each pair then represents the two minima
                in a single gait cycle.
                Returns None if the jerk vector's frequency peak could not be detected.
            non_dominant_peaks (list):
                A list of all detected non-dominant peaks.
                Returns None if the sensor is centered.
                Returns None if the jerk vector's frequency peak could not be detected.
            step_frequency (float):
                The jerk vector's frequency peak.
                Returns None if no frequency peak could not be detected.
    """
    # Convert jerk_vector to a numpy array, in case it is a list
    input_vector = np.array(input_vector)
    # Isolate jerk vector values
    jerk_vector = input_vector[:, 0]
    # Detect step frequency
    step_frequency = _detect_step_frequency(jerk_vector, sample_rate, plot=False)
    if step_frequency:
        # Detect dominant peaks
        dominant_peaks = _detect_dominant_peaks(jerk_vector, sample_rate, step_frequency, centered)
        # Detect minima
        minima = _detect_minima(jerk_vector, dominant_peaks, centered)
        if not centered:
            # Detect non-dominant peaks
            non_dominant_peaks = _detect_non_dominant_peaks(jerk_vector, minima)
        else:
            non_dominant_peaks = None
            
        if plot:  
            plt.plot(jerk_vector)
            plt.plot(dominant_peaks, jerk_vector[dominant_peaks], 'b.')
            if centered:
                plt.plot(minima, jerk_vector[minima], 'r.')
            else:
                for minima_pair in minima:
                    plt.plot(minima_pair[0], jerk_vector[minima_pair[0]], 'r.')
                    plt.plot(minima_pair[1], jerk_vector[minima_pair[1]], 'r.')
            if not centered:
                plt.plot(non_dominant_peaks, jerk_vector[non_dominant_peaks], 'g.')
            plt.show()
        
        
        return (dominant_peaks, minima, non_dominant_peaks, step_frequency)
    else:
        return (None, None, None, None)

def extract_gait_cycles(input_vector, minima, centered, activity_index=None):
    """
    Extracts the gait cycles from a provided input vector.

    Args:
        input_vector (list/numpy array):
            The jerk vector the gait cycles should be extracted from.
            Must contain jerk values in first column.
            May contain additional columns.
        minima (list/numpy array):
            A list containing the detected minima of the provided jerk vector.
            If sensor is not centered (see centered argument), must contain lists of minima pairs instead.
        centered (bool):
            A flag containing information about if the sensor used in the jerk vector's underlying recording was
            attached to the body center.
            If True, the sensor was centered. If False, it was attached to either the left or the right body side.
        activity_index (int):
            An optional field for providing the index of the additional column activity.
            If given, the cycle's activity foreign key will not be chosen by the most frequent occurance, but instead
            be labeled as "Mixed".
            Defaults to None.

    Returns:
        gait_cycles_list (list):
            A list of lists, containing the extracted gait cycles.
            Each gait cycle consists of a list of jerk values, and if provided, the most frequent foreign keys
            of the cycle.
    """
    # Initialize return list
    gait_cycles_list = []
    # Calculate amount of foreign key columns in input vector
    input_vector_foreign_key_columns_length = len(input_vector[0]) - 1
    second_minima_list = []
    # Extract second minimum from each minima pair if sensor is not centered
    if not centered:
        minima_temp = []
        for minima_pair in minima:
            minima_temp.append(minima_pair[1])
            second_minima_list.append(minima_pair[0])
        minima = minima_temp
    else:
        second_minima_list = minima[::2]
        minima = minima[1:]
        minima = minima[::2]
    second_minima_list = second_minima_list[1:]
    # Cut cycles and add them to the return list
    for index, minimum in enumerate(minima):
        # Make sure minimum is not last minimum, since it would lack a following minimum
        if not minimum == minima[-1]:
            gait_cycle_row = []
            next_minimum = minima[index+1]
            current_gait_cycle = np.array(input_vector[minimum:next_minimum], dtype=object)
            current_gait_values = current_gait_cycle[:, 0]
            gait_cycle_row.append(current_gait_values)
            for i in range(0, input_vector_foreign_key_columns_length):
                current_foreign_key_list = []
                for point in current_gait_cycle:
                    current_foreign_key = point[i+1]
                    current_foreign_key_list.append(current_foreign_key)
                # Check if current foreign key is the activity key, and if the activity keys are mixed
                if (i + 1 == activity_index and not current_foreign_key_list.count(current_foreign_key_list[0]) ==
                                                    len(current_foreign_key_list)):
                    activity_foreign_key = 17
                    gait_cycle_row.append(activity_foreign_key)
                else:     
                    most_frequent_foreign_key_in_cycle = statistics.mode(current_foreign_key_list)
                    gait_cycle_row.append(most_frequent_foreign_key_in_cycle)

            minimum_two = second_minima_list[index]-minimum

            dominant_peak = np.argmax(input_vector[minimum:second_minima_list[index]][ :,0]).item()
            non_dominant_peak = (np.argmax(input_vector[second_minima_list[index]:next_minimum][ :,0])+
                                 minimum_two).item()
            gait_cycle_row.append(minimum_two)
            gait_cycle_row.append(dominant_peak)
            gait_cycle_row.append(non_dominant_peak)

            gait_cycles_list.append(gait_cycle_row)
    return gait_cycles_list

def normalize_gait_cycle_length(gait_cycle, resample_size):
    """
    Normalizes the x-axis of the provided gait cycle.

    Args:
        gait_cycle (list/numpy array):
            The gait cycle to be normalized, in form of a list of jerk values.
        resample_size (int):
            The size the cycle should be normalized to.

    Returns:
        (list):
            The normalized cycle.
    """
    return resample(gait_cycle, resample_size)

def calculate_mean_gait_cycle(gait_cycle_list):
    """
    Calculates a mean gait cycle from the provided gait cycles.

    Args:
        gait_cycle_list (list/numpy array):
            A list of gait cycles to calculate the mean cycle for.
            Each gait cycle must itself be list, containing the jerk values.

    Returns:
        mean curve (list):
            The mean cycle.
    """
    # Define return list
    mean_curve = []
    # Get the vertical combinations of the input list
    gait_cycle_column_tuples = zip(*gait_cycle_list)
    # Iterate through the zipped total list
    for tuple in gait_cycle_column_tuples:
        # Calculate a mean value for each data point using all cycles
        column_mean = statistics.mean(tuple)
        # Add the mean for the current data point ot the return list
        mean_curve.append(column_mean)
    return mean_curve

def extract_feature_M_DP(gait_cycles):
    """
    Extracts the mean value of dominant peaks (M_DP) for the provided dominant peaks of the given jerk_vector.

    Args:
        gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks
            as well as minimum.

    Returns:
        dominant_peaks_mean (float):
            Mean value of dominant peaks
    """
    peaks_to_mean = []

    for gait_cycle in gait_cycles:
        dominant_peak_index = int(gait_cycle[202]+1)
        peaks_to_mean.append(gait_cycle[dominant_peak_index])
    dominant_peaks_mean = statistics.mean(peaks_to_mean)
    return dominant_peaks_mean

def extract_feature_SD_DP(gait_cycles):
    """
    Extracts the standard deviation of dominant peaks (SD_DP) for the provided dominant peaks of the given jerk_vector.

    Args:
        gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks as well
            as minimum.

    Returns:
        dominant_peaks_std (float):
            Standard deviation of dominant peaks
    """
    peaks_to_std = []
    for gait_cycle in gait_cycles:
        dominant_peak_index = int(gait_cycle[202]+1)
        peaks_to_std.append(gait_cycle[dominant_peak_index])
    dominant_peaks_std = np.std(peaks_to_std)
    return dominant_peaks_std

def extract_feature_R_M_DNP(gait_cycles):
    """
    Extracts the ratio of mean values of dominant and non-dominant peaks (R_M_DNP) for the provided dominant peaks and
    non-dominant peaks of the given jerk_vector.
    If the sensor is centered, the ratio of the peaks within two steps/one cycle is calculated.

    Args:
        gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks as
            well as minimum

    Returns:
        mean_ratio (float):
            Ratio of mean values of dominant and non-dominant peaks
    """
    non_dominant_peaks_to_mean = []

    for gait_cycle in gait_cycles:
        non_dominant_peak_index = int(gait_cycle[203]+1)
        non_dominant_peaks_to_mean.append(gait_cycle[non_dominant_peak_index])

    dominant_peaks_mean = extract_feature_M_DP(gait_cycles)
    non_dominant_peaks_mean = statistics.mean(non_dominant_peaks_to_mean)
    mean_ratio = dominant_peaks_mean / non_dominant_peaks_mean

    return mean_ratio

def extract_feature_R_SD_DNP(gait_cycles):
    """
    Extracts the Ratio of standard deviations of dominant and non-dominant peaks (R_SD_DNP) for the provided dominant
    peaks and non-dominant peaks of the given jerk_vector.
    If the sensor is centered, the ratio of the peaks within two steps/one cycle is calculated.

    gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks as
            well as minimum

    Returns:
        std_ratio (float):
            Ratio of standard deviations of dominant and non-dominant peaks
    """

    non_dominant_peaks_to_std = []

    for gait_cycle in gait_cycles:
        non_dominant_peak_index = int(gait_cycle[203]+1)
        non_dominant_peaks_to_std.append(gait_cycle[non_dominant_peak_index])

    dominant_peaks_std = extract_feature_SD_DP(gait_cycles)
    non_dominant_peaks_std = np.std(non_dominant_peaks_to_std)

    std_ratio = dominant_peaks_std / non_dominant_peaks_std
    return std_ratio

def extract_feature_M_SD_DS(gait_cycles):
    """
    Extracts the mean standard deviation of dominant steps (M_SD_DS) for the provided jerk_vector.
    If the sensor is centered, the std of the second step within one cycle is calculated.

    Args:
        gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks as
            well as minimum

    Returns:
        dominant_steps_std_mean (float):
            Mean standard deviation of dominant steps
    """
    dominant_std_list = []
    for gait_cycle in gait_cycles:
        minimum_index = int(gait_cycle[201]+1)
        dominant_step = gait_cycle[1:minimum_index]
        dominant_step_std = np.std(dominant_step)
        dominant_std_list.append(dominant_step_std)

    dominant_steps_std_mean = statistics.mean(dominant_std_list)
    return dominant_steps_std_mean

def extract_feature_R_M_SD_DNS(gait_cycles):
    """
    Extracts the ratio of mean standard deviations of dominant and non-dominant steps (R_M_SD_DNS) for the provided
    jerk_vector.
    If the sensor is centered, the ratio of the second step with the first step within one cycle is calculated.

    Args:
        gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks as well
            as minimum

    Returns:
        mean_stds_ratio (float):
            Ratio of mean standard deviations of dominant and non-dominant steps
    """

    non_dominant_std_list = []

    for gait_cycle in gait_cycles:
        minimum_index = int(gait_cycle[201]+1)
        non_dominant_step = gait_cycle[minimum_index:201]
        non_dominant_step_std = np.std(non_dominant_step)
        non_dominant_std_list.append(non_dominant_step_std)

    dominant_steps_std_mean = extract_feature_M_SD_DS(gait_cycles)
    non_dominant_steps_std_mean = statistics.mean(non_dominant_std_list)
    mean_stds_ratio = dominant_steps_std_mean / non_dominant_steps_std_mean
    return mean_stds_ratio

def extract_feature_SD_SD_DS(gait_cycles):
    """
    Extracts the standard deviation of standard deviations of dominant steps (SD_SD_DS) for the provided jerk_vector.
    If the sensor is centered, the std of stds of the second step within one cycle is calculated.

    Args:
        gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks as well
            as minimum

    Returns:
        dominant_steps_stds_std (float):
            Standard deviation of standard deviations of dominant steps
    """
    dominant_std_list = []
    for gait_cycle in gait_cycles:
        minimum_index = int(gait_cycle[201]+1)
        dominant_step = gait_cycle[1:minimum_index]
        dominant_step_std = np.std(dominant_step)
        dominant_std_list.append(dominant_step_std)

    dominant_steps_stds_std = np.std(dominant_std_list)

    return dominant_steps_stds_std

def extract_feature_R_SD_SD_DNS(gait_cycles):
    """
    Extracts the ratio of standard deviations of standard deviations of dominant and non-dominant steps (R_SD_SD_DNS)
    for the provided jerk_vector.
    If the sensor is centered, the ratio of the second step with the first step within one cycle is calculated.
    Args:
        gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks as well
            as minimum

    Returns:
        std_stds_ratio (float):
            Ratio of standard deviations of standard deviations of dominant and non-dominant steps
    """

    non_dominant_std_list = []

    for gait_cycle in gait_cycles:
        minimum_index = int(gait_cycle[201]+1)
        non_dominant_step = gait_cycle[minimum_index:201]
        non_dominant_step_std = np.std(non_dominant_step)
        non_dominant_std_list.append(non_dominant_step_std)

    dominant_steps_stds_std = extract_feature_SD_SD_DS(gait_cycles)
    non_dominant_steps_stds_std = np.std(non_dominant_std_list)
    std_stds_ratio = dominant_steps_stds_std / non_dominant_steps_stds_std
    return std_stds_ratio

def extract_feature_R_M_SL(gait_cycles):
    """
    Extracts the Ratio of means of dominant and non-dominant step length (R_M_SL) for the provided dominant peaks and
    non-dominant peaks of the given jerk_vector.
    If the sensor is centered, the ratio of the peaks within two steps/one cycle is calculated.

    gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks as well
            as minimum

    Returns:
        std_ratio (float):
            Ratio of standard deviations of dominant and non-dominant peaks
    """

    dominant_step_lengths = []
    non_dominant_step_lengths = []

    for gait_cycle in gait_cycles:
        dominant_step_lengths.append(gait_cycle[201])
        non_dominant_step_lengths.append(200-gait_cycle[201])

    dominant_step_lengths_mean = statistics.mean(dominant_step_lengths)
    non_dominant_step_lengths_mean = statistics.mean(non_dominant_step_lengths)

    mean_ratio = dominant_step_lengths_mean / non_dominant_step_lengths_mean
    return mean_ratio

def extract_feature_R_SD_SL(gait_cycles):
    """
    Extracts the Ratio of standard deviations of dominant and non-dominant step length (R_M_SL) for the provided
    dominant peaks and non-dominant peaks of the given jerk_vector.
    If the sensor is centered, the ratio of the peaks within two steps/one cycle is calculated.

    gait_cycles (list/numpy array):
            Gait cycle array with jerk values and information on position of dominant and non-dominant peaks as well
            as minimum

    Returns:
        std_ratio (float):
            Ratio of standard deviations of dominant and non-dominant peaks
    """

    dominant_step_lengths = []
    non_dominant_step_lengths = []

    for gait_cycle in gait_cycles:
        dominant_step_lengths.append(gait_cycle[201])
        non_dominant_step_lengths.append(200-gait_cycle[201])

    dominant_step_lengths_std = np.std(dominant_step_lengths)
    non_dominant_step_lengths_std = np.std(non_dominant_step_lengths)

    std_ratio = dominant_step_lengths_std / non_dominant_step_lengths_std
    return std_ratio


## PRIVATE FUNCTIONS
def _calculate_jerk(data_vector):
    """
    Calculates the jerk from the provided accelerometer data.

    Args:
        data_vector (list/numpy array):
            The accelerometer data to calculate the jerk of.
            The first four columns must contain X, Y, Z, and Timestamp respectively.
            May contain additional columns.

    Returns:
        total_jerk (list):
            The caluclated jerk data.
            Contains X, Y, and Z values in the first three columns.
            If provided, additional columns are inherited from the first sample used in the calculation
            of each jerk value.
    """
    # Calculate amount of rows of the input data
    array_length = len(data_vector)
    # Define return list
    total_jerk = []
    # Loop through all rows of the input data
    for index, sample in enumerate(data_vector):
        # Exclude final point, since there is no next point to calculate the jerk between
        if not (index == array_length - 1):
            # Calulcate Jerk values (if clause to prevent too small time differences between samples to result
            # in an error)
            if data_vector[index + 1][3] - sample[3] != 0:
                jerk_x = (data_vector[index + 1][0] - sample[0]) / (data_vector[index + 1][3] - sample[3])
                jerk_y = (data_vector[index + 1][1] - sample[1]) / (data_vector[index + 1][3] - sample[3])
                jerk_z = (data_vector[index + 1][2] - sample[2]) / (data_vector[index + 1][3] - sample[3])
            else:
                jerk_x = (data_vector[index + 1][0] - sample[0]) / 1
                jerk_y = (data_vector[index + 1][1] - sample[1]) / 1
                jerk_z = (data_vector[index + 1][2] - sample[2]) / 1
            # Define return list row
            sample_jerk = [jerk_x, jerk_y, jerk_z]
            # Calulcate number of fields to add due to foreign keys in the input (-3 due to: X, Y, Z, Time)
            fields_to_add = len(sample) - 3
            # Iteratively add foreign key fields to return list row
            for i in range(0, fields_to_add):
                sample_jerk.append(sample[i+3])
            # Add row to return list
            total_jerk.append(sample_jerk)

    # Return list after all loops are completed
    return total_jerk

def _calculate_jerk_vector(jerk_per_axis):
    """
    Calculates the jerk vector of a provided series of jerk axis values.

    Args:
        jerk_per_axis (list/numpy array):
            A series of jerk axis values.
            The first three columns must be X-, Y-, and Z-jerk respectively.
            May contain additional columns.

    Returns:
        jerk_vector (list):
            The calculated jerk vector.
            If provided, additional columns are preserved.
    """
    # Define return list
    jerk_vector = []
    # Loop through all input list rows
    for entry in jerk_per_axis:
        # Calculate jerk vector value from Jerk_X, Jerk_Y, and Jerk_Z
        jerk_vector_value = math.sqrt(entry[0] ** 2 + entry[1] ** 2 + entry[2] ** 2)
        # Define return list row
        jerk_vector_entry = [jerk_vector_value]
        # Calculate number of fields to add due to foreign keys in the input (-3 due to: Jerk_X, Jerk_Y, Jerk_Z)
        fields_to_add = len(entry) - 3
        # Iteratively add foreign key fields to return list row
        for i in range(0, fields_to_add):
            jerk_vector_entry.append(entry[i+3])
        # Add row to return list
        jerk_vector.append(jerk_vector_entry)
    # Return list after all loops are completed 
    return jerk_vector

def _apply_moving_average_filter(jerk_vector, window_size):
    """
    Applies a moving average filter with a chosen window size to a provided jerk_vector.

    Args:
        jerk_vector (list/numpy array):
            The jerk vector the filter should be applied to.
            Must contain jerk values in first column.
            May contain additional columns.
        window_size (int):
            The window size of the moving average filter to be applied.

    Returns:
        filtered_jerk_vector (list):
            The filtered jerk vector.
            NaN elements on the edges are discarded, causing the result to be shorter than the input.
            If provided, additional columns are preserved.
    """
    # Convert jerk_vector to a numpy array, in case it is a list
    jerk_vector = np.array(jerk_vector)
    # Isolate jerk column
    jerk_vector_values = jerk_vector[:, 0]
    # Define return list
    filtered_jerk_vector = []
    # Apply filter
    moving_average = pd.Series(jerk_vector_values).rolling(window_size).mean()
    moving_average =  moving_average.to_numpy()
    # Loop through result
    for i, entry in enumerate(moving_average):
        # Skip NaN values on both edges
        if not math.isnan(entry):
            # Define row of return list
            filtered_jerk_vector_entry = []
            # Add filtered value to return list row
            filtered_jerk_vector_entry.append(entry)
            # Select correct row of input jerk_vector to pull the foreign key fields from
            jerk_vector_row = jerk_vector[i]
            # Calculate number of fields to add due to foreign keys in the input (-1 due to jerk value)
            fields_to_add = len(jerk_vector_row) - 1
            # Add all foreign key fields to the row
            for j in range(0, fields_to_add):
                filtered_jerk_vector_entry.append(jerk_vector_row[j+1])
            # Add row to return list
            filtered_jerk_vector.append(filtered_jerk_vector_entry)
    # Return list after all loops are completed 
    return filtered_jerk_vector

def normalize(data):
        """
        Normalizes data between 0 and 1 considering outliers
        the 95th percentile value will be counted as the max value
        Args:
            data:
                the data to be normalized
        Returns:
            normalized:
                the normalized data
        """
        max_data = np.percentile(data, 95)
        min_data = np.min(data)
        normalized = (data - min_data) / (max_data - min_data)
        return normalized

def _detect_step_frequency(input_vector, sample_rate, plot=False):
    """
    Detects the lowest relevant frequency peak of a provided jerk vector.

    Args:
        input_vector (list/numpy array):
            The jerk vector values the step frequency should be detected in.
        sample_rate (float):
            The sample rate of the provided jerk vector.
        plot (bool, optional): 
            A flag deciding if the frequency spectrum and the detected peak should be plotted. 
            Defaults to False.

    Returns:
        step frequency (float):
            The detected step frequency in Hertz.
            If peak detection fails, None is returned instead.
    """
    # Number of samples
    input_vector_length = len(input_vector)
    # Sample spacing (e.g. sample rate: 120Hz -> 120 samples/second -> 120 samples/unit on the frequency x axis
    # -> 1/120 Hz/sample)
    hertz_per_sample = 1.0/sample_rate
    # Apply Fast Fourier Transform
    fourier_coefficients = fft(input_vector)
    # Define x-axis and remove redundancy caused by symmetry (// for floor division)
    frequency_axis = fftfreq(input_vector_length, hertz_per_sample)[0:int(input_vector_length//2)]
    # Alter Fourier Coefficients to remove symmerty redundencies, remove complex portion (np.abs),
    # and normalize values (factor)
    fourier_coefficients = 2/input_vector_length * np.abs(fourier_coefficients[0:int(input_vector_length//2)])
    # Calculate sample size of one hertz
    one_hertz_sample_size = len(frequency_axis)/max(frequency_axis)
    # Define check margin to ignore on the left side to avoid fake peaks close to 0
    check_margin = int(one_hertz_sample_size//5)
    # Set check margin to 1 in case of very low input_vector_length
    if check_margin == 0:
        check_margin = 1
    # Calculate maximum value excluding the area left of the check margin
    max_value = max(fourier_coefficients[check_margin:])
    # Find all peak samples higher than half of the max_value and with enough distance between another
    # (to prevent multiple peaks close to another)
    i = 5
    distance = 0
    while distance < 1:
        distance = 3 / i * one_hertz_sample_size
        i-=1
    peaks, _ = find_peaks(fourier_coefficients, height=max_value/3, distance=distance)
    # Deduce peak frequencies from peak samples 
    frequency_peaks = frequency_axis[peaks]
    # Initialize upper bound of possible peak values
    first_peak = len(fourier_coefficients) - 1
    first_peak_index = None
    for idx, peak in enumerate(peaks):
        # Disqualify peaks smaller than the check margin
        if peak < check_margin:
            # Remove peak from the peak frequencies list
            frequency_peaks = np.delete(frequency_peaks, np.where(frequency_peaks == fourier_coefficients[peak]))
            # Remove peak from the peak samples list
            peaks = np.delete(peaks, np.where(peaks == peak))
        # Iteratively find peak with lowest x value
        elif peak < first_peak:
            first_peak = peak
            first_peak_index = idx
    if not first_peak_index == None:
        # Define step frequency as first frequency peak 
        step_frequency = frequency_peaks[first_peak_index]
        if plot:
            plt.plot(frequency_axis, fourier_coefficients)
            plt.plot(frequency_axis[first_peak_index], fourier_coefficients[first_peak_index])
            plt.show()
        return step_frequency
    else:
        print("Frequency detection failed. Frequency peak could not be detected.")
        return None

def _detect_dominant_peaks(jerk_vector, sample_rate, step_frequency, centered):
    """
    Detects dominant peaks in a provided jerk vector.
    
    Short algorithm summary:
        If sensor is centered:
            Find all peaks with enough distance to another.
        If sensor is not centered:
            Calculates signal mean.
            Calculates all peaks above signal mean.
            Calculates mean of all peaks above signal mean.
            Calculates all peaks above the mean of all peaks above signal mean, and assumes them to be dominant peaks.
            Iteratively calculates the distance between two consecutive dominant peaks and compares it to the
            mean cycle length (calculated through frequency analysis).
            Calculates amount of missing cycles for each gap, and thereby the amount of missing peaks.
            Searches for candidates for the missing peaks.
            If too few peaks are found, searches for the highest peak between all found candidates.
            If too many peaks are found, disqualifies lowest, and thereby least likely, peak.
            Repeat the peak search for one missing cycle less and one missing cycle more. Pick the missing cycle amount
            with the best Results.

    Args:
        jerk_vector (list/numpy array):
            The jerk vector values to detect the dominant peaks in.
        sample_rate (float):
            The sample rate of the provided jerk vector.
        step_frequency (float):
            The step frequency of the provided jerk vector.
        centered (bool):
            A flag containing information about if the sensor used in the jerk vector's underlying recording was
            attached to the body center.
            If True, the sensor was centered. If False, it was attached to either the left or the right body side.

    Returns:
        peaks (list):
            The sample numbers of the detected dominant peaks in the provided jerk vector.
    """
    # Calculate samples per cycle (// is floor division)
    samples_per_cycle = int(sample_rate//step_frequency)
    # Calculate total cycle amount
    total_cycles_amount = len(jerk_vector)/samples_per_cycle
    # Define how many cycles to include in a local frequency window
    local_frequency_window_cycle_amount = 128
    # Limit local frequency window cycle amount to total cycle amount
    if local_frequency_window_cycle_amount > total_cycles_amount:
        local_frequency_window_cycle_amount = total_cycles_amount
    # Calculate size of margin in each direction for the local frequency window
    local_frequency_window_margin = int(local_frequency_window_cycle_amount/2*samples_per_cycle)
    ## Centered
    if centered:
        # Define minimum distance between peaks
        find_peaks_distance = int(6/8*samples_per_cycle)
        # Find peaks
        peaks, _ = find_peaks(jerk_vector, distance=find_peaks_distance)
    ## Non-Centered
    else:
        # Calculate total mean of jerk_vector
        total_mean = statistics.mean(jerk_vector)
        # Find all peaks above the total mean
        peaks_above_total_mean, _ = find_peaks(jerk_vector, height=total_mean, distance=samples_per_cycle/3)
        # Calculate the mean of all peaks above the total mean
        mean_of_peaks_above_total_mean = statistics.mean(jerk_vector[peaks_above_total_mean])
        # Find all peaks above the mean of all peaks above the total mean
        peaks_above_mean_of_peaks_above_total_mean, _ = find_peaks(jerk_vector, height=mean_of_peaks_above_total_mean,
                                                                   distance=samples_per_cycle*2/3)
        # Initialize a list for missing peaks
        missing_dominant_peaks = []
        # Iterate through peaks to search for dominant peaks between detected peaks
        for index, peak in enumerate(peaks_above_mean_of_peaks_above_total_mean):
            # Check if the peak is closer to 0 than the local frequency window size
            if peak - local_frequency_window_margin < 0:
                # Start local frequency check area from 0 instead of peak - margin
                local_frequency_check_area = jerk_vector[0:peak+local_frequency_window_margin]
            # Check if the peak is closer to the maximum x-value than the local frequency window size
            elif peak + local_frequency_window_margin > len(jerk_vector) - 1:
                # Stop local frequency check area at max x-value instead of peak + margin
                local_frequency_check_area = jerk_vector[peak-local_frequency_window_margin:len(jerk_vector)-1]
            # Standard case
            else:
                # Define the local frequency check area
                local_frequency_check_area = jerk_vector[peak-local_frequency_window_margin:peak+
                                                                                    local_frequency_window_margin]
            # Detect local step frequency
            local_step_frequency = _detect_step_frequency(local_frequency_check_area, sample_rate)
            # Use global step frequency if local frequency cannot be caluclated
            if local_step_frequency == None:
                local_step_frequency = step_frequency
            if local_step_frequency < 0.7:
                local_step_frequency = step_frequency
            # Calculate local samples per cycle
            local_samples_per_cycle = int(sample_rate//local_step_frequency)
            # Exclude last peak, since it has no next peak to check
            if index < len(peaks_above_mean_of_peaks_above_total_mean)-1:
                # Define next peak
                next_peak = peaks_above_mean_of_peaks_above_total_mean[index+1]
                # Calculate distance between current and next peak
                distance_to_next_peak = next_peak - peak
                # Calculate amount of missing cycles between peaks
                missing_cycles_estimate = round(distance_to_next_peak/local_samples_per_cycle) - 1
                
                if missing_cycles_estimate > 0:
                    # Define margins to avoid peaks too close to the known peaks
                    check_margin = int(local_samples_per_cycle//5)
                    # Define check_area
                    check_area = jerk_vector[peak+check_margin:next_peak-check_margin]
                    # Calculate mean of the check_margin
                    check_area_mean = statistics.mean(check_area)
                    mean_list = []
                    
                    # To ensure that the correct amount of missing cycles was detected, the peak detection is also
                    # run for one cycle less and one cycle more (if possible), and the Results are compared.
                    ## Test with exact estimate
                    # Detect the peaks
                    exact_missing_cycles_estimation_result = _detect_missing_dominant_peaks(jerk_vector, peak,
                                                                    next_peak, missing_cycles_estimate, check_margin)
                    # If no peaks could be identified, the score for the comparison is 0
                    if len(exact_missing_cycles_estimation_result) == 0:
                        mean_list.append(0)
                    else:
                        # Split found peaks into dominant and non-dominant peaks
                        exact_missing_cycles_estimation_dominant_peaks = exact_missing_cycles_estimation_result[1::2]
                        exact_missing_cycles_estimation_non_dominant_peaks =(
                                                                        exact_missing_cycles_estimation_result)[0::2]
                        # Calculate mean of dominant peaks
                        dominant_peak_value_list = []
                        for dominant_peak in exact_missing_cycles_estimation_dominant_peaks:
                            dominant_peak_value = jerk_vector[dominant_peak]
                            dominant_peak_value_list.append(dominant_peak_value)
                        dominant_peak_size_mean = statistics.mean(dominant_peak_value_list)
                        # Calculate mean of non-dominant peaks
                        non_dominant_peak_value_list = []
                        for non_dominant_peak in exact_missing_cycles_estimation_non_dominant_peaks:
                            non_dominant_peak_value = jerk_vector[non_dominant_peak]
                            non_dominant_peak_value_list.append(non_dominant_peak_value)
                        non_dominant_peak_size_mean = statistics.mean(non_dominant_peak_value_list)
                        # Calculate ratio of dominant to non-dominant peaks
                        dominant_non_dominant_peak_size_ratio = dominant_peak_size_mean / non_dominant_peak_size_mean
                        # Add all peak values to a list, punishing peak values below the cycle mean by setting
                        # them to 0. Then calculate the mean value of said list.
                        exact_missing_cycles_values = []
                        for result_peak in exact_missing_cycles_estimation_result:
                            result_peak_y = jerk_vector[result_peak]
                            if result_peak_y > check_area_mean:
                                exact_missing_cycles_values.append(result_peak_y)
                            else:
                                exact_missing_cycles_values.append(0)
                        exact_missing_cycles_mean = statistics.mean(exact_missing_cycles_values)
                        # Caluclate the final score by multiplying the ratio of dominant to non-dominant peaks with the
                        # punished mean peak value list.
                        exact_missing_cycles_result = exact_missing_cycles_mean * dominant_non_dominant_peak_size_ratio
                        # Add the result to the comparison list between missing cycle amounts
                        mean_list.append(exact_missing_cycles_result)
                    
                    ## Test with one cycle less
                    # Set the score to 0, if there are already no cycles estimated to be between the peaks
                    if missing_cycles_estimate > 1:
                        # Detect the peaks
                        below_missing_cycles_estimation_result = _detect_missing_dominant_peaks(jerk_vector, peak,
                                                                next_peak, missing_cycles_estimate - 1, check_margin)
                        # If no peaks could be identified, the score for the comparison is 0
                        if len(below_missing_cycles_estimation_result) == 0:
                            mean_list.append(0)
                        else:
                            # Split found peaks into dominant and non-dominant peaks
                            below_missing_cycles_estimation_dominant_peaks =(
                                                                        below_missing_cycles_estimation_result)[1::2]
                            below_missing_cycles_estimation_non_dominant_peaks =(
                                                                        below_missing_cycles_estimation_result)[0::2]
                            # Calculate mean of dominant peaks
                            dominant_peak_value_list = []
                            for dominant_peak in below_missing_cycles_estimation_dominant_peaks:
                                dominant_peak_value = jerk_vector[dominant_peak]
                                dominant_peak_value_list.append(dominant_peak_value)
                            dominant_peak_size_mean = statistics.mean(dominant_peak_value_list)
                            # Calculate mean of non-dominant peaks
                            non_dominant_peak_value_list = []
                            for non_dominant_peak in below_missing_cycles_estimation_non_dominant_peaks:
                                non_dominant_peak_value = jerk_vector[non_dominant_peak]
                                non_dominant_peak_value_list.append(non_dominant_peak_value)
                            non_dominant_peak_size_mean = statistics.mean(non_dominant_peak_value_list)
                            # Calculate ratio of dominant to non-dominant peaks
                            dominant_non_dominant_peak_size_ratio = dominant_peak_size_mean / non_dominant_peak_size_mean
                            # Add all peak values to a list, punishing peak values below the cycle mean by setting them
                            # to 0. Then calculate the mean value of said list.
                            below_missing_cycles_values = []
                            for result_peak in below_missing_cycles_estimation_result:
                                result_peak_y = jerk_vector[result_peak]
                                if result_peak_y > check_area_mean:
                                    below_missing_cycles_values.append(result_peak_y)
                                else:
                                    below_missing_cycles_values.append(0)
                            below_missing_cycles_mean = statistics.mean(below_missing_cycles_values)
                            # Caluclate the final score by multiplying the ratio of dominant to non-dominant peaks with
                            # the punished mean peak value list.
                            below_missing_cycles_result = (below_missing_cycles_mean *
                                                           dominant_non_dominant_peak_size_ratio)
                            # Add the result to the comparison list between missing cycle amounts
                            mean_list.append(below_missing_cycles_result)     
                    else:
                        mean_list.append(0)
                        
                    ## Test with one cycle more
                    # Detect the peaks
                    above_missing_cycles_estimation_result = _detect_missing_dominant_peaks(jerk_vector, peak,
                                                                next_peak, missing_cycles_estimate + 1, check_margin)
                    # If no peaks could be identified, the score for the comparison is 0
                    if len(above_missing_cycles_estimation_result) == 0:
                        mean_list.append(0)
                    else:
                        # Split found peaks into dominant and non-dominant peaks
                        above_missing_cycles_estimation_dominant_peaks = above_missing_cycles_estimation_result[1::2]
                        above_missing_cycles_estimation_non_dominant_peaks =(
                                                                        above_missing_cycles_estimation_result)[0::2]
                        # Calculate mean of dominant peaks
                        dominant_peak_value_list = []
                        for dominant_peak in above_missing_cycles_estimation_dominant_peaks:
                            dominant_peak_value = jerk_vector[dominant_peak]
                            dominant_peak_value_list.append(dominant_peak_value)
                        dominant_peak_size_mean = statistics.mean(dominant_peak_value_list)
                        # Calculate mean of non-dominant peaks
                        non_dominant_peak_value_list = []
                        for non_dominant_peak in above_missing_cycles_estimation_non_dominant_peaks:
                            non_dominant_peak_value = jerk_vector[non_dominant_peak]
                            non_dominant_peak_value_list.append(non_dominant_peak_value)
                        non_dominant_peak_size_mean = statistics.mean(non_dominant_peak_value_list)
                        # Calculate ratio of dominant to non-dominant peaks
                        dominant_non_dominant_peak_size_ratio = dominant_peak_size_mean / non_dominant_peak_size_mean
                        # Add all peak values to a list, punishing peak values below the cycle mean by setting
                        # them to 0. Then calculate the mean value of said list.
                        above_missing_cycles_values = []
                        for result_peak in above_missing_cycles_estimation_result:
                            result_peak_y = jerk_vector[result_peak]
                            if result_peak_y > check_area_mean:
                                above_missing_cycles_values.append(result_peak_y)
                            else:
                                above_missing_cycles_values.append(0)
                        above_missing_cycles_mean = statistics.mean(above_missing_cycles_values)
                        # Caluclate the final score by multiplying the ratio of dominant to non-dominant peaks with the
                        # punished mean peak value list.
                        above_missing_cycles_result = above_missing_cycles_mean * dominant_non_dominant_peak_size_ratio
                        # Add the result to the comparison list between missing cycle amounts
                        mean_list.append(above_missing_cycles_result)

                    # Pick the amount of peaks with best score
                    highest_mean_index = mean_list.index(max(mean_list))
                    if highest_mean_index == 0:
                        missing_peaks_list = exact_missing_cycles_estimation_result
                    elif highest_mean_index == 1:
                        missing_peaks_list = below_missing_cycles_estimation_result
                    else:
                        missing_peaks_list = above_missing_cycles_estimation_result
                        
                    # Filter out the non-dominant peaks (odd ones), and add check margin and peak to regain global
                    # x-axis values
                    local_missing_dominant_peaks = missing_peaks_list[1::2]
                    # Add dominant peaks to the missing dominant peaks list
                    for peak in local_missing_dominant_peaks:
                        missing_dominant_peaks.append(peak)
        
        # Combine the new dominant peaks and the originally found dominant peaks together
        total_dominant_peaks = np.concatenate((peaks_above_mean_of_peaks_above_total_mean,
                                               missing_dominant_peaks), axis=None)
        # Sort the new combined list by their x values
        total_dominant_peaks.sort()
        # Cast all peaks to integers
        peaks = [int(peak) for peak in total_dominant_peaks]
    return peaks

def _detect_missing_dominant_peaks(jerk_vector, peak, next_peak, missing_cycles, check_margin):
    """
    Internal function called in _detect_dominant_peaks.
    Detects a chosen amount of missing peaks between two given peaks.

    Args:
        jerk_vector (list/numpy array):
            The underlying jerk vector.
        peak (int):
            Sample index of the first peak.
        next_peak (int):
            Sample index of the second peak.
        missing_cycles (int):
            Amount of cycles missing between the two peaks.
        check_margin (int):
            Size of gap (in samples) to exclude from the search for peaks on each side.

    Returns:
        (list): 
            Detected peaks (dominant and non-dominant).
    """
    # Calculate distance between peaks
    distance_to_next_peak = next_peak - peak
    # Calculate total missing peak amount (dominant + non-dominant)
    missing_peak_amount = 2 * missing_cycles + 1
    # Define check area for missing peaks, respecting the margins
    check_area = jerk_vector[peak+check_margin:next_peak-check_margin]
    # Find all peaks with sufficient distance to another
    missing_peaks, _ = find_peaks(check_area, distance=distance_to_next_peak/(1.85*missing_peak_amount))
    # Define a peak threshold to filter out too small peaks
    peak_threshold = statistics.mean(check_area[missing_peaks])/3
    # Iterate through the found peaks
    for missing_peak_1 in missing_peaks:
        # Check if the current peak is smaller than the threshold
        if check_area[missing_peak_1] < peak_threshold:
            # Remove peak
            missing_peaks = np.delete(missing_peaks, np.where(missing_peaks == missing_peak_1))
    # If peaks are still missing
    if len(missing_peaks) < missing_peak_amount:
        # Keep looping until number of required peaks is met
        while(len(missing_peaks) != missing_peak_amount):
            # Initialize empty list for peak candidates
            potential_peak_list = []
            # Define list for all points/peaks to search between
            temp_peak_list = missing_peaks
            # Add first point of the check area to the point/peak list
            temp_peak_list = np.append(temp_peak_list, peak+check_margin)
            # Add last point of the check area to the point/peak list
            temp_peak_list = np.append(temp_peak_list, next_peak-check_margin)
            # Iterate through all points/peaks in the search list
            for i, temp_peak in enumerate(temp_peak_list):
                # Exclude final point/peak, since it has no next point/peak
                if i < len(temp_peak_list)-1:
                    # Define local area between two search points
                    local_check_area = check_area[temp_peak+check_margin:temp_peak_list[i+1]-check_margin]
                    # Find all peaks in the new search area
                    potential_peaks, _ = find_peaks(local_check_area)
                    # Iterate through all found peaks
                    for potential_peak in potential_peaks:
                        # Add the found peak to the potential peak list
                        potential_peak_list.append(temp_peak + check_margin + potential_peak)
            # Initialize start value for comparison of highest peak value
            currently_highest_potential_peak = None
            currently_highest_potential_peak_value = 0
            # Iterate through all found potential peaks
            for potential_peak in potential_peak_list:
                # Check if current peak is bigger than the currently highest peak
                if check_area[potential_peak] > currently_highest_potential_peak_value:
                    # Take current peak as new currently highest peak
                    currently_highest_potential_peak_value = check_area[potential_peak]
                    currently_highest_potential_peak = potential_peak
            if currently_highest_potential_peak == None:
                return []
            # Add highest peak of all potential peaks to the missing peak list
            missing_peaks = np.append(missing_peaks, currently_highest_potential_peak)
    # If there are too many peaks
    elif len(missing_peaks) > missing_peak_amount:
        # Keep looping until number of required peaks is met
        while (len(missing_peaks) != missing_peak_amount):
            # Find lowest peak
            lowest_peak_index = np.argmin(check_area[missing_peaks])
            lowest_peak_x = missing_peaks[lowest_peak_index]
            # Remove lowest peak from the missing peaks list
            missing_peaks = np.delete(missing_peaks, np.where(missing_peaks == lowest_peak_x))
    # Add check margin and peak to regain global x-axis values and return
    return missing_peaks + check_margin + peak

def _detect_minima(jerk_vector, dominant_peaks, centered):
    """
    Detects minima in provided jerk vector.
    
    Short algorithm summary:
        Breaks jerk vector down into gait cycles, each being a gap between consecutive dominant peaks.
        For each gait cycle:
            Calculate absolute minimum.
            If sensor is not centered:
                Calculate all other minima.
                Calculate maximum between absolute minimum and all other minima.
                Choose minima pair with highest value between them, and lowest minium value itself.

    Args:
        jerk_vector (list/numpy array):
            The jerk vector to detect the minima in.
        dominant_peaks (list):
            Sample indices of dominant peaks in the jerk vector.
        centered (bool):
            A flag containing information about if the sensor used in the jerk vector's underlying recording was
            attached to the body center.
            If True, the sensor was centered. If False, it was attached to either the left or the right body side.

    Returns:
        global_minima (list):
            Minima of the jerk_vector.
            Returns lists of minima pairs for each cycle if sensor is not centered.
    """
    margin_threshold_factor = 1/7
    global_minima = []
    for i, peak in enumerate(dominant_peaks):
        # Reset values of previous loop
        absolute_minimum_x = None
        second_absolute_minimum_x = None
        # Exclude the last peak, due to lack of a next peak
        if not peak == dominant_peaks[-1]:
            # Define next peak
            next_peak = dominant_peaks[i+1]
            # Iterate through all sections between peaks
            check_area = jerk_vector[peak:next_peak]
            x = np.linspace(0, next_peak-peak-1, next_peak-peak)
            # Find all minima
            minima = argrelmin(check_area)[0]
            # Skip to next peak if there are no minima to be found (indicates incorrect dominant peak)
            if len(minima) < 2:
                continue
            # Find absolute minimum, the lowest point
            absolute_minimum_x = int(x[check_area.argmin()])
            if centered:
                global_minima.append(int(absolute_minimum_x + peak))
            else:
                # Remove absolute minimum from minima list, since we want to check it against the other minima
                minima = np.delete(minima, np.where(minima == absolute_minimum_x))
                minima_backup = minima
                # Remove minima too close at the two dominant peaks
                too_close_threshold = len(check_area)*margin_threshold_factor
                for minimum in minima:
                    if minimum > next_peak - peak - too_close_threshold:
                        minima = np.delete(minima, np.where(minima == minimum))
                    elif minimum < too_close_threshold:
                        minima = np.delete(minima, np.where(minima == minimum))
                # Revert minima removal due to margin if otherwise there would be no minima left
                if len(minima) == 0:
                    minima = minima_backup
                # Calulate the mean value of all values of the section
                check_area_mean = statistics.mean(check_area)
                # Calculate mean of the left half
                check_area_left_mean = statistics.mean(check_area[:len(check_area)//2])
                # Calculate mean of the right half
                check_area_right_mean = statistics.mean(check_area[len(check_area)//2:])
                # Calculate mean_ration between left and right half
                mean_ratio = check_area_left_mean/check_area_right_mean
                # If left and right halves are not too dissimilar
                if mean_ratio > 0.5 and mean_ratio < 1.5:
                    filtered_minima = minima
                    # Iterate through all minima
                    for minimum in minima:
                        # Exclude minima with values higher than the section mean
                        if check_area[minimum] > check_area_mean:
                            filtered_minima = np.delete(filtered_minima, np.where(filtered_minima == minimum))
                    # Don't apply exlusion if no minima are left
                    if not len(filtered_minima) == 0:
                        minima = filtered_minima
                non_dominant_peak_y = 0
                # Iterate through all minima
                for minimum in minima:
                    # Define a sub-section between the absolute minimum and the minimum currently being tested
                    if minimum > absolute_minimum_x:
                        potential_non_dominant_peak_area = check_area[absolute_minimum_x:minimum]
                    else:
                        potential_non_dominant_peak_area = check_area[minimum:absolute_minimum_x]
                    # Calculate peak of sub-section
                    potential_non_dominant_peak_y = max(potential_non_dominant_peak_area)
                    # Check if peaks are identical, if so, decide by lower minima y-value
                    if potential_non_dominant_peak_y == non_dominant_peak_y:
                        if check_area[minimum] < check_area[second_absolute_minimum_x]:
                            non_dominant_peak_y = potential_non_dominant_peak_y
                            second_absolute_minimum_x = minimum
                    # Check if peak is higher than previous peaks of other minima
                    elif potential_non_dominant_peak_y > non_dominant_peak_y:
                        non_dominant_peak_y = potential_non_dominant_peak_y
                        second_absolute_minimum_x = minimum
                # Add minima to global minima list
                if absolute_minimum_x < second_absolute_minimum_x:
                    global_minima.append([int(absolute_minimum_x + peak), int(second_absolute_minimum_x + peak)])
                else:
                    global_minima.append([int(second_absolute_minimum_x + peak), int(absolute_minimum_x + peak)])
    return global_minima

def _detect_non_dominant_peaks(jerk_vector, minima):
    """
    Detect non-dominant peaks in the provided jerk_vector
    
    Short algorithm summary:
        Find maximum value between each minima pair.

    Args:
        jerk_vector (list/numpy array):
            Jerk vector to detect the non-dominant peaks in.
        minima (list):
            List of minima pairs.

    Returns:
        non_dominant_peaks (list):
            Sample numbers of non-dominant peaks in provided jerk vector.
    """
    non_dominant_peaks = []
    for minima_pair in minima:
        minima_left = minima_pair[0]
        minima_right = minima_pair[1]
        check_area = jerk_vector[minima_left:minima_right]
        non_dominant_peak = check_area.argmax()
        non_dominant_peaks.append(int(non_dominant_peak + minima_left))
    return non_dominant_peaks
