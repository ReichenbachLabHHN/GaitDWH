"""
This module contains helper functions for setting up and initializing
the project database.
"""
import psycopg2
from psycopg2 import Error
import os
from dotenv import load_dotenv

def create_db():
    """
    Creates the standard database tables using postgresql
    """
    print("Current working directory:", os.getcwd())

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

        # Clean database
        clean_db(connection, cursor)

        ### DIMENSIONS

        ## ACTIVITY

        # SQL query to create the Activity table
        create_activity_table_query = '''CREATE TABLE Activity (
            Activity_ID int NOT NULL,
            Activity_Type_ID int,
            Activity_Type_Title text,
            Activity_Name_ID int,
            Activity_Name_Title text,
            PRIMARY KEY (Activity_ID)
            ); '''
        # execute code to create Activity table
        cursor.execute(create_activity_table_query)
        connection.commit()
        print("Activity table created successfully.")

        ## GROUND

        # SQL query to create the Ground table
        create_ground_table_query = '''CREATE TABLE Ground (
            Ground_ID int NOT NULL,
            Outside_ID int,
            Outside_Title text,
            Even_Slope_Stairs_ID int,
            Even_Slope_Stairs_Title text,
            Treadmill_ID int,
            Treadmill_Title text,
            Surface_ID int,
            Surface_Title text,
            PRIMARY KEY (Ground_ID)
            ); '''
        # execute code to create Ground table
        cursor.execute(create_ground_table_query)
        connection.commit()
        print("Ground table created successfully.")

        ## PERSON

        # SQL query to create the Person table
        create_person_table_query = '''CREATE TABLE Person (
                    Person_ID int NOT NULL,
                    Height real,
                    Weight real,
                    Age int,
                    Sex_ID int,
                    Sex_Title text,
                    Smoker_ID int,
                    Smoker_Title text,
                    Fitness_Level int,
                    PRIMARY KEY (Person_ID)
                    ); '''
        # execute code to create Person table
        cursor.execute(create_person_table_query)
        connection.commit()
        print("Person table created successfully.")

        ## RECORDING

        # SQL query to create the Recording table
        create_recording_table_query = '''CREATE TABLE Recording (
            Recording_ID BIGSERIAL,
            Year int,
            Month int,
            Day int,
            Starting_Time text,
            Duration int,
            Dataset_ID int,
            Dataset_Title text,
            Repetition int,
            Sample_Frequency real,
            PRIMARY KEY (Recording_ID)
            ); '''
        # execute code to create Recording table
        cursor.execute(create_recording_table_query)
        connection.commit()
        print("Recording table created successfully.")

        ## SENSOR

        # SQL query to create the Sensor table
        create_sensor_table_query = '''CREATE TABLE Sensor (
            Sensor_ID int NOT NULL,
            Modality_ID int,
            Modality_Title text,
            Model text,
            Sensor_Type_ID int,
            Sensor_Type_Title text,
            Internal_Coordinate_System_ID int,
            Internal_Coordinate_System_Title text,
            Rotation_To_Standard_Coordinate_System text,
            PRIMARY KEY (Sensor_ID)
            ); '''
        # execute code to create Sensor table
        cursor.execute(create_sensor_table_query)
        connection.commit()
        print("Sensor table created successfully.")

        ## SENSOR_LOCATION

        # SQL query to create the Sensor_Location table
        create_sensor_location_table_query = '''CREATE TABLE Sensor_Location (
            Sensor_Location_ID int NOT NULL,
            Body_Side_ID int,
            Body_Side_Title text,
            Body_Area_ID int,
            Body_Area_Title text,
            Position_ID int,
            Position_Title text,
            Rotation text,
            PRIMARY KEY (Sensor_Location_ID)
            ); '''
        # execute code to create Sensor_Location table
        cursor.execute(create_sensor_location_table_query)
        connection.commit()
        print("Sensor_Location table created successfully.")

        ## STEP_EVENT

        # SQL query to create the Step_Event table
        create_step_event_table_query = '''CREATE TABLE Step_Event (
            Step_Event_ID BIGSERIAL,
            Ground_Truth_Event_ID int,
            Ground_Truth_Event_Title text,
            Ground_Truth_Order_Flag boolean,
            Ground_Truth_Step_Number int,
            Detected_Event_ID int,
            Detected_Event_Title text,
            Detected_Event_Reliability real,
            Detected_Event_Reliable_Flag boolean,
            PRIMARY KEY (Step_Event_ID)
            ); '''
        # execute code to create Step_Event table
        cursor.execute(create_step_event_table_query)
        cursor.execute('''ALTER SEQUENCE Step_Event_Step_Event_ID_seq RESTART WITH 2''')
        connection.commit()
        print("Step_Event table created successfully.")

        ## WORLD_COORDINATE_SYSTEM

        # SQL query to create the World_Coordinate_System table
        create_world_coordinate_system_table_query = '''CREATE TABLE World_Coordinate_System (
            World_Coordinate_System_ID int NOT NULL,
            Alignment_ID int,
            Alignment_Title text,
            Rotation_To_World_Coordinate_System text,
            PRIMARY KEY (World_Coordinate_System_ID)
            ); '''
        # execute code to create World_Coordinate_System table
        cursor.execute(create_world_coordinate_system_table_query)
        connection.commit()
        print("World_Coordinate_System table created successfully.")

        ### FACTS

        ## RAW_ACCELEROMETER

        # SQL query to create the Raw_Accelerometer table
        create_raw_accelerometer_table_query = '''CREATE TABLE Raw_Accelerometer (
            Raw_Accelerometer_ID BIGSERIAL,
            X real,
            Y real,
            Z real,
            Time int,
            Recording_ID int,
            Person_ID int,
            Sensor_ID int,
            Activity_ID int,
            Sensor_Location_ID int,
            World_Coordinate_System_ID int,
            Step_Event_ID int,
            Ground_ID int,
            PRIMARY KEY (Raw_Accelerometer_ID),
            FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
            FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
            FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
            FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
            FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
            FOREIGN KEY (World_Coordinate_System_ID) REFERENCES World_Coordinate_System(World_Coordinate_System_ID),
            FOREIGN KEY (Step_Event_ID) REFERENCES Step_Event(Step_Event_ID),
            FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
            ); '''
        # execute code to create Raw_Accelerometer table
        cursor.execute(create_raw_accelerometer_table_query)
        connection.commit()
        print("Raw_Accelerometer table created successfully.")

        ## RAW_EMG

        # SQL query to create the Raw_EMG table
        create_raw_emg_table_query = '''CREATE TABLE Raw_EMG (
                    Raw_EMG_ID BIGSERIAL,
                    R real,
                    L real,
                    Time int,
                    Recording_ID int,
                    Person_ID int,
                    Sensor_ID int,
                    Activity_ID int,
                    Sensor_Location_ID int,
                    Step_Event_ID int,
                    Ground_ID int,
                    PRIMARY KEY (Raw_EMG_ID),
                    FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
                    FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
                    FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
                    FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
                    FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
                    FOREIGN KEY (Step_Event_ID) REFERENCES Step_Event(Step_Event_ID),
                    FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
                    ); '''
        # execute code to create Raw_EMG table
        cursor.execute(create_raw_emg_table_query)
        connection.commit()
        print("Raw_EMG table created successfully.")

        ## RAW_GYROSCOPE

        # SQL query to create the Raw_Gyroscope table
        create_raw_gyroscope_table_query = '''CREATE TABLE Raw_Gyroscope (
            Raw_Gyroscope_ID BIGSERIAL,
            X real,
            Y real,
            Z real,
            Time int,
            Recording_ID int,
            Person_ID int,
            Sensor_ID int,
            Activity_ID int,
            Sensor_Location_ID int,
            World_Coordinate_System_ID int,
            Step_Event_ID int,
            Ground_ID int,
            PRIMARY KEY (Raw_Gyroscope_ID),
            FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
            FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
            FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
            FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
            FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
            FOREIGN KEY (World_Coordinate_System_ID) REFERENCES World_Coordinate_System(World_Coordinate_System_ID),
            FOREIGN KEY (Step_Event_ID) REFERENCES Step_Event(Step_Event_ID),
            FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
            ); '''
        # execute code to create Raw_Gyroscope table
        cursor.execute(create_raw_gyroscope_table_query)
        connection.commit()
        print("Raw_Gyroscope table created successfully.")

        ## RAW_MAGNETOMETER

        # SQL query to create the Raw_Magnetometer table
        create_raw_magnetometer_table_query = '''CREATE TABLE Raw_Magnetometer (
            Raw_Magnetometer_ID BIGSERIAL,
            X real,
            Y real,
            Z real,
            Time int,
            Recording_ID int,
            Person_ID int,
            Sensor_ID int,
            Activity_ID int,
            Sensor_Location_ID int,
            World_Coordinate_System_ID int,
            Step_Event_ID int,
            Ground_ID int,
            PRIMARY KEY (Raw_Magnetometer_ID),
            FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
            FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
            FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
            FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
            FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
            FOREIGN KEY (World_Coordinate_System_ID) REFERENCES World_Coordinate_System(World_Coordinate_System_ID),
            FOREIGN KEY (Step_Event_ID) REFERENCES Step_Event(Step_Event_ID),
            FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
            ); '''
        # execute code to create Raw_Magnetometer table
        cursor.execute(create_raw_magnetometer_table_query)
        connection.commit()
        print("Raw_Magnetometer table created successfully.")


    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()

