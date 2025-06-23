import os
import pandas as pd
from collections import Counter

# Changes the cwd to the directory of the file
current_directory = os.path.dirname(__file__)
os.chdir(current_directory)

# Steps
# ✅ 1. import an export of all swimlane cases, only three columns are needed: "input_sl_tickets", change to default SL export name when the script is finished
#       > Current Owner
#       > Make
#       > Model
input_sl_tickets = pd.read_csv("input_sl_tickets.csv")

# ✅ 2. reduce dataframe to the 3 necessary columns
trimmed_input = input_sl_tickets[["Make", "Model", "Current Owner"]]
# caveat: some models are "null" from Cynerio, these get dropped from the assignment. We'll see how big of an issue it becomes.
trimmed_input.fillna("EMPTY", inplace=True)

# ✅ 3. separate unassigned models into a list, drop all rows with "EMPTY" from dataframe
unassigned_models = []

for index, row in trimmed_input.iterrows():
    if row["Current Owner"] == "EMPTY":
        unassigned_models.append(row["Model"])
        trimmed_input.drop([index], inplace=True)
    elif row["Model"] == "EMPTY":
        trimmed_input.drop([index], inplace=True)
# verified: numbers are expected!

# 4. create dictionary of assigned models, assign analyst by # of occurrences a given model is assigned to them
# rename this dictionary for clarity?
assignment_dict = {}

# somehow this works 🤯 probably should have broken this up but 🤷‍♂️
for index, row in trimmed_input.iterrows():
    if row["Model"] not in assignment_dict:
        assignment_dict[row["Model"]] = {}
        if row["Current Owner"] not in assignment_dict[row["Model"]]:
            assignment_dict[row["Model"]][row["Current Owner"]] = 0
    elif row["Model"]  in assignment_dict:
        if row["Current Owner"] not in assignment_dict[row["Model"]]:
            assignment_dict[row["Model"]][row["Current Owner"]] = 0
        if row["Current Owner"] in assignment_dict[row["Model"]]:
            assignment_dict[row["Model"]][row["Current Owner"]] += 1
# verified: analyst with the most occurrences of a model gets assigned the model 🙌

existing_assignments = {}

for model in assignment_dict:
    res = max(assignment_dict[model], key=assignment_dict[model].get)
    existing_assignments[model] = res

# forgot what this did, but I'm gonna include it anyway
existing_assignments.pop("Model", None)

# ✅ 5. remove duplicate models (if they appear in existing_assignments dictionary) from unassigned model list
for model in unassigned_models:
    if model in existing_assignments:
        unassigned_models.remove(model)

# ✅ 6. sort and assign unassigned models as a dictionary
analysts_import = pd.read_csv("analysts.csv")
analysts = analysts_import["Analysts"].to_list()

    # sort model list by frequency of occurence
sorted_unassigned_models = [item for items, c in Counter(unassigned_models).most_common()
                 for item in [items] * c]

    # remove duplicates in model list, but keep the placement of the list items
final_unassigned_model_list = []
for item in sorted_unassigned_models:
    if item == "":
        continue
    if item not in final_unassigned_model_list:
        final_unassigned_model_list.append(item)

new_model_assignments = {}
analyst = 0

for key in final_unassigned_model_list:
    new_model_assignments[key] = analysts[analyst]
    analyst = analyst + 1
    if analyst == len(analysts):
        analysts.reverse()
        analyst = 0

# ✅ 7. combine the two dictionaries
new_model_assignments.update(existing_assignments)

# ✅ 8. export the final dictionary as csv
dictionary_output = pd.DataFrame.from_dict(new_model_assignments, orient="index",
                                            columns=["Current Owner"])
dictionary_output.index.name = "Model"
dictionary_output.to_csv("dictionary test.csv", sep=",", index=True, encoding="utf-8")
input("Success! Press Enter to exit...")
