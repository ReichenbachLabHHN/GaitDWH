"""
This module contains  functions for plotting information about database and sensor location pairs.
This includes comparison between two pairs as well as Pearson correlations within and between pairs.
The three main methods here are

compare_sensors(database_id_one, sensor_location_id_one, database_id_two, sensor_location_id_two):
    Compares the gait cycle and statistical features of two database-sensor location pairs with each other.
draw_gait_cycles_correlations():
    Plots Pearson correlation values for database and sensor location pairs. The correlation within the gait cycles of
    a subject will be plotted (box plot) as well as the correlation between the averaged gait cycle of each subject
    (triangle).:
    Note that the database and sensor location pairs have to be added to the lost below ('db_sensor_pairs').
correlate_sensors()
    Plots a correlation matrix using the Pearson correlation for a list of database and sensor location pairs. This is
    done separately for centred and non-centred sensors.
    Note: The database and sensor location ids need to be filled in the two lists below.
"""
import math
import os
import warnings
import numpy as np
import pandas as pd
import psycopg2
from dotenv import load_dotenv
from matplotlib import pyplot as plt
from matplotlib.patches import Rectangle
from psycopg2 import Error
from scipy.stats import ttest_ind, ttest_rel
import seaborn as sns


def compare_sensors(database_id_one, sensor_location_id_one, database_id_two, sensor_location_id_two,
                    feature_frame = 10):
    """
    Compares the gait cycle and statistical features of two database-sensor location pairs with each other.

    Args:
        database_id_one:
            id of the first database to compare
        sensor_location_id_one
            id of the first sensor location to compare
        database_id_two:
            id of the second database to compare
        sensor_location_id_two
            id of the second sensor location to compare
        feature_frame:
            during the feature_extraction phase, the statistical features were calculated from a different amount of
            gait cycles. This parameter indicates which of those calculated statistical features the comparison will
            be based of. Note: Only feature amounts that were indicated in the .envs file during feature extraction
            are valid here. Default 10.
    """

    color_one = get_color(database_id_one)
    color_two = get_color(database_id_two)

    database_title_one, database_title_two, location_one, location_two =(
        get_location_and_database_names(database_id_one, database_id_two, sensor_location_id_one, sensor_location_id_two))

    statistical_features_one, statistical_features_two, person_list_one, person_list_two = (
        get_statistical_features(database_id_one, database_id_two, sensor_location_id_one, sensor_location_id_two,
                             feature_frame))

    paired = database_id_one == database_id_two

    if paired:
        overlapping_ids = set(person_list_one) & set(person_list_two)

        statistical_features_one = np.array([
            feat for feat, pid in zip(statistical_features_one, person_list_one)
            if pid in overlapping_ids
        ])

        statistical_features_two = np.array([
            feat for feat, pid in zip(statistical_features_two, person_list_two)
            if pid in overlapping_ids
        ])

    t_tests = perform_t_test_on_statistical_features(statistical_features_one, statistical_features_two, paired)

    mean_cycle_values_one, mean_ci_one = extract_mean_gait_cycle_by_database_ID_and_sensor_location(database_id_one,
                                                                                                    sensor_location_id_one)
    mean_cycle_values_two, mean_ci_two = extract_mean_gait_cycle_by_database_ID_and_sensor_location(database_id_two,
                                                                                                    sensor_location_id_two)

    plot_comparison_results(mean_cycle_values_one, mean_cycle_values_two, mean_ci_one, mean_ci_two, color_one,
                            color_two, database_title_one, database_title_two, location_one, location_two, t_tests,
                            statistical_features_one, statistical_features_two)

def get_color(db_id):
    """
    Returns a color corresponding to a database id.
    Note this is based on the databases used in our paper. You might have to adapt this individually.

    Args:
        db_id:
            id of the database

    Returns:
        color:
            Color corresponding to a database id.
    """
    mapping = {
        0: "blue",
        1: "red",
        2: "green",
        3: "cyan",
        4: "sandybrown",
        5: "peru",
        6: "goldenrod",
        7: "purple",
    }

    return mapping.get(db_id, "Invalid ID")

def get_location_and_database_names(database_id_one, database_id_two, sensor_location_id_one, sensor_location_id_two):
    """
    Returns sensor location and database names for the corresponding ids.

    Args:
        database_id_one:
            id of the first database to compare
        sensor_location_id_one
            id of the first sensor location to compare
        database_id_two:
            id of the second database to compare
        sensor_location_id_two
            id of the second sensor location to compare

    Returns:
        database_title_one:
            Name of the first database.
        database_title_one:
            Name of the second database.
        location_one:
            Name of the first sensor location.
        location_two:
            Name of the second sensor location.
    """

    database_title_one = database_name(database_id_one)
    database_title_two = database_name(database_id_two)

    database_title_one = database_title_one[0]
    database_title_two = database_title_two[0]

    sensor_location_one = sensor_location(sensor_location_id_one)
    sensor_location_two = sensor_location(sensor_location_id_two)

    location_one = ''
    location_two = ''

    for string in sensor_location_one[0]:
        location_one += str(string)
    for string in sensor_location_two[0]:
        location_two += str(string)

    return database_title_one, database_title_two, location_one, location_two

def database_name(database_id):
    """
    Returns database name for the corresponding id.

    Args:
        database_id:
            id of the database.

    Returns:
        database_title:
            Name of the database.
    """
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

        query = f"""SELECT
                        database_title
                    FROM 
                        Recording R
                    WHERE 
                        R.database_id = {database_id}
                """
        cursor.execute(query)
        database_title = cursor.fetchone()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

    return database_title

