# program setup
from __future__ import annotations

import math
import os
import pprint
import tkinter as tk
from tkinter import messagebox
from typing import Any, Optional, TextIO

from classes import Graph
from vis import visualize_graph

# variables to be used later
EQUIPMENT = {}
TRAITS = {}
SKILLS = {}
CHOSEN_TRAITS = []
PLAYSTYLE_PREFERENCES = []
SPECIALDICT = {}

NORMALIZATION_DATA_WEPS = [
    ["Damage per shot", 1, 1075],
    ["Damage per second", 1.3, 390],
    ["Rate of fire", 0.2, 30],
    ["Critical chance multiplier", 0, 100],
    ["Critical hit Damage", 1, 110],
    ["Magazine capacity (shots per reload)", 1, 240],
    ["Weapon weight", 0.25, 40],
    ["Skill required", 0, 100],
    ["STR required", 1, 10]
]

NORMALIZATION_DATA_CLOTH = [
    ["DT", 0, 28],
    ["DR", 0, 3],
    ["Weight", 1, 45]
]

WEIGHT_WEPS = [0.3, 0.2, 0.1, 0.1, 0.1, 0.1, -0.001, -0.01, -0.001]

WEIGHT_CLOTH = [3, 1, -1]


def get_rest(directory: str) -> dict[Any, list]:
    """
    Reads the weapon information from the files in the provided directory and stores them in a dictionary.

    Preconditions:
        - directory contains only valid .csv files
    """

    # extract each file in the local data directory
    files = os.listdir(directory)
    files = [x for x in files if ".csv" in x]
    database = {key[:-4].capitalize(): [] for key in files}

    # we begin to categorize our data
    for file in files:
        file_name = file[:-4].lower()

        for category in database:
            if category.lower() in file_name:
                database[category].append(file)

    # we call parse_rest to parse through the whole spreadsheet
    for category, files in database.items():
        items = []

        for file in files:
            with open(os.path.join(directory, file), 'r', encoding="ISO-8859-1") as f:
                items.extend(parse_rest(f))

        database[category] = items

    # adds an extra "No Trait" option
    if "traits" in directory.lower():
        global TRAITS
        TRAITS = database
        TRAITS["Traits - vanilla"].insert(0, {
            'Name': 'No Trait',
            'Benefit': "No downsides...",
            'Penalty': "You are officially boring."
        })

    # we print out our equipment information
    with open("output/equipmentInfo.txt", "a") as log_file:
        for category, items in database.items():
            print(category, file=log_file)
            for item in items:
                pprint.pprint(item, stream=log_file, sort_dicts=False)
                print("", file=log_file)
            print("---------------", file=log_file)

    # return the equipment database
    return database


def parse_rest(file: TextIO) -> list[dict[str, str]]:
    """
    Parses through a .csv file and standardizes its format into a categorized list of dictionaries.
    """
    # var setup
    attributes = file.readline().strip().split(",")
    res = []

    # for each row -
    for row in file:

        row_list = row.split(",")

        # - we remove leftovers from bad encoding and standardize the format
        for index in range(len(row_list)):
            row_list[index] = row_list[index].replace(u'\xa0', u' ')
            row_list[index] = row_list[index].replace('*', '')
            row_list[index] = row_list[index].replace('/comma', ',')

        res.append({attributes[i].strip(): row_list[i].strip() for i in range(len(attributes))})

    # returning the list
    return res


