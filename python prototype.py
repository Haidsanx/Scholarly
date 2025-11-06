users = {}
current_user = None
current_session = None
current_page = "main_menu"
username = ""
confirm_password = ""
self = None

CONTINUE_PROMPT = "Press Enter to continue"

class User:
    def __init__(self, username, password, goal =10):
        self.username = username
        self.password = password
        self.study_logs = []
        self.goal = goal

    def add_study_session(self, subject, duration, notes=""):
        session = {
            "subject": subject,
            "duration": duration,
            "notes": notes
        }
        self.study_logs.append(session)
        print(f"Study session added for {subject}.")
        print(f"Total study sessions for {self.username}: {len(self.study_logs)}")
        print(f"Study session details: {session}")
        
        progress = len(self.study_logs)
        goal = max(10, progress)  
        percent = round((progress / goal) * 100, 1)
        bar_length = 20
        filled = int(bar_length * percent / 100)
        bar = "#" * filled + "-" * (bar_length - filled)
        print(f"Progress: |{bar}| {percent}% ({progress}/{goal} sessions)")


print("Study Tracker App - Core Python Prototype")
input(CONTINUE_PROMPT + "...")
running = True
input(CONTINUE_PROMPT)
running = True
while running:
    print("Welcome to the Main Menu!")
    input(CONTINUE_PROMPT)
    print("Select an option:")
    print("1. User Registration")
    print("2. User Login")
    print("3. Add Study Session")
    print("4. View Study Summary")
    print("5. Logout")
    print("6. Exit")
    choice = input("Enter your choice: ")
    if choice in ['1', '2', '3', '4', '5']:
        print(f"You selected option {int(choice)}.")


    if choice == '1':
        print("Please enter your desired username and password to register.")
        username = input("Username: ").strip()
        password = input("Password: ")
        confirm_password = input("Confirm Password: ")
        if not username or not password:
            print("Username and password cannot be empty.")
            input("Press Enter to try again")
        elif password != confirm_password:
            if username in users:
                print("Username already exists. Please try a different one.")
            input(CONTINUE_PROMPT)
        else:
            users[username] = User(username, password)
            print(f"User {username} registered successfully!")
            input("Press Enter to continue to login")
            print("\nPlease enter your username and password to login.")
            input("Press Enter to continue to login")
            print("\nPlease enter your username and password to login.")
            login_username = input("Username: ")
            login_password = input("Password: ")
            if login_username == username and login_password == password:
                current_user = users[username]
                print(f"User {login_username} logged in successfully!")
            else:
                print("Invalid username or password.")
        if not users:
            print("No users are registered yet. Please register first.")
            input(CONTINUE_PROMPT)
            continue

        attempts = 0
        max_attempts = 3

        while attempts < max_attempts:
            username = input("Enter Username: ").strip()
            password = input("Enter Password: ").strip()

            if not username or not password:
                print("Username and password cannot be empty.")
                attempts += 1
                print(f"{max_attempts - attempts} attempts left.\n")
                continue

            if username in users and users[username].password == password:
                current_user = users[username]
                print(f"User {username} logged in successfully!")
                input("Press Enter to continue to the dashboard")
                break  
            else:
                print("Invalid username or password.")
            print("Maximum login attempts reached. Returning to main menu.")
            input(CONTINUE_PROMPT)
            print("Maximum login attempts reached. Returning to main menu.")
            input(CONTINUE_PROMPT)

        if current_user is None:
            print("You must be logged in to add a study session.")
            input(CONTINUE_PROMPT)
        print("Add a new study session.")
        input("Press Enter to continue")
        print("Add a new study session.")
        subject = input("Subject: ")
        duration = int(input("Duration (in minutes): "))
        notes = input("Notes (optional): ")
    else:
        print("Please login first to add a study session.")
        input(CONTINUE_PROMPT)
    
    if choice == '4':
        if current_user is None:
            print("You must be logged in to view study summary.")
            input(CONTINUE_PROMPT)
            continue
        print("Study Summary:")
        total_sessions = len(current_user.study_logs)
        total_time = sum(session["duration"] for session in current_user.study_logs)
        print(f"Total Study Sessions: {total_sessions}")
        print(f"Total Time Studied: {total_time} minutes")
        input("Press Enter to view sessions...")
        if current_user.study_logs:
            print("\nYour Study Sessions:")  
            for i, session in enumerate(current_user.study_logs, 1):
                print(f"Session {i}: Subject: {session['subject']}, Duration: {session['duration']} minutes, Notes: {session['notes']}")
        else:
            print("No study sessions logged yet.")
            input(CONTINUE_PROMPT)
        

    elif choice == '5':
        if current_user:
            print(f"User {current_user.username} has been logged out successfully.")
            current_user = None
            input(CONTINUE_PROMPT)
        else:
            print("No user is currently logged in.")
            input(CONTINUE_PROMPT)

if choice == '6':
     print("Exiting the Study Tracker App. Goodbye!")