def sensor_location(sensor_location_id):
    """
    Returns sensor location name for the corresponding id.

    Args:
        sensor_location_id:
            id of the sensor location.

    Returns:
        sensor_location_title:
            Name of the sensor location.
    """
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

        # body_side_title, body_area_title
        query = f"""SELECT                
                       position_title
                    FROM 
                        Sensor_Location SL
                    WHERE 
                        SL.sensor_location_id = {sensor_location_id}
                """
        cursor.execute(query)
        sensor_location_title = cursor.fetchone()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

    return sensor_location_title

def get_statistical_features(database_id_one, database_id_two, sensor_location_id_one, sensor_location_id_two,
                             feature_frame):
    """
    Returns the mean value of the statistical features for each individual person of two database and
    sensor location pair.

    Args:
        database_id_one:
            id of the first database
        sensor_location_id_one
            id of the first sensor location
        database_id_two:
            id of the second database
        sensor_location_id_two
            id of the second sensor location
        feature_frame:
            during the feature_extraction phase, the statistical features were calculated from a different amount of
            gait cycles. This parameter indicates which of those calculated statistical features the comparison will
            be based of. Note: Only feature amounts that were indicated in the .envs file during feature extraction
            are valid here.

    Returns:
        statistical_features_one:
            Means of statistical values for each person of the first database and sensor location pair.
        person_list_one:
            IDs of persons whose data is contained in statistical_features_one. The first entry in this list
            corresponds to the first entry in the mean_statistical_values list and so on.
        statistical_features_two:
            Means of statistical values for each person of the second database and sensor location pair.
        person_list_two:
            IDs of persons whose data is contained in statistical_features_two. The first entry in this list
            corresponds to the first entry in the mean_statistical_values list and so on.
    """

    statistical_features_one, person_list_one = (
        extract_mean_features_statistical_measures_by_database_ID_and_sensor_location(
        database_id_one, sensor_location_id_one, feature_frame))
    statistical_features_two, person_list_two = (
        extract_mean_features_statistical_measures_by_database_ID_and_sensor_location(
        database_id_two, sensor_location_id_two, feature_frame))

    statistical_features_one = statistical_features_one.astype(float)
    statistical_features_two = statistical_features_two.astype(float)

    return statistical_features_one, statistical_features_two, person_list_one, person_list_two

def extract_mean_features_statistical_measures_by_database_ID_and_sensor_location\
                (database_ID, sensor_location_ID, feature_frame):
    """
    Returns the mean value of the statistical features for each individual person of a database and
    sensor location pair.

    Args:
        database_ID:
            id of the database
        sensor_location_ID:
            id of the sensor location
        feature_frame:
            during the feature_extraction phase, the statistical features were calculated from a different amount of
            gait cycles. This parameter indicates which of those calculated statistical features the comparison will
            be based of. Note: Only feature amounts that were indicated in the .envs file during feature extraction
            are valid here.

    Returns:
        mean_statistical_values:
            Means of statistical values for each person.
        person_list:
            IDs of persons whose data is contained in the feature list. The first entry in this list corresponds to the
            first entry in the mean_statistical_values list and so on.
    """
    #mean feature statistical measures of persons
    mean_feature_statistical_measure_of_each_person = []
    all_statistical_measures = extract_feature_stat_measure_subset(database_ID, sensor_location_ID, feature_frame)

    person_statistical_features_dict = {}

    for statistical_measures in all_statistical_measures:
        person_id = statistical_measures[12]
        if person_id not in person_statistical_features_dict:
            person_statistical_features_dict[person_id] = []
        person_statistical_features_dict[person_id].append(statistical_measures)

    person_statistical_features_dict = dict(sorted(person_statistical_features_dict.items()))
    person_list = list(person_statistical_features_dict.keys())

    if len(person_statistical_features_dict) == 1:
        statistical_features_one_person = next(iter(person_statistical_features_dict.values()))
        statistical_features_one_person = np.array(statistical_features_one_person)
        statistical_features_subset_values = statistical_features_one_person[:, 1:11]
        return calculate_mean_statistical_values(statistical_features_subset_values), person_list
    else:

        individual_person_statistical_features_arrays = list(person_statistical_features_dict.values())

        for statistical_features_one_person in individual_person_statistical_features_arrays:
            statistical_features_one_person = np.array(statistical_features_one_person)
            statistical_features_subset_values = statistical_features_one_person[:, 1:11]
            (mean_feature_statistical_measure_of_each_person.
             append(calculate_mean_statistical_values(statistical_features_subset_values)))

        return np.array(mean_feature_statistical_measure_of_each_person), person_list

def extract_feature_stat_measure_subset(database_ID, sensor_location_ID, feature_frame):
    """
    Extracts the statistical measures for a specific database and sensor location pair.

    Args:
        database_ID:
            id of the database
        sensor_location_ID:
            id of the sensor location
        feature_frame:
            during the feature_extraction phase, the statistical features were calculated from a different amount of
            gait cycles. This parameter indicates which of those calculated statistical features the comparison will
            be based of. Note: Only feature amounts that were indicated in the .envs file during feature extraction
            are valid here.

    Returns:
        statistical features:
            The statistical features.
    """

    statistical_features = []
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

        query = f"""SELECT
                        *
                    FROM 
                        Feature_Statistical_Measure_""" + str(feature_frame) + """ F
                        INNER JOIN Recording R ON F.Recording_ID = R.Recording_ID
                        INNER JOIN Ground G ON F.Ground_ID = G.Ground_ID
                    WHERE 
                        R.Database_Id = """ + str(database_ID) + """
                        AND F.Sensor_Location_ID = """ + str(sensor_location_ID) + """
                        AND G.Treadmill_ID = 0
                """
        cursor.execute(query)
        statistical_features = cursor.fetchall()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

    return np.array(statistical_features)

