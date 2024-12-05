"""
If the model is not good at outputting the TP-specific JSON schema, do the 2-step transformation explicitly.

Adapted from:
https://github.com/OSU-NLP-Group/TravelPlanner/blob/main/postprocess/openai_request.py
https://github.com/OSU-NLP-Group/TravelPlanner/blob/main/postprocess/parsing.py
"""
import json

from kani import Kani
from kani.engines.openai import OpenAIEngine

prefix = (
    "Please assist me in extracting valid information from a given natural language text and reconstructing it in JSON"
    " format, as demonstrated in the following example. If transportation details indicate a journey from one city to"
    " another (e.g., from A to B), the 'current_city' should be updated to the destination city (in this case, B)."
    " Use a ';' to separate different attractions, with each attraction formatted as 'Name, City'. If there's"
    " information about transportation, ensure that the 'current_city' aligns with the destination mentioned in the"
    " transportation details (i.e., the current city should follow the format 'from A to B'). Also, ensure that all"
    " flight numbers and costs are followed by a colon (i.e., 'Flight Number:' and 'Cost:'), consistent with the"
    " provided example. Each item should include ['day', 'current_city', 'transportation', 'breakfast',"
    " 'attraction', 'lunch', 'dinner', 'accommodation']. Replace non-specific information like 'eat at home/on"
    " the road' with '-'. Additionally, delete any '$' symbols.\n-----EXAMPLE-----\n [{\n        \"days\": 1,\n     "
    '   "current_city": "from Dallas to Peoria",\n        "transportation": "Flight Number: 4044830, from Dallas to'
    ' Peoria, Departure Time: 13:10, Arrival Time: 15:01",\n        "breakfast": "-",\n        "attraction": "Peoria'
    ' Historical Society, Peoria;Peoria Holocaust Memorial, Peoria;",\n        "lunch": "-",\n        "dinner":'
    ' "Tandoor Ka Zaika, Peoria",\n        "accommodation": "Bushwick Music Mansion, Peoria"\n    },\n    {\n       '
    ' "days": 2,\n        "current_city": "Peoria",\n        "transportation": "-",\n        "breakfast": "Tandoor Ka'
    ' Zaika, Peoria",\n        "attraction": "Peoria Riverfront Park, Peoria;The Peoria PlayHouse, Peoria;Glen Oak'
    ' Park, Peoria;",\n        "lunch": "Cafe Hashtag LoL, Peoria",\n        "dinner": "The Curzon Room - Maidens'
    ' Hotel, Peoria",\n        "accommodation": "Bushwick Music Mansion, Peoria"\n    },\n    {\n        "days": 3,\n  '
    '      "current_city": "from Peoria to Dallas",\n        "transportation": "Flight Number: 4045904, from Peoria to'
    ' Dallas, Departure Time: 07:09, Arrival Time: 09:20",\n        "breakfast": "-",\n        "attraction": "-",\n    '
    '    "lunch": "-",\n        "dinner": "-",\n        "accommodation": "-"\n    }]\n-----EXAMPLE END-----\n'
)


async def nl_to_tp_json(text):
    engine = OpenAIEngine(model="gpt-4", temperature=0)
    ai = Kani(engine)
    query = f"{prefix}\nText: {text}\nPlease output the corresponding JSON only."
    resp = await ai.chat_round_str(query)
    try:
        return json.loads(resp)
    except json.JSONDecodeError:
        json_text = resp[resp.find("["):resp.rfind("]") + 1]
        return json.loads(json_text)
