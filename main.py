import os
import re
import logging
import threading
import streamlit as st
from core.main_app_miscellaneous import *
from core.calculate_nutrient_intake import NutrientMaster
from core.diabetes_assessor import *
from core.telegram_bot import *
from core.dish_recommendation import *
from core.utils import wait_while_condition_is_valid
from streamlit_option_menu import option_menu
from streamlit_extras.row import row


OPENAI_API_KEY = "OPENAI_API_KEY"
OPENAI_CLIENT = OpenAI(
  api_key=os.environ.get(OPENAI_API_KEY),
)
TELEGRAM_BOT_API_KEY_ENV_KEY = "TELEGRAM_BOT_API_KEY"
TELEGRAM_BOT_TOKEN = os.environ.get(TELEGRAM_BOT_API_KEY_ENV_KEY)
DIABETES_MODEL_PATH = "core/ml_models/diabetes_random_forest_model.sav"

main_app_miscellaneous = MainAppMiscellaneous(openai_client=OPENAI_CLIENT)
diabetes_assessor = DiabetesAssessor(model_path=DIABETES_MODEL_PATH)
telegram_bot = TelegramBot(telegram_bot_token=TELEGRAM_BOT_TOKEN)
logging.basicConfig(level=logging.INFO)
logging.root.setLevel(logging.NOTSET)
# st.set_page_config(layout='centered')
st.set_page_config(layout='wide')


# @Nyan
# Login option.
# A class in a python file (Nyan.py file - please rename it) e.g. Authenticator = Authenticator(), with methods like:
# Authenticator.log_in()
# Authenticator.recover_password()
# Authenticator.create_new_account()

### TODO: replace this with actual input
st.session_state['is_logged_in'] = True
st.session_state['user_name'] = "Ardy"
st.session_state['user_id'] = "ardy@uts"
def reset_session_state():
    st.session_state['dish_description'] = None
    st.session_state['ingredient_df'] = None
    st.session_state['confirm_ingredient_weights_button'] = False
    st.session_state['total_nutrients_based_on_food_intake'] = None
    st.session_state['user_personal_data'] = None
    st.session_state['assess_diabetes_risk_button'] = False
    st.session_state['get_intake_history_button'] = False
    st.session_state['user_age_and_gender'] = None  # for diabetes prediction
    st.session_state['has_fruit_and_veggie_intake'] = True
    st.session_state['save_meal_result'] = None
    st.session_state['user_telegram_user_name'] = None
    st.session_state['recommended_recipe'] = None
    st.session_state["sending_telegram_message_result"] = None

# container, grid, row settings
buff1, maincol, buff2 = st.columns([1,8,1])
# buff1, col5, col10, buff2 = st.columns([1,5,5,1])
# my_grid = grid(2, [2, 4, 1], 1, 4, vertical_align="bottom")
# row1 = row(2, vertical_align="center")

# Set the Main title
with maincol:
    original_title = '<h1 style="font-family: monospace; color:#D44A1A; font-size: 75px;">MealMinder </h1>'
    st.markdown(original_title, unsafe_allow_html=True)

# Set the Background image
background_image = """
<style>
[data-testid="stAppViewContainer"] > .main {
    background-image: url("https://i.pinimg.com/originals/57/b5/e2/57b5e2121c57ac65eaff26ef584ecd65.jpg");
    background-size: cover;
    # background-size: 100% 100%;
    # background-size: 100vw 100vh;  # This sets the size to cover 100% of the viewport width and height
    background-position: center;  
    # background-repeat: no-repeat;
}
</style>
"""
st.markdown(background_image, unsafe_allow_html=True)

###
# st.text_input("", placeholder="Streamlit CSS ")
# input_style = """
# <style>
# input[type="text"] {
#     background-color: transparent;
#     color: #a19eae;  // This changes the text color inside the input box
# }
# div[data-baseweb="base-input"] {
#     background-color: transparent !important;
# }
# [data-testid="stAppViewContainer"] {
#     background-color: transparent !important;
# }
# </style>
# """
# st.markdown(input_style, unsafe_allow_html=True)
####

with maincol:
    main_app_miscellaneous.say_hello(user_name=st.session_state['user_name'])
    # intro_message = main_app_miscellaneous.say_hello(user_name=st.session_state['user_name'])