def calculate_mean_statistical_values(statistical_values):
    """
    Calculates the mean value for a list of statistical values.

    Args:
        statistical_values:
            List of statistical values.

    Returns:
        mean_statistical_values features:
            List of means for those statistical values.
    """
    statistical_values = np.array(statistical_values, dtype=object)
    statistical_values = statistical_values.astype(float)

    # Calculate Mean Cycle
    mean_statistical_values = np.array([])
    for i in range(0, 10):
        mean_statistical_values = np.append(mean_statistical_values, np.mean(statistical_values[:, i]))

    return mean_statistical_values

def perform_t_test_on_statistical_features(statistical_features_one, statistical_features_two, paired):
    """
    Performs a t-tet on each of the statistical features.

    Args:
        statistical_features_one:
            List of statistical features from the first dataset/sensor location pair.
        statistical_features_two:
            List of statistical features from the second dataset/sensor location pair.
        paired:
            If True, performs a paired t-test; otherwise, performs an independent (unpaired) t-test.

    Returns:
        t_tests features:
            List of p values for each t-test.
    """
    t_tests = []

    if statistical_features_one.size > 0 and statistical_features_two.size > 0:
        for i in range(statistical_features_one.shape[1]):
            current_feature_column_one = statistical_features_one[:, i].tolist()
            current_feature_column_two = statistical_features_two[:, i].tolist()
            if isinstance(current_feature_column_one[0], str):
                current_feature_column_one = [eval(i) for i in current_feature_column_one]
            if isinstance(current_feature_column_two[0], str):
                current_feature_column_two = [eval(i) for i in current_feature_column_two]

            t_tests.append(t_test_statistical_measures(current_feature_column_one, current_feature_column_two, paired))

    return t_tests

def t_test_statistical_measures(statistical_measures_one, statistical_measures_two, paired):
    """
    Performs a t-test on two sets of numerical measures.

    Args:
        statistical_measures_one:
            First sample of values.
        statistical_measures_two:
            Second sample of values.
        paired:
            If True, performs a paired t-test; otherwise, performs an independent (unpaired) t-test.

    Returns:
        p_val:
            The p value for the t-test.
    """
    warnings.simplefilter("error", RuntimeWarning)

    try:
        if paired:
            t_stat, p_val = ttest_rel(statistical_measures_one, statistical_measures_two)
        else:
            t_stat, p_val = ttest_ind(statistical_measures_one, statistical_measures_two)

    except RuntimeWarning:
        # Fallback to non-parametric test
        p_val = 1.0

    return p_val

def extract_mean_gait_cycle_by_database_ID_and_sensor_location(database_ID, sensor_location_ID):
    """
    Extracts the mean gait cycle for a specific database and sensor location pair.

    Args:
         database_ID:
            id of the database.
        sensor_location_ID:
            id of the sensor location.

    Returns:
        p_val:
            The p value for the t-test.
    """
    #mean gait cycles of persons
    mean_gait_cylce_of_each_person = []
    all_gait_cycles = extract_normalized_gait_cycle_subset(database_ID, sensor_location_ID)

    person_gait_cycle_dict = {}

    for gait_cycle in all_gait_cycles:
        person_id = gait_cycle[211]
        if person_id not in person_gait_cycle_dict:
            person_gait_cycle_dict[person_id] = []
        person_gait_cycle_dict[person_id].append(gait_cycle)

    if len(person_gait_cycle_dict) == 1:
        cylces_one_person = next(iter(person_gait_cycle_dict.values()))
        cylces_one_person = np.array(cylces_one_person)
        gait_cycle_subset_values = cylces_one_person[:, 1:201]
        return calculate_mean_gait_cycle_and_95_CI(gait_cycle_subset_values, True)
    else:

        individual_person_cycles_arrays = list(person_gait_cycle_dict.values())

        i = 0;
        for cylces_one_person in individual_person_cycles_arrays:
            cylces_one_person = np.array(cylces_one_person)
            gait_cycle_subset_values = cylces_one_person[:, 1:201]
            mean_gait_cylce_of_each_person.append(calculate_mean_gait_cycle_and_95_CI(gait_cycle_subset_values,
                                                                                      False))

        return calculate_mean_gait_cycle_and_95_CI(mean_gait_cylce_of_each_person, True)

def extract_normalized_gait_cycle_subset(database_ID, sensor_location_ID, correlation_flag=True):
    """
    Extracts the y- and y- normalized gait cycles for a specific database and sensor location pair.

    Args:
         database_ID:
            id of the database
        sensor_location_ID:
            id of the sensor location
        correlation_flag:
            boolean, indicating whether the quality measure should be considered when extracting the gait cycles or if
            all cycles should be returned.

    Returns:
        gait_cycles:
            y- and y- normalized gait cycles.
    """
    gait_cycles = []
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

        query = f"""SELECT
                        *
                    FROM 
                        Feature_Uniform_Accelerometer_Gait_Cycle F
                        INNER JOIN Recording R ON F.Recording_ID = R.Recording_ID
                        INNER JOIN Ground G ON F.Ground_ID = G.Ground_ID
                    WHERE 
                        R.Database_Id = {database_ID}
                        AND F.Sensor_Location_ID = {sensor_location_ID}
                        AND G.Treadmill_ID = 0
                """
        if correlation_flag:
            query = query + " AND F.Usable_Flag = True"
        cursor.execute(query)
        gait_cycles = cursor.fetchall()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

    return np.array(gait_cycles)

