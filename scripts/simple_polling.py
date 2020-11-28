import time
from loguru import logger

CONFIG = {
    'buy_q': .01, # the low drift percentage to execute a buy
    'sell_q': .01, # the high drift percentage to execute as sell
    'n_buys_more_than_sell': 5, # how many more buys we can have without a sell
    'n_sell_more_than_buy': 5, # how many more sells we can have without a buy
    'buy_portion': .05, # what portion of the entire value to buy at each execution
    'sell_portion': .05, # what portion of the entire value to sell at each execution
    'lb_portion': .5, # lower bound of the portion of value not to be exceeded in sells
    'ub_portion': 1.5, # upper bound of the portion of value not to be exceeded in buys
    'lb_free_fund_portion': .5 # what portion of the entire free fund to buy
}

poll_wait = 5 * 60

def get_instrument_crnt_price(api, name):
    # TODO: change this to retrieve only the given inst price directly from the page.
    return api.get_portfolio_table()['current_price']

def check_and_buy_instrument(api, name, instrument_data, original_free_funds, buy_sell_rec):
    """

    Args:
        api:
        name:
        instrument_data: the data got from the previous poll
        instrument_original_market_value:

    Returns:

    """
    # Check if we have still capacity to buy
    if api.get_bottom_info()['free_fund'] > CONFIG['lb_free_fund_portion'] * original_free_funds:
        # if the price drifted down
        if get_instrument_crnt_price(api, name) < instrument_data['current_price'] * CONFIG['buy_q']:
            # if we have not exhausted our capacity to buy this specific instrument
            if buy_sell_rec[name] < CONFIG['n_buys_more_than_sell']: # TODO: make this smarter?
                api.buy(
                    instrument_data['name'],
                    instrument_data['data_code'],
                    max(instrument_data['market_value'] * CONFIG['buy_portion'], original_free_funds)
                )
                return  True
    return False

def check_and_sell_instrument(api, name, instrument_data, buy_sell_rec):
        """

        Args:
            api:
            name:
            instrument_data: the data got from the previous poll
            instrument_original_market_value:

        Returns:

        """
        # if the price drifted down
        if get_instrument_crnt_price(api, name) < instrument_data['current_price'] * CONFIG['buy_q']:
            # if we have not exhausted our capacity to buy this specific instrument
            if buy_sell_rec[name] < CONFIG['n_sell_more_than_buy']:  # TODO: make this smarter?
                api.sell(
                    instrument_data['name'],
                    instrument_data['data_code'],
                    min(instrument_data['market_value'] * CONFIG['sell_portion'], instrument_data['quantity'])
                )
                return True
        return False

def start_poll(api):
    original_positions = api.get_portfolio_table()
    original_free_funds = api.get_bottom_info()['free_fund']

    portfolio = original_positions
    # following track the number of consecutive buy and sell (e.g. negative -3 means 3 sells more than buys)
    buy_sell_record = {k: 0 for k in original_positions.keys()}
    # sell_record = {k: 0 for k in original_positions.keys()}

    while True:
        for inst_name, inst_data in portfolio.items():
            portfolio = api.get_portfolio_table()
            time.sleep(poll_wait)
            logger.info(f"Checking {inst_name}")

            if check_and_buy_instrument(api, inst_name, inst_data, original_free_funds, buy_sell_record):
                buy_sell_record[inst_name] += 1

            if check_and_sell_instrument(api, inst_name, inst_data, buy_sell_record):
                buy_sell_record[inst_name] -= 1



