CREATE TABLE videos (id TEXT, 
					channel_name TEXT,
					topic TEXT,
					headline TEXT, 
					description TEXT, 
					views INT);
CREATE TABLE registration (email TEXT PRIMARY KEY, 
					name_surname TEXT, 
					password TEXT);
CREATE TABLE subscriptions (id TEXT, user TEXT, channel TEXT);
CREATE TABLE likes (id TEXT, user TEXT, channel TEXT);
CREATE TABLE dislikes (id TEXT, user TEXT, channel TEXT);
CREATE TABLE article (name TEXT PRIMARY KEY, topic TEXT, article TEXT, views INT, author TEXT);
CREATE TABLE likes_article (id TEXT, user TEXT, blog TEXT);
CREATE TABLE dislikes_article (id TEXT, user TEXT, blog TEXT);
CREATE TABLE comment (comment TEXT, user TEXT, title_article TEXT, time_comment TEXT);