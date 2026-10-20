"""
This module contains  functions for performing a bi-gender classification tasks and plotting the results.
The three main methods here are

calculate_accuracies():
    Calculates classification accuracy for a bi-gender classification task using different ways of training and testing
    data, originating from two database and sensor location pairs, as well as classifiers.
plot_accuracies():
    Plots the accuracies of several performed classifications with comparison boxes/comparison bars.
get_csvs_for_anova():
    Extract csv for performance of an anova.

"""
import ast
import copy
import csv
import os
import random
import numpy as np
import pandas as pd
from dotenv import load_dotenv
from scipy import stats

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, roc_auc_score
from sklearn.model_selection import StratifiedKFold, StratifiedGroupKFold
import matplotlib.pyplot as plt

from Database.Visualization import plot_data as mle
import psycopg2
from psycopg2 import Error
from sklearn.decomposition import PCA


def calculate_accuracies():
    """
    Calculates classification accuracy for a bi-gender classification task using different ways of training and testing
    data, originating from two database and sensor location pairs, as well as classifiers.
    Note that the comparison pairs need to be added manually below.
    """
    create_csv()

    list_comparisons = []
    list_explained_variances = []

    # right and left shin DBHuGa
    list_comparisons.append([7, 22, 7, 23])
    # right shin and right thigh DBHuGa
    list_comparisons.append([7, 22, 7, 24])
    # right shin and wrist DBHuGa
    list_comparisons.append([7, 22, 7, 17])

    # left waist and left waist ISIR SAID
    list_comparisons.append([6, 12, 6, 16])

    # left waist ISIR SAID and Vajdi
    list_comparisons.append([6, 12, 3, 13])

    # right pocket Vajdi and right thigh DbHuGa
    list_comparisons.append([3, 9, 7, 24])

    # left pocket McGill and right pocket Vajdi
    list_comparisons.append([3, 9, 1, 11])

    seen_pairs = set()

    for comparison in list_comparisons:
        print(comparison)
        database_ID_one = comparison[0]
        sensor_location_ID_one = comparison[1]

        database_ID_two = comparison[2]
        sensor_location_ID_two = comparison[3]

        person_IDs_one, statistical_features_data_one = get_statistical_features_for_ml(database_ID_one,
                                                                                        sensor_location_ID_one)
        person_IDs_two, statistical_features_data_two = get_statistical_features_for_ml(database_ID_two,
                                                                                        sensor_location_ID_two)

        pca_cycle_data_one, explained_variances_one = get_cycles_for_ml(database_ID_one, sensor_location_ID_one,
                                                                       person_IDs_one)
        pca_cycle_data_two, explained_variances_two = get_cycles_for_ml(database_ID_two, sensor_location_ID_two,
                                                                     person_IDs_two)

        pair_one = (database_ID_one, sensor_location_ID_one)
        pair_two = (database_ID_two, sensor_location_ID_two)

        if pair_one not in seen_pairs:
            list_explained_variances.append(sum(explained_variances_one))
        seen_pairs.add(pair_one)

        if pair_two not in seen_pairs:
            list_explained_variances.append(sum(explained_variances_two))
        seen_pairs.add(pair_two)


        ml_calculations(statistical_features_data_one, statistical_features_data_two, pca_cycle_data_one,
                        pca_cycle_data_two)

    print(len(list_explained_variances))
    print(list_explained_variances)
    print(np.mean(list_explained_variances))
    print(np.std(list_explained_variances))

def create_csv():
    """
    Creates the csv file for the results of the classification task.
    """

    column_names = ['DB_1_ID', 'DB_1_name', 'Sensor_1_ID', 'Sensor_1_name', 'number_persons_one', 'DB_2_ID',
                    'DB_2_name', 'Sensor_2_ID', 'Sensor_2_name', 'number_persons_two', 'Classifier', 'comparison_type',
                    'feature_type', 'n_folds', 'accuracy_mean', 'accuracy_std', 'precision', 'recall', 'specificity',
                    'F1_score', 'auc_mean', 'auc_std', 'all_accuracies', 'fold_sizes', 'significant', 'p_value']

    file_path = os.path.join('..', '..', 'Results', 'results.csv')

    # Open a new CSV file for writing
    with open(file_path, mode='w', newline='') as file:
        writer = csv.writer(file, delimiter=';')

        # Write the column names (header)
        writer.writerow(column_names)

def get_statistical_features_for_ml(database_ID, sensor_location_ID):
    """
    Extracts one random set of statistical features for each person of a database and
    sensor location pair togeter with te corresponding metadata (database, sensor location...).

    Args:
        database_ID:
            id of the database.
        sensor_location_ID:
            id of the sensor location.

    Returns:
        person_IDs:
            List of person_ids for the data.
        data:
            The statistical features and metadata.
    """
    database_name = get_database_name(database_ID)[0]
    sensor_location_name = get_sensor_location_name(sensor_location_ID)

    statistical_features = extract_statistical_features_by_database_ID_and_sensor_location_per_person(database_ID,
                                                                                                    sensor_location_ID)
    statistical_features = select_random_items(statistical_features, 1)

    # Convert dictionary items to a list
    statistical_features = list(statistical_features.values())

    person_IDs = [statistical_features_one_person[0][12] for statistical_features_one_person in statistical_features]

    gender_IDs = []
    for person_ID in person_IDs:
        gender_IDs.append(extract_gender_ID_by_person_ID(person_ID)[0])

    # Only keep gait cycle information
    only_statistical_features = [[one_feature_set[1:11] for one_feature_set in statistical_features_one_person]
                                 for statistical_features_one_person in statistical_features]
    only_statistical_features = [arr[0] for arr in only_statistical_features]
    only_statistical_features = np.array(only_statistical_features)

    data = pd.DataFrame(only_statistical_features, columns=[None] * 10)
    data['Person_ID'] = person_IDs
    data['Gender_ID'] = gender_IDs
    data['Database_ID'] = [database_ID] * len(data)
    data['Database_name'] = [database_name] * len(data)
    data['Sensor_Location_ID'] = [sensor_location_ID] * len(data)
    data['Sensor_Location_name'] = [sensor_location_name] * len(data)

    return person_IDs, data