def create_feature_indices(connection, cursor):
    """
    Creates indices for foreign keys often used in queries of feature tables.

    Args:
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations
    """
    try:

        # SQL query to create index for Feature_Accelerometer_Gait_Cycle table
        create_accelerometer_gait_cycle_indices_query = '''
        CREATE INDEX idx_acc_gait_recording_Id ON Feature_Accelerometer_Gait_Cycle (Recording_ID);
        CREATE INDEX idx_acc_gait_person_Id ON Feature_Accelerometer_Gait_Cycle (Person_ID);
        CREATE INDEX idx_acc_gait_sensor_Id ON Feature_Accelerometer_Gait_Cycle (Sensor_ID);
        CREATE INDEX idx_acc_gait_activity_Id ON Feature_Accelerometer_Gait_Cycle (Activity_ID);
        CREATE INDEX idx_acc_gait_sensor_location_Id ON Feature_Accelerometer_Gait_Cycle (Sensor_Location_ID);
        CREATE INDEX idx_acc_gait_ground_Id ON Feature_Accelerometer_Gait_Cycle (Ground_ID);
                                        '''
        # execute code to create index
        cursor.execute(create_accelerometer_gait_cycle_indices_query)
        connection.commit()

        # SQL query to create index for Feature_Fourier_Coefficients table
        create_fourier_coefficients_indices_query = '''
        CREATE INDEX idx_four_coeff_recording_Id ON Feature_Fourier_Coefficients (Recording_ID);
        CREATE INDEX idx_four_coeff_person_Id ON Feature_Fourier_Coefficients (Person_ID);
        CREATE INDEX idx_four_coeff_sensor_Id ON Feature_Fourier_Coefficients (Sensor_ID);
        CREATE INDEX idx_four_coeff_activity_Id ON Feature_Fourier_Coefficients (Activity_ID);
        CREATE INDEX idx_four_coeff_sensor_location_Id ON Feature_Fourier_Coefficients (Sensor_Location_ID);
        CREATE INDEX idx_four_coeff_ground_Id ON Feature_Fourier_Coefficients (Ground_ID);
                                '''
        # execute code to create index
        cursor.execute(create_fourier_coefficients_indices_query)
        connection.commit()

        # SQL query to create index for Feature_Mean_Accelerometer_Gait_Cycle table
        create_mean_accelerometer_gait_cycle_indices_query = '''
        CREATE INDEX idx_mean_acc_gait_recording_Id ON Feature_Mean_Accelerometer_Gait_Cycle (Recording_ID);
        CREATE INDEX idx_mean_acc_gait_person_Id ON Feature_Mean_Accelerometer_Gait_Cycle (Person_ID);
        CREATE INDEX idx_mean_acc_gait_sensor_Id ON Feature_Mean_Accelerometer_Gait_Cycle (Sensor_ID);
        CREATE INDEX idx_mean_acc_gait_activity_Id ON Feature_Mean_Accelerometer_Gait_Cycle (Activity_ID);
        CREATE INDEX idx_mean_acc_gait_sensor_location_Id ON
        Feature_Mean_Accelerometer_Gait_Cycle (Sensor_Location_ID);
        CREATE INDEX idx_mean_acc_gait_ground_Id ON Feature_Mean_Accelerometer_Gait_Cycle (Ground_ID);
                                                        '''
        # execute code to create index
        cursor.execute(create_mean_accelerometer_gait_cycle_indices_query)
        connection.commit()

        # SQL query to create index for Feature_Uniform_Accelerometer_Gait_Cycle table
        create_uniform_accelerometer_gait_cycle_indices_query = '''
        CREATE INDEX idx_uni_acc_gait_recording_Id ON Feature_Uniform_Accelerometer_Gait_Cycle (Recording_ID);
        CREATE INDEX idx_uni_acc_gait_person_Id ON Feature_Uniform_Accelerometer_Gait_Cycle (Person_ID);
        CREATE INDEX idx_uni_acc_gait_sensor_Id ON Feature_Uniform_Accelerometer_Gait_Cycle (Sensor_ID);
        CREATE INDEX idx_uni_acc_gait_activity_Id ON Feature_Uniform_Accelerometer_Gait_Cycle (Activity_ID);
        CREATE INDEX idx_uni_acc_gait_sensor_location_Id ON
        Feature_Uniform_Accelerometer_Gait_Cycle (Sensor_Location_ID);
        CREATE INDEX idx_uni_acc_gait_ground_Id ON Feature_Uniform_Accelerometer_Gait_Cycle (Ground_ID);
                                                '''
        # execute code to create index
        cursor.execute(create_uniform_accelerometer_gait_cycle_indices_query)
        connection.commit()

        # SQL query to create index for Feature_Y_Normalized_Accelerometer_Gait_Cycle table
        create_y_normalized_accelerometer_gait_cycle_indices_query = '''
        CREATE INDEX idx_y_norm_acc_gait_recording_Id ON Feature_Y_Normalized_Accelerometer_Gait_Cycle (Recording_ID);
        CREATE INDEX idx_y_norm_acc_gait_person_Id ON Feature_Y_Normalized_Accelerometer_Gait_Cycle (Person_ID);
        CREATE INDEX idx_y_norm_acc_gait_sensor_Id ON Feature_Y_Normalized_Accelerometer_Gait_Cycle (Sensor_ID);
        CREATE INDEX idx_y_norm_acc_gait_activity_Id ON Feature_Y_Normalized_Accelerometer_Gait_Cycle (Activity_ID);
        CREATE INDEX idx_y_norm_acc_gait_sensor_location_Id ON
        Feature_Y_Normalized_Accelerometer_Gait_Cycle (Sensor_Location_ID);
        CREATE INDEX idx_y_norm_acc_gait_ground_Id ON Feature_Y_Normalized_Accelerometer_Gait_Cycle (Ground_ID);
                                                '''
        # execute code to create index
        cursor.execute(create_y_normalized_accelerometer_gait_cycle_indices_query)
        connection.commit()

        # SQL query to create index forPre_Accelerometer table
        create_pre_accelerometer_indices_query = '''
        CREATE INDEX idx_pre_acc_recording_Id ON Pre_Accelerometer (Recording_ID);
        CREATE INDEX idx_pre_acc_person_Id ON Pre_Accelerometer (Person_ID);
        CREATE INDEX idx_pre_acc_sensor_Id ON Pre_Accelerometer (Sensor_ID);
        CREATE INDEX idx_pre_acc_activity_Id ON Pre_Accelerometer (Activity_ID);
        CREATE INDEX idx_pre_acc_sensor_location_Id ON Pre_Accelerometer (Sensor_Location_ID);
        CREATE INDEX idx_pre_acc_step_event_Id ON Pre_Accelerometer (Step_Event_ID);
        CREATE INDEX idx_pre_acc_ground_Id ON Pre_Accelerometer (Ground_ID);
                        '''
        # execute code to create index
        cursor.execute(create_pre_accelerometer_indices_query)
        connection.commit()

        # SQL query to create index for Raw_Accelerometer table
        create_raw_accelerometer_indices_query = '''
        CREATE INDEX IF NOT EXISTS idx_raw_acc_recording_Id ON Raw_Accelerometer (Recording_ID);
        CREATE INDEX IF NOT EXISTS idx_raw_acc_person_Id ON Raw_Accelerometer (Person_ID);
        CREATE INDEX IF NOT EXISTS idx_raw_acc_sensor_Id ON Raw_Accelerometer (Sensor_ID);
        CREATE INDEX IF NOT EXISTS idx_raw_acc_activity_Id ON Raw_Accelerometer (Activity_ID);
        CREATE INDEX IF NOT EXISTS idx_raw_acc_sensor_location_Id ON Raw_Accelerometer (Sensor_Location_ID);
        CREATE INDEX IF NOT EXISTS idx_raw_acc_step_event_Id ON Raw_Accelerometer (Step_Event_ID);
        CREATE INDEX IF NOT EXISTS idx_raw_acc_ground_Id ON Raw_Accelerometer (Ground_ID);
                        '''
        # execute code to create index
        cursor.execute(create_raw_accelerometer_indices_query)
        connection.commit()

        print("Fact indices created successfully.")

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)

