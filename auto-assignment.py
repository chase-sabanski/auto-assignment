import os
import pandas as pd
from datetime import datetime
from collections import Counter

# Changes the cwd to the directory of the file
current_directory = os.path.dirname(__file__)
os.chdir(current_directory) 

# ✅ import an export of all swimlane cases, only three columns are needed: "input_sl_tickets", change to default SL export name when the script is finished
for filename in os.listdir(current_directory):
    if filename.startswith("Case and Incident Management"):
        input_sl_tickets = pd.read_csv(filename)
        sl_tickets_with_CU = pd.read_csv(filename)
        sl_tickets_with_CU.fillna("EMPTY", inplace=True)
    elif filename.startswith("model_assignment"):
        os.remove(filename)
    elif filename.startswith("Swimlane Tickets with Updated Owners"):
        os.remove(filename)

# ✅ reduce dataframe to the 3 necessary columns
trimmed_input = input_sl_tickets[["Make", "Model", "Current Owner"]]
# caveat: some models are "null" from Cynerio, these get dropped from the assignment. We'll see how big of an issue it becomes.
trimmed_input.fillna("EMPTY", inplace=True)

# ✅ separate unassigned models into a list, drop all rows with "EMPTY" from dataframe
unassigned_models = []

# fix: empty is getting passed to unassigned models (empty in current owner and model)
for index, row in trimmed_input.iterrows():
    if row["Current Owner"] == "EMPTY" and row["Model"] == "EMPTY":
        trimmed_input.drop([index], inplace=True)
    elif row["Current Owner"] == "EMPTY":
        unassigned_models.append(row["Model"])
        trimmed_input.drop([index], inplace=True)
    elif row["Model"] == "EMPTY":
        trimmed_input.drop([index], inplace=True)

# 4. create dictionary of assigned models, assign analyst by # of occurrences a given model is assigned to them
# rename this dictionary for clarity?
assignment_dict = {}

# nested if statements... somehow this works 🤯 probably should have broken this up but 🤷‍♂️
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

existing_assignments = {}

for model in assignment_dict:
    res = max(assignment_dict[model], key=assignment_dict[model].get)
    existing_assignments[model] = res

# forgot what this did, but I'm gonna include it anyway
existing_assignments.pop("Model", None)

# ✅ remove duplicate models (if they appear in existing_assignments dictionary) from unassigned model list
for model in unassigned_models:
    if model in existing_assignments:
        unassigned_models.remove(model)

# ✅ sort and assign unassigned models as a dictionary
analysts_import = pd.read_csv("analysts.csv")
analysts = analysts_import["Analysts"].to_list()

# 6.5 sort analyst list by ticket count before assigning new models, analyst with most tickets is last and vice versa
current_owner_list = trimmed_input["Current Owner"].to_list()
filtered_owners = []

# removes analysts from sorted_current_owner_list if they aren't present on the analysts.csv
for item in current_owner_list:
    if item in analysts:
        filtered_owners.append(item)

    # sort current owner list by frequency of occurence, then reverse
sorted_current_owner_list = [item for items, c in Counter(filtered_owners).most_common()
                 for item in [items] * c]
    
    # removes duplicate values and reverses the list so that the analyst with the fewest tickets is the first item
sorted_current_owner_list = list(dict.fromkeys(sorted_current_owner_list))
sorted_current_owner_list.reverse()

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

# this section does several things:
# > it determines the average amount of tickets an analyst should receive by dividing the total number of unassigned tickets by the number of analysts
# > if an analyst already has more than or equal to the average after assigning tickets based on who has the most instances of a given model, it excludes that analyst from getting new unassigned tickets/models
# > it assigns new tickets based on whether the analyst has less than the average tickets
input_sl_tickets.fillna("EMPTY", inplace=True)

count_unassigned_tickets = 0
for index, row in input_sl_tickets.iterrows():
    if row["Current Owner"] == "EMPTY":
        count_unassigned_tickets += 1

average_tickets = round(count_unassigned_tickets/len(analysts))

def model_assign(row):
    if row["Model"] in existing_assignments and row["Current Owner"] == "EMPTY":
        return existing_assignments[row["Model"]]
    else:
        return

input_sl_tickets["Model Assignment"] = input_sl_tickets.apply(model_assign, axis=1)

tickets_from_existing_assignments = {}

for index, row in input_sl_tickets.iterrows():
    if row["Model Assignment"] not in tickets_from_existing_assignments and row["Model Assignment"] in analysts:
        tickets_from_existing_assignments[row["Model Assignment"]] = 1
    elif row["Model Assignment"] in tickets_from_existing_assignments:
        tickets_from_existing_assignments[row["Model Assignment"]] += 1

# this sorts analysts by the count of tickets assigned to them from the model assignment section, ordered from least amount to most amount (value)
# found this one-liner from geeksforgeeks, it's beautiful 😭
analysts_sorted_by_values = {k: v for k, v in sorted(tickets_from_existing_assignments.items(), key=lambda item: item[1])}

analysts_under_ticket_average = []

for key in analysts_sorted_by_values:
    if analysts_sorted_by_values[key] < average_tickets:
        analysts_under_ticket_average.append(key)

# assigns tickets with models that no analyst is currently working
new_model_assignments = {}
analyst = 0

for key in final_unassigned_model_list:
    new_model_assignments[key] = analysts_under_ticket_average[analyst]
    analyst = analyst + 1
    if analyst == len(analysts_under_ticket_average):
        analysts_under_ticket_average.reverse()
        analyst = 0

# ✅ combine the two dictionaries
new_model_assignments.update(existing_assignments)

# apply updated current owner column to Swimlane export
def current_owner(row):
    if row["Model"] != "EMPTY" and row["Outdated Current Owner"] == "EMPTY":
        return new_model_assignments[row["Model"]]
    elif row["Outdated Current Owner"] != "EMPTY":
        return row["Outdated Current Owner"]

sl_tickets_with_CU.rename(columns={"Current Owner": "Outdated Current Owner"}, inplace=True)
sl_tickets_with_CU["Current Owner"] = sl_tickets_with_CU.apply(current_owner, axis=1)

# ✅ export the final dictionary as csv
dictionary_output = pd.DataFrame.from_dict(new_model_assignments, orient="index",
                                            columns=["Current Owner"])
dictionary_output.index.name = "Model"
timestamp = datetime.now().strftime("%Y_%m_%d-%I.%M.%S %p")
dictionary_output.to_csv(f"model_assignments - {timestamp}.csv", sep=",", index=True, encoding="utf-8")
sl_tickets_with_CU.to_csv(f"Swimlane Tickets with Updated Owners - {timestamp}.csv", sep=",", index=False, encoding="utf-8")

input("Success! Press Enter to exit...")
