"""
Sets up and fills the initial database (without preprocessing)
"""
import time
import decimal
import create_postgres_db
import insert_dimensions
import insert_facts_HuGaDB
import insert_facts_McGill
import insert_facts_MAREA
import insert_facts_Vajdi
import insert_facts_OU_ISIR_ISD1
import insert_facts_OU_ISIR_ISD2
import insert_facts_OU_ISIR_SAID
import insert_facts_A_database_of_human_gait

def run_etl():
    """
    Runs all extraction functions in correct order
    """

    print("Starting Process...")
    start = time.time()

    print("Creating Database.")
    create_postgres_db.create_db()

    print("Inserting Dimensions.")
    insert_dimensions.insert_dimensions()

    print("Inserting Facts.")

    print("Progress 0/8")

    insert_facts_HuGaDB.insert_facts()
    hugadb_time = time.time()
    print("HuGaDB Dataset inserted in: " + str(int(decimal.Decimal((hugadb_time - start)))) + " seconds")
    print("Progress 1/8")

    insert_facts_McGill.insert_facts()
    mcgill_time = time.time()
    print("McGill Dataset inserted in: " + str(int(decimal.Decimal((mcgill_time - hugadb_time)))) + " seconds")
    print("Progress 2/8")

    insert_facts_MAREA.insert_facts()
    marea_time = time.time()
    print("MAREA Dataset inserted in: " + str(int(decimal.Decimal((marea_time - mcgill_time)))) + " seconds")
    print("Progress 3/8")

    insert_facts_Vajdi.insert_facts()
    vajdi_time = time.time()
    print("Vajdi Dataset inserted in: " + str(int(decimal.Decimal((vajdi_time - marea_time)))) + " seconds")
    print("Progress 4/8")

    insert_facts_OU_ISIR_ISD1.insert_facts()
    ou_isir_1_time = time.time()
    print("OU-ISIR-ISD1 Dataset inserted in: " + str(int(decimal.Decimal((ou_isir_1_time - vajdi_time)))) + " seconds")
    print("Progress 5/8")

    insert_facts_OU_ISIR_ISD2.insert_facts()
    ou_isir_2_time = time.time()
    print("OU-ISIR-ISD2 Dataset inserted in: " + str(int(decimal.Decimal((ou_isir_2_time - ou_isir_1_time)))) + " seconds")
    print("Progress 6/8")

    insert_facts_OU_ISIR_SAID.insert_facts()
    ou_isir_3_time = time.time()
    print("OU-ISIR-SAID Dataset inserted in: " + str(int(decimal.Decimal((ou_isir_3_time - ou_isir_2_time)))) + " seconds")
    print("Progress 7/8")

    insert_facts_A_database_of_human_gait.insert_facts()
    a_database_time = time.time()
    print("A database of human gait Dataset inserted in: " + str(int(decimal.Decimal((a_database_time - ou_isir_3_time)))) + " seconds")
    print("Progress 8/8")

    end = time.time()
    print("Database has been filled.")
    print("Total time elapsed: " + str(int(decimal.Decimal((end - start)))) + " seconds")
    print("Ending Process...")
    
    
if __name__ == "__main__":
    run_etl()