def clean_db_features(connection, cursor):
    """
    Drops all database fact tables.

    Args:
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations
        """
    try:
        clean_db_feature_tables_query = '''
            DROP TABLE IF EXISTS Feature_Accelerometer_Gait_Cycle CASCADE;
            DROP TABLE IF EXISTS Feature_Fourier_Coefficients CASCADE;
            DROP TABLE IF EXISTS Feature_Mean_Accelerometer_Gait_Cycle CASCADE;
            DROP TABLE IF EXISTS Feature_Uniform_Accelerometer_Gait_Cycle CASCADE;
            DROP TABLE IF EXISTS Feature_Y_Normalized_Accelerometer_Gait_Cycle CASCADE;
            DROP TABLE IF EXISTS Pre_Accelerometer CASCADE;
            DROP TABLE IF EXISTS Raw_Jerk CASCADE;          
            '''
        # execute code to drop tables
        cursor.execute(clean_db_feature_tables_query)
        connection.commit()
        print("Database features cleaned successfully.")

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)

def clean_db(connection, cursor, features_only=False):
    """
    Drops all database tables. Alternatively cleans all feature tables if features_only flag is True.

    Args:
        features_only (bool, optional):
            Decides if only feature tables should be cleaned. Defaults to False.
        connection:
            Database connection.
        cursor:
            Cursor to perform database operations
    """
    try:

        # Define query
        if features_only:
            clean_db_features(connection, cursor)
        else:
            clean_db_features(connection, cursor)
            clean_db_query = '''
                DROP TABLE IF EXISTS Activity CASCADE;            
                DROP TABLE IF EXISTS Ground CASCADE;
                DROP TABLE IF EXISTS Person CASCADE;
                DROP TABLE IF EXISTS Raw_Accelerometer CASCADE;
                DROP TABLE IF EXISTS Raw_EMG CASCADE;
                DROP TABLE IF EXISTS Raw_Gyroscope CASCADE;
                DROP TABLE IF EXISTS Raw_Magnetometer CASCADE;
                DROP TABLE IF EXISTS Recording CASCADE;
                DROP TABLE IF EXISTS Sensor CASCADE;
                DROP TABLE IF EXISTS Sensor_Location CASCADE;
                DROP TABLE IF EXISTS Step_Event CASCADE;
                DROP TABLE IF EXISTS World_Coordinate_System CASCADE;
                '''
            # execute code to drop tables
            cursor.execute(clean_db_query)
            connection.commit()
            print("Database cleaned successfully.")

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)

