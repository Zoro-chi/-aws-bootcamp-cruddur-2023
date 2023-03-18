import json
import psycopg2
import os

def lambda_handler(event, context):
    user = event['request']['userAttributes']
    print('userAttributes')
    print(user)

    user_display_name  = user['name']
    user_email         = user['email']
    user_handle        = user['preferred_username']
    user_cognito_id    = user['sub']
    
    conn = None  # assign conn a value of None at the beginning of the function
    
    try:
        print('entered-try')
        sql = f"""
            INSERT INTO public.users (
                display_name, 
                email,
                handle, 
                cognito_user_id
            ) 
            VALUES(%s,%s,%s,%s)
        """
        print('SQL Statement ----')
        print(sql)

        # wrap the entire database interaction block in another try block
        try:
            conn = psycopg2.connect(os.getenv('CONNECTION_URL'))  # assign the connection object to conn inside the inner try block
            cur = conn.cursor()
            params = [
                user_display_name,
                user_email,
                user_handle,
                user_cognito_id
            ]
            cur.execute(sql,*params)
            conn.commit() 
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        finally:
            if conn is not None:
                cur.close()
                conn.close()
                print('Database connection closed.')
    except:
        pass  # handle the exception here if needed
    
    return event