from datetime import timedelta,datetime

"""
This module defines the VaccinationDues class, which handles vaccine-related operations.
"""
class VaccinationDues:
    @staticmethod
    def calculate_due_date(last_vacc_date:datetime,months_until_due:int=6)->datetime:
        """
        This function calculates the vaccination due datetime based on the the datetime
        provided and the time until the due.
        Args:
            last_vacc_date (datetime): The date of last vaccination.
            months_until_due (int): Due in time. Defaulted to 6 months.
        Returns:
            datetime: datetime data of the vacination due date.
        """
        return last_vacc_date+timedelta(days=months_until_due*30)
    @staticmethod
    def vaccinations(animal_data:dict)->dict:
        """
        Gets animal data dict, takes the last vaccination date and then calls the 
        calculate_due_date function, add the vaccination due date to the animal dict 
        and returns it.
        Args:
            animal_data (dict): Dictionary containing the animal's data.
        Returns:
            animal_data (dict): Dictoinary with the animal's updated data with the vaccination dues.
        """
        last_vacc=animal_data.get("own_animal_last_vacc")
        if last_vacc:
            try:
                due_date=VaccinationDues.calculate_due_date(last_vacc)
                animal_data["vaccination_due_date"]=due_date.isoformat()
            except Exception as e:
                animal_data["vaccination_due_date"]=None
        else:
            animal_data["vaccination_due_date"]=None
        return animal_data