def drop_statistical_measure_tables(feature_frame, connection, cursor):
    """
    Drops any existing Statistical Measure table of the provided frame size.

    Args:
        feature_frame (int):
            Feature frame size of which the table should be dropped.
        cursor (object):
            Psycopg2 cursor object. Prevents having to set up the database connection.
        connection (object):
            Psycopg2 connection object. Prevents having to set up the database connection.
    """
    clean_db_query = '''
        DROP TABLE IF EXISTS Feature_Statistical_Measure_''' + str(feature_frame) + ''' CASCADE;
        '''
    cursor.execute(clean_db_query)
    connection.commit()

def create_statistical_measure_tables_indices(feature_frame, connection, cursor):
    """
    Creates indices for foreign keys often used in queries of the statistical feature tables.

    Args:
        feature_frame (int):
            Feature frame size of which the table should be dropped.
        connection (object):
            Psycopg2 connection object. Prevents having to set up the database connection.
        cursor (object):
            Psycopg2 cursor object. Prevents having to set up the database connection.
    """
    # SQL query to create index for Feature_Statistical_Measure_ table
    create_accelerometer_gait_cycle_indices_query = ('''
    CREATE INDEX idx_recording_Id_''' + str(feature_frame) + ''' ON Feature_Statistical_Measure_''' +
                                                     str(feature_frame) + ''' (Recording_ID);
    CREATE INDEX idx_person_Id_''' + str(feature_frame) + ''' ON Feature_Statistical_Measure_''' +
                                                     str(feature_frame) + ''' (Person_ID);
    CREATE INDEX idx_sensor_Id_''' + str(feature_frame) + ''' ON Feature_Statistical_Measure_''' +
                                                     str(feature_frame) + ''' (Sensor_ID);
    CREATE INDEX idx_activity_Id_''' + str(feature_frame) + ''' ON Feature_Statistical_Measure_''' +
                                                     str(feature_frame) + ''' (Activity_ID);
    CREATE INDEX idx_sensor_location_Id_''' + str(feature_frame) + ''' ON Feature_Statistical_Measure_''' +
                                                     str(feature_frame) + ''' (Sensor_Location_ID);
    CREATE INDEX idx_ground_Id_''' + str(feature_frame) + ''' ON Feature_Statistical_Measure_''' +
                                                     str(feature_frame) + ''' (Ground_ID);
                                    ''')
    # execute code to create index
    cursor.execute(create_accelerometer_gait_cycle_indices_query)
    connection.commit()


