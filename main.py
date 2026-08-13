from utils.output import create_output_folder

print("="*60)

print(" Universal Job Scraper ")

print("="*60)

print()

print("1. Dice")

print("2. Randstad")

print("3. Workday")

print("4. Greenhouse")

print("5. Lever")

print("6. ICIMS")

print("7. SmartRecruiters")

print("8. Oracle Cloud")

choice = input("\nSelect Portal: ")

url = input("\nPaste Career/Search URL:\n")

portal_map = {

    "1": ("Dice", "scrapers.dice"),

    "2": ("Randstad", "scrapers.randstad"),

    "3": ("Workday", "scrapers.workday"),

    "4": ("Greenhouse", "scrapers.greenhouse"),

    "5": ("Lever", "scrapers.lever"),

    "6": ("ICIMS", "scrapers.icims"),

    "7": ("SmartRecruiters", "scrapers.smartrecruiters"),

    "8": ("Oracle", "scrapers.oracle")

}

portal_name, module_name = portal_map[choice]

output_folder = create_output_folder(portal_name)

print()

print("Output Folder:")

print(output_folder)

print()

module = __import__(module_name, fromlist=["scrape"])

module.scrape(

    url,

    output_folder

)