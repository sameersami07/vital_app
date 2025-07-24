import pandas as pd
import sys
import json

from Bio_Epidemiology_NER.bio_recognizer import ner_prediction

pd.set_option('display.max_colwidth', 20)

if len(sys.argv) < 6:
    print("Usage: python check.py <age> <brand> <market_status> <case_description> <allergies>")
    sys.exit(1)

try:
    age = int(sys.argv[1])
except ValueError:
    print("Error: Age must be an integer.")
    sys.exit(1)

brand = sys.argv[2]
market_status = sys.argv[3].lower() == "true"
case_description = sys.argv[4]
allergies_input = sys.argv[5].replace(" ", "").split(",") if sys.argv[5] else []

doc = f"CASE: {case_description}"
analysed = ner_prediction(corpus=doc, compute='cpu')

if analysed.shape == (0, 0):
    print("Cannot analyse your status: Please be more specific!")
    sys.exit(f"args: {analysed.shape}")

analysed_filtered = analysed[
    analysed["entity_group"].isin(["Diagnostic_procedure", "Biological_structure"])
]

# Load and combine data
sup_merged = pd.concat([
    pd.read_csv("LabelStatements_1.csv", engine='python'),
    pd.read_csv("LabelStatements_2.csv", engine='python')
], ignore_index=True)

prover_merged = pd.concat([
    pd.read_csv("ProductOverview_1.csv", engine='python'),
    pd.read_csv("ProductOverview_2.csv", engine='python')
], ignore_index=True)

othing_merged = pd.concat([
    pd.read_csv("OtherIngredients_1.csv", engine='python'),
    pd.read_csv("OtherIngredients_2.csv", engine='python')
], ignore_index=True)

sup_merged = sup_merged[sup_merged["Statement Type"] == "Other"]

# Merge all datasets
full_merged = pd.merge(prover_merged, sup_merged, on=["URL", "DSLD ID", "Product Name"], how="right")
full_merged = pd.merge(full_merged, othing_merged, on=["URL", "DSLD ID", "Product Name"], how="right")

# NER Filtering
analysed_df = pd.DataFrame()
for _, row in analysed_filtered.iterrows():
    matches = full_merged[full_merged["Statement"].str.contains(row['value'], na=False)]
    analysed_df = pd.concat([analysed_df, matches], ignore_index=True)

if analysed_df.shape == (0, 0):
    print("No supplements available that satisfy your requirements")
    sys.exit("Bailing out of the program.")

# Age filtering
if age <= 6:
    kids_forms = ["Powder", "Liquid", "Gummy or Jelly"]
    kids_df = pd.concat([
        analysed_df[analysed_df["Supplement Form [LanguaL]"].str.contains(form, case=False, na=False)]
        for form in kids_forms
    ], ignore_index=True)
    others_df = analysed_df.drop(kids_df.index, errors='ignore')
    analysed_df = pd.concat([kids_df, others_df], ignore_index=True)

# Brand filtering
if brand.lower() != "nan":
    brand_df = analysed_df[analysed_df["Brand Name"].str.contains(brand, case=False, na=False)]
    rest_df = analysed_df.drop(brand_df.index, errors='ignore')
    analysed_df = pd.concat([brand_df, rest_df], ignore_index=True)

# Market status filtering
if market_status:
    analysed_df = analysed_df[analysed_df["Market Status"].str.contains("On Market", case=False, na=False)]

# Allergy filtering
allergic_food_dict = {
    'peanuts': ['peanuts'],
    'nuts': ['nuts', 'Walnuts', 'almonds', 'cashews', 'pistachios', 'pecans', 'hazelnuts'],
    'milk': ['cheese', 'butter', 'yogurt', 'milk', 'dairy'],
    'eggs': ['chicken', 'egg', 'eggs'],
    'fish': ['fish', 'salmon', 'tuna', 'halibut'],
    'shellfish': ['shellfish', 'shrimp', 'crab', 'lobster', 'mussel'],
    'wheat': ['bread', 'wheat', 'pasta', 'baked'],
    'soy': ['soy', 'tofu'],
    'mustard': ['mustard', 'mustard seed'],
    'sesame': ['sesame', 'sesame oil', 'sesame seed'],
    'celery': ['celery'],
    'sulfites': ['sulfite'],
    'lupin': ['lupin'],
    'mollusks': ['octopus', 'squid', 'cuttlefish'],
    'kiwi': ['kiwi'],
    'pineapple': ['pineapple'],
    'avocado': ['avocado', 'guacamole'],
    'banana': ['banana'],
    'strawberries': ['strawberry'],
    'tomato': ['tomato']
}

allergy_keys = {
    key for allergy in allergies_input
    for key, values in allergic_food_dict.items()
    if any(allergy.lower() == val.lower() for val in values)
}

for key in allergy_keys:
    analysed_df = analysed_df[~analysed_df["Other Ingredients"].str.contains(key, case=False, na=False)]

# Output
print(json.dumps(json.loads(analysed_df.to_json(orient="split")), indent=2))