from datetime import timedelta, datetime

"""
This module defines enhanced vaccination handling for multiple vaccinations.
"""

class VaccinationService:
    @staticmethod
    def calculate_due_date(last_vacc_date: datetime, months_until_due: int = 6) -> datetime:
        """
        Calculate vaccination due date based on the datetime provided.
        """
        return last_vacc_date + timedelta(days=months_until_due * 30)
    
    @staticmethod
    def process_vaccinations(animal_data: dict) -> dict:
        """
        Process animal vaccination data using the new multiple vaccination structure.
        Handles both old single vaccination field and new multiple vaccinations list.
        
        Args:
            animal_data (dict): Dictionary containing animal's data.
        Returns:
            animal_data (dict): Dictionary with updated vaccination data.
        """
        # Check if the new vaccinations list structure is being used
        vaccinations_list = animal_data.get("vaccinations", [])
        
        if vaccinations_list and len(vaccinations_list) > 0:
            # New structure: multiple vaccinations with name and next date
            upcoming_vaccinations = []
            for vacc in vaccinations_list:
                if isinstance(vacc, dict):
                    next_date = vacc.get("next_vaccination_date")
                    upcoming_vaccinations.append({
                        "vaccination_name": vacc.get("vaccination_name", ""),
                        "next_vaccination_date": next_date.isoformat() if next_date else ""
                    })
            
            animal_data["upcoming_vaccinations"] = upcoming_vaccinations
            animal_data["next_vaccination_due"] = upcoming_vaccinations[0]["next_vaccination_date"] if upcoming_vaccinations else None
        else:
            # Fallback to old structure for backward compatibility
            last_vacc = animal_data.get("own_animal_last_vacc")
            if last_vacc:
                try:
                    due_date = VaccinationService.calculate_due_date(last_vacc)
                    animal_data["vaccination_due_date"] = due_date.isoformat()
                    animal_data["next_vaccination_due"] = due_date.isoformat()
                except Exception as e:
                    animal_data["vaccination_due_date"] = None
                    animal_data["next_vaccination_due"] = None
            else:
                animal_data["vaccination_due_date"] = None
                animal_data["next_vaccination_due"] = None
        
        return animal_data
