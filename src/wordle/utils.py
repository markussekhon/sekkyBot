import os
import random
import asyncio
import psycopg2

from collections import Counter
from dotenv import load_dotenv
from datetime import datetime

def findCount(cursor):
    query = """
            SELECT COUNT(*)
            FROM wordlemasterlist;
            """
    try:
        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            count = result[0]
            return count
        else:
            return 0

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        print("Failed to execute query")


def findWord(cursor, id):
    query = """
            SELECT
                word
            FROM
                wordlemasterlist
            WHERE
                id = %s;
            """
    try:
        cursor.execute(query, (id,))
        result = cursor.fetchone()

        if result:
            word = result[0]
            return word
        else:
            return None

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        print("Failed to execute query")


def validWord(cursor, guess):
    query = """
            SELECT
                COUNT(*)
            FROM
                wordlemasterlist
            WHERE
                word = %s;
            """
    if len(guess) != 5:
        return False

    #Safe guard to prevent SQL injection
    if not guess.isalnum():
        return False

    try:
        cursor.execute(query, (guess,))
        result = cursor.fetchone()

        if result:
            count = result[0]
            return count > 0
        else:
            return False

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        print("Failed to execute query")


def findAttempts(cursor, serverID, discordID):
    query = """
            SELECT
                attempts
            FROM
                wordlegames
            WHERE
                serverID = %s
                AND
                discordID = %s;
            """
    try:
        cursor.execute(query, (serverID, discordID))
        result = cursor.fetchone()

        if result:
            count = result[0]
            return count
        
        else:
            updateAttempts(cursor, serverID, discordID, 0)
            return 0
    
    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        return 6


def updateAttempts(cursor, serverID, discordID, attempts):
    insertion = """
                INSERT INTO
                    wordlegames (serverID, discordID, attempts)
                VALUES
                    (%s , %s , %s)
                ON CONFLICT
                    (serverID, discordID)
                DO UPDATE
                    SET attempts = EXCLUDED.attempts;
                """
    try:
        cursor.execute(insertion, (serverID, discordID, attempts))
        cursor.connection.commit()

    except psycopg2.Error as e:
        print(f"An error occurred: {e}")
        cursor.connection.rollback()


def pickTarget(cursor, seed=str(datetime.today().date())):
    count = findCount(cursor)
    random.seed(seed)
    id = random.randint(1, count)
    word = findWord(cursor, id)
    return word


async def wordleRound(cursor, serverID, discordID, guess):
    seed = str(serverID) + str(datetime.today().date())
    target = pickTarget(cursor, seed=seed)
    attempts = findAttempts(cursor, serverID, discordID)

    if attempts < 6:
        if not validWord(cursor, guess):
            #bot should notify user guess was invalid based on 0
            return 2

        if guess == target:
            #based on gamestate, bot should notify user it won
            updateAttempts(cursor, serverID, discordID, 6)
            return 1

        gamestate = [0,0,0,0,0]
        library = Counter(target)
        
        for index, t_char, g_char in zip(range(0,5), target, guess):
            if t_char == g_char:
                gamestate[index] = 2
                library[t_char] -= 1

        for index, g_char in enumerate(guess):
            if library.get(g_char, 0) > 0:
                gamestate[index] = 1
                library[g_char] -= 1

        attempts += 1
        updateAttempts(cursor, serverID, discordID, attempts)
        return [gamestate,attempts]

    else:
        #bot should notify user that it cant play until reset
        return 0


async def test():
    # Load environment variables
    load_dotenv()
    DB_NAME = str(os.getenv('POSTGRES_DB'))
    DB_USER = str(os.getenv('POSTGRES_USER'))
    DB_PASSWORD = str(os.getenv('POSTGRES_PASSWORD'))
    DB_HOST = str(os.getenv('POSTGRES_HOST'))

    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST
        )
        cursor = conn.cursor()

        serverID = "1"
        discordID = "1"

        for _ in range(7):
            guess = input("Guess: ")
            result = await wordleRound(
                cursor, serverID, discordID, guess)
            print(result)

    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    asyncio.run(test())