def create_feature_tables(connection, cursor):
    """
    Creates the Feature database tables using postgresql

    Args:
        cursor (object):
            Psycopg2 cursor object. Prevents having to set up the database connection.
        connection (object):
            Psycopg2 connection object. Prevents having to set up the database connection.
    """
    ## PRE_ACCELEROMETER

    # SQL query to create the Pre_Accelerometer table
    create_pre_accelerometer_table_query = '''CREATE TABLE Pre_Accelerometer (
        Pre_Accelerometer_ID BIGSERIAL,
        X real,
        Y real,
        Z real,
        Time int,
        Recording_ID int,
        Segment_Number int,
        Person_ID int,
        Sensor_ID int,
        Activity_ID int,
        Sensor_Location_ID int,
        Step_Event_ID int,
        Ground_ID int,
        PRIMARY KEY (Pre_Accelerometer_ID),
        FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
        FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
        FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
        FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
        FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
        FOREIGN KEY (Step_Event_ID) REFERENCES Step_Event(Step_Event_ID),
        FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
        ); '''
    # execute code to create Pre_Accelerometer table
    cursor.execute(create_pre_accelerometer_table_query)
    connection.commit()
    print("Pre_Accelerometer table created successfully.")

    ## Raw_Jerk

    # SQL query to create the Raw_Jerk table
    create_pre_accelerometer_table_query = '''CREATE TABLE Raw_Jerk (
                Jerk_ID BIGSERIAL,
                Jerk_value real,
                Time int,
                Recording_ID int,
                Segment_Number int,
                Person_ID int,
                Sensor_ID int,
                Activity_ID int,
                Sensor_Location_ID int,
                Step_Event_ID int,
                Ground_ID int,
                PRIMARY KEY (Jerk_ID),
                FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
                FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
                FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
                FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
                FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
                FOREIGN KEY (Step_Event_ID) REFERENCES Step_Event(Step_Event_ID),
                FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
                ); '''
    # execute code to create Pre_Accelerometer table
    cursor.execute(create_pre_accelerometer_table_query)
    connection.commit()
    print("Raw_Jerk table created successfully.")

    ## FEATURE_FOURIER_COEFFICIENTS

    # SQL query to create the Feature_Fourier_Coefficients table
    create_feature_fourier_coefficients_table_query = '''CREATE TABLE Feature_Fourier_Coefficients (
        Feature_Fourier_Coefficients_ID BIGSERIAL,
        Fourier_Coefficients text,
        Length_Signal int,
        Frequency_Peaks text,
        Frequency_Peaks_Values text,
        Recording_ID int,
        Person_ID int,
        Sensor_ID int,
        Activity_ID int,
        Sensor_Location_ID int,
        Ground_ID int,
        PRIMARY KEY (Feature_Fourier_Coefficients_ID),
        FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
        FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
        FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
        FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
        FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
        FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
        ); '''
    # execute code to create Feature_Fourier_Coefficients table
    cursor.execute(create_feature_fourier_coefficients_table_query)
    connection.commit()
    print("Feature_Fourier_Coefficients table created successfully.")

    ## FEATURE_ACCELEROMETER_GAIT_CYCLE

    # SQL query to create the Feature_Accelerometer_Gait_Cycle table
    create_feature_accelerometer_gait_cycle_table_query = '''CREATE TABLE Feature_Accelerometer_Gait_Cycle (
        Feature_Accelerometer_Gait_Cycle_ID BIGSERIAL,
        Cycle text,
        Minimum_Index int,
        Dominant_Peak_Index int,
        Non_Dominant_Peak_Index int,
        Recording_ID int,
        Segment_Number int,
        Cycle_Number int,
        Person_ID int,
        Sensor_ID int,
        Activity_ID int,
        Sensor_Location_ID int,
        Ground_ID int,
        PRIMARY KEY (Feature_Accelerometer_Gait_Cycle_ID),
        FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
        FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
        FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
        FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
        FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
        FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
        ); '''
    # execute code to create Feature_Accelerometer_Gait_Cycle table
    cursor.execute(create_feature_accelerometer_gait_cycle_table_query)
    connection.commit()
    print("Feature_Accelerometer_Gait_Cycle table created successfully.")

    ## FEATURE_Y_Normalized_ACCELEROMETER_GAIT_CYCLE

    # SQL query to create the Feature_Y_Normalized_Accelerometer_Gait_Cycle table
    create_feature_y_normalized_accelerometer_gait_cycle_table_query \
        = '''CREATE TABLE Feature_Y_Normalized_Accelerometer_Gait_Cycle (
            Feature_Y_Normalized_Accelerometer_Gait_Cycle_ID BIGSERIAL,
            Cycle text,
            Minimum_Index int,
            Dominant_Peak_Index int,
            Non_Dominant_Peak_Index int,
            Recording_ID int,
            Segment_Number int,
            Cycle_Number int,
            Person_ID int,
            Sensor_ID int,
            Activity_ID int,
            Sensor_Location_ID int,
            Ground_ID int,
            PRIMARY KEY (Feature_Y_Normalized_Accelerometer_Gait_Cycle_ID),
            FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
            FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
            FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
            FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
            FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
            FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
            ); '''
    # execute code to create Feature_Y_Normalized_Accelerometer_Gait_Cycle table
    cursor.execute(create_feature_y_normalized_accelerometer_gait_cycle_table_query)
    connection.commit()
    print("Feature_Y_Normalized_Accelerometer_Gait_Cycle table created successfully.")

    ## FEATURE_UNIFORM_ACCELEROMETER_GAIT_CYCLE

    # SQL query to create the Feature_Uniform_Accelerometer_Gait_Cycle table
    create_feature_uniform_accelerometer_gait_cycle_table_query = '''CREATE TABLE Feature_Uniform_Accelerometer_Gait_Cycle (
        Feature_Uniform_Accelerometer_Gait_Cycle_ID BIGSERIAL,'''

    for i in range(200):
        create_feature_uniform_accelerometer_gait_cycle_table_query += "Value_" + str(i)+" real,"

    create_feature_uniform_accelerometer_gait_cycle_table_query += '''Minimum_Index int,
        Dominant_Peak_Index int,
        Non_Dominant_Peak_Index int,
        Correlation_To_Mean_Recording real,
        Usable_Flag boolean,
        Correlation_To_Mean_Person real,
        Correlation_To_Mean_Dataset real,
        Recording_ID int,
        Segment_Number int,
        Cycle_Number int,
        Person_ID int,
        Sensor_ID int,
        Activity_ID int,
        Sensor_Location_ID int,
        Ground_ID int,
        PRIMARY KEY (Feature_Uniform_Accelerometer_Gait_Cycle_ID),
        FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
        FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
        FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
        FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
        FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
        FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
        ); '''

   # execute code to create Feature_Uniform_Accelerometer_Gait_Cycle table
    cursor.execute(create_feature_uniform_accelerometer_gait_cycle_table_query)
    connection.commit()
    print("Feature_Uniform_Accelerometer_Gait_Cycle table created successfully.")

    ## FEATURE_MEAN_ACCELEROMETER_GAIT_CYCLE

    # SQL query to create the Feature_Mean_Accelerometer_Gait_Cycle table
    create_feature_mean_accelerometer_gait_cycle_table_query = '''CREATE TABLE Feature_Mean_Accelerometer_Gait_Cycle (
            Feature_Mean_Accelerometer_Gait_Cycle_ID BIGSERIAL,'''

    for i in range(200):
        create_feature_mean_accelerometer_gait_cycle_table_query += "Value_" + str(i) + " real,"

    create_feature_mean_accelerometer_gait_cycle_table_query += '''Amount_Gait_Cycles int,
        Recording_ID int,
        Person_ID int,
        Sensor_ID int,
        Activity_ID int,
        Sensor_Location_ID int,
        Ground_ID int,
        PRIMARY KEY (Feature_Mean_Accelerometer_Gait_Cycle_ID),
        FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
        FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
        FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
        FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
        FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
        FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
        ); '''
    # execute code to create Feature_Mean_Accelerometer_Gait_Cycle table
    cursor.execute(create_feature_mean_accelerometer_gait_cycle_table_query)
    connection.commit()
    print("Feature_Mean_Accelerometer_Gait_Cycle table created successfully.")

