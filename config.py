import os

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql://root:password@localhost:3306/dining_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = 'workindiajwt'
    ADMIN_API_KEY = 'workindiaadmin'
