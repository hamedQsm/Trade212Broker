import time
from loguru import logger

CONFIG = {
    'under_value_prcnt': .01, #
    'over_value_prcnt': .005, #
    'max_buy_threshold': 10000,
    'sell_portion': .1, # what portion to sell once profitable
    'lb_free_fund_portion': .5 # what portion of the entire free fund to buy
}

poll_wait = 5 * 60


def get_instrument_crnt_price(api, name):
    # TODO: change this to retrieve only the given inst price directly from the page.
    inst_data = api.get_portfolio_table()[name]
    return inst_data['market_value']/inst_data['quantity']  # to get the price comparable to market value (in Euro)


def check_and_buy_instrument(api, name, max_buy_quantity):

    # Check if we have still capacity to buy

    instrument_data = api.get_portfolio_table()[name]
    crnt_market_value = instrument_data['market_value']
    payed_value = crnt_market_value - instrument_data['profit']
    return_percent = instrument_data['return_percent']

    # to get the price comparable to market value (in Euro)
    crnt_corrected_price = crnt_market_value/instrument_data['quantity']

    logger.info('{}: profit: {:.3f}%'.format(name, return_percent))

    # if the price drifted down
    if return_percent < -CONFIG['under_value_prcnt']:
        print(type(return_percent))
        print(-CONFIG['under_value_prcnt'])
        # if we have not exhausted our capacity to buy this specific instrument
        buy_quantity = min(
            (crnt_market_value/(1 + CONFIG['under_value_prcnt']) - payed_value)/crnt_corrected_price,
            max_buy_quantity
        )
        logger.debug(f"Buying {buy_quantity} of {name}")
        api.buy(
            name,
            instrument_data['data_code'],
            buy_quantity
        )
        return buy_quantity
    else:
        return 0


def check_and_sell_instrument(api, name):

    instrument_data = api.get_portfolio_table()[name]
    crnt_market_value = instrument_data['market_value']
    return_percent = instrument_data['return_percent']
    crnt_corrected_price = crnt_market_value / instrument_data['quantity']

    # if the price drifted down
    if return_percent > CONFIG['over_value_prcnt']:
        sell_quantity = (crnt_market_value*CONFIG['sell_portion'])/crnt_corrected_price
        api.sell(
            name,
            instrument_data['data_code'],
            sell_quantity
        )
        return sell_quantity
    return 0


def start_poll(api):
    original_positions = api.get_portfolio_table()
    original_free_funds = api.get_bottom_info()['free_funds']

    portfolio = original_positions
    # following track the number of consecutive buy and sell (e.g. negative -3 means 3 sells more than buys)
    # buy_sell_record = {k: 0 for k in original_positions.keys()}
    # sell_record = {k: 0 for k in original_positions.keys()}

    max_to_buy = original_free_funds * CONFIG['lb_free_fund_portion']
    while True:
        for inst_name in portfolio.keys():
            time.sleep(poll_wait)
            logger.info(f"Checking {inst_name}")
            bought_quantity = check_and_buy_instrument(api, inst_name, max_to_buy)
            if bought_quantity > 0:
                max_to_buy -= bought_quantity
                continue

            max_to_buy += check_and_sell_instrument(api, inst_name)