def get_database_name(database_id):
    """
    Retrieves the database name for a specific database_id.

    Args:
        database_ID:
            id of the database.

    Returns:
        database_name:
            name of the database.
    """
    database_name = []
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

        query = f"""SELECT DISTINCT
                            Database_Title
                        FROM 
                            Recording R
                        WHERE 
                            R.Database_ID = {database_id}
                    """
        cursor.execute(query)
        database_name = cursor.fetchone()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

    return database_name

def get_sensor_location_name(sensor_location_id):
    """
    Retrieves the sensor location name for a specific database_id.

    Args:
        database_ID:
            id of the sensor location.

    Returns:
        sensor_location:
            body_side and body_area of the sensor location.
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
                        Body_Side_Title, Body_Area_Title
                    FROM 
                        Sensor_Location S
                    WHERE 
                        S.Sensor_Location_ID = {sensor_location_id}
                        """
        cursor.execute(query)
        body_side, body_area = cursor.fetchone()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

    return body_side + ' ' + body_area

def extract_statistical_features_by_database_ID_and_sensor_location_per_person(database_ID, sensor_location_ID):
    """
    Extracts the statistical measures for a specific database and sensor location pair grouped by person_id.

    Args:
        database_ID:
            id of the database.
        sensor_location_ID:
            id of the sensor location.

    Returns:
        person_statistical_measure_dict:
            statistical features grouped by person_id.
    """
    all_statistical_features = mle.extract_feature_stat_measure_subset(database_ID, sensor_location_ID, 10)

    person_statistical_measure_dict = {}

    for statistical_features in all_statistical_features:
        person_id = statistical_features[12]
        if person_id not in person_statistical_measure_dict:
            person_statistical_measure_dict[person_id] = []
        person_statistical_measure_dict[person_id].append(statistical_features)

    return person_statistical_measure_dict

def select_random_items(data_dict, num_items):
    """
    Extracts the statistical measures for a specific database and sensor location pair grouped by person_id.

    Args:
        data_dict:
            input_data.
        num_items:
            amount of items to be randomly picked.

    Returns:
        selected_items:
            randomly selected items.
    """
    selected_items = {}
    for key, value_list in data_dict.items():
        if len(value_list) >= num_items:
            selected_items[key] = random.sample(value_list, num_items)
        else:
            selected_items[key] = value_list
    return selected_items

