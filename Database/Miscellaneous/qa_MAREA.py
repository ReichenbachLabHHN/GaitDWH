"""
Functions for quality assurance within the MAREA Database
"""
import os
import pandas as pd
import numpy as np
import psycopg2
from dotenv import load_dotenv
from psycopg2 import Error
from matplotlib import pyplot as plt
import seaborn as sns
import Database.Feature_Extraction.gait_toolbox as gt
from Database.ETL import insert_facts_MAREA
from Database.ETL import database_id_mapping as mapping

MAREA_database_ID = 2
# Event Order
def check_MAREA_ground_truth_event_order_percentage():
    """
    Checks how many of the MAREA ground truth events are in the correct order.
    This is necessary since some of the ground truth events are not in the correct order and hence, cannot be correct.
    """
    global_flag_list = []
    flag_matrix = np.empty((11,7))
    ground_truth_array = insert_facts_MAREA._get_ground_truth_array()
    for outer_index, row in enumerate(ground_truth_array):
        for inner_index, element in enumerate(row):
            inner_flag_list = []
            if not element:
                flag_matrix[outer_index, inner_index] = np.NaN
                continue
            for entry in element:
                inner_flag_list.append(entry[2])
            inner_flag_dict = {flag:inner_flag_list.count(flag) for flag in inner_flag_list}
            inner_amount_true_flags = inner_flag_dict.get(True, 0)
            inner_amount_false_flags = inner_flag_dict.get(False, 0)
            inner_flag_percentage = inner_amount_true_flags / (inner_amount_true_flags + inner_amount_false_flags)
            flag_matrix[outer_index, inner_index] = round(inner_flag_percentage, 2)
            global_flag_list.extend(inner_flag_list)
    global_flag_dict = {flag:global_flag_list.count(flag) for flag in global_flag_list}
    global_amount_true_flags = global_flag_dict.get(True, 0)
    global_amount_false_flags = global_flag_dict.get(False, 0)
    global_flag_percentage = global_amount_true_flags / (global_amount_true_flags + global_amount_false_flags)
    print(global_amount_true_flags)
    print(global_amount_false_flags)
    print(global_flag_percentage)


