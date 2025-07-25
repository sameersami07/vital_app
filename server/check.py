import pandas as pd
import sys
import json
import argparse
import time

from Bio_Epidemiology_NER.bio_recognizer import ner_prediction

pd.set_option('display.max_colwidth', 20)

def error_response(message):
    print(json.dumps({"success": False, "error": message}))
    sys.exit(0)

def main():
    print("Starting script...", file=sys.stderr)
    parser = argparse.ArgumentParser(description="Supplement Recommendation Engine")
    parser.add_argument('--age', type=int, required=True)
    parser.add_argument('--brand', type=str, default="")
    parser.add_argument('--market_status', type=str, default="false")
    parser.add_argument('--description', type=str, required=True)
    parser.add_argument('--allergies', type=str, default="")

    args = parser.parse_args()

    age = args.age
    brand = args.brand.strip()
    market_status = args.market_status.lower() == "true"
    case_description = args.description.strip()
    allergies_input = [a.strip().lower() for a in args.allergies.split(",") if a.strip()]

    print("Running NER prediction...", file=sys.stderr)
    doc = f"CASE: {case_description}"
    try:
        analysed = ner_prediction(corpus=doc, compute='cpu')
    except Exception as e:
        error_response(f"NER prediction failed: {str(e)}")

    if analysed.shape == (0, 0):
        error_response("Cannot analyse your status: Please be more specific!")

    analysed_filtered = analysed[
        analysed["entity_group"].isin(["Diagnostic_procedure", "Biological_structure"])
    ]

    print("Loading CSV data...", file=sys.stderr)
    try:
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
    except Exception as e:
        error_response(f"Error loading data: {str(e)}")

    sup_merged = sup_merged[sup_merged["Statement Type"] == "Other"]
    full_merged = pd.merge(prover_merged, sup_merged, on=["URL", "DSLD ID", "Product Name"], how="right")
    full_merged = pd.merge(full_merged, othing_merged, on=["URL", "DSLD ID", "Product Name"], how="right")

    print("Filtering by NER results...", file=sys.stderr)
    analysed_df = pd.DataFrame()
    for _, row in analysed_filtered.iterrows():
        matches = full_merged[full_merged["Statement"].str.contains(row['value'], na=False)]
        analysed_df = pd.concat([analysed_df, matches], ignore_index=True)

    if analysed_df.empty:
        error_response("No supplements available that satisfy your requirements")

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
    if brand and brand.lower() != "nan":
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
        if any(allergy == val.lower() for val in values)
    }

    for key in allergy_keys:
        analysed_df = analysed_df[~analysed_df["Other Ingredients"].str.contains(key, case=False, na=False)]

    # Output
    recommendations = json.loads(analysed_df.head(20).to_json(orient="records"))  # Limit to 20 results
    print(json.dumps({"success": True, "recommendations": recommendations}, indent=2))
    print("Script finished successfully.", file=sys.stderr)

if __name__ == "__main__":
    main()