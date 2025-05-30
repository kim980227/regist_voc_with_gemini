import psycopg2
from psycopg2 import Error
import os

# config.py에서 DB 접속 정보 임포트
from src.config.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, GET_INSA_INFO_SQL_PATH, GET_AUTH_INFO_SQL_PATH

class Repository:
    """
    데이터베이스 연결 및 데이터 조회 작업을 캡슐화하는 클래스입니다.
    """
    def __init__(self):
        # 클래스 초기화 시 DB 접속 정보가 config에 정의되어 있는지 확인
        # 모든 필수 정보가 없으면 경고 메시지 출력
        if not all([DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD]):
            print("❌ 오류: config.py에 데이터베이스 접속 정보가 누락되었습니다.")
            # 실제 운영 환경에서는 여기서 더 강력한 예외 처리를 고려할 수 있습니다.

    def get_db_connection(self):
        """
        PostgreSQL 데이터베이스 연결을 설정하고 반환합니다.
        """
        conn = None
        try:
            print(f"Connecting to the PostgreSQL database '{DB_NAME}'...")
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT
            )
            print("Database connection successful!")
            return conn
        except Error as e:
            print(f"❌ 데이터베이스 연결 오류: {e}")
            return None

    def get_insa_info(self):
        """
        PostgreSQL 데이터베이스에서 인사 정보를 조회합니다.
        """
        conn = None
        cursor = None
        records_as_dicts = []

        try:
            conn = self.get_db_connection() # 클래스 내의 get_db_connection 메서드 호출
            if not conn:
                return []

            cursor = conn.cursor()

            sql_file_path = GET_INSA_INFO_SQL_PATH
            try:
                with open(sql_file_path, "r", encoding="utf-8") as f:
                    sql_query = f.read()
            except FileNotFoundError:
                print(f"오류: '{sql_file_path}' 파일을 찾을 수 없습니다. SQL 파일을 확인해주세요.")
                return []

            print(f"Executing SQL query from '{sql_file_path}' for 인사 정보...")
            cursor.execute(sql_query)

            column_names = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                records_as_dicts.append(dict(zip(column_names, row)))

            print(f"Query executed successfully. Found {len(records_as_dicts)} records.")

            return records_as_dicts

        except Error as e:
            print(f"Error executing SQL query for 인사 정보: {e}")
            if conn:
                conn.rollback() # 오류 발생 시 롤백
            return []
        finally:
            if cursor:
                cursor.close()
                print("Cursor closed.")
            if conn:
                conn.close()
                print("Database connection closed.")

    def get_auth_info(self):
        """
        PostgreSQL 데이터베이스에서 권한(auth) 정보를 조회합니다.
        sr_member 테이블에서 active_yn = 'Y'이고 auth가 'SM' 또는 'ADMIN'인 멤버 정보를 가져옵니다.
        """
        conn = None
        cursor = None
        auth_records = []

        try:
            conn = self.get_db_connection()
            if not conn:
                return []

            cursor = conn.cursor()

            sql_file_path = GET_AUTH_INFO_SQL_PATH
            try:
                with open(sql_file_path, "r", encoding="utf-8") as f:
                    sql_query = f.read()
            except FileNotFoundError:
                print(f"오류: '{sql_file_path}' 파일을 찾을 수 없습니다. SQL 파일을 확인해주세요.")
                return []

            print(f"Executing SQL query from '{sql_file_path}' for 인사 정보...")
            
            print("Executing SQL query for 담당자 정보 (SM, ADMIN)...")
            cursor.execute(sql_query)

            column_names = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                auth_records.append(dict(zip(column_names, row)))

            print(f"Query executed successfully. Found {len(auth_records)} authentication records.")
            
            return auth_records

        except Error as e:
            print(f"Error executing SQL query for 권한 정보: {e}")
            if conn:
                conn.rollback() # 오류 발생 시 롤백
            return []
        finally:
            if cursor:
                cursor.close()
                print("Cursor closed.")
            if conn:
                conn.close()
                print("Database connection closed.")