# Main page with 2 tabs
with maincol:
    track_new_meal_tab, user_recommended_intake_history_tab, assess_diabetes_risk_tab = st.tabs(
        ["🍔 Track the food I ate ", "📖 See my nutrition intake history ", "🩺 Assess my diabetes risk "]
)

# 1. Get dish description from user and estimate its ingredients
with track_new_meal_tab:
    estimated_ingredient_container = st.expander(":orange[**1. Today's Meal**]")
    # estimated_ingredient_container = st.container(border=True)
    dish_description = estimated_ingredient_container.text_input("What have you eaten today? 😋", help="Describe your meal taken as best possible.").strip()
    if dish_description != st.session_state.get('dish_description', '###') and dish_description!= '':
        reset_session_state()   # rerun the whole app when user inputs a new dish
        st.session_state['dish_description'] = dish_description

# Flow 3 - 12. User wants to get their historical data
get_intake_history_button = user_recommended_intake_history_tab.button("I want to get my nutrition intake history", type="primary")
if not st.session_state.get('get_intake_history_button') and get_intake_history_button:
    st.session_state['get_intake_history_button'] = True

if st.session_state.get('get_intake_history_button'):
    logging.info("-----------Running get_user_historical_data()-----------")
    selected_date_range = main_app_miscellaneous.select_date_range(layout_position=user_recommended_intake_history_tab)
    user_recommended_intake_history_result = main_app_miscellaneous.show_user_historical_data_result(
        is_logged_in=st.session_state['is_logged_in'],
        user_id=st.session_state['user_id'],
        layout_position=user_recommended_intake_history_tab,
        selected_date_range=selected_date_range
    )
    user_recommended_intake_history_df = user_recommended_intake_history_result.get("value")
    st.session_state['user_recommended_intake_history_df'] = user_recommended_intake_history_df
    logging.info("-----------Finished get_user_historical_data.-----------")


# Diabetes prediction
assess_diabetes_risk_button = assess_diabetes_risk_tab.button("Start assessing my diabetes risk", type="primary")
if not st.session_state.get('assess_diabetes_risk_button') and assess_diabetes_risk_button:
    st.session_state['assess_diabetes_risk_button'] = True


if st.session_state.get('assess_diabetes_risk_button'):
    if st.session_state.get('user_age_and_gender') is None:
        logging.info("----------- Running main_app_miscellaneous.get_user_age_and_gender()-----------")
        user_age_and_gender =  main_app_miscellaneous.get_user_age_and_gender(
            is_logged_in=st.session_state['is_logged_in'],
            user_id=st.session_state['user_id'],
            get_user_age_gender_message="First of all, we need your age 📆 and gender ♀♂ to assess your diabetes risk.",
            layout_position=assess_diabetes_risk_tab
        )
        st.session_state['user_age_and_gender'] = user_age_and_gender
        logging.info("----------- Finished running main_app_miscellaneous.get_user_age_and_gender.-----------")

    has_fruit_and_veggie_intake = diabetes_assessor.get_user_fruit_and_veggie_intake(
        user_id=st.session_state['user_id'],
        layout_position=assess_diabetes_risk_tab
    )
    if has_fruit_and_veggie_intake != st.session_state.get('has_fruit_and_veggie_intake'):
        st.session_state['has_fruit_and_veggie_intake'] = has_fruit_and_veggie_intake

    logging.info("-----------Running make_diabetes_prediction()-----------")
    diabetes_risk_message = diabetes_assessor.make_diabetes_prediction(
        is_logged_in=st.session_state['is_logged_in'],
        user_age_and_gender=st.session_state.get('user_age_and_gender'),
        has_fruit_and_veggie_intake=st.session_state.get('has_fruit_and_veggie_intake'),
        layout_position=assess_diabetes_risk_tab,
    )
    logging.info("-----------Finished running make_diabetes_prediction-----------")

# Main flow
# wait for users' input
wait_while_condition_is_valid((st.session_state.get('dish_description') is None))

if st.session_state.get('ingredient_df') is None:
    logging.info("-----------Running get_user_input_dish_and_estimate_ingredients()-----------")
    ingredient_df = main_app_miscellaneous.get_user_input_dish_and_estimate_ingredients(
        dish_description=st.session_state['dish_description'],
        layout_position=track_new_meal_tab
    )
    st.session_state['ingredient_df'] = ingredient_df
    logging.info("-----------Finished get_user_input_dish_and_estimate_ingredients.-----------")

wait_while_condition_is_valid((st.session_state.get('ingredient_df') is None))