def evaluate_peak_detection(sensor_location_id, activity_name_id = 0, peak_type="dom", plot=False):
    """
    Evaluates the gait extraction algorithm on the MAREA ground truth events. Only works for sensor_locations in the
    MAREA dataset (sensor_location_id 18-21).

        Args:
        sensor_location_id:
            ID of the sensor to evaluate, available are: 20 for left ankle and 21 for right ankle.

        activity_name_id:
            Activity name_id of the activity to check. Default 0 for walking. Marea also has running data, if you
            included that in your pipline you can use activity_name_id 1 for running data. Note that the gait
            extraction was developed for walking data.

        peak_type:
            Peak type used for evaluation. Default "dom" for dominant peaks. Every other input checks non-dominant
            peaks. Nonetheless, for clarity we suggest to us "non-dom".

        plot:
            Boolean whether gait cycles with detected event (dominant or non-dominant peak) and ground truth
            (heel strike event) should be plotted together with the calculated difference between them.
    """

    local_person_list = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]

    global_person_list = [mapping.get_global_person_id_marea(x) for x in local_person_list]
    
    try:
        # Load environment variables from .env file
        load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

        connection = psycopg2.connect(
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME")
        )

        # Create a cursor to perform database operations
        cursor = connection.cursor()
        
        global_gap_list = []
        global_gap_true_percentage_list = []
        global_test_list = []
        mean_gaps_per_person = []
        for person_ID in global_person_list:
        
            query = f"""SELECT
                            P.Pre_Accelerometer_ID,
                            P.X,
                            P.Y,
                            P.Z,
                            P.Time,
                            S.Ground_Truth_Event_ID,
                            S.Detected_Event_ID,
                            S.Detected_Event_Reliable_Flag
                        FROM 
                            Pre_Accelerometer P
                            INNER JOIN Step_Event S ON P.Step_Event_ID = S.Step_Event_ID
                            INNER JOIN Ground G ON P.Ground_ID = G.Ground_ID
                            INNER JOIN Activity A ON P.Activity_ID = A.Activity_ID
                        WHERE 
                            P.Person_ID = {person_ID}
                            AND P.Sensor_Location_ID = {sensor_location_id}
                            AND G.Treadmill_ID = 1
                            AND G.Even_Slope_Stairs_ID = 0
                            AND G.Outside_ID = 0
                            AND A.Activity_Name_ID = {activity_name_id}
                        ORDER BY
                            Time
                    """
            cursor.execute(query)
            results = cursor.fetchall()
            global_test_list.append(results)
            results = pd.DataFrame(zip(*results), ["Pre_Accelerometer_ID", "X", "Y", "Z", "Time",
                                                   "Ground_Truth_Event_ID", "Detected_Event_ID",
                                                   "Detected_Event_Reliable_Flag"]).T
            if peak_type == "dom":
                # if left body side
                if sensor_location_id ==20:
                    heel_strike_events = results.loc[results["Ground_Truth_Event_ID"] == 3]
                # if right body side
                if sensor_location_id ==21:
                    heel_strike_events = results.loc[results["Ground_Truth_Event_ID"] == 4]
                peak_events = results.loc[(results["Detected_Event_ID"] == 1)]
            else:
                # if left body side
                if sensor_location_id == 20:
                    heel_strike_events = results.loc[results["Ground_Truth_Event_ID"] == 4]
                # if right body side
                if sensor_location_id == 21:
                    heel_strike_events = results.loc[results["Ground_Truth_Event_ID"] == 3]
                peak_events = results.loc[(results["Detected_Event_ID"] == 2)]
            
            filter_window_size = 4
            if results.empty:
                continue
            jerk_vector = gt.extract_jerk_vector(results[["X", "Y", "Z", "Time"]], None, cursor,
                                                 connection, filter_window_size=filter_window_size, persist=False)
            plot_peak_events = peak_events
            plot_peak_events.index = plot_peak_events.index - filter_window_size/2
            plot_heel_strike_events = heel_strike_events
            plot_heel_strike_events.index = plot_heel_strike_events.index - filter_window_size/2
            
            if plot:

                # Optional plot section
                jerk = [entry[0] for entry in jerk_vector]
                time = [entry[1] for entry in jerk_vector]

                start_time = 0
                end_time = 4000

                filtered_indices = [i for i, t in enumerate(time) if start_time <= t <= end_time]

                start_index = filtered_indices[0]
                end_index = filtered_indices[-1]

                filtered_time = [time[i] for i in filtered_indices]
                filtered_jerk = [jerk[i] for i in filtered_indices]

                filtered_peak_indices = [i - start_index for i in peak_events.index if start_index <= i <= end_index]
                filtered_heel_strike_indices = [i - start_index for i in heel_strike_events.index if
                                                start_index <= i <= end_index]

                test = peak_events["Pre_Accelerometer_ID"].index

                x = np.linspace(0, len(filtered_jerk) - 1, len(filtered_jerk))

                plt.figure(figsize=(10, 5))
                #exchange x with time if you want time on x axis instead of samples
                plt.plot(x, filtered_jerk, label="Jerk Signal")

                plt.vlines(filtered_peak_indices, ymin=0, ymax=5, color="black")
                plt.vlines(filtered_heel_strike_indices, ymin=0, ymax=5, color="green")


                plt.xlabel("Time [samples]", fontsize="20", labelpad = 15)
                plt.ylabel("Normalized Jerk", fontsize="20", labelpad = 15)
                plt.xticks(fontsize=15)
                plt.yticks(fontsize=15)
                plt.grid(True)
                plt.tight_layout()

                plt.show()
            
            gap_list = []
            if len(heel_strike_events) > len(peak_events):
                for index, peak_event in peak_events.iterrows():
                    peak_time = peak_event["Time"]
                    closest_ground_truth_event_index = min(heel_strike_events.index, key=lambda x:abs(x-index))
                    closest_ground_truth_event = heel_strike_events.loc[closest_ground_truth_event_index]
                    gap_list.append(abs(peak_time-closest_ground_truth_event["Time"]))
            else:
                for index, heel_strike_event in heel_strike_events.iterrows():
                    heel_strike_time = heel_strike_event["Time"]
                    closest_peak_event_index = min(peak_events.index, key=lambda x:abs(x-index))
                    closest_peak_event = peak_events.loc[closest_peak_event_index]
                    time_dif = abs(heel_strike_time-closest_peak_event["Time"])
                    if time_dif > 500:
                        print(time_dif)
                    gap_list.append(time_dif)

            # Calculate correct peak detection percentage
            if peak_type == "dom":
                gap_boolean_list = [x<123 for x in gap_list]
            else:
                gap_boolean_list = [x < 209 for x in gap_list]
            gap_flag_dict = {flag:gap_boolean_list.count(flag) for flag in gap_boolean_list}
            gap_amount_true_flags = gap_flag_dict.get(True, 0)
            gap_amount_false_flags = gap_flag_dict.get(False, 0)
            gap_true_percentage = gap_amount_true_flags / (gap_amount_true_flags + gap_amount_false_flags)
            print(gap_true_percentage)
            global_gap_true_percentage_list.append(gap_true_percentage)
            # Visualize ditribution
            global_gap_list.extend(gap_list)
            mean_gaps_per_person.append(np.mean(gap_list))
        print(np.mean(global_gap_true_percentage_list))
        print(np.std(global_gap_true_percentage_list))
        gap_dataframe = pd.DataFrame(global_gap_list, columns=["Time Gap [ms]"])
        ax = sns.boxplot(x=gap_dataframe["Time Gap [ms]"])#, showfliers=False)
        plt.xticks(fontsize=16)
        plt.xlabel('Time Gap [ms]', fontsize=20, labelpad=30)
        plt.show()

        print('global mean')
        print(np.mean(global_gap_list))
        print('global std')
        print(np.std(global_gap_list))

        print('persons mean')
        print(np.mean(mean_gaps_per_person))
        print('persons std')
        print(np.std(mean_gaps_per_person))


    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

if __name__ == '__main__':
    #check_MAREA_ground_truth_event_order_percentage()
    evaluate_peak_detection(21, plot = True)
