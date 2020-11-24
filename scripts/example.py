from trader212_broker.api import Api
import pandas as pd


if __name__ == '__main__':
    USER = ''
    PASS = ''

    api = Api()
    api.launch('./chromedriver')

    api.login(USER, PASS)

    print(
        pd.DataFrame.from_dict(
            api.get_portfolio_table()
        )
    )

    api.buy('Tesla', 'TSLA_US_EQ', .2)

    api.sell('Tesla', 'TSLA_US_EQ', .2)