def calculate_mean_gait_cycle_and_95_CI(gait_cycles, confidence_intervall):
    """
    Extracts the y- and y- normalized gait cycles for a specific database and sensor location pair.

    Args:
         gait_cycles:
            list of gait cycles.
        confidence_intervall:
            boolean whether the confidence intervall should be calculated

    Returns:
        mean_cycle_values:
            Values of the mean gait cycle.
        mean_ci_values
            Values of the confidence intervall.
    """
    gait_cycles = np.array(gait_cycles, dtype=object)
    gait_cycles = gait_cycles.astype(float)

    # Calculate Mean Cycle
    mean_cycle_values = np.array([])
    mean_ci_values = np.array([])
    for i in range(0, 200):
        mean_cycle_values = np.append(mean_cycle_values, np.mean(gait_cycles[:, i]))
        if confidence_intervall:
            mean_deviation = np.std(gait_cycles[:, i], ddof=1)
            ci_value = 1.96 * mean_deviation / math.sqrt(len(gait_cycles))
            mean_ci_values = np.append(mean_ci_values, ci_value)
    if confidence_intervall:
        return (mean_cycle_values, mean_ci_values)
    else:
        return mean_cycle_values

def plot_comparison_results(mean_cycle_values_one, mean_cycle_values_two, mean_ci_one, mean_ci_two, color_one,
                            color_two, database_title_one, database_title_two, location_one, location_two, t_tests,
                            statistical_features_one, statistical_features_two):
    """
    Plots the result of comparison of a database and sensor location pair.

    Args:
         mean_cycle_values_one:
            Values of the first mean gait cycle.
        mean_cycle_values_two:
            Values of the second mean gait cycle.
        mean_ci_one:
            Values of the first confidence intervall.
        mean_ci_two:
            Values of the second confidence intervall.
        color_one:
            color for the plot of the first database and sensor location pair.
        color_two:
            color for the plot of the second database and sensor location pair.
        database_title_one:
            title of the first database.
        database_title_two:
            title of the second database.
        location_one:
            title of the first sensor location.
        location_two:
            title of the second sensor location.
        t_tests:
            p-values for the statistical comparison of the 10 statistical features
        statistical_features_one:
            List of statistical features from the first dataset/sensor location pair.
        statistical_features_two:
            List of statistical features from the second dataset/sensor location pair.
    """
    correlation_coefficient = np.corrcoef(mean_cycle_values_one, mean_cycle_values_two)

    plot_mean_with_95_CI(mean_cycle_values_one, mean_ci_one, color_one, database_title_one)
    plot_mean_with_95_CI(mean_cycle_values_two, mean_ci_two, color_two, database_title_two)
    plt.xlabel('Mean average gait cycle ' + location_one + ' ' + database_title_one + ' and ' + location_two + ' ' +
               database_title_two + '\n correlation coefficient: ' + str(round(correlation_coefficient[0, 1], 3)),
               ha='center')

    plt.savefig("figs/gait_cycle_comparison.svg", format='svg', dpi=600, bbox_inches='tight')

    plt.show()

    plot_boxplot_for_statistical_features(statistical_features_one, statistical_features_two, color_one, color_two,
                                          t_tests)

def plot_mean_with_95_CI(mean_cycle_values, mean_ci, color, legend):
    """
    Plots the result of comparison of a database and sensor location pair.

    Args:
         mean_cycle_values:
            Values of the first mean gait cycle.
        mean_ci:
            Values of the first confidence intervall.
        color:
            color for the plot.
        legend:
            possible text for the legend.
    """
    x_values = np.arange(len(mean_cycle_values))

    # Plotting mean values
    plt.plot(x_values, mean_cycle_values, color=color, label=legend)

    # Plotting the area between mean plus and minus ci
    plt.fill_between(x_values, mean_cycle_values - mean_ci, mean_cycle_values + mean_ci, color=color, alpha=0.5,
                     linewidth = 0, edgecolor = 'none')

    # Adding labels and title
    plt.xlabel('one gait cycle', fontname='Times New Roman', fontsize=8)
    plt.ylabel('normalized jerk', fontname='Times New Roman', fontsize=8)
    # Changing font to Times New Roman and size to 8 points
    plt.rcParams.update({'font.family': 'Arial', 'font.size': 8})
    # Changing font to Times New Roman and size to 8 points for ticks
    plt.xticks(fontname='Arial', fontsize=8)
    plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0], fontname='Times New Roman', fontsize=8)
    plt.tight_layout()

    # Adding legend
    plt.legend()

    new_rc_params = {
                     "svg.fonttype": 'none'
                     }
    plt.rcParams.update(new_rc_params)

    # Removing the top and right spines (lines)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Hiding y-axis labels and ticks
    #ax.yaxis.set_visible(False)

    # Fixing the y-axis range from 0 to 1.1
    plt.ylim(0, 1.1)

    return plt

