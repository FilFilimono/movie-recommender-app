from backend.core.config import AppConfig
from backend.database.manager import DatabaseManager  
from backend.database.prefs_repo import PreferencesRepository

db = DatabaseManager(AppConfig.DB_PATH)
db.connect()
prefs = PreferencesRepository(db).get_by_user_id(1)
# print(prefs.certification)  # должно быть "NC-17"
# print(prefs.to_criteria_dict())  # certification должно быть в словаре

prefs = PreferencesRepository(db).get_by_user_id(1)
# print(repr(prefs.certification))  # что выводит?



import json
row = db.execute("SELECT data FROM preferences WHERE user_id = 1").fetchone()
# print(json.loads(row['data']))

prefs = PreferencesRepository(db).get_by_user_id(1)
print(prefs.to_criteria_dict())