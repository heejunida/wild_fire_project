import pandas as pd

df = pd.read_csv("preprocess/csv/datetime_changed_end.csv")

df = df.drop(columns="forest_type_mode_5x5")

df.to_csv("preprocess/csv/forest_type_deleted.csv", index = False)
df.to_excel("preprocess/csv/forest_type_deleted.xlsx", index = False)