def plot_boxplot_for_statistical_features(statistical_features_one, statistical_features_two, color_one,
                                          color_two, t_tests):
    """
    Plots the result of comparison of a database and sensor location pair.

    Args:
         statistical_features_one:
            List of statistical features from the first dataset/sensor location pair.
        statistical_features_two:
            List of statistical features from the second dataset/sensor location pair.
        color_one:
            color for the plot of the first database and sensor location pair.
        color_two:
            color for the plot of the second database and sensor location pair.
        t_tests:
            p-values for the statistical comparison of the 10 statistical features.
    """
    all_stars = []
    for i in range(len(t_tests)):
        current = t_tests[i]
        if current < 0.001:
            all_stars.append('***')
        elif current < 0.01:
            all_stars.append('**')
        elif current < 0.05:
            all_stars.append('*')
        else:
            all_stars.append('')

    ratios_one = statistical_features_one[:, [2, 3, 5, 7, 8, 9]]
    ratios_two = statistical_features_two[:, [2, 3, 5, 7, 8, 9]]
    ratios_names = ['r_m_dnp', 'r_sd_dnp', 'r_m_sd_dns', 'r_sd_sd_dns', 'r_m_sl', 'r_sd_sl']
    ratio_stars = [all_stars[x] for x in [2, 3, 5, 7, 8, 9]]

    m_dp_one = statistical_features_one[:, 0]
    m_dp_one = m_dp_one.reshape(m_dp_one.shape[0],1)
    m_dp_two = statistical_features_two[:, 0]
    m_dp_two = m_dp_two.reshape(m_dp_two.shape[0], 1)
    m_dp_name = ['m_dp']
    m_dp_star = [all_stars[0]]

    remaining_one = statistical_features_one[:, [1, 6, 4]]
    remaining_two = statistical_features_two[:, [1, 6, 4]]
    remaining_names = ['sd_dp', 'sd_sd_ds', 'm_sd_ds']
    remaining_stars = [all_stars[x] for x in [1, 6, 4]]
    def draw_plot(axis, data, offset, edge_color, fill_color):
        pos = np.arange(data.shape[1]) + offset
        bp = axis.boxplot(data, positions=pos, widths=0.3, patch_artist=True)
        for element in ['boxes', 'whiskers', 'fliers', 'medians', 'caps']:
            plt.setp(bp[element], color=edge_color)
        for patch in bp['boxes']:
            patch.set(facecolor=fill_color)
        for flier in bp['fliers']:
            flier.set(markeredgecolor=edge_color, alpha=0.5)

    fig, ax = plt.subplots()
    draw_plot(ax, ratios_one, -0.2, color_one, "white")
    draw_plot(ax, ratios_two, +0.2, color_two, "white")

    for i in range(len(ratios_names)):
        midpoint = (i - 0.2 + i + 0.2) / 2  # Center point between the two boxplots
        ax.text(midpoint, ax.get_ylim()[1], ratio_stars[i],
                 ha='center', va='bottom', fontsize=12)

    plt.xticks(range(np.shape(ratios_one)[1]), ratios_names, rotation=45)

    ytick_loc = [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0, 5.5, 6.0, 6.5, 7.0]
    ax.set_yticks(ytick_loc)
    # Changing font to Times New Roman and size to 8 points
    plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 8})
    new_rc_params = {
        "svg.fonttype": 'none'
    }
    plt.rcParams.update(new_rc_params)

    # Removing the top and right spines (lines)
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    # Hiding y-axis labels and ticks
    #ax.yaxis.set_visible(False)

    plt.tight_layout()
    plt.savefig("figs/statistical_features_one.svg", format='svg', dpi=600, bbox_inches='tight')

    plt.show()
    plt.close()

    # draw boxplot for m_dp and remaining features, with two y-axis
    fig, ax1 = plt.subplots()

    bp = ax1.boxplot(m_dp_one[:, 0], positions=[0 - 0.2], widths=0.3, patch_artist=True)
    for element in ['boxes', 'whiskers', 'fliers', 'medians', 'caps']:
        plt.setp(bp[element], color=color_one)
    for patch in bp['boxes']:
        patch.set(facecolor='white')
    for flier in bp['fliers']:
        flier.set(markeredgecolor=color_one, alpha=0.5)

    bp = ax1.boxplot(m_dp_two[:, 0], positions=[0 + 0.2], widths=0.3, patch_artist=True)
    for element in ['boxes', 'whiskers', 'fliers', 'medians', 'caps']:
        plt.setp(bp[element], color=color_two)
    for patch in bp['boxes']:
        patch.set(facecolor='white')
    for flier in bp['fliers']:
        flier.set(markeredgecolor=color_two, alpha=0.5)

    midpoint = (0 - 0.2 + 0 + 0.2) / 2  # Center point between the two boxplots
    ax1.text(midpoint, 1.44, m_dp_star[0],
            ha='center', va='bottom', fontsize=12)

    # Create a second y-axis sharing the same x-axis
    ax2 = ax1.twinx()

    for i in range(remaining_one.shape[1]):
        bp = ax2.boxplot(remaining_one[:, i], positions=[i+1-0.2], widths=0.3, patch_artist=True)
        for element in ['boxes', 'whiskers', 'fliers', 'medians', 'caps']:
            plt.setp(bp[element], color=color_one)
        for patch in bp['boxes']:
            patch.set(facecolor='white')
        for flier in bp['fliers']:
            flier.set(markeredgecolor=color_one, alpha=0.5)


        bp = ax2.boxplot(remaining_two[:, i], positions=[i+1+0.2], widths=0.3, patch_artist=True)
        for element in ['boxes', 'whiskers', 'fliers', 'medians', 'caps']:
            plt.setp(bp[element], color=color_two)
        for patch in bp['boxes']:
            patch.set(facecolor='white')
        for flier in bp['fliers']:
            flier.set(markeredgecolor=color_two, alpha=0.5)

    for i in range(len(remaining_names)):
        midpoint = (i + 1 - 0.2 + i + 1 + 0.2) / 2  # Center point between the two boxplots
        ax2.text(midpoint, ax2.get_ylim()[1], remaining_stars[i],
                 ha='center', va='bottom', fontsize=12)

    ytick_loc1 = [1.0, 1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5]
    ax1.set_yticks(ytick_loc1)

    ytick_loc2 = [0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45]
    ax2.set_yticks(ytick_loc2)

    plt.xticks(range(np.shape(remaining_one)[1]+1), rotation=45)

    x_label = np.concatenate((m_dp_name, remaining_names))

    ax1.set_xticks(np.arange(len(x_label)))
    ax1.set_xticklabels(x_label, rotation=45)
    # Change color of only one x-axis tick to green
    xticks = ax1.get_xticklabels()
    xticks[0].set_color('green')  # Change the color of the 4th x-axis tick to green
    # Changing font to Times New Roman and size to 8 points
    plt.rcParams.update({'font.family': 'Times New Roman', 'font.size': 8})
    new_rc_params = {
        "svg.fonttype": 'none'
    }
    plt.rcParams.update(new_rc_params)

    # Change color of only one x-axis tick to green
    yticks = ax1.get_yticklabels()
    for tick in yticks:
        tick.set_color('green')

    # Hide "0-ytick" including the tick itself
    ax1.yaxis.set_major_locator(plt.FixedLocator([1.05, 1.1, 1.15, 1.2, 1.25, 1.3, 1.35, 1.4, 1.45, 1.5]))
    # Removing the top and right spines (lines)
    ax1.spines['top'].set_visible(False)
    ax2.spines['top'].set_visible(False)


    plt.tight_layout()
    plt.savefig("figs/statistical_features_two.svg", format='svg', dpi=600, bbox_inches='tight')

    plt.show()
    plt.close()