def create_statistical_measure_feature_table(window_size, connection, cursor):
    """
        Creates Statistical Measure table of the provided frame size.

        Args:
            feature_frame (int):
                Feature frame size of which the table should be dropped.
            cursor (object):
                Psycopg2 cursor object. Prevents having to set up the database connection.
            connection (object):
                Psycopg2 connection object. Prevents having to set up the database connection.
        """
    # SQL query to create the Feature_Statistical_Measure table
    create_feature_statistical_measure_table_query = '''CREATE TABLE Feature_Statistical_Measure_''' + str(
        window_size) + ''' (
        Feature_Statistical_Measure_''' + str(window_size) + '''_ID BIGSERIAL,
        M_DP_Value float,
        SD_DP_Value float,
        R_M_DNP_Value float,
        R_SD_DNP_Value float,
        M_SD_DS_Value float,
        R_M_SD_DNS_Value float,
        SD_SD_DS_Value float,
        R_SD_SD_DNS_Value float,
        R_M_SL_Value float,
        R_SD_SL_Value float,
        Recording_ID int,
        Person_ID int,
        Sensor_ID int,
        Activity_ID int,
        Sensor_Location_ID int,
        Ground_ID int,
        PRIMARY KEY (Feature_Statistical_Measure_''' + str(window_size) + '''_ID),
        FOREIGN KEY (Recording_ID) REFERENCES Recording(Recording_ID),
        FOREIGN KEY (Person_ID) REFERENCES Person(Person_ID),
        FOREIGN KEY (Sensor_ID) REFERENCES Sensor(Sensor_ID),
        FOREIGN KEY (Activity_ID) REFERENCES Activity(Activity_ID),
        FOREIGN KEY (Sensor_Location_ID) REFERENCES Sensor_Location(Sensor_Location_ID),
        FOREIGN KEY (Ground_ID) REFERENCES Ground(Ground_ID)
        ); '''
    # execute code to create Feature_Statistical_Measure table
    cursor.execute(create_feature_statistical_measure_table_query)
    connection.commit()