with track_new_meal_tab:
    edited_ingredient_df = main_app_miscellaneous.display_and_let_user_edit_ingredient(
        ingredient_df=st.session_state.get('ingredient_df'),
        layout_position=estimated_ingredient_container
    )

with track_new_meal_tab:
    if st.session_state.get('ingredient_df') is not None:
        estimated_ingredient_container.write("Press continue to get your nutrition estimation...")
        if estimated_ingredient_container.button(label="Continue", key="confirm_ingredient_weights", type="primary"):
            st.session_state['confirm_ingredient_weights_button'] = True

        wait_while_condition_is_valid((not st.session_state.get('confirm_ingredient_weights_button', False)))

# Wait and let user edit their ingredients until user click confirm_ingredient_weights_button
st.session_state['ingredient_df'] = edited_ingredient_df

# # 2-3. Nutrient actual intake
if st.session_state.get('total_nutrients_based_on_food_intake') is None:
    Nutrient = NutrientMaster(openai_client=OPENAI_CLIENT)
    total_nutrients_based_on_food_intake = Nutrient.total_nutrients_based_on_food_intake(
                                            ingredients_from_user=st.session_state['ingredient_df'],
                                            layout_position=track_new_meal_tab
                                        )
    st.session_state['total_nutrients_based_on_food_intake'] = total_nutrients_based_on_food_intake

wait_while_condition_is_valid((st.session_state.get('total_nutrients_based_on_food_intake') is None))

main_app_miscellaneous.display_user_intake_df(
    user_intake_df=st.session_state['total_nutrients_based_on_food_intake'],
    layout_position=track_new_meal_tab
)

# 3. Check user's log in status
# @Nyan
# TODO: create the a table storing user's personal data: age, gender etc.
# Update this data if there are any changes.

wait_while_condition_is_valid((st.session_state.get('total_nutrients_based_on_food_intake') is None))

### TODO: replace this with actual input
user_intake_df_temp = st.session_state['total_nutrients_based_on_food_intake']
user_intake_df_temp["user_id"] = st.session_state['user_id']
###

# 4 + 5. Get user's age + gender
has_user_intake_df_temp_empty = user_intake_df_temp.empty if isinstance(user_intake_df_temp, pd.DataFrame) else True
if st.session_state.get('user_personal_data') is None:
    logging.info("----------- Running get_user_personal_data()-----------")
    user_personal_data = main_app_miscellaneous.get_user_personal_data(
        is_logged_in=st.session_state['is_logged_in'],
        user_id=st.session_state['user_id'],
        has_user_intake_df_temp_empty=has_user_intake_df_temp_empty,   ## handle case total_nutrients_based_on_food_intake is not a DataFrame but a dict
        layout_position=track_new_meal_tab
    )
    st.session_state['user_personal_data'] = user_personal_data
    logging.info("-----------Finished get_user_personal_data-----------")


# 6. Join with recommended intake
# Only run when we have user_personal_data
# @Tu
with track_new_meal_tab:
    nutrient_intake_chart_container = st.expander(":orange[**2. Your Nutrient Intake Today**]")
    # nutrient_intake_chart_container = st.container(border=True)
    logging.info("-----------Running combine_and_show_users_recommended_intake()-----------")
    user_recommended_intake_result = main_app_miscellaneous.combine_and_show_users_recommended_intake(
        user_personal_data=st.session_state['user_personal_data'],
        user_intake_df_temp=user_intake_df_temp,
        user_intake_df_temp_name="user_intake_df_temp",
        layout_position=nutrient_intake_chart_container
    )
    logging.info("-----------Finished combine_and_show_users_recommended_intake-----------")

# # 6. @Michael
# # Visualize data
with track_new_meal_tab:
    # consumuption_date_save_info_container = st.container(border=True)
    consumuption_date_save_info_container = st.expander(":orange[**3. Start Meal Tracking**]")
    meal_record_date = main_app_miscellaneous.get_meal_record_date(
        layout_position=consumuption_date_save_info_container,
        has_user_intake_df_temp_empty=has_user_intake_df_temp_empty
    )
    user_intake_df_temp['meal_record_date'] = meal_record_date

    logging.info("-----------Running get_user_confirmation_and_try_to_save_their_data()-----------")
    if st.session_state.get('save_meal_result') is None:
        save_meal_result = main_app_miscellaneous.get_user_confirmation_and_try_to_save_their_data(
            dish_description=st.session_state['dish_description'],
            user_id=st.session_state['user_id'],
            is_logged_in=st.session_state['is_logged_in'],
            layout_position=consumuption_date_save_info_container,
            has_user_intake_df_temp_empty=has_user_intake_df_temp_empty
        )
        st.session_state['save_meal_result'] = save_meal_result
    logging.info("-----------Finished get_user_confirmation_and_try_to_save_their_data-----------")