def draw_gait_cycles_correlations():
    """
    Plots Pearson correlation values for database and sensor location pairs. The correlation within the gait cycles of
    a subject will be plotted (box plot) as well as the correlation between the averaged gait cycle of each subject
    (triangle).
    Note that the database and sensor location pairs have to be added to the lost below ('db_sensor_pairs').
    """
    db_sensor_pairs = [(1, 9, 'Pk'), (1, 10, 'Pk'), (1, 11, 'Pk'), (2, 20, 'Ak'), (2, 21, 'Ak'), (2, 18, 'Wr'),
                       (2, 19, 'Wa'), (3, 9, 'Pk'), (3, 13, 'Wa'), (4, 14, 'Wa'), (5, 16, 'Wa'), (5, 12, 'Wa'),
                       (5, 14, 'Wa'), (5, 15, 'Wa'), (6, 16, 'Wa'), (6, 12, 'Wa'), (6, 14, 'Wa'), (7, 17, 'Wr'),
                       (7, 22, 'Sh'), (7, 24, 'Tg'), (7, 23, 'Sh'), (7, 25, 'Tg'), (7, 26, 'Wa')]

    list_of_mean_across = []
    list_of_means_within = []

    for pair in db_sensor_pairs:

        mean_across, ci = calculate_correlation_across_subject_cycles_by_database_ID_and_sensor_location(pair[0],
                                                                                                         pair[1])
        list_of_mean_across.append(mean_across)
        means_within = calculate_correlation_within_each_subject_cycles_by_database_ID_and_sensor_location(pair[0],
                                                                                                           pair[1])
        list_of_means_within.append(means_within)

    plot_correlations(list_of_means_within, list_of_mean_across, db_sensor_pairs)

def calculate_correlation_across_subject_cycles_by_database_ID_and_sensor_location(database_ID, sensor_location_ID):
    """
    Calculates the average Pearson correlation coefficient between the mean cycles of each person of one db
    and sensor position.

    Args:
        database_ID:
            id of the database
        sensor_location_ID:
            id of the sensor location

    Returns:
        average_corr:
            Average Pearson correlation coefficient.
        ci_value:
            Confidence interval value for the averaged correlation coefficient.
    """
    #mean gait cycles of persons
    mean_gait_cylce_of_each_person = []
    person_gait_cycle_dict = extract_gait_cycles_ordered_by_subject(database_ID, sensor_location_ID)

    if len(person_gait_cycle_dict) == 1:
        return None, None
    else:
        individual_person_cycles_arrays = list(person_gait_cycle_dict.values())

        for cylces_one_person in individual_person_cycles_arrays:
            gait_cycle_subset_values = extract_gait_cycle_values(cylces_one_person)
            mean_gait_cylce_of_each_person.append(calculate_mean_gait_cycle_and_95_CI(gait_cycle_subset_values, False))

        return calculate_average_correlation(mean_gait_cylce_of_each_person)

def extract_gait_cycles_ordered_by_subject(database_ID, sensor_location_ID):
    """
    Extracts all gait cycles for a specific database_id and sensor_location_id grouped by subject_id.

    Args:
        database_ID:
            id of the database
        sensor_location_ID:
            id of the sensor location

    Returns:
        person_gait_cycle_dict:
            List of gait cycles grouped by subject_id.
    """
    all_gait_cycles = extract_normalized_gait_cycle_subset(database_ID, sensor_location_ID)

    person_gait_cycle_dict = {}

    for gait_cycle in all_gait_cycles:
        person_id = gait_cycle[211]
        if person_id not in person_gait_cycle_dict:
            person_gait_cycle_dict[person_id] = []
        person_gait_cycle_dict[person_id].append(gait_cycle)
    return person_gait_cycle_dict

