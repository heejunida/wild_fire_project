import oracledb
import sys
import json

# --- IMPORTANT: DATABASE CREDENTIALS ---
# For security, it's best to load these from environment variables or a secure config file.
# Do not commit real credentials to version control.
DB_USER = "wildfire"
DB_PASSWORD = "1234"
DB_DSN = "localhost:1521:XE"  # e.g., "localhost:1521/XEPDB1"

def save_prediction_to_oracle(fire_id, fire_datetime, lat, lon, area_pred, fwi_pred, dir_pred, dist_pred, features_json):
    """
    Connects to the Oracle database and inserts a single prediction record.
    """
    sql = """
        INSERT INTO ML_TRAINING_FEATURES (
            ID, FIRE_DATETIME, LATITUDE, LONGITUDE, 
            AREA_PRED, FWI_PRED, DIR_PRED, DISTANCE_PRED, 
            FEATURES_JSON
        ) VALUES (:1, TO_DATE(:2, 'YYYY-MM-DD HH24:MI:SS'), :3, :4, :5, :6, :7, :8, :9)
    """
    
    try:
        # Establish a connection to the Oracle database
        with oracledb.connect(user=DB_USER, password=DB_PASSWORD, dsn=DB_DSN) as connection:
            with connection.cursor() as cursor:
                # Create a CLOB object for the JSON data
                features_clob = cursor.var(oracledb.DB_TYPE_CLOB)
                features_clob.setvalue(0, json.dumps(features_json))

                # Execute the insert statement
                cursor.execute(sql, [
                    fire_id,
                    fire_datetime,
                    lat,
                    lon,
                    area_pred,
                    fwi_pred,
                    dir_pred,
                    dist_pred,
                    features_clob
                ])
                
                # Commit the transaction
                connection.commit()
                print("✅ Successfully saved prediction to Oracle database.")

    except oracledb.Error as e:
        print(f"❌ Oracle Database Error: {e}", file=sys.stderr)
        # Optionally, re-raise the exception if the calling script should handle it
        # raise e
    except Exception as e:
        print(f"❌ An unexpected error occurred during database operation: {e}", file=sys.stderr)
        # raise e

# The __main__ block is intentionally left empty for this module,
# as it is designed to be imported and used by other scripts.
if __name__ == '__main__':
    pass
