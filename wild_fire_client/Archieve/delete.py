import pandas as pd
df = pd.read_csv('final_data.csv', dtype=str)
print(df.columns.tolist())