# Aggregate user_recommended_intake_df by day
if st.session_state.get('user_recommended_intake_df') is None:
    date_to_filter = main_app_miscellaneous.compare_and_return_the_smaller_date(
        date_input_1=meal_record_date
    )
    user_recommended_intake_from_database_df = main_app_miscellaneous.get_user_historical_data(
        user_id=st.session_state["user_id"],
        selected_date_range=(date_to_filter, date_to_filter)
    )
    st.session_state['user_recommended_intake_df'] = user_recommended_intake_from_database_df

# user_recommended_intake_df = st.session_state['user_recommended_intake_df']

# 5. Recommend dish.
dishrecommend = DishRecommender(openai_client=OPENAI_CLIENT)

logging.info("Retrieving nutrient intake information.")
nutrient_info = dishrecommend.retrieve_nutrient_intake_info(user_recommended_intake_result)
logging.info("Finished collecting the nutrient intake information for the dish recommendation.")

# Asking the user if they want dish recommendation
with track_new_meal_tab:
    # dish_recommendation_preference_container = st.container(border=True)
    dish_recommendation_preference_container = st.expander(":orange[**4. Your Next Dish Preferences**]")
    dish_recommend_user_input = dish_recommendation_preference_container.selectbox("Do you want a dish recommendation?", ["Yes", "No"])
    if not st.session_state.get('dish_recommend_user_input') and dish_recommend_user_input:
        st.session_state['dish_recommend_user_input'] = True
    # If user selected "Yes", calling the dish recommendation function
    if st.session_state.get('dish_recommend_user_input'):

        logging.info("Checking user preferences for cuisine, allergies, if any leftover ingredients.")
        cuisine, allergies, ingredients = dishrecommend.get_user_input(layout_position=dish_recommendation_preference_container)
        logging.info("Finished reading user preferences for the dish recommendation..")

        logging.info("Recommending dish to the user based on the given preferences.")
        if dish_recommendation_preference_container.button("Recommend Dish", type="primary"):
            # dish_recommendation_output_container = st.container(border=True)
            dish_recommendation_output_container = st.expander(":orange[**5. MealMinder's Dish Recommendation**]")
            recommended_dish = dishrecommend.get_dish_recommendation(nutrient_info, cuisine, ingredients, allergies)
            dish_recommendation_output_container.write(recommended_dish)
            st.session_state['recommended_recipe'] = recommended_dish
        logging.info("Finished dish recommendation based on the user preferences.")

    wait_while_condition_is_valid(condition=(st.session_state.get('recommended_recipe') is None))

    if st.session_state.get('recommended_recipe') is not None:
        telegram_container = st.expander(":orange[**6. Dish Receipe Sent To Your Phone With Telegram**]")
        telegram_container.info("""
            If this is your first time with us,
            please search for @meal_minder_bot on Telegram and say hi so that we can reach out to you 😉
        """)
        user_telegram_user_name = telegram_container.text_input("Let us know your Telegram user name to receive this recipe")

        # reset session_state if user inputs another user namse
        if st.session_state.get('user_telegram_user_name') is not None and user_telegram_user_name != "" and user_telegram_user_name != st.session_state.get('user_telegram_user_name'):
            st.session_state['user_telegram_user_name'] = None

        if st.session_state.get('user_telegram_user_name') is None and user_telegram_user_name != "":
            st.session_state['user_telegram_user_name'] = user_telegram_user_name

        if st.session_state.get('user_telegram_user_name') is not None:
            print("-----------Running send_message_to_user_name-----------")
            if st.session_state.get("sending_telegram_message_result") is None:
                sending_message_result = telegram_bot.send_message_to_user_name(
                    user_name=st.session_state.get('user_telegram_user_name'),
                    message=st.session_state.get('recommended_recipe'),
                    layout_position=dish_recommendation_preference_container
                )
                if sending_message_result.get("status") == 200:
                    st.session_state["sending_telegram_message_result"] = sending_message_result

            print("-----------Finished send_message_to_user_name-----------")

