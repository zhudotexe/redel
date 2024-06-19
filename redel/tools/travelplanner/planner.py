from typing import Annotated

from kani import AIParam, ai_function

from redel.base_kani import BaseKani


class TravelPlannerRootMixin(BaseKani):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_plan = []

    @ai_function()
    def submit_day_plan(
        self,
        day: int,
        current_city: Annotated[
            str,
            AIParam(
                'The city for this day. If the plan is to travel between two cities, indicate it as "from A to B" (e.g.'
                ' "from Ithaca to Charlotte").'
            ),
        ],
        transportation: Annotated[
            str,
            AIParam(
                'e.g. "Flight Number: F3633413, from Ithaca to Charlotte, Departure Time: 05:38, Arrival Time: 07:46"'
            ),
        ],
        breakfast: Annotated[
            str, AIParam('The name of a restaurant in the city, e.g. "Nagaland\'s Kitchen, Charlotte"')
        ],
        attraction: Annotated[
            str,
            AIParam(
                'Use a ";" to separate different attractions, with each attraction formatted as "Name, City". e.g. "The'
                ' Charlotte Museum of History, Charlotte;"'
            ),
        ],
        lunch: Annotated[str, AIParam('e.g. "Cafe Maple Street, Charlotte"')],
        dinner: Annotated[str, AIParam('e.g. "Bombay Vada Pav, Charlotte"')],
        accommodation: Annotated[str, AIParam('e.g. "Affordable Spacious Refurbished Room in Bushwick!, Charlotte"')],
    ):
        """
        Once you have collected information about the trip, call this function once for each day of the trip, starting on day 1.
        If a field does not apply for a given day, use "-" to indicate this.
        You MUST call this function to save the plan for each query.
        """
        self.current_plan.append({
            "day": day,
            "current_city": current_city,
            "transportation": transportation,
            "breakfast": breakfast,
            "attraction": attraction,
            "lunch": lunch,
            "dinner": dinner,
            "accommodation": accommodation,
        })
        return f"Saved plan for day {day}."