def extract_gender_ID_by_person_ID(person_ID):
    """
    Extracts the gender ID of a person.

    Args:
        person_ID (int):
            Person ID of the person whose gender we want to know.

    Returns:
        gender_ID (int):
            Gender ID of the person (0 = male, 1 = female)
    """

    gender_ID = []
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
                        sex_id
                    FROM 
                        Person p
                    WHERE 
                        P.Person_ID = {person_ID}
                """
        cursor.execute(query)
        gender_ID = cursor.fetchone()

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

    return gender_ID

def get_cycles_for_ml(database_ID, sensor_location_ID, person_IDs_to_use):
    """
    Extracts 10 gait cycles for each person for a database and sensor location pair and performs a pca on it.

    Args:
        database_ID:
            id of the database.
        sensor_location_ID:
            id of the sensor location.
        person_IDs_to_use:
            ids of persons whose data we want to extract.

    Returns:
        data:
            PCA reduced data of the gait cycles (first 10. components).
        explained_variances:
            Explained variances of the gait cycles.
    """
    database_name = get_database_name(database_ID)[0]
    sensor_location_name = get_sensor_location_name(sensor_location_ID)

    cycles = extract_mean_gait_cycle_by_database_ID_and_sensor_location_per_person(database_ID, sensor_location_ID)
    cycles = select_random_items(cycles, 10)
    # Convert dictionary items to a list
    cycles = list(cycles.values())
    #delete persons that don't appear in person_IDs_to_use
    cycles = [
        inner_list for inner_list in cycles if inner_list[0][211] in person_IDs_to_use
    ]


    person_IDs = [cycles_one_person[0][211] for cycles_one_person in cycles]
    person_IDs = list(set(person_IDs) & set(person_IDs_to_use))

    gender_IDs = []
    for person_ID in person_IDs:
        gender_IDs.append(extract_gender_ID_by_person_ID(person_ID)[0])

    # Only keep gait cycle information
    only_gait_cycles = [[one_cycle[1:201] for one_cycle in cycles_one_person] for cycles_one_person in cycles]

    only_gait_cycles_concatenated = []
    for cycles_one_person in only_gait_cycles:
        # Concatenate all arrays in the inner list
        data = np.concatenate(cycles_one_person, axis=0)
        only_gait_cycles_concatenated.append(data)

    only_gait_cycles_concatenated = np.array(only_gait_cycles_concatenated)
    # Perform PCA
    pca = PCA(n_components=10, random_state=42)
    principal_components = pca.fit_transform(only_gait_cycles_concatenated)
    explained_variances = pca.explained_variance_ratio_

    # Combine the array and lists into a DataFrame
    data = pd.DataFrame(principal_components, columns=[None] * 10)
    data['Person_ID'] = person_IDs
    data['Gender_ID'] = gender_IDs
    data['Database_ID'] = [database_ID] * len(data)
    data['Database_name'] = [database_name] * len(data)
    data['Sensor_Location_ID'] = [sensor_location_ID] * len(data)
    data['Sensor_Location_name'] = [sensor_location_name] * len(data)

    return data, explained_variances

def extract_mean_gait_cycle_by_database_ID_and_sensor_location_per_person(database_ID, sensor_location_ID):
    """
    Extracts the gait cycles for a specific database and sensor location pair grouped by person_id.

    Args:
        database_ID:
            id of the database.
        sensor_location_ID:
            id of the sensor location.

    Returns:
        person_statistical_measure_dict:
            statistical features grouped by person_id.
    """

    all_gait_cycles = mle.extract_normalized_gait_cycle_subset(database_ID, sensor_location_ID)

    person_gait_cycle_dict = {}

    for gait_cycle in all_gait_cycles:
        person_id = gait_cycle[211]
        if person_id not in person_gait_cycle_dict:
            person_gait_cycle_dict[person_id] = []
        person_gait_cycle_dict[person_id].append(gait_cycle)

    return person_gait_cycle_dict

def ml_calculations(statistical_features_data_one, statistical_features_data_two, pca_cycle_data_one,
                    pca_cycle_data_two):
    """
    Perform a bi-gender classification task using different ways of training and testing
    data, originating from two database and sensor location pairs, as well as classifiers.

    Args:
        statistical_features_data_one:
            statistical features from the first database sensor location pair.
        statistical_features_data_two:
            statistical features from the second database sensor location pair.
        pca_cycle_data_one:
            pca reduced gait cycle data from the first database sensor location pair.
        pca_cycle_data_two:
            pca reduced gait cycle data from the second database sensor location pair.
    """
    comparison_information_first_part = get_comparison_information(statistical_features_data_one,
                                                                   statistical_features_data_two)

    n_data_one = statistical_features_data_one.shape[0]
    n_data_two = statistical_features_data_two.shape[0]

    if n_data_one > n_data_two:
        size_smaller_dataset = n_data_two
        statistical_features_data_one, pca_cycle_data_one = subsampleToSameSizes(statistical_features_data_one,
                                                                            pca_cycle_data_one, size_smaller_dataset)
    else:
        size_smaller_dataset = n_data_one
        statistical_features_data_two, pca_cycle_data_two = subsampleToSameSizes(statistical_features_data_two,
                                                                            pca_cycle_data_two, size_smaller_dataset)

    k = min(size_smaller_dataset // 5, 10)

    #only first sensor
    calculate_one_sensor(statistical_features_data_one, True, True,
                         comparison_information_first_part, k)
    calculate_one_sensor(pca_cycle_data_one, False, True,
                         comparison_information_first_part, k)

    #only second sensor
    calculate_one_sensor(statistical_features_data_two, True, False,
                         comparison_information_first_part, k)
    calculate_one_sensor(pca_cycle_data_two, False, False,
                         comparison_information_first_part, k)

    calculate_on_both_sensors(statistical_features_data_one, statistical_features_data_two, True,
                                  comparison_information_first_part, k)
    calculate_on_both_sensors(pca_cycle_data_one, pca_cycle_data_two, False,
                                  comparison_information_first_part, k)

    train_on_one_test_on_other(statistical_features_data_one, statistical_features_data_two,
                                   True, comparison_information_first_part, k)
    train_on_one_test_on_other(pca_cycle_data_one, pca_cycle_data_two,
                                   False, comparison_information_first_part, k)


def get_comparison_information(data_sensor_one, data_sensor_two):
    """
    Extracts metadata for the classification task like number of persons and name of database and sensor location used.

    Args:
        data_sensor_one:
            data of first database and sensor location pair.
        data_sensor_two:
            data of second database and sensor location pair.

    Returns:
        comparison_information:
            metadata for the classification task (number persons, name of database and sensor location used)
    """
    database_id_one = data_sensor_one.iloc[0]['Database_ID']
    database_name_one = data_sensor_one.iloc[0]['Database_name']
    sensor_location_id_one = data_sensor_one.iloc[0]['Sensor_Location_ID']
    sensor_location_name_one = data_sensor_one.iloc[0]['Sensor_Location_name']
    number_persons_one = data_sensor_one.shape[0]

    database_id_two = data_sensor_two.iloc[0]['Database_ID']
    database_name_two = data_sensor_two.iloc[0]['Database_name']
    sensor_location_id_two = data_sensor_two.iloc[0]['Sensor_Location_ID']
    sensor_location_name_two = data_sensor_two.iloc[0]['Sensor_Location_name']
    number_persons_two = data_sensor_two.shape[0]

    comparison_information = [database_id_one, database_name_one, sensor_location_id_one,
                              sensor_location_name_one, number_persons_one, database_id_two, database_name_two,
                              sensor_location_id_two, sensor_location_name_two, number_persons_two]
    return comparison_information

def subsampleToSameSizes(statistical_features, pca_cycles, size):
    """
    Subsamples a set of statistical features and pca reduced gait cycles to the same size (stratified).
    The two resulting datasets will be from the same persons.

    Args:
        statistical_features:
            te statistical features.
        pca_cycles:
            the pca reduced gait cycles.
        size:
            size the datasets should be sub-sampled to.

    Returns:
        statistical_features:
            te statistical features.
        pca_cycles:
            the pca reduced gait cycles.
    """
    statistical_features = sample_data_stratified(statistical_features, size)
    pca_cycles = pca_cycles[pca_cycles["Person_ID"].isin(statistical_features["Person_ID"])]
    return statistical_features, pca_cycles

def calculate_one_sensor(data, statistical_feature_boolean, first_sensor_boolean, comparison_information_first_part, k):
    """
    Perform a bi-gender classification task using different classifiers (SVM and Random forest) for data of one
    database and sensor location pair.

    Args:
        data:
            the data.
        statistical_feature_boolean:
            indication whether the data are statistical features (other option is pca reduced gait_cycle data).
        first_sensor_boolean:
            indication whether the data is from the first or the second sensor (each classification is done for two
            datbase and sensor location pairs).
        comparison_information_first_part:
            metadata for the classification task.
        k
            amount of folds for the cross validation.
    """
    comparison_information = copy.deepcopy(comparison_information_first_part)
    if first_sensor_boolean:
        comparison_information.append('Only Sensor A')
    else:
        comparison_information.append('Only Sensor B')

    if statistical_feature_boolean:
        comparison_information.append('Statistical_Features')
    else:
        comparison_information.append('Gait_Cycles')

    y = data['Gender_ID']
    x = data.iloc[:, :10]

    comparison_information.append(k)

    kf = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
    # generate folds
    folds = list(kf.split(x, y))

    training(y, x, folds, comparison_information)

def calculate_on_both_sensors(data_sensor_one, data_sensor_two, statistical_feature_boolean,
                              comparison_information_first_part, k):
    """
    Perform a bi-gender classification task using different classifiers (SVM and Random forest) for data of two
    database and sensor location pairs. The classifier is trained and tested on both.

    Args:
        data_sensor_one:
            data of the first sensor.
        data_sensor_two:
            data of the second sensor.
        statistical_feature_boolean:
            indication whether the data are statistical features (other option is pca reduced gait_cycle data).
        comparison_information_first_part:
            metadata for the classification task.
        k
            amount of folds for the cross validation.
    """
    modes = [('Train on Both keep smaller size', 0), ('Train on Both Double Smaller size', 1)]


    for mode in modes:

        comparison_information = copy.deepcopy(comparison_information_first_part)
        database_id_one = comparison_information[0]
        database_id_two = comparison_information[5]

        combined_data = combine_data(data_sensor_one, data_sensor_two, mode[1])

        comparison_information.append(mode[0])

        if statistical_feature_boolean:
            comparison_information.append('Statistical_Features')
        else:
            comparison_information.append('Gait_Cycles')

        comparison_information.append(k)

        y = combined_data['Gender_ID']
        x = combined_data.iloc[:, :10]

        group_ids = pd.factorize(list(zip(combined_data['Database_ID'], combined_data['Sensor_Location_ID'])))[0]
        group_ids = pd.Series(group_ids, index=combined_data.index, name='group_id')

        group_ids = np.asarray(group_ids).astype(str)
        gender_array = np.asarray(y).astype(str)

        y_strat = np.char.add(np.char.add(group_ids, "_"), gender_array)

        folds = []

        if database_id_one == database_id_two:
            sgkf = StratifiedGroupKFold(n_splits=k)

            for train_idx, test_idx in sgkf.split(x, y_strat, groups=combined_data['Person_ID']):
                folds.append((train_idx, test_idx))
        else:
            kf = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
            # generate folds
            folds = list(kf.split(x, y_strat))

        training(y, x, folds, comparison_information)

def combine_data(data_sensor_one, data_sensor_two, mode):
    """
    Combines two sets of data in a way, that the result contains the same amount of data from both.

    Args:
        data_sensor_one:
            data of first database and sensor location pair.
        data_sensor_two:
            data of second database and sensor location pair.
        mode:
            mode of data combination (0 if the size of the smaller dataset is to be doubled, here we use half of the
            data from the smaller dataset and add the same amount of data from the larger one, 1 if we want to keep all
            the data from the smaller dataset, enriched by the same amount of dta from the larger dataset, therefore
            doubling the size of the smaller dataset)

    Returns:
        combined_data:
            the combined data
    """
    if mode == 0:
        combined_data = combine_data_keep_size(data_sensor_one, data_sensor_two)

    elif mode == 1:
        combined_data = combine_data_double_size(data_sensor_two, data_sensor_one)

    return combined_data.sample(frac=1, random_state=42).reset_index(drop=True)

def combine_data_keep_size(data_sensor_one, data_sensor_two):
    """
    Combines two sets of data in a way, that the result contains the same amount of data from both. Half of the data
    from the smaller dataset is kept, enriched by the same amount of data from the larger one, therfore keeping the
    size of the smaller dataset.

    Args:
        data_sensor_one:
            data of first database and sensor location pair.
        data_sensor_two:
            data of second database and sensor location pair.

    Returns:
        combined_data:
            the combined data
    """
    if len(data_sensor_one) <= len(data_sensor_two):
        shorter_data = data_sensor_one
        longer_data = data_sensor_two
    else:
        shorter_data = data_sensor_two
        longer_data = data_sensor_one


    half_size = len(shorter_data) // 2
    shorter_data_reduced = sample_data_stratified(shorter_data, half_size)

    longer_data_sampled = sample_data_stratified(longer_data, len(shorter_data) - half_size)

    combined_data = pd.concat([shorter_data_reduced, longer_data_sampled]).reset_index(drop=True)

    return combined_data

def combine_data_double_size(data_sensor_one, data_sensor_two):
    """
    Combines two sets of data in a way, that the result contains the same amount of data from both. All data
    from the smaller dataset is kept, enriched by the same amount of data from the larger one, therefore doubling the
    size of the smaller dataset.

    Args:
        data_sensor_one:
            data of first database and sensor location pair.
        data_sensor_two:
            data of second database and sensor location pair.

    Returns:
        combined_data:
            the combined data.
    """
    if len(data_sensor_one) <= len(data_sensor_two):
        shorter_data = data_sensor_one
        longer_data = data_sensor_two
    else:
        shorter_data = data_sensor_two
        longer_data = data_sensor_one

    longer_data_sampled = sample_data_stratified(longer_data, len(shorter_data))

    combined_data = pd.concat([shorter_data, longer_data_sampled]).reset_index(drop=True)

    return combined_data

def sample_data_stratified(data, n):
    """
    Randomly subsamples data, stratified after gender_id.

    Args:
        data:
            data to be subsampled.
        n:
            size of the resulting list.

    Returns:
        sampled_df:
            stratified and subsampled list.
    """
    # Split by gender
    df0 = data[data['Gender_ID'] == 0]
    df1 = data[data['Gender_ID'] == 1]

    # Target equal distribution
    half = n // 2

    # Determine desired samples
    if n % 2 == 0:
        need0 = half
        need1 = half
    else:
        # Assign the extra sample to gender 1 (arbitrary; can be swapped)
        need0 = half
        need1 = half + 1

    # Actual available rows
    avail0 = len(df0)
    avail1 = len(df1)

    # Sample as much as possible from each group
    take0 = min(need0, avail0)
    take1 = min(need1, avail1)

    # How many are missing?
    missing = n - (take0 + take1)

    # Fill missing values from the group that has more remaining
    if missing > 0:
        if avail0 - take0 >= missing:
            take0 += missing
        elif avail1 - take1 >= missing:
            take1 += missing
        else:
            # Fallback: take everything available (when dataset < n)
            take0 = avail0
            take1 = avail1

    # Final sampling
    sample0 = df0.sample(n=take0, random_state=42)
    sample1 = df1.sample(n=take1, random_state=42)

    # Concatenate the two samples
    sampled_df = pd.concat([sample0, sample1])
    # Shuffle the resulting DataFrame to mix the rows
    sampled_df = sampled_df.sample(frac=1).reset_index(drop=True)

    return sampled_df

def train_on_one_test_on_other(data_sensor_one, data_sensor_two, statistical_feature_boolean,
                               comparison_information_first_part, k):
    """
    Perform a bi-gender classification task using different classifiers (SVM and Random forest) for data of two
    database and sensor location pairs. The classifier is trained on data from one sensor and tested on the other.

    Args:
        data_sensor_one:
            data of the first sensor.
        data_sensor_two:
            data of the second sensor.
        statistical_feature_boolean:
            indication whether the data are statistical features (other option is pca reduced gait_cycle data).
        comparison_information_first_part:
            metadata for the classification task.
        k
            amount of folds for the cross validation.
    """
    if len(data_sensor_one) <= len(data_sensor_two):
        data_sensor_two = sample_data_stratified(data_sensor_two, len(data_sensor_one))
    else:
        data_sensor_one = sample_data_stratified(data_sensor_one, len(data_sensor_two))

    for i in range (2):
        comparison_information = copy.deepcopy(comparison_information_first_part)

        if i == 0:
            comparison_information.append('Train on A Test on B')
        else:
            comparison_information.append('Train on B Test on A')

        if statistical_feature_boolean:
            comparison_information.append('Statistical_Features')
        else:
            comparison_information.append('Gait_Cycles')

        comparison_information.append(k)

        data_sensor_one, data_sensor_two = (
            sort_data_according_to_corresponding_person_IDs(data_sensor_one, data_sensor_two))

        if i == 0:
            y_one = data_sensor_one['Gender_ID']
            x_one = data_sensor_one.iloc[:, :10]

            y_two = data_sensor_two['Gender_ID']
            x_two = data_sensor_two.iloc[:, :10]
        else:
            y_one = data_sensor_two['Gender_ID']
            x_one = data_sensor_two.iloc[:, :10]

            y_two = data_sensor_one['Gender_ID']
            x_two = data_sensor_one.iloc[:, :10]

        kf = StratifiedKFold(n_splits=k, shuffle=True, random_state=42)
        # generate folds
        folds_one = list(kf.split(x_one, y_one))

        if not data_sensor_one['Database_ID'].equals(data_sensor_two['Database_ID']):
            folds_two = list(kf.split(x_two, y_two))
        else:
            folds_two = None

        training(y_one, x_one, folds_one, comparison_information, y_two, x_two, folds_two)

def sort_data_according_to_corresponding_person_IDs(data_one, data_two):
    # Find common person_ids
    common_ids = set(data_one['Person_ID']).intersection(set(data_two['Person_ID']))

    # Separate common and unique person_ids in both dataframes
    df1_common = data_one[data_one['Person_ID'].isin(common_ids)].sort_values(by='Person_ID').reset_index(drop=True)
    df2_common = data_two[data_two['Person_ID'].isin(common_ids)].sort_values(by='Person_ID').reset_index(drop=True)

    df1_unique = data_one[~data_one['Person_ID'].isin(common_ids)].sort_values(by='Person_ID').reset_index(drop=True)
    df2_unique = data_two[~data_two['Person_ID'].isin(common_ids)].sort_values(by='Person_ID').reset_index(drop=True)

    # Concatenate common and unique parts
    df1_sorted = pd.concat([df1_common, df1_unique]).reset_index(drop=True)
    df2_sorted = pd.concat([df2_common, df2_unique]).reset_index(drop=True)

    return df1_sorted, df2_sorted

def training(y, x, folds, comparison_information, y_two = None, x_two = None, folds_two = None):
    """
    Trains and tests classifiers (SVM and Random Forest).

    Args:
        y:
            labels of the data.
        x:
            features of the data.
        folds:
            folds of the data.
        comparison_information:
            metadata for the classification task.
        y_two:
            labels of the second sensor, when training is supposed to happen on one and testing on the other sensor.
        x_two:
            features of the second sensor, when training is supposed to happen on one and testing on the other sensor.
        folds_two:
            folds of the second sensor, when training is supposed to happen on one and testing on the other sensor.
    """
    # define models
    models = {
        "logistic Regression": LogisticRegression(),
        "Random Forest (Ensemble)": RandomForestClassifier()
    }


    # train and evaluate defined models
    for classifier, model in models.items():

        fold_sizes = []

        accuracies = []
        tns = 0
        fns = 0
        tps = 0
        fps = 0

        f1_scores = []
        aucs = []

        # iterate over folds to do training and validation
        for fold, (train_index, test_index) in enumerate(folds):
            # extract train and test set from current fold  (.iloc to get content of indices)
            if y_two is not None:
                if folds_two is not None:
                    train_index_two, test_index_two = folds_two[fold]
                    x_fold_train, x_fold_test = x.iloc[train_index], x_two.iloc[test_index_two]
                    y_fold_train, y_fold_test = y.iloc[train_index], y_two.iloc[test_index_two]
                else:
                    x_fold_train, x_fold_test = x.iloc[train_index], x_two.iloc[test_index]
                    y_fold_train, y_fold_test = y.iloc[train_index], y_two.iloc[test_index]
            else:
                x_fold_train, x_fold_test = x.iloc[train_index], x.iloc[test_index]
                y_fold_train, y_fold_test = y.iloc[train_index], y.iloc[test_index]

            # train model with current fold
            model.fit(x_fold_train, y_fold_train)

            # predict model on current test fold
            Y_pred = model.predict(x_fold_test)

            fold_sizes.append(len(Y_pred))
            # Accuracy
            accuracies.append(round(accuracy_score(y_fold_test, Y_pred),2))

            cm = confusion_matrix(y_fold_test, Y_pred)
            tn, fp, fn, tp = cm.ravel()

            tns += tn
            fps += fp
            fns += fn
            tps += tp


            if not len(np.unique(y_fold_test)) == 1:
                # AUC
                aucs.append(roc_auc_score(y_fold_test, Y_pred))

            # calculate confusion matrix for current fold and add to final confusion matrix
#            conf_matrix = confusion_matrix(Y_fold_test, Y_pred)
#            final_conf_matrix += conf_matrix

        # calculate mean and std for the metrics
        accuracy_mean = round(np.mean(accuracies), 2)
        accuracy_std = round(np.std(accuracies), 2)

        significant, p_value = t_test_above_chance_level(accuracies)

        precision = round((tps/(tps+fps)), 2)

        recall = round((tps / (tps + fns)), 2)

        specificity = round((tns / (tns + fps)), 2)

        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = round(2 * (precision * recall) / (precision + recall), 2)

        auc_mean = round(np.mean(aucs), 2)
        auc_std = round(np.std(aucs), 2)

        write_row_in_csv(comparison_information[0], comparison_information[1], comparison_information[2],
                         comparison_information[3], comparison_information[4], comparison_information[5],
                         comparison_information[6], comparison_information[7], comparison_information[8],
                         comparison_information[9], classifier, comparison_information[10], comparison_information[11],
                         comparison_information[12], accuracy_mean, accuracy_std, precision, recall, specificity,
                         f1_score, auc_mean, auc_std, accuracies, fold_sizes, significant, p_value)
        calculate_all_weighted_avergae_of_the_means()

def confusion_matrix(y_true, y_pred):
    """
    Calculates a confusion matrix for a performed classification task.

    Args:
        y_true:
            true labels.
        y_pred:
            predicted labels.

    Returns:
        cm:
            values of the confusion matrix.
    """
    # Initialize counters for confusion matrix
    TN = FP = FN = TP = 0

    # Loop through the actual and predicted labels
    for true, pred in zip(y_true, y_pred):
        if true == 0 and pred == 0:
            TN += 1  # True Negative
        elif true == 0 and pred == 1:
            FP += 1  # False Positive
        elif true == 1 and pred == 0:
            FN += 1  # False Negative
        elif true == 1 and pred == 1:
            TP += 1  # True Positive

    cm = np.array([[TN, FP],
                   [FN, TP]])

    return cm

def t_test_above_chance_level(accuracy_values, alpha=0.01):
    """
    Performs a t test for significance above chance level for a performed classification task.

    Args:
        accuracy_values:
            true labels.
        alpha:
            allowed alpha error.

    Returns:
        significant:
            indication whether the classifier performed significant over chance level.
        p_value:
            p value.
    """
    t_statistic, p_value = stats.ttest_1samp(accuracy_values, 0.5)
    p_value = p_value/2
    if np.mean(accuracy_values)<0.5:
        p_value = 1-p_value
    # Check if p-value is less than alpha

    if np.mean(accuracy_values) > 0.5 and p_value < alpha:
        return True, p_value
    else:
        return False, p_value

def write_row_in_csv(dB_1_ID, dB_1_name, sensor_1_ID, sensor_1_name, number_persons_one, dB_2_ID,
                    dB_2_name, sensor_2_ID, sensor_2_name, number_persons_two, classifier, comparison_type,
                     feature_type, n_folds, accuracy_mean, accuracy_std, precision, recall, specificity, f1_score,
                     auc_mean, auc_std, all_accuracies, fold_sizes, significant, p_value):
    """
    Writes results of classification to csv file.

    Args:
        dB_1_ID:
            id of first database.
        dB_1_name:
            name of first database.
        sensor_1_ID:
            id of first sensor.
        sensor_1_name:
            name of first sensor.
        number_persons_one:
            number subjects in data 1.
        dB_2_ID:
            id of second database.
        dB_2_name:
            name of second database.
        sensor_2_ID:
            id of second sensor.
        sensor_2_name:
            name of second sensor.
        number_persons_two:
            number subjects in data 2.
        classifier:
            classifier used (SVM or RF)
        comparison_type:
            comparison used (trained and tested on only one sensor, both or trained on one and tested on the other).
        feature_type:
            feature type used for classification (statistical features or gait cycles)
        n_folds:
            number of folds in classification.
        accuracy_mean:
            average classification accuracy over all folds.
        accuracy_std:
            std of classification accuracy over all folds.
        precision:
            precision of classification.
        recall:
            recall of classification.
        specificity:
            specificity of classification.
        f1_score:
            f1 score of classification.
        auc_mean:
            mena of auc of classification over all folds.
        auc_std:
             std of auc of classification over all folds.
        all_accuracies:
            classification accuracy for each fold.
        fold_sizes:
            sizes of the individual folds.
        significant:
            indication whether classifier performed significantly over chance level.
        p_value:
            p value for test of significance over chance level.
    """

    data = [dB_1_ID, dB_1_name, sensor_1_ID, sensor_1_name, number_persons_one, dB_2_ID, dB_2_name, sensor_2_ID,
                    sensor_2_name, number_persons_two, classifier, comparison_type, feature_type, n_folds,
                    accuracy_mean, accuracy_std, precision, recall, specificity, f1_score, auc_mean, auc_std,
                    all_accuracies, fold_sizes, significant, p_value]

    file_path = os.path.join('..', '..', 'Results', 'Results.csv')

    with open(file_path, mode='a', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        # Write the data rows
        writer.writerow(data)

def calculate_all_weighted_avergae_of_the_means():
    """
    Calculates weighted average of the means for classification accuracy for the performed classification task.
    """
    file_path = os.path.join('..', '..', 'Results', 'Results.csv')
    data = pd.read_csv(file_path, delimiter=';')

    weighted_values = []
    for i, row in data.iterrows():
        # Parse string lists
        accs = np.array(ast.literal_eval(row["all_accuracies"]), dtype=float)
        sizes = np.array(ast.literal_eval(row["fold_sizes"]), dtype=float)

        # Weighted mean
        weighted_mean = (accs * sizes).sum() / sizes.sum()
        weighted_values.append(weighted_mean)

    # Add column
    data["weighted_average_of_the_mean"] = weighted_values

    # Save CSV back
    data.to_csv(file_path, sep=';', index=False)

def plot_accuracies():
    """
    Plots the accuracies of several performed classifications with comparison boxes/comparison bars.
    """
    grouped_dfs = split_columns_according_to_comparisons()

    for comparison in grouped_dfs.values():
        plot_one_comparison_box(comparison)
        plot_one_comparison_bar(comparison)

def split_columns_according_to_comparisons():
    """
    Splits classification results according to comparison type.

    Returns:
        grouped_dfs:
            classification results, grouped into comparison types.
    """
    file_path = os.path.join('..', '..', 'Results', 'Results.csv')
    data = pd.read_csv(file_path, delimiter=';')
    # Columns to split by
    split_columns = ['DB_1_ID', 'Sensor_1_ID', 'DB_2_ID', 'Sensor_2_ID']

    # Group by the specified columns and create separate dataframes
    grouped_dfs = {name: group for name, group in data.groupby(split_columns)}

    return grouped_dfs

def plot_one_comparison_box(data):
    """
    Plots the accuracies of several performed classifications with comparison boxes.

    Args:
        data:
            data to be plotted.
    """
    _, _, all_accuracies, _ = get_accuracy_values (data)

    database_name_one = data.iloc[0]['DB_1_name']
    sensor_location_name_one = data.iloc[0]['Sensor_1_name']

    database_name_two = data.iloc[0]['DB_2_name']
    sensor_location_name_two = data.iloc[0]['Sensor_2_name']

    title = database_name_one + ' ' + sensor_location_name_one + ' vs ' + database_name_two + sensor_location_name_two

    comparison_types = ['Only Sensor A', 'Only Sensor B', 'Train on A Test on B',
                        'Train on B Test on A', 'Train on Both keep smaller size',
                        'Train on Both Double Smaller size']

    colors = ['darkorange', 'green', 'gold', 'lime']

    # plt.figure(figsize=(14,12))
    fig, ax = plt.subplots(figsize=(14, 12))

    offsets = [-0.15, -0.05, 0.05, 0.15]
    handles = []

    for i, key in enumerate(all_accuracies):
        x_values = np.arange(len(all_accuracies[key])) + offsets[i]
        for j in range(len(all_accuracies[key])):
            accuracies = all_accuracies[key][j]
            accuracies = ast.literal_eval(accuracies)
            significant, p_value = t_test_above_chance_level(accuracies)
            box = ax.boxplot(accuracies, positions=[x_values[j] + offsets[i]],
                       boxprops=dict(color=colors[i]), medianprops=dict(color=colors[i]),
                             labels=[key] if j == 0 else [""])
            if j == 0:
                handles.append(box["boxes"][0])

            if significant:
                ax.plot(x_values[j] + offsets[i], 1.1, marker='*', color=colors[i])

    # Add title and labels
    plt.title(title, fontsize=12)
    plt.ylabel('accuracy')
    plt.ylim(-0.1, 1.2)
    plt.yticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])

    # Set x-ticks
    plt.xticks(range(len(comparison_types)), comparison_types, rotation=25)

    # Remove top and right spines
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Plot a line at y = 0.5
    plt.axhline(y=0.5, color='gray', linestyle='--')

    # Add legend
    ax.legend(handles, list(all_accuracies.keys()))

    name = title +".svg"
    plt.savefig('figs/comparison_box_'+name, format='svg', dpi=600, bbox_inches='tight')

    # Show the plot
    plt.show()

def plot_one_comparison_bar(data):
    """
    Plots the accuracies of several performed classifications with comparison bars.

    Args:
        data:
            data to be plotted.
    """
    all_accuracies_mean, all_accuracies_std, _, all_p_values = get_accuracy_values(data)

    database_name_one = str(data.iloc[0]['DB_1_ID'])
    sensor_location_name_one = str(data.iloc[0]['Sensor_1_ID'])

    database_name_two = str(data.iloc[0]['DB_2_ID'])
    sensor_location_name_two = str(data.iloc[0]['Sensor_2_ID'])

    number_folds = str(data.iloc[0]['n_folds'])

    n_one = str(data.iloc[0]['number_persons_one'])
    n_two = str(data.iloc[0]['number_persons_two'])

    title = database_name_one + ' ' + sensor_location_name_one + ' n '+ n_one + ' vs ' + database_name_two + ' ' + sensor_location_name_two + ' n '+ n_two + ' folds ' + number_folds

    comparison_types = ['Only Sensor A', 'Only Sensor B', 'Train on A Test on B',
                        'Train on B Test on A', 'Train on Both keep smaller size',
                        'Train on Both Double Smaller size']

    colors = ['darkorange', 'green', 'gold', 'lime']

    plt.figure(figsize=(14,12))

    plt.rcParams.update({'font.family': 'Arial', 'font.size': 17})
    new_rc_params = {
        "svg.fonttype": 'none'
    }
    plt.rcParams.update(new_rc_params)
    plt.tick_params(axis='both', which='both', length=10, width=1)

    offsets = [-0.15, -0.05, 0.05, 0.15]
    for i, key in enumerate(all_accuracies_mean):
        x_values = np.arange(len(all_accuracies_mean[key])) + offsets[i]
        plt.errorbar(x_values, all_accuracies_mean[key], yerr=all_accuracies_std[key],
                     label=key, color=colors[i], fmt='o')

        significant_indices = []
        p_values = all_p_values[key]
        for p_value in p_values:
            if p_value<0.001:
                significant_indices.append('***')
            elif p_value<0.01:
                significant_indices.append('**')
            elif p_value<0.05:
                significant_indices.append('*')
            else:
                significant_indices.append('')

        # Draw stars above each point
        for j, star in enumerate(significant_indices):
            x = x_values[j]
            y = all_accuracies_mean[key][j] + all_accuracies_std[key][j] + 0.02  # small offset above the bar
            plt.text(
                x,
                y,
                star,
                ha='center',
                va='bottom',
                fontsize=14,
                color=colors[i]
                )

    # Add title and labels
    plt.title(title, fontsize=12)
    plt.ylabel('accuracy')
    plt.ylim(0, 1)

    # Set x-ticks
    plt.xticks(range(len(comparison_types)), comparison_types)

    # Remove top and right spines
    ax = plt.gca()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    # Plot a line at y = 0.5
    plt.axhline(y=0.5, color='gray', linestyle='--')

    # Add legend
    plt.legend()

    name = title +".svg"
    plt.savefig('figs/comparison_bar_'+name, format='svg', dpi=600, bbox_inches='tight')

    # Show the plot
    plt.show()

def get_accuracy_values(data):
    """
    Extract values for accuracy and t tests from the data.

    Args:
        data:
            the data.

    Returns:
        all_accuracies_mean:
            mean accuracies of the classification.
        all_accuracies_std:
            std of all accuracies of the classification.
        all_accuracies_values:
            all accuracy values of the classification.
        all_p_values
            p values of the classification for test for significance against chance level.
    """
    all_accuracies_mean = {}
    all_accuracies_std = {}
    all_accuracies_values = {}
    all_p_values = {}

    classifier_grouped = {name: group for name, group in data.groupby('Classifier')}
    for classifier_name, classifier_values in classifier_grouped.items():
        feature_grouped = {name: group for name, group in classifier_values.groupby('feature_type')}
        for feature_type_name, feature_type_values in feature_grouped.items():
            comparison_types = ['Only Sensor A', 'Only Sensor B', 'Train on A Test on B',
                                'Train on B Test on A', 'Train on Both keep smaller size',
                                'Train on Both Double Smaller size']
            mean_accuracies = []
            std_accuracies = []
            accuracies = []
            p_values = []

            for comparison_type in comparison_types:
                mean_accuracies.extend(feature_type_values[feature_type_values['comparison_type'] == comparison_type]
                                       ['accuracy_mean'].values)
                std_accuracies.extend(feature_type_values[feature_type_values['comparison_type'] == comparison_type]
                                      ['accuracy_std'].values)
                accuracies.extend(feature_type_values[feature_type_values['comparison_type'] == comparison_type]
                                      ['all_accuracies'].values)
                p_values.extend(feature_type_values[feature_type_values['comparison_type'] == comparison_type]
                                  ['p_value'].values)

            name = classifier_name+'_'+feature_type_name
            all_accuracies_mean[name] = mean_accuracies
            all_accuracies_std[name] = std_accuracies
            all_accuracies_values[name] = accuracies
            all_p_values[name] = p_values


    return all_accuracies_mean, all_accuracies_std, all_accuracies_values, all_p_values

def get_csvs_for_anova():
    """
    Extract csv for performance of an anova.
    """
    grouped_dfs = split_columns_according_to_comparisons()
    columns_to_delete = ['precision', 'recall', 'specificity', 'F1_score', 'accuracy_mean', 'accuracy_std', 'auc_mean',
                         'auc_std', 'DB_1_name', 'DB_2_name', 'Sensor_1_name', 'Sensor_2_name', 'number_persons_one',
                         'number_persons_two', 'significant', 'p_value', 'weighted_average_of_the_mean', 'fold_sizes',
                         'weighted_average_of_the_mean']
    for key in grouped_dfs:
        grouped_dfs[key] = grouped_dfs[key].drop(columns=columns_to_delete, errors='ignore')

    column_to_expand = 'all_accuracies'

    for key in grouped_dfs:
        expanded_df = grouped_dfs[key].copy()

        expanded_df[column_to_expand] = expanded_df[column_to_expand].apply(ast.literal_eval)

        expanded_df['original_index'] = expanded_df.index

        expanded_df = expanded_df.explode(column_to_expand)

        expanded_df.rename(columns={column_to_expand: 'accuracy'}, inplace=True)

        expanded_df.rename(columns={'Classifier': 'classifier'}, inplace=True)

        expanded_df['accuracy'] = pd.to_numeric(expanded_df['accuracy'], errors='coerce')

        expanded_df['fold'] = expanded_df.groupby('original_index').cumcount() + 1

        expanded_df.drop(columns='original_index', inplace=True)

        expanded_df = map_string_values(expanded_df)

        name = "_".join(str(x) for x in key)

        expanded_df.to_csv('../../Results/'+name+'.csv', sep='\t', index=False)

        grouped_dfs[key] = expanded_df.reset_index(drop=True)

def map_string_values(df):
    """
    Maps string values to integer values.

    Args:
        df:
            the data.
    Returns:
        df:
            the data with string values remapped to integer values.
    """
    classifier_mapping = {
        'logistic Regression': 1,
        'Random Forest (Ensemble)': 2,
    }

    comparison_mapping = {
        'Only Sensor A': 1,
        'Only Sensor B': 2,
        'Train on Both keep smaller size': 3,
        'Train on Both Double Smaller size': 4,
        'Train on A Test on B': 5,
        'Train on B Test on A': 6
    }

    feature_mapping = {
        'Statistical_Features': 1,
        'Gait_Cycles': 2,
    }

    df['classifier'] = df['classifier'].map(classifier_mapping)
    df['comparison_type'] = df['comparison_type'].map(comparison_mapping)
    df['feature_type'] = df['feature_type'].map(feature_mapping)

    return df

if __name__ == '__main__':

    calculate_accuracies()
    #plot_accuracies()
    #get_csvs_for_anova()
