"""Simple, standard health calculations used for the daily calorie target.

These are general population formulas for healthy adults. They are estimates, not
medical advice, and they do not replace a doctor or dietitian.
"""

ACTIVITY_LEVELS = {
    "Sedentary (little or no exercise)": 1.2,
    "Lightly active (exercise 1-3 days/week)": 1.375,
    "Moderately active (exercise 3-5 days/week)": 1.55,
    "Very active (exercise 6-7 days/week)": 1.725,
}

GOALS = {
    "Lose weight gently": -400,
    "Maintain weight": 0,
    "Gain weight gently": 300,
}

# Never suggest a daily target below these commonly used minimums.
MIN_CALORIES = {"Female": 1200, "Male": 1500}


def bmi(weight_kg, height_cm):
    height_m = height_cm / 100.0
    return weight_kg / (height_m * height_m)


def bmi_category(value):
    """WHO adult categories."""
    if value < 18.5:
        return "Underweight"
    if value < 25:
        return "Healthy range"
    if value < 30:
        return "Overweight"
    return "Obese range"


def bmr_mifflin_st_jeor(sex, age, height_cm, weight_kg):
    """Basal metabolic rate (kcal/day) with the Mifflin-St Jeor equation."""
    base = 10 * weight_kg + 6.25 * height_cm - 5 * age
    return base + (5 if sex == "Male" else -161)


def daily_target(profile):
    """Work out BMI, BMR, maintenance calories and a daily calorie target.

    `profile` needs: sex, age, height_cm, weight_kg, activity, goal.
    Returns a dict, or None if the profile is incomplete or invalid.
    """
    try:
        sex = profile["sex"]
        age = int(profile["age"])
        height = float(profile["height_cm"])
        weight = float(profile["weight_kg"])
        factor = ACTIVITY_LEVELS[profile["activity"]]
        adjust = GOALS[profile["goal"]]
    except (KeyError, TypeError, ValueError):
        return None
    if sex not in MIN_CALORIES or age < 10 or not (80 <= height <= 250) or not (20 <= weight <= 300):
        return None

    bmr = bmr_mifflin_st_jeor(sex, age, height, weight)
    maintenance = bmr * factor
    floor = MIN_CALORIES[sex]
    target = max(maintenance + adjust, floor)
    value = bmi(weight, height)
    return {
        "bmi": round(value, 1),
        "bmi_category": bmi_category(value),
        "bmr": round(bmr),
        "maintenance": round(maintenance),
        "target": round(target),
        "floor_applied": maintenance + adjust < floor,
        "adult": age >= 18,
    }
