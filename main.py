import os
import logging
import threading
import streamlit as st
from core.openai_api import *
from core.duckdb_connector import *
from core.main_app_miscellaneous import *


OPENAI_API_KEY = "OPENAI_API_KEY"
OPENAI_CLIENT = OpenAI(
  api_key=os.environ.get(OPENAI_API_KEY),
)
main_app_miscellaneous = MainAppMiscellaneous(openai_client=OPENAI_CLIENT)
logging.basicConfig(level=logging.INFO)
st.set_page_config(layout='wide')


# @Nyan
# Login option.
# A class in a python file (Nyan.py file - please rename it) e.g. Authenticator = Authenticator(), with methods like:
# Authenticator.log_in()
# Authenticator.recover_password()
# Authenticator.create_new_account()

### TODO: replace this with actual input
is_logged_in = True
user_name = "Tu"
user_id = "abc"
# user_id = "tu@gmail.com"
###

main_app_miscellaneous.say_hello(user_name=user_name)

# Main page with 2 tabs
track_new_meal_tab, user_recommended_intake_history_tab = st.tabs(
    [":green[Track the food I ate] 🍔", "See my nutrition intake history 📖"]
)

# Flow 3 - 12. User wants to get their historical data
logging.info("-----------Running get_user_historical_data()-----------")
user_recommended_intake_history_df = main_app_miscellaneous.show_user_historical_data_result(
    is_logged_in=is_logged_in,
    user_id=user_id,
    layout_position=user_recommended_intake_history_tab
)
logging.info("-----------Finished get_user_input_dish_and_estimate_ingredients.-----------")


# 1. Get dish description from user and estimate its ingredients
logging.info("-----------Running get_user_input_dish_and_estimate_ingredients()-----------")
dish_description = track_new_meal_tab.text_input("What have you eaten today? 😋").strip()
ingredient_df = main_app_miscellaneous.get_user_input_dish_and_estimate_ingredients(
    dish_description=dish_description,
    layout_position=track_new_meal_tab
)

# wait until user input
event = threading.Event()
while not dish_description:
    event.wait()
    event.clear()
logging.info("-----------Finished get_user_input_dish_and_estimate_ingredients.-----------")

# 2-3. Nutrient actual intake
# @Michael @Johnny
    # Ask users' information:
        # age, gender, date
    # I think your methods should be in the same class in the same python file (Michael_Johnny.py file - please rename it).
    # E.g. NutrientMaster = NutrientMaster()
    # NutrientMaster.calculate_recommended_intake_from_database()
    # NutrientMaster.calculate_recommended_intake_using_openapi()


# 3. Check user's log in status
# @Nyan
# TODO: create the a table storing user's personal data: age, gender etc.
# Update this data if there are any changes.


### TODO: replace this with actual input
user_intake_df_temp = pd.DataFrame(
    [
        {
            "user_id": "tu@gmail.com",
            "gender": "female",
            "age": 20,
            "dish_description": "beef burger",
            "nutrient": "Protein",
            "actual_intake": 2,
        },
        {
            "user_id": "tu@gmail.com",
            "gender": "female",
            "age": 20,
            "dish_description": "beef burger",
            "nutrient": "Vitamin A",
            "actual_intake": 3,
        }
    ]
)

###

# 4 + 5. Get user's age + gender
# @Tu
logging.info("----------- Running get_user_personal_data()-----------")
user_personal_data = main_app_miscellaneous.get_user_personal_data(
    is_logged_in=is_logged_in,
    user_id=user_id,
    has_user_intake_df_temp_empty=user_intake_df_temp.empty,
    layout_position=track_new_meal_tab
)
logging.info("-----------Finished get_user_personal_data-----------")

# 6. Join with recommended intake
# Only run when we have user_personal_data
# @Tu
logging.info("-----------Running combine_and_show_users_recommended_intake()-----------")
user_recommended_intake_df = main_app_miscellaneous.combine_and_show_users_recommended_intake(
    user_personal_data=user_personal_data,
    user_intake_df_temp=user_intake_df_temp,
    user_intake_df_temp_name="user_intake_df_temp",
    layout_position=track_new_meal_tab
)
logging.info("-----------Finished combine_and_show_users_recommended_intake-----------")

# 6. @Michael
# Visualize data


# 7. Store data into duckdb
# @Tu
### TODO: replace this with actual input
# is_logged_in = True
user_recommended_intake_df["user_id"] = user_id
###

logging.info("-----------Running get_user_confirmation_and_try_to_save_their_data()-----------")
if not user_recommended_intake_df.empty:
    result = main_app_miscellaneous.get_user_confirmation_and_try_to_save_their_data(
        dish_description=dish_description,
        user_id=user_id,
        is_logged_in=is_logged_in,
        layout_position=track_new_meal_tab
    )
    login_or_create_account = result.get("login_or_create_account")
logging.info("-----------Finished get_user_confirmation_and_try_to_save_their_data-----------")


# 5. Recommend dish.
# @Anika
# A python class in a separate file (Anika.py - Please rename it), containing different methods:
    # E.g. DishRecommender = DishRecommender()
    # DishRecommender.get_user_preference()
    # DishRecommender.recommend_recipe()
# Ask user's preference (diet/ what do you have left in your fridge?)