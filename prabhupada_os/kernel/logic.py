from typing import List, Dict, Any

# Mock Data - In a real scenario, this would load from a file or database.
# Using Bhagavad Gita verses as the "Scripture" for this reference implementation.
SCRIPTURE_DATA = [
    {
        "source": "Bhagavad Gita 2.13",
        "text": "As the embodied soul continuously passes, in this body, from boyhood to youth to old age, the soul similarly passes into another body at death. A sober person is not bewildered by such a change.",
        "keywords": ["soul", "death", "reincarnation", "change", "body"]
    },
    {
        "source": "Bhagavad Gita 2.47",
        "text": "You have a right to perform your prescribed duty, but you are not entitled to the fruits of action. Never consider yourself the cause of the results of your activities, and never be attached to not doing your duty.",
        "keywords": ["duty", "action", "fruits", "karma", "results"]
    },
    {
        "source": "Bhagavad Gita 18.66",
        "text": "Abandon all varieties of religion and just surrender unto Me. I shall deliver you from all sinful reactions. Do not fear.",
        "keywords": ["surrender", "religion", "sin", "fear", "deliver"]
    }
]

def search(query: str) -> List[Dict[str, Any]]:
    """
    Performs a simple keyword search against the SCRIPTURE_DATA.
    Case-insensitive.
    """
    query_lower = query.lower()
    results = []
    
    for entry in SCRIPTURE_DATA:
        # Check if query is in text or keywords
        if query_lower in entry["text"].lower():
            results.append(entry)
            continue
        
        for keyword in entry["keywords"]:
            if query_lower == keyword.lower():
                results.append(entry)
                break
                
    return results
