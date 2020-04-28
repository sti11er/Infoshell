import sqlite3

conn = sqlite3.connect("video_anketa.bd")
with conn:
	cursor = conn.cursor()
	cursor.execute("DROP TABLE IF EXISTS videos;")
	cursor.execute("DROP TABLE IF EXISTS registration;")
	cursor.execute("CREATE TABLE videos (id TEXT, channel_name TEXT, headline TEXT, description TEXT, views INT, subscription INT)")
	cursor.execute("CREATE TABLE registration (email TEXT PRIMARY KEY, name_surname TEXT, password TEXT)")
	cursor.execute("SELECT * FROM registration")
	conn.commit()
	rc = cursor.fetchall()
	print(rc)