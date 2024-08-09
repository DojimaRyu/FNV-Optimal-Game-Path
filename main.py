from __future__ import annotations

import math
import os
import pprint
import tkinter as tk
from tkinter import messagebox
from typing import Any, Optional, TextIO

from classes import Graph
from vis import visualize_graph

TRAITS = {}

EQUIPMENT = {}


def get_rest(directory: str) -> dict[Any, list]:
    """
    Reads the weapon information from the files in the provided directory and stores them in a dictionary.

    Preconditions:
        - directory contains only valid .csv files
    """
    files = os.listdir(directory)
    database = {key[:-4].capitalize(): [] for key in files}

    for file in files:
        file_name = file[:-4].lower()
        for category in database:
            if category.lower() in file_name:
                database[category].append(file)

    for category, files in database.items():
        items = []
        for file in files:
            with open(os.path.join(directory, file), 'r', encoding="ISO-8859-1") as f:
                items.extend(parse_rest(f))
        database[category] = items

    if "traits" in directory.lower():
        global TRAITS
        TRAITS = database
        TRAITS["Traits - vanilla"].insert(0, {'Name': 'No Trait',
                                              'Benefit': "No downsides...",
                                              'Penalty': "you are officially boring."}
                                          )

    with open("output/equipmentInfo.txt", "a") as log_file:
        for category, items in database.items():
            print(category, file=log_file)
            for item in items:
                pprint.pprint(item, stream=log_file, sort_dicts=False)
                print("", file=log_file)
            print("---------------", file=log_file)

    return database


def parse_rest(file: TextIO) -> list[dict[str, str]]:
    attributes = file.readline().split(",")
    res = []

    for row in file:

        hm = row.split(",")

        for index in range(len(hm)):
            hm[index] = hm[index].replace(u'\xa0', u' ')
            hm[index] = hm[index].replace('*', '')
            hm[index] = hm[index].replace('/comma', ',')

        res.append({attributes[i].strip(): hm[i].strip() for i in range(len(attributes))})

    return res


SPECIALDICT = {}


class SpecialAllocator(tk.Tk):
    stats: dict[str, tk.IntVar]
    total_points: int
    total_label: tk.Label
    reset_button: tk.Button
    quit_button: tk.Button

    def __init__(self) -> None:
        super().__init__()

        self.title("SPECIAL Allocator")
        self.geometry("200x450")

        self.stats = {stat: tk.IntVar(value=5) for stat in
                      ["Strength", "Perception", "Endurance", "Charisma", "Intelligence", "Agility", "Luck"]}

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
    stats: dict[str, tk.IntVar]
    backup: dict[str, tk.IntVar]
    tagged: set[Optional[str]]
    labels: dict[str, tk.Label]

    total_label: tk.Label
    reset_button: tk.Button
    quit_button: tk.Button

    def __init__(self) -> None:
        super().__init__()

        self.title("Skill Allocator")
        self.geometry("225x700")

        self.stats = {
            "Barter": tk.IntVar(value=2 + (2 * SPECIALDICT["Charisma"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Energy Weapons": tk.IntVar(value=2 + (2 * SPECIALDICT["Perception"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Explosives": tk.IntVar(value=2 + (2 * SPECIALDICT["Perception"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Guns": tk.IntVar(value=2 + (2 * SPECIALDICT["Agility"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Lockpick": tk.IntVar(value=2 + (2 * SPECIALDICT["Perception"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Medicine": tk.IntVar(value=2 + (2 * SPECIALDICT["Intelligence"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Melee Weapons": tk.IntVar(value=2 + (2 * SPECIALDICT["Strength"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Repair": tk.IntVar(value=2 + (2 * SPECIALDICT["Intelligence"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Science": tk.IntVar(value=2 + (2 * SPECIALDICT["Intelligence"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Sneak": tk.IntVar(value=2 + (2 * SPECIALDICT["Agility"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Speech": tk.IntVar(value=2 + (2 * SPECIALDICT["Charisma"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Survival": tk.IntVar(value=2 + (2 * SPECIALDICT["Endurance"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
            "Unarmed": tk.IntVar(value=2 + (2 * SPECIALDICT["Endurance"]) + math.ceil(SPECIALDICT["Luck"] / 2)),
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
            self.tagged.add(stat)
            self.stats[stat].set(self.stats[stat].get() + delta)
            self.labels[stat].config(fg="green")

        elif delta < 0 and stat in self.tagged:
            self.tagged.remove(stat)
            self.stats[stat].set(self.stats[stat].get() + delta)
            self.labels[stat].config(fg="black")

        self.update_total_label()

    def update_total_label(self) -> None:
        remaining_tags = 3 - len(self.tagged)
        self.total_label.config(text=f"Remaining Tags: {remaining_tags}", fg='red' if remaining_tags < 0 else 'black')

    def reset_stats(self) -> None:
        for key, var in self.backup.items():
            self.stats[key].set(var.get())

        for stat in self.labels:
            self.labels[stat].config(fg="black")

        self.tagged.clear()
        self.update_total_label()

    def end(self) -> None:
        if len(self.tagged) == 3:
            self.destroy()
            with open("output/playerinfo.txt", "a") as log_file:
                print("\nSkills:", file=log_file)
                pprint.pprint({i: self.stats[i].get() for i in self.stats}, log_file, sort_dicts=False)
        else:
            messagebox.showinfo("Error - Allocate all tags", "You must allocate all tags before ending.")


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

    def update_traits(self) -> None:
        selected_trait1 = self.clicked1.get()
        selected_trait2 = self.clicked2.get()

        if selected_trait1 == selected_trait2 and selected_trait1 != "No Trait":
            messagebox.showinfo("Error", "You cannot select the same trait twice.")
            self.clicked1.set("No Trait")
            self.clicked2.set("No Trait")

    def end(self) -> None:
        name = self.name_var.get().strip()
        trait1 = self.clicked1.get()
        trait2 = self.clicked2.get()
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

    def __init__(self, parent) -> None:
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


# Run the application
def main() -> None:
    EQUIPMENT["weapons"] = get_rest("data/weapons")

    files = ["perks", "traits", "companions", "armour"]
    tree = Graph()

    for item in files:
        EQUIPMENT[item] = get_rest(f"data/{item}")

    first = {type.split(" -")[0].capitalize(): "NULL" for type in EQUIPMENT["weapons"]}

    range_ref = ["Close range", "Mid range", "Long range", "Placed"]

    for key in EQUIPMENT["weapons"]:
        for i in EQUIPMENT["weapons"][key]:
            skill = key.split(" -")[0].capitalize()
            fire_mode = i["Tags"].strip(" ").split(",")

            test = [k in fire_mode for k in range_ref]

            curr = []

            for index in range(len(test)):
                if test[index]:
                    curr += [range_ref[index]]

            tree.add_vertex(item=i["Name"], kind=key, skill=key.split(" -")[0].capitalize(), ranges=curr)

            if first[skill] == "NULL":
                first[skill] = i["Name"]

            tree.add_edge(i["Name"], first[skill])

    # visualize_graph(tree)

    # character_allocator = CharacterAllocator()
    # DisplayTraits(character_allocator)
    #
    # character_allocator.mainloop()
    #
    # app3 = SpecialAllocator()
    # app3.mainloop()
    #
    # app4 = SkillAllocator()
    # app4.mainloop()


if __name__ == "__main__":
    # requirement for "code quality"
    # "code-checking tools"
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

    main()