class SpecialAllocator(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("SPECIAL Allocator")
        self.geometry("200x450")

        self.stats = {stat: tk.IntVar(value=5) for stat in
                      ["STR", "PER", "END", "CHR", "INT", "AGL", "LCK"]}

        self.total_points = 40
        self.init_ui()

    def init_ui(self) -> None:
        row = 0
        for stat, var in self.stats.items():
            tk.Label(self, text=stat).grid(row=row, column=0, padx=10, pady=10)
            tk.Button(self, text="-", command=lambda s=stat: self.change_stat(s, -1)).grid(row=row, column=1, padx=5)
            tk.Entry(self, textvariable=var, state='readonly', width=5).grid(row=row, column=2, padx=5)
            tk.Button(self, text="+", command=lambda s=stat: self.change_stat(s, 1)).grid(row=row, column=3, padx=5)
            row += 1

        self.total_label = tk.Label(self, text="Remaining Points: 5")
        self.total_label.grid(row=row, column=0, columnspan=4, pady=10)

        self.reset_button = tk.Button(self, text="Reset", command=self.reset_stats)
        self.reset_button.grid(row=row + 1, column=0, columnspan=4, pady=10)

        self.quit_button = tk.Button(self, text="Finish", command=self.end)
        self.quit_button.grid(row=row + 2, column=0, columnspan=4, pady=10)

    def change_stat(self, stat: str, delta: int) -> None:
        current_value = self.stats[stat].get()
        if 1 <= current_value + delta <= 10:
            new_total = self.get_total_points() + delta
            if new_total <= self.total_points:
                self.stats[stat].set(current_value + delta)
                self.update_total_label()

    def get_total_points(self) -> int:
        return sum(var.get() for var in self.stats.values())

    def update_total_label(self) -> None:
        remaining_points = self.total_points - self.get_total_points()
        self.total_label.config(text=f"Remaining Points: {remaining_points}",
                                fg='red' if remaining_points < 0 else 'black')

    def reset_stats(self) -> None:
        for var in self.stats.values():
            var.set(5)
        self.update_total_label()

    def end(self) -> None:
        if self.total_points == self.get_total_points():
            self.destroy()
            with open("output/PlayerInfo.txt", "a") as log_file:
                print("S.P.E.C.I.A.L:", file=log_file)
                pprint.pprint({i: self.stats[i].get() for i in self.stats}, log_file, sort_dicts=False)

            global SPECIALDICT
            SPECIALDICT = {i: self.stats[i].get() for i in self.stats}

        else:
            messagebox.showinfo("Error - Allocate all skills", "You must allocate all points before ending.")


class SkillAllocator(tk.Tk):
    def __init__(self) -> None:
        super().__init__()

        self.title("Skill Allocator")
        self.geometry("225x700")

        self.stats = {
            "Barter": tk.IntVar(value=2 + (2 * SPECIALDICT["CHR"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Energy weapons": tk.IntVar(value=2 + (2 * SPECIALDICT["PER"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Explosives": tk.IntVar(value=2 + (2 * SPECIALDICT["PER"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Guns": tk.IntVar(value=2 + (2 * SPECIALDICT["AGL"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Lockpick": tk.IntVar(value=2 + (2 * SPECIALDICT["PER"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Medicine": tk.IntVar(value=2 + (2 * SPECIALDICT["INT"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Melee weapons": tk.IntVar(value=2 + (2 * SPECIALDICT["STR"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Repair": tk.IntVar(value=2 + (2 * SPECIALDICT["INT"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Science": tk.IntVar(value=2 + (2 * SPECIALDICT["INT"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Sneak": tk.IntVar(value=2 + (2 * SPECIALDICT["AGL"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Speech": tk.IntVar(value=2 + (2 * SPECIALDICT["CHR"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Survival": tk.IntVar(value=2 + (2 * SPECIALDICT["END"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
            "Unarmed": tk.IntVar(value=2 + (2 * SPECIALDICT["END"]) + math.ceil(SPECIALDICT["LCK"] / 2)),
        }

        self.backup = {key: tk.IntVar(value=var.get()) for key, var in self.stats.items()}
        self.tagged = set()
        self.labels = {}

        self.init_ui()

    def init_ui(self) -> None:
        row = 0
        for stat, var in self.stats.items():
            label = tk.Label(self, text=stat)
            label.grid(row=row, column=0, padx=10, pady=10)
            self.labels[stat] = label

            tk.Button(self, text="-", command=lambda s=stat: self.change_stat(s, -15)).grid(row=row, column=1, padx=5)
            tk.Entry(self, textvariable=var, state='readonly', width=5).grid(row=row, column=2, padx=5)
            tk.Button(self, text="+", command=lambda s=stat: self.change_stat(s, 15)).grid(row=row, column=3, padx=5)

            row += 1

        self.total_label = tk.Label(self, text="Remaining Tags: 3")
        self.total_label.grid(row=row, column=0, columnspan=4, pady=10)

        self.reset_button = tk.Button(self, text="Reset", command=self.reset_stats)
        self.reset_button.grid(row=row + 1, column=0, columnspan=4, pady=10)

        self.quit_button = tk.Button(self, text="Finish", command=self.end)
        self.quit_button.grid(row=row + 2, column=0, columnspan=4, pady=10)

    def change_stat(self, stat: str, delta: int) -> None:
        if delta > 0 and len(self.tagged) < 3 and stat not in self.tagged:
            self.stats[stat].set(self.stats[stat].get() + delta)
            self.tagged.add(stat)
            self.labels[stat].config(fg="green")

        elif delta < 0 and stat in self.tagged:
            self.stats[stat].set(self.stats[stat].get() + delta)
            self.tagged.remove(stat)
            self.labels[stat].config(fg="black")

        self.update_total_label()

    def update_total_label(self) -> None:
        remaining_tags = 3 - len(self.tagged)
        self.total_label.config(text=f"Remaining Tags: {remaining_tags}")

    def reset_stats(self) -> None:
        for key, var in self.stats.items():
            var.set(self.backup[key].get())
            self.labels[key].config(fg="black")

        self.tagged = set()
        self.update_total_label()

    def end(self) -> None:
        if len(self.tagged) == 3:
            self.destroy()
            global SKILLS
            SKILLS = self.stats

            with open("output/PlayerInfo.txt", "a") as log_file:
                print("Tagged Skills:", file=log_file)
                pprint.pprint(self.tagged, log_file, sort_dicts=False)

                print("\nSkill Points:", file=log_file)
                for key in self.stats:
                    print(f'{key}: {self.stats[key].get()}', file=log_file)
                print("", file=log_file)

                tk.messagebox.showinfo("Preferences Saved", "Your preferences have been saved successfully!")
        else:
            messagebox.showinfo("Error - Allocate all tags", "You must tag exactly 3 skills before ending.")


class CharacterAllocator(tk.Tk):
    sex: Optional[str]
    name_var: tk.StringVar
    trait1: tk.StringVar
    trait2: tk.StringVar
    entry: tk.Entry
    choose_male_button: tk.Button
    choose_female_button: tk.Button
    clicked1: tk.StringVar
    clicked2: tk.StringVar
    choose_trait1_button: tk.OptionMenu
    choose_trait2_button: tk.OptionMenu
    quit_button: tk.Button
    traits: list[str]

    def __init__(self) -> None:
        super().__init__()

        self.title("Character Allocator")
        self.geometry("300x300")

        self.sex = None
        self.name_var = tk.StringVar()

        self.trait1 = tk.StringVar()
        self.trait2 = tk.StringVar()

        self.trait1.set("No Trait")
        self.trait2.set("No Trait")

        self.init_ui()

    def init_ui(self) -> None:
        # Name selection
        tk.Label(self, text="Enter your character's name:").pack(pady=10)
        self.entry = tk.Entry(self, textvariable=self.name_var, width=25)
        self.entry.pack(pady=5)

        # Sex selection
        tk.Label(self, text="Choose your sex:").pack(pady=10)
        button_frame = tk.Frame(self)
        button_frame.pack()
        self.choose_male_button = tk.Button(button_frame, text="Male", command=lambda: self.set_sex("Male"))
        self.choose_male_button.pack(side=tk.LEFT, padx=10)
        self.choose_female_button = tk.Button(button_frame, text="Female", command=lambda: self.set_sex("Female"))
        self.choose_female_button.pack(side=tk.LEFT, padx=10)

        # Trait selection
        tk.Label(self, text="Choose up to two traits:").pack(pady=10)
        trait_frame = tk.Frame(self)
        trait_frame.pack()

        hm = [x["Name"] for x in TRAITS["Traits - vanilla"]]

        hm += [f"[Old World Blues] {x["Name"]}" for x in TRAITS["Traits - old world blues"]]

        self.clicked1 = tk.StringVar()
        self.clicked1.set("No Trait")
        self.clicked2 = tk.StringVar()
        self.clicked2.set("No Trait")

        self.choose_trait1_button = tk.OptionMenu(trait_frame, self.clicked1, *hm, command=self.update_traits)
        self.choose_trait1_button.pack(side=tk.LEFT, padx=10)

        self.choose_trait2_button = tk.OptionMenu(trait_frame, self.clicked2, *hm, command=self.update_traits)
        self.choose_trait2_button.pack(side=tk.LEFT, padx=10)

        # Finish button
        self.quit_button = tk.Button(self, text="Finish", command=self.end)
        self.quit_button.pack(pady=20)

    def set_sex(self, sex: str) -> None:
        if sex == "Male":
            self.choose_male_button.config(fg="Green")
            self.choose_female_button.config(fg="Black")
        else:
            self.choose_female_button.config(fg="Green")
            self.choose_male_button.config(fg="Black")
        self.sex = sex

    def update_traits(self, selected_trait: tk.StringVar) -> None:
        selected_trait1 = self.clicked1.get()
        selected_trait2 = self.clicked2.get()

        if selected_trait1 == selected_trait2 and selected_trait != "No Trait":
            messagebox.showinfo("Error", "You cannot select the same trait twice.")
            self.clicked1.set("No Trait")
            self.clicked2.set("No Trait")

    def end(self) -> None:
        name = self.name_var.get().strip()
        trait1 = self.clicked1.get()
        trait2 = self.clicked2.get()

        global CHOSEN_TRAITS
        CHOSEN_TRAITS = [trait1, trait2]

        if self.sex and name:
            self.destroy()
            with open("output/playerinfo.txt", "w") as log_file:
                print(f"Name: {name}", file=log_file)
                print(f"Sex: {self.sex}", file=log_file)
                print(f"Trait 1: {trait1}", file=log_file)
                print(f"Trait 2: {trait2}\n", file=log_file)
        else:
            messagebox.showinfo("Error - Incomplete Information",
                                "You must choose your sex, enter a name, and select traits before ending.")


class DisplayTraits(tk.Toplevel):
    traits: list[str]

    def __init__(self, parent: CharacterAllocator) -> None:
        super().__init__(parent)

        self.title("Trait Information")

        w = 800  # width for the Tk root
        h = 650  # height for the Tk root

        # get screen width and height
        ws = self.winfo_screenwidth()  # width of the screen
        hs = self.winfo_screenheight()  # height of the screen

        # calculate x and y coordinates for the Tk root window
        x = (ws / 2) - (w / 2)
        y = (hs / 2) - (h / 2)

        # set the dimensions of the screen
        # and where it is placed
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))

        global TRAITS

        self.traits = [f"{string['Name']}:\n\t- {string['Benefit']}\n\t- However, {string['Penalty']}" for string in
                       TRAITS["Traits - vanilla"]]

        self.traits += [f"[Old World Blues] {trait['Name']}:\n\t- {trait['Benefit']}\n\t- However, {trait['Penalty']}"
                        for trait in TRAITS["Traits - old world blues"]]

        self.init_ui()

    def init_ui(self) -> None:
        t = tk.Text(self)

        t.configure(font=("Times New Roman", 12), wrap="word")

        for trait in self.traits:
            t.insert(tk.END, trait + "\n\n")

        t.pack(expand=True, fill=tk.BOTH)  # Make the text box fill the entire window


class PreferenceAllocator(tk.Tk):
    options_range: list[str]
    options_stealth: list[str]
    selected_range: list[str]
    selected_stealth: list[str]

    def __init__(self) -> None:
        super().__init__()

        self.title("Preference Allocator")
        self.geometry("300x400")

        self.options_range = ["Close Range", "Mid Range", "Long Range", "Traps"]
        self.options_stealth = ["Stealth", "Loud"]

        self.selected_range = []
        self.selected_stealth = []

        self.init_ui()

    def init_ui(self) -> None:
        tk.Label(self, text="Select your preferred ranges:").grid(row=0, column=0, padx=10, pady=10)

        for i, option in enumerate(self.options_range):
            chk = tk.Checkbutton(self, text=option, command=lambda o=option: self.toggle_option(o, 'range'))
            chk.grid(row=i + 1, column=0, sticky='w', padx=10, pady=5)

        tk.Label(self, text="Select your preferred combat methods:").grid(row=len(self.options_range) + 1, column=0,
                                                                          padx=10, pady=10)

        for i, option in enumerate(self.options_stealth):
            chk = tk.Checkbutton(self, text=option, command=lambda o=option: self.toggle_option(o, 'stealth'))
            chk.grid(row=len(self.options_range) + 2 + i, column=0, sticky='w', padx=10, pady=5)

        self.submit_button = tk.Button(self, text="Submit", command=self.submit_preferences)
        self.submit_button.grid(row=len(self.options_range) + len(self.options_stealth) + 3, column=0, pady=20)

    def toggle_option(self, option: str, category: str) -> None:
        if category == 'range':
            if option in self.selected_range:
                self.selected_range.remove(option)
            else:
                self.selected_range.append(option)
        elif category == 'stealth':
            if option in self.selected_stealth:
                self.selected_stealth.remove(option)
            else:
                self.selected_stealth.append(option)

    def submit_preferences(self) -> None:
        if self.selected_stealth and self.selected_range:
            global PLAYSTYLE_PREFERENCES
            PLAYSTYLE_PREFERENCES = self.selected_range + ["Yes" if "Stealth" in self.selected_stealth else "N/A",
                                                           "No" if "Loud" in self.selected_stealth else "N/A"]
            print(PLAYSTYLE_PREFERENCES)

            self.destroy()
        else:
            tk.messagebox.showinfo("Error", "You must check at least one item from each category.")


def main() -> None:
    # Load weapons data
    EQUIPMENT["weapons"] = get_rest("data/weapons")

    # List of other equipment categories to load
    files = ["perks", "traits", "companions", "armour"]

    # Load data for each category
    for item in files:
        EQUIPMENT[item] = get_rest(f"data/{item}")

    # Initialize the first weapon by skill type
    first = {item.split(" -")[0].capitalize(): "NULL" for item in EQUIPMENT["weapons"]}

    # Reference list for range categories
    # range_ref = ["Close range", "Mid range", "Long range", "Placed"]

    # Initialize the graph
    tree = Graph()

    # Process each weapon
    for key in EQUIPMENT["weapons"]:

        for i in EQUIPMENT["weapons"][key]:

            skill = key.split(" -")[0].capitalize()
            # fire_mode = i["Tags"].strip().split(",")
            #
            # # Check which range categories are present
            # test = [k in fire_mode for k in range_ref]

            # Create a list of applicable ranges
            # curr = [range_ref[index] for index in range(len(test)) if test[index]]

            # Add vertex to the graph
            tree.add_vertex(item=i["Name"], kind=key, skill=skill, ranges=[])
            tree.vertices[i["Name"]].effective_ranges = i["Range"].split("/comma")

            # Establish the first weapon of each skill type
            if first[skill] == "NULL":
                first[skill] = i["Name"]

            # Add edge between the current weapon and the first weapon of its skill type
            tree.add_edge(i["Name"], first[skill])

    # Visualize the constructed graph
    visualize_graph(tree)

    preferences = PreferenceAllocator()
    preferences.mainloop()

    character_allocator = CharacterAllocator()
    DisplayTraits(character_allocator)

    character_allocator.mainloop()

    app3 = SpecialAllocator()
    app3.mainloop()

    app4 = SkillAllocator()
    app4.mainloop()


def get_details(name: str, item_type: str, key: str) -> dict[str, str]:
    """Fetch and return the details of a specific weapon."""
    for item in EQUIPMENT[key][item_type]:
        if item["Name"] == name:
            return item

    return {"Error": "Weapon not found"}


def get_wep_score(name: str, wep_type: str) -> float:
    sum_so_far = 0.0
    weapon = get_details(name, wep_type, "weapons")

    skill_factor = SKILLS[wep_type.split(" -")[0]].get() / 100

    for index in range(len(NORMALIZATION_DATA_WEPS)):
        curr = NORMALIZATION_DATA_WEPS[index]
        if curr[0] in weapon and "AOE" not in weapon:

            sum_so_far += WEIGHT_WEPS[index] * skill_factor * (float(weapon[curr[0]]) - curr[1]) / (curr[2] - curr[1])

        elif curr[0] in weapon and "AOE" in weapon:

            sum_so_far += (0.3 * WEIGHT_WEPS[index] * skill_factor * (float(weapon[curr[0]]) - curr[1]) /
                           (curr[2] - curr[1]))

    global CHOSEN_TRAITS
    action_points = 65 + 3 * SPECIALDICT["AGL"]
    crit_chance = (SPECIALDICT["LCK"] + 3 * ("Built to Destroy" in CHOSEN_TRAITS)) / 100

    if "Melee" in wep_type:
        str_factor = SPECIALDICT["STR"]
    else:
        str_factor = SPECIALDICT["PER"]

    if weapon["Range"] not in PLAYSTYLE_PREFERENCES:
        if "Weapon spread" in weapon:
            sum_so_far -= int(weapon["Weapon spread"]) + 0.5
        else:
            sum_so_far /= 2

    if weapon["Silent"] in PLAYSTYLE_PREFERENCES:
        sum_so_far += 1

    else:
        sum_so_far /= 3

    sum_so_far += ((str_factor * skill_factor) + (0.01 * (action_points / int(weapon["Action point cost"]))
                                                  * float(weapon["Damage per Action Point"])))

    if "Critical hit Damage" in weapon:
        sum_so_far += 0.05 * crit_chance * float(weapon["Critical chance multiplier"]) * int(
            weapon["Critical hit Damage"]) * (skill_factor / 10)

    if "Weapon Spread" in weapon:
        sum_so_far -= 0.05 * float(weapon["Weapon Spread"]) / skill_factor

    return round(sum_so_far, 2)


def get_cloth_score(name: str, cloth_type: str) -> float:
    sum_so_far = 0.0
    armour = get_details(name, cloth_type, "armour")

    for index in range(2):
        sum_so_far += WEIGHT_CLOTH[index] * (
                float(armour[NORMALIZATION_DATA_CLOTH[index][0]]) - NORMALIZATION_DATA_CLOTH[index][1]) / (
                              NORMALIZATION_DATA_CLOTH[index][2] - NORMALIZATION_DATA_CLOTH[index][1])

    if (150 + int(SPECIALDICT["STR"]) * 10) / 8 <= float(armour["Weight"]):
        sum_so_far += WEIGHT_CLOTH[2] * (
                float(armour[NORMALIZATION_DATA_CLOTH[2][0]]) - NORMALIZATION_DATA_CLOTH[2][1]) / (
                              NORMALIZATION_DATA_CLOTH[2][2] - NORMALIZATION_DATA_CLOTH[2][1])

    if "Yes" in PLAYSTYLE_PREFERENCES and "stealth" in name.lower():
        sum_so_far += 3

    return round(sum_so_far, 2)


if __name__ == "__main__":
    # requirement for "code quality"
    "code-checking tools"
    import doctest

    doctest.testmod(verbose=True)

    # import python_ta.contracts
    # python_ta.contracts.check_all_contracts()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': ["csv", "networkx", "typing", "io", "time", "visualization1", "visualization2", "classes"],
        'allowed-io': ["get_favourite_movie", "get_favourite_genres", "load_weighted_review_graph",
                       "print_recommended_movies", "display_recommendations"],
        'max-line-length': 120
    })

    get_rest("data/weapons")
    get_rest("data/armour")

    main()

    weps = {}
    types = ["Unarmed", "Melee weapons", "Guns", "Energy weapons", "Explosives"]
    max_skill = max([SKILLS[x].get() for x in types])

    types = [x for x in types if abs(SKILLS[x].get() - max_skill) <= 10]

    cloths = {}

    for t in EQUIPMENT["armour"]:
        for item in EQUIPMENT["armour"][t]:
            cloths[item["Name"]] = get_cloth_score(item["Name"], t)

    result = dict(sorted(cloths.items(), key=lambda item: item[1]))

    with open("output/PlayerInfo.txt", "a") as log_file:
        print("\nWeapons:\n", file=log_file)
        pprint.pprint(result, stream=log_file, sort_dicts=False)
        print("", file=log_file)
        print("---------------", file=log_file)

    for t in EQUIPMENT["weapons"]:
        if t.split(" -")[0].capitalize() in types:
            for item in EQUIPMENT["weapons"][t]:
                weps[item["Name"]] = get_wep_score(item["Name"], t)

    result = dict(sorted(weps.items(), key=lambda item: item[1]))

    with open("output/PlayerInfo.txt", "a") as log_file:
        print("\nArmour:\n", file=log_file)
        pprint.pprint(result, stream=log_file, sort_dicts=False)
        print("", file=log_file)
        print("---------------", file=log_file)
