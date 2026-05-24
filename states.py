from aiogram.fsm.state import State, StatesGroup


class PaymentStates(StatesGroup):
    choosing_package = State()
    waiting_receipt = State()


class PresentationStates(StatesGroup):
    topic = State()
    slides_count = State()
    language = State()
    style = State()
    color = State()
    output_type = State()
    confirming = State()


class AdminStates(StatesGroup):
    # Coin management
    enter_user_id_add = State()
    enter_coins_add = State()
    enter_user_id_remove = State()
    enter_coins_remove = State()

    # Broadcast
    broadcast_message = State()

    # Package management
    package_edit_id = State()
    package_edit_field = State()
    package_edit_value = State()
    package_new_coins = State()
    package_new_price = State()

    # Card settings
    card_number_edit = State()
    card_owner_edit = State()

    # Block user
    block_user_id = State()