def extract_gait_cycle_values(cylces_one_person):
    """
    Extracts only the gait cycle values of a gait cycle instance from the db.

    Args:
        cylces_one_person:
            Gait cycles retrieved from the database.

    Returns:
        gait_cycle_subset_values:
            Gait cycle values without foreign keys.
    """
    cylces_one_person = np.array(cylces_one_person)
    gait_cycle_subset_values = cylces_one_person[:, 1:201]
    return gait_cycle_subset_values

def calculate_average_correlation(value_list):
    """
    Calculates average Pearson correlation coefficient between a list of values.

    Args:
        value_list:
            List of values whose correlation coefficient is to be calculated.

    Returns:
        average_corr:
            Average Pearson correlation coefficient.
        ci_value:
            Confidence interval value for the averaged correlation coefficient.
    """
    num_entries = len(value_list)
    correlations = []

    if num_entries == 1:
        return None, None
    # Loop over each pair of entries
    for i in range(num_entries):
        for j in range(i + 1, num_entries):
            # Calculate the correlation coefficient between the two entries
            corr = np.corrcoef(value_list[i], value_list[j])[0, 1]
            correlations.append(corr)

    # Calculate the average correlation coefficient
    average_corr = np.mean(correlations)
    std_correlation = np.std(correlations)
    ci_value = 1.96 * std_correlation / math.sqrt(len(value_list))

    return average_corr, ci_value

def calculate_correlation_within_each_subject_cycles_by_database_ID_and_sensor_location\
                (database_ID, sensor_location_ID):
    """
    Calculates the average Pearson correlation coefficient between all cycles of one subject. This is done for each
    subject of one database and sensor location pair.

    Args:
        database_ID:
            id of the database.
        sensor_location_ID:
            id of the sensor location.

    Returns:
        mean_r_value_of_each_person:
            averaged Pearson correlation coefficient for each person.
    """
    mean_r_value_of_each_person = []
    person_gait_cycle_dict = extract_gait_cycles_ordered_by_subject(database_ID, sensor_location_ID)

    individual_person_cycles_arrays = list(person_gait_cycle_dict.values())

    for cylces_one_person in individual_person_cycles_arrays:
        gait_cycle_subset_values = extract_gait_cycle_values(cylces_one_person)
        gait_cycle_subset_values = gait_cycle_subset_values.tolist()
        gait_cycle_subset_values = [
            [float(value) for value in sublist]
            for sublist in gait_cycle_subset_values
        ]

        mean, ci = calculate_average_correlation(gait_cycle_subset_values)
        if mean is not None:
            mean_r_value_of_each_person.append(mean)

    return mean_r_value_of_each_person

def plot_correlations(list_of_means_within, list_of_mean_across, db_sensor_pairs):
    """
    Plots Pearson correlation values for database and sensor location pairs. The correlation within the gait cycles of
    a subject will be plotted (box plot) as well as the correlation between the averaged gait cycle of each subject
    (triangle).

    Args:
        list_of_means_within:
            List of averaged Pearson correlation coefficient for each person.
        list_of_mean_across:
            id of the sensor location.

    Returns:
        list_of_means_within:
            list of averaged Pearson correlation coefficient for correlation of gait cycles within each person.
        list_of_mean_across:
            list of averaged Pearson correlation coefficient for correlation between the gait cycles averaged for
            each person.
        db_sensor_pairs:
            database_id and sensor_location_id as well as acronym for the location for each database and
            sensor location pair in this plot.
    """
    # Number of elements in list_of_means_within
    num_elements = len(list_of_means_within)

    # Create a figure and axis
    fig, ax = plt.subplots()

    # Iterate over each element in list_of_means_within and list_of_mean_across
    for i in range(num_elements):
        db_id = db_sensor_pairs[i][0]
        color = get_color(db_id)
        # Create boxplot for the current element in list_of_means_within
        ax.boxplot(list_of_means_within[i], positions=[i + 1], widths=0.6, patch_artist=False,
                   boxprops=dict(color=color),
                   whiskerprops = dict(color=color),
                   capprops=dict(color=color),
                   medianprops=dict(color=color),
                   flierprops=dict(markeredgecolor=color, alpha=0.5)
                   )

        # Mark the value of the current element in list_of_mean_across with a triangle
        if list_of_mean_across[i] is not None:
            ax.plot(i + 1, list_of_mean_across[i], 'k^')

        ## Display the number of elements in the boxplot above it
        ax.text(i + 1, 1.005, str(len(list_of_means_within[i])), ha='center', va='bottom', rotation=45)

    # Set x ticks labels
    ax.set_xticks(np.arange(1, num_elements + 1))
    ax.set_xticklabels([str(tup[2]) for tup in db_sensor_pairs])

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Rotate x-tick labels 45 degrees
    plt.xticks(rotation=45)

    plt.savefig("figs/gait_cycle_correlations_within_and_across.svg", format='svg', dpi=600)

    # Show the plot
    plt.show()

