import requests
import time 
from datetime import datetime


def get_all_vacancies(params):
    # List to store all retrieved vacancies
    all_vacancies = []

    page = 0
    while True:
        # Set the current page number in the request parameters
        params['page'] = page
        
        # Send a GET request to the hh.ru API to retrieve job vacancies
        response = requests.get('https://api.hh.ru/vacancies', params=params)
        
        # Convert the response to JSON format
        data = response.json()
        
        # Extract the list of vacancies from the response
        items = data.get('items', [])

        # If there are no vacancies, break the loop
        if not items:
            break

        # Add the current page's vacancies to the total list
        all_vacancies.extend(items)

        # Stop if the last page has been reached
        if page >= data.get('pages', 1) - 1:
            break

        # Go to the next page
        page += 1

    # Sort all collected vacancies by publication date (most recent first)
    all_sorted_vacancies = sorted(
        all_vacancies, 
        key=lambda v: datetime.strptime(v['published_at'], "%Y-%m-%dT%H:%M:%S+%f"), 
        reverse=True
    )

    # Return the sorted list of vacancies
    return all_sorted_vacancies


# Function to search for job vacancies based on specified parameters
def search_vacancies(text, keyword, period, experience, availability_salary, collect_stats):
    # Parameters for the request to the hh.ru API
    params = {
        'area': 53,  # Region (Krasnodar)
        'per_page': 100,  # Number of vacancies per page
        # "vacancy_search_order": "publication_time",  # Vacancy search order by date
        'text': text,  # Search query
        'period': period,  # Period (in days) to search for vacancies
        'experience': experience,  # Required work experience
        'only_with_salary': availability_salary  # Whether to search only for vacancies with salary specified
    }

    try:
        all_sorted_vacancies = get_all_vacancies(params)

        # Filtering vacancies by keyword in the job title
        filtered_vacancies = [vacancy for vacancy in all_sorted_vacancies if keyword in vacancy['name'].lower()]

        # Statistics lists
        salary_from_list = []
        salary_to_list = []

        # Opening the file to write the results
        with open("jobs.txt", "w", encoding="UTF-8") as f:
            # Writing the total number of vacancies found
            f.write(f"Total {len(filtered_vacancies)} vacancies found for query {text} in the last {period} days\n\n")

            # Loop through each vacancy and write its information to the file
            for index, vacancy in enumerate(filtered_vacancies):
                # Writing the vacancy name
                f.write(f"{index + 1}) Vacancy: {vacancy['name']}\n")
                # Writing the employer's name
                f.write(f"Name company: {vacancy['employer']['name']}\n")
                
                # Getting salary information
                salary = vacancy.get('salary')
                
                # Checking if salary is provided and writing the corresponding information
                if salary:
                    f.write(f"Salary from {salary['from']} to {salary['to']} {salary['currency']}\n")
                    if collect_stats:  # Checking if salary statistics should be collected
                        if salary['from'] is not None:
                            salary_from_list.append(salary['from'])  # Add the 'from' salary to the list
                        if salary['to'] is not None:
                            salary_to_list.append(salary['to'])  # Add the 'to' salary to the list
                else:
                    f.write("Salary not specified\n")
                
                # Writing a link to more details about the vacancy
                f.write(f"More info: {vacancy['alternate_url']}\n")

                # Calculate the number of days since the publication
                published_date = datetime.strptime(vacancy['published_at'], "%Y-%m-%dT%H:%M:%S+%f")
                days_passed = (datetime.now() - published_date).days
                f.write(f"Published {days_passed} day(s) ago\n\n")
            
            # If collect_stats is True, calculate and write salary statistics
            if collect_stats:
                all_salaries = []
                
                # Calculating average salary based on 'from' and 'to' values
                for a, b in zip(salary_from_list, salary_to_list):
                    if a is not None and b is not None:
                        all_salaries.append((a + b) // 2)  # Add the average of 'from' and 'to' to the list
                    elif a is not None:
                        all_salaries.append(a)  # If only 'from' is provided, add it
                    elif b is not None:
                        all_salaries.append(b)  # If only 'to' is provided, add it

                # Calculate and write the average salary offer
                if all_salaries:
                    avg_salary = sum(all_salaries) // len(all_salaries)  # Calculate the average of all salaries
                    f.write(f"Average salary offer: {avg_salary}\n")

                # Calculate and write the average salary 'FROM'
                if salary_from_list:
                    avg_from = sum(salary_from_list) // len(salary_from_list)  # Calculate the average 'from' salary
                    f.write(f"Average salary FROM: {avg_from}\n")
                else:
                    f.write("Average salary FROM: not enough data\n")  # If there's no data, print this message

                # Calculate and write the average salary 'TO'
                if salary_to_list:
                    avg_to = sum(salary_to_list) // len(salary_to_list)  # Calculate the average 'to' salary
                    f.write(f"Average salary TO: {avg_to}\n")
                else:
                    f.write("Average salary TO: not enough data\n")  # If there's no data, print this message

            print("The file has been saved")
    except requests.exceptions.RequestException as e:
        # This block will catch errors related to the HTTP request (network issues, bad responses, etc.)
        print(f"Error while making the request: {e}")
    except Exception as e:
        # This block will catch any other unexpected errors
        print(f"An unexpected error occurred: {e}")


# Main block to execute the program
if __name__ == "__main__":
    # Asking the user for input data to search for jobs
    print("Enter your search query: ")
    text = input(">> ").strip()  # Search query input
    print("Enter a keyword in the search (optional): ")
    keyword = input(">> ").strip()  # Keyword input for filtering vacancies
    print("Enter the number of days within which the job search is performed (default is 7): ")
    period = input(">> ").strip()
    int_period = int(period) if period.isdigit() else 7  # Number of days for search (default is 7)
    print('''Enter your work experience (default is noExperience): 
          noExperience - no experience,
          between1And3 - from 1 year to 3 years,
          between3And6 - from 3 to 6 years,
          moreThan6 - more than 6 years''')
    experience = input(">> ").strip() or "noExperience"  # Required work experience input (default is noExperience)
    print("Only with the stated salary? YES/NO")
    availability_salary = True if input(">> ").lower() == "yes" else False  # Whether to search for vacancies with salary specified
    print("Collect salary statistics? YES/NO")
    collect_stats = True if input(">> ").lower() == "yes" else False  # Whether to collect salary statistics

    # Loop that performs job search with a delay between searches
    while True:
        search_vacancies(text, keyword, int_period, experience, availability_salary, collect_stats)
        
        # Wait for _ minutes between searches
        time_wait = 10
        print(f"Please wait {time_wait} minutes...")
        time.sleep(time_wait * 60)  # Waiting before the next search
