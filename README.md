# dining-reservation-system
1. pip install Flask Flask-SQLAlchemy Flask-JWT-Extended python-dateutil
2. create env:
        ADMIN_API_KEY = 'workindiaadmin'
3. edit config file
4. create tables:
   
        CREATE TABLE User(
          id INT AUTO_INCREMENT PRIMARY KEY,
          username VARCHAR(50) NOT NULL UNIQUE,
          password VARCHAR(255) NOT NULL,
          email VARCHAR(255) NOT NULL UNIQUE
        );
        
        CREATE TABLE dining_place (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            address VARCHAR(100) NOT NULL,
            website VARCHAR(100),
            phone_no VARCHAR(10) NOT NULL UNIQUE,
            open_time TIME NOT NULL,
            close_time TIME NOT NULL,
            booked_slots BLOB
        );
        
        CREATE TABLE Booking (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            place_id INTEGER NOT NULL,
            start_time TIMESTAMP NOT NULL,
            end_time TIMESTAMP NOT NULL,
            FOREIGN KEY (user_id) REFERENCES User(id),
            FOREIGN KEY (place_id) REFERENCES dining_place(id)
        );