def correlate_sensors():
    """
    Plots a correlation matrix using the Pearson correlation for a list of database and sensor location pairs. This is
    done separately for centred and non-centred sensors.
    Note: The database and sensor location ids need to be filled in the two lists below.
    """
    list_non_centered = [(1, 9, 'Pk'), (1, 10, 'Pk'), (1, 11, 'Pk'), (2, 20, 'Ak'), (2, 21, 'Ak'), (2, 18, 'Wr'),
                         (3, 9, 'Pk'), (3, 13, 'Wa'), (5, 16, 'Wa'), (5, 12, 'Wa'), (6, 16, 'Wa'), (6, 12, 'Wa'),
                         (7, 17, 'Wr'), (7, 22, 'Sh'), (7, 24, 'Tg'), (7, 23, 'Sh'), (7, 25, 'Tg')]
    list_centered = [(2,19, 'Wa'), (4,14, 'Wa'), (5,14, 'Wa'), (5,15, 'Wa'), (6,14, 'Wa'), (7,26, 'Wa')]


    calculate_correlations_between_sensors(list_non_centered, False)
    calculate_correlations_between_sensors(list_centered, True)

def calculate_correlations_between_sensors(list_sensors, centered):
    """
    Plots correlation matrix using the Pearson correlation for a list of database and sensor location pairs.

        Args:
            list_sensors:
                list of database_id and sensor_location_id as well as acronym for the location for each database and
                sensor location pair in this correlation matrix.
            centered:
                boolean, indicating whether the list is from centred sensors.
        """
    mean_cycle_list = []
    positions = []

    for db_sensor_pair in list_sensors:
        mean_cycle, _ = extract_mean_gait_cycle_by_database_ID_and_sensor_location(db_sensor_pair[0], db_sensor_pair[1])
        mean_cycle_list.append(mean_cycle)
        positions.append(db_sensor_pair[2])

    # Convert the data to a DataFrame
    df = pd.DataFrame(mean_cycle_list).transpose()

    # Calculate the correlation matrix
    corr_matrix = df.corr()

    mask = np.tril(np.ones_like(corr_matrix, dtype=bool))

    if centered:
        map = sns.clustermap(corr_matrix, mask = mask, row_cluster=False, col_cluster=False, cmap="magma_r", vmin=0.5,
                             vmax=1, figsize=(10,10), xticklabels=positions, yticklabels=positions, cbar=False)
        map.cax.set_visible(False)

        fig = map.fig

        # Databases colorbar
        heatmap_pos = map.ax_heatmap.get_position()
        ax1 = fig.add_axes([heatmap_pos.x0, heatmap_pos.y1 + 0.03, heatmap_pos.width, 0.02])
        ax1.set_xlim(0, 10)
        ax1.set_ylim(0, 1)
        ax1.axis('off')
        colors = ['green', 'sandybrown', 'peru', 'goldenrod', 'purple']
        labels = ['Marea', 'OU-ISIR-ISD1', 'OU-ISIR-ISD2', 'OU-ISIR-SAID', 'DBHuGa']
        segments_length = [1, 1, 2, 1, 1]
        widths = []
        for i, length in enumerate(segments_length):
            widths.append(10 * segments_length[i] / 6)
        start = 0
        for i in range(len(labels)):
            ax1.add_patch(Rectangle((start, 0), widths[i], 1, color=colors[i]))
            ax1.text(start + widths[i] / 2, 0.5, labels[i], ha='center', va='center', fontsize=8)
            start += widths[i]

    else:
        map = sns.clustermap(corr_matrix, mask=mask, row_cluster=False, col_cluster=False, cmap="magma_r",
                             vmin=0.5, vmax=1, xticklabels=positions, yticklabels=positions, figsize=(10,10))

        heatmap_pos = map.ax_heatmap.get_position()
        map.cax.set_position([
            heatmap_pos.x0 - 0.05,
            heatmap_pos.y0,
            0.02,
            heatmap_pos.height
        ])

        fig = map.fig

        # Databases colorbar
        ax1 = fig.add_axes([heatmap_pos.x0, heatmap_pos.y1 + 0.03, heatmap_pos.width, 0.02])
        ax1.set_xlim(0, 10)
        ax1.set_ylim(0, 1)
        ax1.axis('off')

        colors = ['red', 'green', 'cyan', 'peru', 'goldenrod', 'purple']
        labels = ['McGill', 'Marea', 'Vajdi', 'OU-ISIR-ISD2', 'OU-ISIR-SAID', 'DBHuGa']
        segments_length = [3, 3, 2, 2, 2, 5]
        widths = []
        for i, length in enumerate(segments_length):
            widths.append(10 * segments_length[i] / 17)
        start = 0
        for i in range(len(labels)):
            ax1.add_patch(Rectangle((start, 0), widths[i], 1, color=colors[i]))
            ax1.text(start + widths[i] / 2, 0.5, labels[i], ha='center', va='center', fontsize=8)
            start += widths[i]

    map.ax_heatmap.xaxis.tick_top()
    map.ax_heatmap.xaxis.set_label_position('top')

    map.ax_heatmap.yaxis.tick_right()
    map.ax_heatmap.yaxis.set_label_position('right')

    for label in map.ax_heatmap.get_yticklabels():
        label.set_verticalalignment('center')

    if centered:
        plt.savefig("figs/correlation_matrix_centered.svg", format='svg', dpi=600)
    else:
        plt.savefig("figs/correlation_matrix_non_centered.svg", format='svg', dpi=600)

    plt.show()

if __name__ == '__main__':
    compare_sensors(7, 22, 7, 24)
    draw_gait_cycles_correlations()
    correlate_sensors()