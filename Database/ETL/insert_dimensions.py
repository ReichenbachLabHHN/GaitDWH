"""
Fills the dimension tables from the meta data files.
"""
import csv
import os
import psycopg2
from dotenv import load_dotenv
from psycopg2 import Error
import database_id_mapping as mapping

def insert_dimensions():
    """
    Inserts dimension tables using the meta data in the central .csv files in the Meta_Data subfolder
    """

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

        ### ACTIVITY

        with open('../Meta_Data/activity_meta.csv', newline='') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            activity_meta = csv_data[1:]

        # Iterate over all activities
        for activity in activity_meta:
            # Extract attributes
            activity_ID = int(activity[0])
            activity_type_id = int(activity[1])
            activity_type_title = mapping.get_activity_type_title(activity_type_id)
            activity_name_id = int(activity[2])
            activity_name_title = mapping.get_activity_name_title(activity_name_id)

            # SQL query to add the activity
            create_add_activity_query = '''INSERT INTO Activity (Activity_ID, Activity_Type_ID, Activity_Type_Title,
            Activity_Name_ID, Activity_Name_Title) VALUES (%s, %s, %s, %s, %s)'''
            # execute code to add Activity table entry
            cursor.execute(create_add_activity_query, (activity_ID, activity_type_id, activity_type_title,
                                                       activity_name_id, activity_name_title))

        connection.commit()
        print("Initialized Activity Dimension.")

        ### GROUND

        with open('../Meta_Data/ground_meta.csv', newline='') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            ground_meta = csv_data[1:]

        # Iterate over all world coordinate systems
        for ground in ground_meta:
            # Extract attributes
            ground_ID = int(ground[0])
            ground_outside_id = ground[1]
            if not ground_outside_id:
                ground_outside_id = None
                ground_outside_title = None
            else:
                ground_outside_id = int(ground_outside_id)
                ground_outside_title = mapping.get_outside_title(ground_outside_id)
            ground_even_slope_stairs_id = int(ground[2])
            ground_even_slope_stairs_title = mapping.get_even_slope_stairs_title(ground_even_slope_stairs_id)
            ground_treadmill_id = int(ground[3])
            ground_treadmill_title = mapping.get_treadmill_title(ground_treadmill_id)
            ground_surface_id = ground[4]
            if not ground_surface_id:
                ground_surface_id = None
                ground_surface_title = None
            else:
                ground_surface_id = int(ground_surface_id)
                ground_surface_title = mapping.get_surface_title(ground_surface_id)

            # SQL query to add the ground
            create_add_ground_query = '''INSERT INTO Ground (Ground_ID, Outside_ID, Outside_Title,
            Even_Slope_Stairs_ID, Even_Slope_Stairs_Title, Treadmill_ID, Treadmill_Title, Surface_ID, Surface_Title)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            # execute code to add Ground table entry
            cursor.execute(create_add_ground_query, (ground_ID, ground_outside_id, ground_outside_title,
                                                     ground_even_slope_stairs_id, ground_even_slope_stairs_title,
                                                     ground_treadmill_id,
                                                     ground_treadmill_title, ground_surface_id, ground_surface_title))

        connection.commit()
        print("Initialized Ground Dimension.")

        ### PERSON

        # Import subject data from person_meta.csv
        with open('../Meta_Data/person_meta.csv', newline='') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            person_meta = csv_data[1:]
            
        # Iterate over all persons
        for person in person_meta:
            person_ID = int(person[0])
            # Extract person weight if given
            if person[1]:
                person_weight = float(person[1])
            else:
                person_weight = None
            # Extract person height if given
            if person[2]:
                person_height = float(person[2])
            else:
                person_height = None
            # Extract person age if given
            if person[3]:
                person_age = int(person[3])
            else:
                person_age = None
            # Extract person sex if given
            if person[4]:
                if person[4] == "M":
                    person_sex_id = 0
                else:
                    person_sex_id = 1
                person_sex_title = mapping.get_sex_title(person_sex_id)
            else:
                person_sex_id = None
                person_sex_title = None
            # Extract Smoker_ID if given
            if person[5]:
                if person[5] == "No":
                    person_smoker_id = 0
                else:
                    person_smoker_id = 1
                person_smoker_title = mapping.get_smoker_title(person_smoker_id)
            else:
                person_smoker_id = None
                person_smoker_title = None
            # Extract Fitness_Level if given
            if person[6]:
                person_fitness_level = person[6]
            else:
                person_fitness_level = None


            # SQL query to add the person
            create_add_person_query = '''INSERT INTO Person (Person_ID, Height, Weight, Age, Sex_ID, Sex_Title,
            Smoker_ID, Smoker_Title, Fitness_Level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            # execute code to add Person table entry
            cursor.execute(create_add_person_query, (person_ID, person_height, person_weight, person_age,
                                                     person_sex_id, person_sex_title, person_smoker_id,
                                                     person_smoker_title, person_fitness_level))
        
        connection.commit()
        print("Initialized Person Dimension.")


        ### SENSOR

        # Import sensor data from person_meta.csv
        with open('../Meta_Data/sensor_meta.csv', newline='') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            sensor_meta = csv_data[1:]

        # Iterate over all sensors
        for sensor in sensor_meta:
            # Extract attributes 
            sensor_ID = int(sensor[0])
            sensor_type_id = int(sensor[1])
            sensor_type_title = mapping.get_sensor_modality_title(sensor_type_id)
            sensor_model = sensor[2]
            if not sensor_model:
                sensor_model = None
            sensor_packaging_id = int(sensor[3])
            sensor_packaging_title = mapping.get_sensor_type_title(sensor_packaging_id)
            sensor_internal_coordinate_system_id = sensor[4]
            if sensor_internal_coordinate_system_id:
                sensor_internal_coordinate_system_id = int(sensor_internal_coordinate_system_id)
                sensor_internal_coordinate_system_title = (mapping.get_internal_coordinate_system_title
                                                           (sensor_internal_coordinate_system_id))
                sensor_rotation_to_standard_coordinate_system = sensor[5]
            else:
                sensor_internal_coordinate_system_id = None
                sensor_internal_coordinate_system_title = None
                sensor_rotation_to_standard_coordinate_system = None
            

            # SQL query to add the sensor
            create_add_sensor_query = '''INSERT INTO Sensor (Sensor_ID, Type_ID, Type_Title, Model, Packaging_ID,
            Packaging_Title, Internal_Coordinate_System_ID, Internal_Coordinate_System_Title,
            Rotation_To_Standard_Coordinate_System) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            # execute code to add Sensor table entry
            cursor.execute(create_add_sensor_query, (sensor_ID, sensor_type_id, sensor_type_title, sensor_model,
                    sensor_packaging_id, sensor_packaging_title, sensor_internal_coordinate_system_id,
                    sensor_internal_coordinate_system_title, sensor_rotation_to_standard_coordinate_system))
        
        connection.commit()
        print("Initialized Sensor Dimension.")

        ### SENSOR_LOCATION

        with open('../Meta_Data/sensor_location_meta.csv', newline='') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            sensor_location_meta = csv_data[1:]

        # Iterate over all sensor locations
        for sensor_location in sensor_location_meta:
            # Extract attributes 
            sensor_location_ID = int(sensor_location[0])
            sensor_location_body_side_id = int(sensor_location[1])
            sensor_location_body_side_title = mapping.get_body_side_title(sensor_location_body_side_id)
            sensor_location_body_area_id = int(sensor_location[2])
            sensor_location_body_area_title = mapping.get_body_area_title(sensor_location_body_area_id)
            sensor_location_position_id = int(sensor_location[3])
            sensor_location_position_title = mapping.get_position_title(sensor_location_position_id)
            sensor_location_rotation = sensor_location[4]

            # SQL query to add the sensor location
            create_add_sensor_location_query = '''INSERT INTO Sensor_Location (Sensor_Location_ID, Body_Side_ID,
            Body_Side_Title, Body_Area_ID, Body_Area_Title, Position_ID, Position_Title, Rotation)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)'''
            # execute code to add Sensor_Location table entry
            cursor.execute(create_add_sensor_location_query, (sensor_location_ID, sensor_location_body_side_id,
                sensor_location_body_side_title, sensor_location_body_area_id, sensor_location_body_area_title,
                sensor_location_position_id, sensor_location_position_title, sensor_location_rotation))

        connection.commit()
        print("Initialized Sensor_Location Dimension.")

        ### STEP_EVENT

        with open('../Meta_Data/step_event_meta.csv', newline='') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            step_event_meta = csv_data[1:]

        # Iterate over all world coordinate systems
        for step_event in step_event_meta:
            # Extract attributes
            step_event_ID = int(step_event[0])

            if step_event[1]:
                ground_truth_event_id = int(step_event[1])
                ground_truth_event_title = mapping.get_ground_truth_event_title(ground_truth_event_id)
            else:
                ground_truth_event_id = None
                ground_truth_event_title = None

            if step_event[2]:
                ground_truth_order_boolean = step_event[2]
            else:
                ground_truth_order_boolean = None

            if step_event[3]:
                ground_truth_step_number = step_event[3]
            else:
                ground_truth_step_number = None

            if step_event[4]:
                detected_event_id = step_event[4]
                detected_event_title = mapping.get_detected_event_title(detected_event_id)
            else:
                detected_event_id = None
                detected_event_title = None

            if step_event[5]:
                detected_event_reliability = step_event[5]
            else:
                detected_event_reliability = None

            if step_event[6]:
                detected_event_reliable_flag = step_event[6]
            else:
                detected_event_reliable_flag = None

            # SQL query to add the world coordinate system
            create_add_step_event_query = '''INSERT INTO Step_Event (Step_Event_ID, Ground_Truth_Event_ID,
            Ground_Truth_Event_Title, Ground_Truth_Order_Flag, Ground_Truth_Step_Number, Detected_Event_ID,
            Detected_Event_Title, Detected_Event_Reliability, Detected_Event_Reliable_Flag)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)'''
            # execute code to add World_Coordinate_System table entry
            cursor.execute(create_add_step_event_query, (step_event_ID, ground_truth_event_id,
                                                         ground_truth_event_title, ground_truth_order_boolean,
                                                         ground_truth_step_number,
                                                         detected_event_id, detected_event_title,
                                                         detected_event_reliability, detected_event_reliable_flag))

        connection.commit()
        print("Initialized Step_Event Dimension.")

        ### WORLD_COORDINATE_SYSTEM

        with open('../Meta_Data/world_coordinate_system_meta.csv', newline='') as f:
            reader = csv.reader(f)
            csv_data = list(reader)
            world_cordinate_system_meta = csv_data[1:]

        # Iterate over all world coordinate systems
        for coordinate_system in world_cordinate_system_meta:
            # Extract attributes 
            world_coordinate_system_ID = int(coordinate_system[0])
            alignment_id = int(coordinate_system[1])
            alignment_name = mapping.get_alignment_title(alignment_id)
            rotation_to_world_coordinate_system = coordinate_system[2]

            # SQL query to add the world coordinate system
            create_add_world_cordinate_system_query = '''INSERT INTO World_Coordinate_System
            (World_Coordinate_System_ID, Alignment_ID, Alignment_Title, Rotation_To_World_Coordinate_System)
            VALUES (%s, %s, %s, %s)'''
            # execute code to add World_Coordinate_System table entry
            cursor.execute(create_add_world_cordinate_system_query, (world_coordinate_system_ID, alignment_id,
                                                                alignment_name, rotation_to_world_coordinate_system))
        
        connection.commit()
        print("Initialized World_Cordinate_System Dimension.")


    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL:", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()